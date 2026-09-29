from importlib import import_module

from PySide6.QtCore import Qt
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

    def __init__(self):
        super().__init__()

        self.setWindowTitle("HealthSync AI")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)

        self.navigation_buttons = []
        self.loaded_pages = {}

        self.setup_ui()
        self.apply_styles()

        self.show_page(0)

    # ---------------------------------------------------------
    # Main UI
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Sidebar
    # ---------------------------------------------------------

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
            button.setCursor(Qt.CursorShape.PointingHandCursor)

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

        version = QLabel("HealthSync AI - Phase 1")
        version.setObjectName("version_label")

        layout.addWidget(version)

        return sidebar

    # ---------------------------------------------------------
    # Content Area
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Page Loading
    # ---------------------------------------------------------

    def load_page(self, index):
        if index in self.loaded_pages:
            return self.loaded_pages[index]

        if index not in self.PAGE_DEFINITIONS:
            raise ValueError(f"Invalid page index: {index}")

        _, module_name, class_name = self.PAGE_DEFINITIONS[index]

        module = import_module(module_name)
        page_class = getattr(module, class_name)

        page = page_class()

        self.loaded_pages[index] = page
        self.pages.addWidget(page)

        return page

    # ---------------------------------------------------------
    # Navigation
    # ---------------------------------------------------------

    def show_page(self, index):
        try:
            page = self.load_page(index)

            self.pages.setCurrentWidget(page)

            for button_index, button in enumerate(
                self.navigation_buttons
            ):
                button.setProperty(
                    "active",
                    button_index == index,
                )

                button.style().unpolish(button)
                button.style().polish(button)

            self.system_status.setText("System Ready")

        except Exception as error:
            self.system_status.setText("Page Load Error")
            print(
                f"Failed to load page {index}: "
                f"{type(error).__name__}: {error}"
            )

    # ---------------------------------------------------------
    # Styling
    # ---------------------------------------------------------

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

