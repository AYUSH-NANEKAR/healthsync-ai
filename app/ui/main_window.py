from importlib import import_module

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    logout_requested = Signal()

    PAGE_DEFINITIONS = {
        0: ("Dashboard", "app.ui.dashboard", "DashboardPage"),
        1: ("My Health", "app.ui.my_health", "MyHealthPage"),
        2: ("Devices", "app.ui.devices", "DevicesPage"),
        3: ("AI Analysis", "app.ui.ai_analysis", "AIAnalysisPage"),
        4: ("Emergency", "app.ui.emergency", "EmergencyPage"),
        5: ("Hospitals", "app.ui.hospitals", "HospitalsPage"),
        6: (
            "Outbreak Analysis",
            "app.ui.outbreak_analysis",
            "OutbreakAnalysisPage",
        ),
    }

    # Dashboard/navigation page names -> page indexes
    NAVIGATION_MAP = {
        "dashboard": 0,
        "my_health": 1,
        "devices": 2,
        "ai_analysis": 3,
        "emergency": 4,
        "hospitals": 5,
        "outbreak_analysis": 6,
    }

    def __init__(self, user_id: int, ble_service=None):
        super().__init__()

        # ---------------------------------------------------------
        # Authenticated user context
        # ---------------------------------------------------------
        # Every user-specific page should receive this ID.
        # This prevents health/device/emergency data from being
        # accidentally shared between different accounts.
        self.user_id = user_id

        # Shared BLE service created by main.py.
        self.ble_service = ble_service

        self.setWindowTitle("HealthSync AI")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)

        # Navigation/page state
        self.navigation_buttons = []
        self.loaded_pages = {}

        self.setup_ui()
        self.apply_styles()

        # Load Dashboard first.
        self.show_page(0)

    # =========================================================
    # MAIN UI
    # =========================================================

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = self.create_sidebar()
        content_area = self.create_content_area()

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content_area, 1)

    # =========================================================
    # SIDEBAR
    # =========================================================

    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 24, 18, 20)
        layout.setSpacing(8)

        logo = QLabel("HealthSync AI")
        logo.setObjectName("logo")

        subtitle = QLabel("AI-Powered Health & IoT")
        subtitle.setObjectName("sidebar_subtitle")

        layout.addWidget(logo)
        layout.addWidget(subtitle)
        layout.addSpacing(24)

        for index, definition in self.PAGE_DEFINITIONS.items():
            page_name = definition[0]

            button = QPushButton(page_name)
            button.setObjectName("nav_button")
            button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )

            button.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )

            button.clicked.connect(
                lambda checked=False, page_index=index:
                self.show_page(page_index)
            )

            self.navigation_buttons.append(button)
            layout.addWidget(button)

        layout.addStretch()

        logout_button = QPushButton("Logout")
        logout_button.setObjectName("logout_button")
        logout_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        logout_button.clicked.connect(
            self.logout_requested.emit
        )

        layout.addWidget(logout_button)

        version = QLabel("HealthSync AI - Phase 1")
        version.setObjectName("version_label")

        layout.addWidget(version)

        return sidebar

    # =========================================================
    # CONTENT AREA
    # =========================================================

    def create_content_area(self):
        content = QWidget()

        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(18)

        header = self.create_header()

        self.pages = QStackedWidget()
        self.pages.setObjectName("page_container")

        layout.addWidget(header)
        layout.addWidget(self.pages, 1)

        return content

    def create_header(self):
        header = QFrame()
        header.setObjectName("header")

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 14, 20, 14)

        title = QLabel("HealthSync AI")
        title.setObjectName("header_title")

        self.system_status = QLabel("System Ready")
        self.system_status.setObjectName("system_status")

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self.system_status)

        return header

    # =========================================================
    # PAGE LOADING
    # =========================================================

    def load_page(self, index):
        """
        Load a page only once.

        User-specific pages receive the authenticated user_id.

        Current page responsibilities:
        - Dashboard -> user_id + BLE service
        - My Health -> user_id
        - Devices -> user_id + BLE service
        - Other pages -> existing constructors

        Pages are cached after their first creation so that
        navigation does not unnecessarily recreate them.
        """

        if index in self.loaded_pages:
            return self.loaded_pages[index]

        if index not in self.PAGE_DEFINITIONS:
            raise ValueError(
                f"Invalid page index: {index}"
            )

        _, module_name, class_name = (
            self.PAGE_DEFINITIONS[index]
        )

        module = import_module(module_name)

        page_class = getattr(
            module,
            class_name,
        )

        # -----------------------------------------------------
        # Dashboard
        # -----------------------------------------------------

        if index == 0:

            page = page_class(
                user_id=self.user_id
            )

            if self.ble_service is not None:
                if hasattr(
                    page,
                    "set_ble_service",
                ):
                    page.set_ble_service(
                        self.ble_service
                    )

            if hasattr(
                page,
                "navigation_requested",
            ):
                page.navigation_requested.connect(
                    self.handle_page_navigation
                )

        # -----------------------------------------------------
        # My Health
        # -----------------------------------------------------

        elif index == 1:

            # MyHealthPage is user-specific.
            #
            # The page uses this authenticated user_id to:
            # - load the correct health profile
            # - save the correct health profile
            # - prevent one user's health data from being
            #   displayed for another logged-in user
            page = page_class(
                user_id=self.user_id
            )

        # -----------------------------------------------------
        # Devices
        # -----------------------------------------------------

        elif index == 2:

            page = page_class(
                user_id=self.user_id
            )

            if self.ble_service is not None:
                if hasattr(
                    page,
                    "set_ble_service",
                ):
                    page.set_ble_service(
                        self.ble_service
                    )

        # -----------------------------------------------------
        # Other pages
        # -----------------------------------------------------

        else:

            page = page_class()

        # -----------------------------------------------------
        # Cache and register page
        # -----------------------------------------------------

        self.loaded_pages[index] = page

        self.pages.addWidget(page)

        return page

    # =========================================================
    # DASHBOARD -> MAIN NAVIGATION
    # =========================================================

    def handle_page_navigation(
        self,
        page_name: str,
    ):
        """
        Handle navigation requests emitted by Dashboard.
        """

        if not page_name:
            return

        page_key = str(
            page_name
        ).strip().lower()

        page_index = self.NAVIGATION_MAP.get(
            page_key
        )

        if page_index is None:
            print(
                f"[NAVIGATION] Unknown page: "
                f"{page_name}"
            )
            return

        self.show_page(
            page_index
        )

    # =========================================================
    # NAVIGATION
    # =========================================================

    def show_page(self, index):
        try:

            page = self.load_page(
                index
            )

            self.pages.setCurrentWidget(
                page
            )

            for button_index, button in enumerate(
                self.navigation_buttons
            ):

                button.setProperty(
                    "active",
                    button_index == index,
                )

                button.style().unpolish(
                    button
                )

                button.style().polish(
                    button
                )

            self.system_status.setText(
                "System Ready"
            )

        except Exception as error:

            self.system_status.setText(
                "Page Load Error"
            )

            print(
                f"Failed to load page {index}: "
                f"{type(error).__name__}: {error}"
            )

    # =========================================================
    # STYLING
    # =========================================================

    def apply_styles(self):

        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #07131F;
            }

            QWidget {
                color: #FFFFFF;
                font-family: "Segoe UI";
                font-size: 14px;
            }

            #sidebar {
                background-color: #07131F;
                border-right: 1px solid #173044;
            }

            #logo {
                color: #FFFFFF;
                font-size: 22px;
                font-weight: 700;
            }

            #sidebar_subtitle {
                color: #90C2E7;
                font-size: 11px;
            }

            #nav_button {
                background-color: transparent;
                color: #90C2E7;
                border: none;
                border-radius: 10px;
                padding: 12px 14px;
                text-align: left;
            }

            #nav_button:hover {
                background-color: #0B1D2A;
                color: #FFFFFF;
            }

            #nav_button[active="true"] {
                background-color: #00A9A5;
                color: #FFFFFF;
                font-weight: 600;
            }

            #logout_button {
                background-color: transparent;
                color: #90C2E7;
                border: 1px solid #29465A;
                border-radius: 10px;
                padding: 10px 14px;
                text-align: left;
            }

            #logout_button:hover {
                background-color: #0B1D2A;
                color: #FFFFFF;
            }

            #version_label {
                color: #55758C;
                font-size: 11px;
            }

            #header {
                background-color: #0B1D2A;
                border: 1px solid #173044;
                border-radius: 14px;
            }

            #header_title {
                color: #FFFFFF;
                font-size: 18px;
                font-weight: 600;
            }

            #system_status {
                color: #00A9A5;
                font-size: 13px;
                font-weight: 600;
            }

            #page_title {
                color: #FFFFFF;
                font-size: 28px;
                font-weight: 700;
            }

            #page_description {
                color: #90C2E7;
                font-size: 14px;
            }
            """
        )