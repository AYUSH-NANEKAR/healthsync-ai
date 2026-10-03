from datetime import datetime
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import threading

from PySide6.QtCore import (
    Qt,
    QTimer,
    Signal,
    QRectF,
    QPointF,
    QObject,
)
from PySide6.QtGui import (
    QPainter,
    QPen,
    QBrush,
    QFont,
)
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QScrollArea,
    QSizePolicy,
)

from app.database.connection import get_connection


# ============================================================
# REVERSE GEOCODING WORKER
# ============================================================

class LocationGeocoder(QObject):

    result_ready = Signal(
        object,
        float,
        float,
    )

    def lookup(
        self,
        latitude,
        longitude,
    ):

        def worker():

            place_name = None

            try:

                query = urlencode(
                    {
                        "lat": latitude,
                        "lon": longitude,
                        "format": "jsonv2",
                        "zoom": 18,
                        "addressdetails": 1,
                    }
                )

                url = (
                    "https://nominatim.openstreetmap.org/"
                    f"reverse?{query}"
                )

                request = Request(
                    url,
                    headers={
                        "User-Agent":
                        "HealthSyncAI/1.0 "
                        "(health monitoring project)"
                    },
                )

                with urlopen(
                    request,
                    timeout=8,
                ) as response:

                    data = json.loads(
                        response.read().decode(
                            "utf-8"
                        )
                    )

                address = data.get(
                    "address",
                    {}
                )

                # ------------------------------------------------
                # Locality
                # ------------------------------------------------

                locality = (
                    address.get("city")
                    or address.get("town")
                    or address.get("village")
                    or address.get("municipality")
                    or address.get("suburb")
                    or address.get("city_district")
                    or address.get("neighbourhood")
                )

                # ------------------------------------------------
                # District
                # ------------------------------------------------

                district = (
                    address.get("county")
                    or address.get("state_district")
                )

                # ------------------------------------------------
                # State
                # ------------------------------------------------

                state = address.get(
                    "state"
                )

                # ------------------------------------------------
                # Build readable name
                # ------------------------------------------------

                if locality and district:

                    if (
                        locality.strip().lower()
                        ==
                        district.strip().lower()
                    ):

                        place_name = (
                            locality.strip()
                        )

                    else:

                        place_name = (
                            f"{locality.strip()}, "
                            f"{district.strip()}"
                        )

                elif locality and state:

                    place_name = (
                        f"{locality.strip()}, "
                        f"{state.strip()}"
                    )

                elif locality:

                    place_name = (
                        locality.strip()
                    )

                elif district and state:

                    place_name = (
                        f"{district.strip()}, "
                        f"{state.strip()}"
                    )

                elif district:

                    place_name = (
                        district.strip()
                    )

                elif state:

                    place_name = (
                        state.strip()
                    )

                else:

                    display_name = data.get(
                        "display_name"
                    )

                    if display_name:

                        parts = [
                            part.strip()
                            for part in
                            display_name.split(",")
                        ]

                        if parts:

                            place_name = ", ".join(
                                parts[:3]
                            )

            except Exception as error:

                print(
                    "[LOCATION] "
                    f"Reverse geocoding failed: "
                    f"{error}"
                )

                place_name = None

            # ----------------------------------------------------
            # IMPORTANT:
            #
            # Do NOT use QTimer.singleShot() here.
            #
            # The worker is a normal Python thread.
            # Send the result through a Qt signal instead.
            # ----------------------------------------------------

            self.result_ready.emit(
                place_name,
                float(latitude),
                float(longitude),
            )

        thread = threading.Thread(
            target=worker,
            daemon=True,
        )

        thread.start()


# ============================================================
# HEART RATE GRAPH
# ============================================================

class HeartRateGraph(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.values = []

        self.setMinimumHeight(
            230
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

    def set_values(
        self,
        values,
    ):

        self.values = []

        for value in values:

            try:

                self.values.append(
                    float(value)
                )

            except (
                TypeError,
                ValueError,
            ):

                continue

        self.update()

    def paintEvent(
        self,
        event,
    ):

        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        rect = self.rect()

        painter.fillRect(
            rect,
            QBrush(
                Qt.GlobalColor.transparent
            ),
        )

        left = 45
        right = 18
        top = 18
        bottom = 32

        graph_width = max(
            1,
            rect.width()
            - left
            - right,
        )

        graph_height = max(
            1,
            rect.height()
            - top
            - bottom,
        )

        graph_rect = QRectF(
            left,
            top,
            graph_width,
            graph_height,
        )

        if len(self.values) < 2:

            painter.setPen(
                QPen(
                    self.palette().text()
                )
            )

            painter.setFont(
                QFont(
                    "Segoe UI",
                    11,
                )
            )

            painter.drawText(
                graph_rect,
                Qt.AlignmentFlag.AlignCenter,
                "Waiting for heart-rate data...",
            )

            return

        minimum = min(
            self.values
        )

        maximum = max(
            self.values
        )

        if minimum == maximum:

            minimum -= 5
            maximum += 5

        padding = max(
            5,
            (maximum - minimum)
            * 0.15,
        )

        minimum -= padding
        maximum += padding

        grid_pen = QPen(
            self._color(
                "#173044"
            )
        )

        grid_pen.setWidth(
            1
        )

        painter.setPen(
            grid_pen
        )

        horizontal_lines = 4

        for index in range(
            horizontal_lines + 1
        ):

            ratio = (
                index
                /
                horizontal_lines
            )

            y = (
                graph_rect.top()
                +
                ratio
                *
                graph_rect.height()
            )

            painter.drawLine(
                QPointF(
                    graph_rect.left(),
                    y,
                ),
                QPointF(
                    graph_rect.right(),
                    y,
                ),
            )

            value = (
                maximum
                -
                ratio
                *
                (
                    maximum
                    -
                    minimum
                )
            )

            painter.setPen(
                QPen(
                    self._color(
                        "#648398"
                    )
                )
            )

            painter.drawText(
                QRectF(
                    0,
                    y - 10,
                    40,
                    20,
                ),
                Qt.AlignmentFlag.AlignRight
                |
                Qt.AlignmentFlag.AlignVCenter,
                f"{value:.0f}",
            )

            painter.setPen(
                grid_pen
            )

        line_pen = QPen(
            self._color(
                "#00A9A5"
            )
        )

        line_pen.setWidth(
            3
        )

        painter.setPen(
            line_pen
        )

        points = []

        count = len(
            self.values
        )

        for index, value in enumerate(
            self.values
        ):

            if count == 1:

                x = (
                    graph_rect
                    .center()
                    .x()
                )

            else:

                x = (
                    graph_rect.left()
                    +
                    (
                        index
                        /
                        (count - 1)
                    )
                    *
                    graph_rect.width()
                )

            normalized = (
                value
                -
                minimum
            ) / (
                maximum
                -
                minimum
            )

            y = (
                graph_rect.bottom()
                -
                normalized
                *
                graph_rect.height()
            )

            points.append(
                QPointF(
                    x,
                    y,
                )
            )

        for index in range(
            len(points) - 1
        ):

            painter.drawLine(
                points[index],
                points[index + 1],
            )

        if points:

            current = points[-1]

            painter.setBrush(
                QBrush(
                    self._color(
                        "#00A9A5"
                    )
                )
            )

            painter.setPen(
                QPen(
                    self._color(
                        "#FFFFFF"
                    ),
                    2,
                )
            )

            painter.drawEllipse(
                current,
                5,
                5,
            )

    @staticmethod
    def _color(
        value,
    ):

        from PySide6.QtGui import QColor

        return QColor(
            value
        )


# ============================================================
# DASHBOARD
# ============================================================

class DashboardPage(QWidget):

    navigation_requested = Signal(
        str
    )

    def __init__(
        self,
        user_id: int,
    ):

        super().__init__()

        self.user_id = user_id

        self.refresh_interval_ms = 3000

        self.latest_vital = None
        self.latest_activity = None
        self.latest_device = None
        self.latest_location = None

        # --------------------------------------------------------
        # Location reverse-geocoding state
        # --------------------------------------------------------

        self.last_geocoded_latitude = None
        self.last_geocoded_longitude = None

        self.location_lookup_running = False

        # --------------------------------------------------------
        # Qt-safe reverse geocoder
        # --------------------------------------------------------

        self.location_geocoder = (
            LocationGeocoder()
        )

        self.location_geocoder.result_ready.connect(
            self.apply_geocoded_location
        )

        self.build_ui()

        self.load_dashboard_data()

        self.refresh_timer = QTimer(
            self
        )

        self.refresh_timer.setInterval(
            self.refresh_interval_ms
        )

        self.refresh_timer.timeout.connect(
            self.load_dashboard_data
        )

        self.refresh_timer.start()

    # ============================================================
    # UI
    # ============================================================

    def build_ui(self):

        root_layout = QVBoxLayout(
            self
        )

        root_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        root_layout.setSpacing(
            0
        )

        scroll_area = QScrollArea()

        scroll_area.setObjectName(
            "dashboard_scroll"
        )

        scroll_area.setWidgetResizable(
            True
        )

        scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        content = QWidget()

        content.setObjectName(
            "dashboard_content"
        )

        content_layout = QVBoxLayout(
            content
        )

        content_layout.setContentsMargins(
            10,
            8,
            10,
            35,
        )

        content_layout.setSpacing(
            20
        )

        # --------------------------------------------------------
        # Welcome
        # --------------------------------------------------------

        header = QHBoxLayout()

        heading_layout = QVBoxLayout()

        heading_layout.setSpacing(
            5
        )

        self.welcome_label = QLabel(
            "Hello"
        )

        self.welcome_label.setObjectName(
            "welcome_title"
        )

        self.subtitle_label = QLabel(
            "Your health overview and real-time monitoring."
        )

        self.subtitle_label.setObjectName(
            "page_description"
        )

        heading_layout.addWidget(
            self.welcome_label
        )

        heading_layout.addWidget(
            self.subtitle_label
        )

        header.addLayout(
            heading_layout
        )

        header.addStretch()

        self.monitoring_label = QLabel(
            "●  MONITORING"
        )

        self.monitoring_label.setObjectName(
            "monitoring_status"
        )

        header.addWidget(
            self.monitoring_label,
            alignment=Qt.AlignmentFlag.AlignTop,
        )

        content_layout.addLayout(
            header
        )

        # --------------------------------------------------------
        # Health status
        # --------------------------------------------------------

        content_layout.addWidget(
            self.create_health_status_card()
        )

        # --------------------------------------------------------
        # Current Health
        # --------------------------------------------------------

        content_layout.addLayout(
            self.create_section_header(
                "Current Health",
                "Latest health measurements received from your HealthSync device.",
            )
        )

        primary_grid = QGridLayout()

        primary_grid.setSpacing(
            12
        )

        self.heart_rate_card = (
            self.create_metric_card(
                "HEART RATE",
                "-- BPM",
                "Waiting for data",
            )
        )

        self.spo2_card = (
            self.create_metric_card(
                "SpO₂",
                "-- %",
                "Waiting for data",
            )
        )

        self.temperature_card = (
            self.create_metric_card(
                "TEMPERATURE",
                "-- °C",
                "Waiting for data",
            )
        )

        self.blood_pressure_card = (
            self.create_metric_card(
                "BLOOD PRESSURE",
                "-- / --",
                "Waiting for data",
            )
        )

        primary_cards = [
            self.heart_rate_card,
            self.spo2_card,
            self.temperature_card,
            self.blood_pressure_card,
        ]

        for index, card in enumerate(
            primary_cards
        ):

            row = index // 2
            column = index % 2

            primary_grid.addWidget(
                card,
                row,
                column,
            )

        content_layout.addLayout(
            primary_grid
        )

        # --------------------------------------------------------
        # Activity
        # --------------------------------------------------------

        content_layout.addLayout(
            self.create_section_header(
                "Today's Activity",
                "Movement, steps, distance, calories and active time collected by your device.",
            )
        )

        content_layout.addWidget(
            self.create_activity_card()
        )

        # --------------------------------------------------------
        # Graph BELOW Activity
        # --------------------------------------------------------

        content_layout.addWidget(
            self.create_graph_card()
        )

        # --------------------------------------------------------
        # Device
        # --------------------------------------------------------

        content_layout.addLayout(
            self.create_section_header(
                "Device",
                "Current HealthSync IoT connection status.",
            )
        )

        content_layout.addWidget(
            self.create_device_card()
        )

        # --------------------------------------------------------
        # Location
        # --------------------------------------------------------

        content_layout.addLayout(
            self.create_section_header(
                "Location",
                "Latest location received from the connected device.",
            )
        )

        content_layout.addWidget(
            self.create_location_card()
        )

        # --------------------------------------------------------
        # Quick Access
        # --------------------------------------------------------

        content_layout.addLayout(
            self.create_section_header(
                "Quick Access",
                "Open another HealthSync module.",
            )
        )

        actions = QHBoxLayout()

        actions.setSpacing(
            10
        )

        actions.addWidget(
            self.create_navigation_button(
                "View Health History",
                "my_health",
            )
        )

        actions.addWidget(
            self.create_navigation_button(
                "Manage Device",
                "devices",
            )
        )

        actions.addWidget(
            self.create_navigation_button(
                "AI Analysis",
                "ai_analysis",
            )
        )

        actions.addWidget(
            self.create_navigation_button(
                "Emergency",
                "emergency",
            )
        )

        content_layout.addLayout(
            actions
        )

        content_layout.addStretch()

        scroll_area.setWidget(
            content
        )

        root_layout.addWidget(
            scroll_area
        )

        self.apply_page_styles()

    # ============================================================
    # HEALTH STATUS CARD
    # ============================================================

    def create_health_status_card(
        self
    ):

        card = QFrame()

        card.setObjectName(
            "health_status_card"
        )

        layout = QVBoxLayout(
            card
        )

        layout.setContentsMargins(
            22,
            19,
            22,
            19,
        )

        layout.setSpacing(
            13
        )

        header = QHBoxLayout()

        title = QLabel(
            "HEALTH MONITORING"
        )

        title.setObjectName(
            "card_overline"
        )

        header.addWidget(
            title
        )

        header.addStretch()

        self.health_status_time = QLabel(
            "Last update: --"
        )

        self.health_status_time.setObjectName(
            "status_time"
        )

        header.addWidget(
            self.health_status_time
        )

        layout.addLayout(
            header
        )

        status_row = QHBoxLayout()

        status_row.setSpacing(
            14
        )

        self.health_status_indicator = QLabel(
            "●"
        )

        self.health_status_indicator.setObjectName(
            "health_indicator"
        )

        self.health_status_value = QLabel(
            "Waiting for health data"
        )

        self.health_status_value.setObjectName(
            "health_status_value"
        )

        status_text = QLabel(
            "Continuous monitoring is active. "
            "HealthSync displays the latest available readings."
        )

        status_text.setObjectName(
            "health_status_description"
        )

        status_text.setWordWrap(
            True
        )

        status_row.addWidget(
            self.health_status_indicator
        )

        status_row.addWidget(
            self.health_status_value
        )

        status_row.addWidget(
            status_text,
            1,
        )

        layout.addLayout(
            status_row
        )

        return card

    # ============================================================
    # SECTION HEADER
    # ============================================================

    def create_section_header(
        self,
        title_text,
        description_text,
    ):

        layout = QVBoxLayout()

        layout.setSpacing(
            3
        )

        title = QLabel(
            title_text
        )

        title.setObjectName(
            "section_title"
        )

        description = QLabel(
            description_text
        )

        description.setObjectName(
            "section_description"
        )

        description.setWordWrap(
            True
        )

        layout.addWidget(
            title
        )

        layout.addWidget(
            description
        )

        return layout

    # ============================================================
    # METRIC CARD
    # ============================================================

    def create_metric_card(
        self,
        title_text,
        value_text,
        status_text,
    ):

        card = QFrame()

        card.setObjectName(
            "metric_card"
        )

        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        card.setMinimumHeight(
            125
        )

        layout = QVBoxLayout(
            card
        )

        layout.setContentsMargins(
            17,
            15,
            17,
            15,
        )

        layout.setSpacing(
            7
        )

        title = QLabel(
            title_text
        )

        title.setObjectName(
            "metric_title"
        )

        value = QLabel(
            value_text
        )

        value.setObjectName(
            "metric_value"
        )

        status = QLabel(
            status_text
        )

        status.setObjectName(
            "metric_status"
        )

        status.setWordWrap(
            True
        )

        layout.addWidget(
            title
        )

        layout.addWidget(
            value
        )

        layout.addWidget(
            status
        )

        layout.addStretch()

        card.value_label = value
        card.status_label = status

        return card

    # ============================================================
    # ACTIVITY CARD
    # ============================================================

    def create_activity_card(
        self
    ):

        card = QFrame()

        card.setObjectName(
            "activity_card"
        )

        layout = QHBoxLayout(
            card
        )

        layout.setContentsMargins(
            16,
            16,
            16,
            16,
        )

        layout.setSpacing(
            10
        )

        self.movement_value = (
            self.create_info_block(
                layout,
                "MOVEMENT",
                "--",
            )
        )

        self.steps_value = (
            self.create_info_block(
                layout,
                "STEPS",
                "--",
            )
        )

        self.distance_value = (
            self.create_info_block(
                layout,
                "DISTANCE",
                "-- km",
            )
        )

        self.activity_calories_value = (
            self.create_info_block(
                layout,
                "CALORIES",
                "-- kcal",
            )
        )

        self.active_time_value = (
            self.create_info_block(
                layout,
                "ACTIVE TIME",
                "--",
            )
        )

        return card

    # ============================================================
    # GRAPH CARD
    # ============================================================

    def create_graph_card(
        self
    ):

        card = QFrame()

        card.setObjectName(
            "graph_card"
        )

        layout = QVBoxLayout(
            card
        )

        layout.setContentsMargins(
            20,
            18,
            20,
            15,
        )

        layout.setSpacing(
            10
        )

        header = QHBoxLayout()

        heading = QVBoxLayout()

        heading.setSpacing(
            3
        )

        title = QLabel(
            "Heart Rate"
        )

        title.setObjectName(
            "section_title"
        )

        description = QLabel(
            "Recent heart-rate readings from continuous monitoring."
        )

        description.setObjectName(
            "section_description"
        )

        heading.addWidget(
            title
        )

        heading.addWidget(
            description
        )

        header.addLayout(
            heading
        )

        header.addStretch()

        self.graph_current = QLabel(
            "-- BPM"
        )

        self.graph_current.setObjectName(
            "graph_current"
        )

        header.addWidget(
            self.graph_current,
            alignment=Qt.AlignmentFlag.AlignTop,
        )

        layout.addLayout(
            header
        )

        self.heart_rate_graph = (
            HeartRateGraph()
        )

        layout.addWidget(
            self.heart_rate_graph
        )

        return card

    # ============================================================
    # DEVICE CARD
    # ============================================================

    def create_device_card(
        self
    ):

        card = QFrame()

        card.setObjectName(
            "device_card"
        )

        layout = QHBoxLayout(
            card
        )

        layout.setContentsMargins(
            18,
            16,
            18,
            16,
        )

        layout.setSpacing(
            18
        )

        icon = QLabel(
            "◉"
        )

        icon.setObjectName(
            "device_icon"
        )

        icon.setFixedWidth(
            30
        )

        layout.addWidget(
            icon
        )

        information = QVBoxLayout()

        information.setSpacing(
            4
        )

        self.device_name_label = QLabel(
            "No device connected"
        )

        self.device_name_label.setObjectName(
            "device_name"
        )

        self.device_type_label = QLabel(
            "Waiting for a HealthSync device..."
        )

        self.device_type_label.setObjectName(
            "device_details"
        )

        information.addWidget(
            self.device_name_label
        )

        information.addWidget(
            self.device_type_label
        )

        layout.addLayout(
            information
        )

        layout.addStretch()

        stats = QHBoxLayout()

        stats.setSpacing(
            10
        )

        self.device_battery_value = (
            self.create_device_stat(
                stats,
                "BATTERY",
                "--",
            )
        )

        self.device_connection_value = (
            self.create_device_stat(
                stats,
                "CONNECTION",
                "--",
            )
        )

        self.device_updated_value = (
            self.create_device_stat(
                stats,
                "LAST UPDATE",
                "--",
            )
        )

        layout.addLayout(
            stats
        )

        return card

    # ============================================================
    # LOCATION CARD
    # ============================================================

    def create_location_card(
        self
    ):

        card = QFrame()

        card.setObjectName(
            "location_card"
        )

        layout = QHBoxLayout(
            card
        )

        layout.setContentsMargins(
            18,
            15,
            18,
            15,
        )

        layout.setSpacing(
            15
        )

        icon = QLabel(
            "⌖"
        )

        icon.setObjectName(
            "location_icon"
        )

        icon.setFixedWidth(
            30
        )

        layout.addWidget(
            icon
        )

        information = QVBoxLayout()

        information.setSpacing(
            4
        )

        self.location_value = QLabel(
            "Location unavailable"
        )

        self.location_value.setObjectName(
            "location_value"
        )

        self.location_coordinates = QLabel(
            "Waiting for location data..."
        )

        self.location_coordinates.setObjectName(
            "location_coordinates"
        )

        information.addWidget(
            self.location_value
        )

        information.addWidget(
            self.location_coordinates
        )

        layout.addLayout(
            information
        )

        layout.addStretch()

        self.location_updated = QLabel(
            "--"
        )

        self.location_updated.setObjectName(
            "location_updated"
        )

        layout.addWidget(
            self.location_updated
        )

        return card

    # ============================================================
    # ACTIVITY INFO BLOCK
    # ============================================================

    def create_info_block(
        self,
        parent_layout,
        title_text,
        value_text,
    ):

        card = QFrame()

        card.setObjectName(
            "activity_stat"
        )

        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        card_layout = QVBoxLayout(
            card
        )

        card_layout.setContentsMargins(
            14,
            12,
            14,
            12,
        )

        card_layout.setSpacing(
            5
        )

        title = QLabel(
            title_text
        )

        title.setObjectName(
            "activity_stat_title"
        )

        value = QLabel(
            value_text
        )

        value.setObjectName(
            "activity_stat_value"
        )

        card_layout.addWidget(
            title
        )

        card_layout.addWidget(
            value
        )

        parent_layout.addWidget(
            card,
            1,
        )

        return value

    # ============================================================
    # DEVICE STAT
    # ============================================================

    def create_device_stat(
        self,
        parent_layout,
        title_text,
        value_text,
    ):

        container = QVBoxLayout()

        container.setSpacing(
            4
        )

        title = QLabel(
            title_text
        )

        title.setObjectName(
            "device_stat_title"
        )

        value = QLabel(
            value_text
        )

        value.setObjectName(
            "device_stat_value"
        )

        container.addWidget(
            title
        )

        container.addWidget(
            value
        )

        parent_layout.addLayout(
            container
        )

        return value

    # ============================================================
    # NAVIGATION BUTTON
    # ============================================================

    def create_navigation_button(
        self,
        text,
        page_name,
    ):

        button = QPushButton(
            text
        )

        button.setObjectName(
            "secondary_button"
        )

        button.setMinimumHeight(
            40
        )

        button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        button.clicked.connect(
            lambda checked=False,
            page=page_name:
            self.navigation_requested.emit(
                page
            )
        )

        return button

    # ============================================================
    # DATABASE
    # ============================================================

    def load_dashboard_data(
        self
    ):

        try:

            connection = get_connection()

            connection.row_factory = (
                __import__(
                    "sqlite3"
                ).Row
            )

            try:

                self.load_user(
                    connection
                )

                self.load_latest_vital(
                    connection
                )

                self.load_activity(
                    connection
                )

                self.load_device(
                    connection
                )

                self.load_location(
                    connection
                )

                self.load_heart_rate_history(
                    connection
                )

            finally:

                connection.close()

        except Exception as error:

            print(
                f"[DASHBOARD] "
                f"Data refresh failed: "
                f"{error}"
            )

    # ============================================================
    # USER
    # ============================================================

    def load_user(
        self,
        connection,
    ):

        row = connection.execute(
            """
            SELECT name
            FROM users
            WHERE id = ?
            LIMIT 1
            """,
            (
                self.user_id,
            ),
        ).fetchone()

        if row is None:

            self.welcome_label.setText(
                "Hello"
            )

            return

        name = row["name"]

        if not name:

            self.welcome_label.setText(
                "Hello"
            )

            return

        self.welcome_label.setText(
            f"Hello, {name}"
        )

    # ============================================================
    # LATEST VITAL
    # ============================================================

    def load_latest_vital(
        self,
        connection,
    ):

        row = connection.execute(
            """
            SELECT *
            FROM vitals
            WHERE user_id = ?
            ORDER BY recorded_at DESC, id DESC
            LIMIT 1
            """,
            (
                self.user_id,
            ),
        ).fetchone()

        self.latest_vital = row

        if row is None:

            self.show_no_vital_data()

            return

        # --------------------------------------------------------
        # Heart Rate
        # --------------------------------------------------------

        heart_rate = self.get_value(
            row,
            "heart_rate",
        )

        if heart_rate is None:

            self.set_metric(
                self.heart_rate_card,
                "-- BPM",
                "No reading",
            )

        else:

            self.set_metric(
                self.heart_rate_card,
                (
                    f"{self.format_number(heart_rate)} "
                    "BPM"
                ),
                "Latest reading",
            )

            self.graph_current.setText(
                (
                    f"{self.format_number(heart_rate)} "
                    "BPM"
                )
            )

        # --------------------------------------------------------
        # SpO2
        # --------------------------------------------------------

        spo2 = self.get_value(
            row,
            "spo2",
        )

        if spo2 is None:

            self.set_metric(
                self.spo2_card,
                "-- %",
                "No reading",
            )

        else:

            self.set_metric(
                self.spo2_card,
                (
                    f"{self.format_number(spo2)} "
                    "%"
                ),
                "Latest reading",
            )

        # --------------------------------------------------------
        # Temperature
        # --------------------------------------------------------

        temperature = self.get_value(
            row,
            "temperature",
        )

        if temperature is None:

            self.set_metric(
                self.temperature_card,
                "-- °C",
                "No reading",
            )

        else:

            self.set_metric(
                self.temperature_card,
                (
                    f"{self.format_number(temperature, 1)} "
                    "°C"
                ),
                "Latest reading",
            )

        # --------------------------------------------------------
        # Blood Pressure
        # --------------------------------------------------------

        systolic = self.get_first_value(
            row,
            (
                "systolic",
                "systolic_bp",
                "blood_pressure_systolic",
            ),
        )

        diastolic = self.get_first_value(
            row,
            (
                "diastolic",
                "diastolic_bp",
                "blood_pressure_diastolic",
            ),
        )

        if (
            systolic is None
            or diastolic is None
        ):

            self.set_metric(
                self.blood_pressure_card,
                "-- / --",
                "No reading",
            )

        else:

            self.set_metric(
                self.blood_pressure_card,
                (
                    f"{self.format_number(systolic)}"
                    " / "
                    f"{self.format_number(diastolic)}"
                ),
                "Latest reading",
            )

        # --------------------------------------------------------
        # Monitoring
        # --------------------------------------------------------

        recorded_at = self.get_value(
            row,
            "recorded_at",
        )

        self.update_monitoring_state(
            recorded_at
        )

    # ============================================================
    # NO VITAL DATA
    # ============================================================

    def show_no_vital_data(
        self
    ):

        self.set_metric(
            self.heart_rate_card,
            "-- BPM",
            "Waiting for data",
        )

        self.set_metric(
            self.spo2_card,
            "-- %",
            "Waiting for data",
        )

        self.set_metric(
            self.temperature_card,
            "-- °C",
            "Waiting for data",
        )

        self.set_metric(
            self.blood_pressure_card,
            "-- / --",
            "Waiting for data",
        )

        self.graph_current.setText(
            "-- BPM"
        )

        self.health_status_value.setText(
            "Waiting for health data"
        )

        self.health_status_indicator.setObjectName(
            "health_indicator_waiting"
        )

        self.refresh_widget_style(
            self.health_status_indicator
        )

        self.health_status_time.setText(
            "Last update: --"
        )

    # ============================================================
    # ACTIVITY
    # ============================================================

    def load_activity(
        self,
        connection,
    ):

        row = None

        try:

            row = connection.execute(
                """
                SELECT *
                FROM activity_data
                WHERE user_id = ?
                ORDER BY recorded_at DESC, id DESC
                LIMIT 1
                """,
                (
                    self.user_id,
                ),
            ).fetchone()

        except Exception:

            row = self.latest_vital

        self.latest_activity = row

        if row is None:

            self.movement_value.setText(
                "--"
            )

            self.steps_value.setText(
                "--"
            )

            self.distance_value.setText(
                "-- km"
            )

            self.activity_calories_value.setText(
                "-- kcal"
            )

            self.active_time_value.setText(
                "--"
            )

            return

        # --------------------------------------------------------
        # Movement
        # --------------------------------------------------------

        movement = self.get_value(
            row,
            "movement",
        )

        if movement is None:

            self.movement_value.setText(
                "--"
            )

        else:

            self.movement_value.setText(
                str(movement)
            )

        # --------------------------------------------------------
        # Steps
        # --------------------------------------------------------

        steps = self.get_first_value(
            row,
            (
                "steps",
                "step_count",
            ),
        )

        if steps is None:

            if self.latest_vital is not None:

                steps = self.get_first_value(
                    self.latest_vital,
                    (
                        "steps",
                        "step_count",
                    ),
                )

        if steps is None:

            self.steps_value.setText(
                "--"
            )

        else:

            self.steps_value.setText(
                self.format_number(
                    steps
                )
            )

        # --------------------------------------------------------
        # Distance
        # --------------------------------------------------------

        distance = self.get_first_value(
            row,
            (
                "distance",
                "distance_km",
            ),
        )

        if distance is None:

            self.distance_value.setText(
                "-- km"
            )

        else:

            self.distance_value.setText(
                (
                    f"{self.format_number(distance, 2)} "
                    "km"
                )
            )

        # --------------------------------------------------------
        # Calories
        # --------------------------------------------------------

        calories = self.get_first_value(
            row,
            (
                "calories",
                "calorie",
            ),
        )

        if calories is None:

            if self.latest_vital is not None:

                calories = self.get_first_value(
                    self.latest_vital,
                    (
                        "calories",
                        "calorie",
                    ),
                )

        if calories is None:

            self.activity_calories_value.setText(
                "-- kcal"
            )

        else:

            self.activity_calories_value.setText(
                (
                    f"{self.format_number(calories)} "
                    "kcal"
                )
            )

        # --------------------------------------------------------
        # Active Time
        # --------------------------------------------------------

        active_time = self.get_first_value(
            row,
            (
                "active_time",
                "active_seconds",
            ),
        )

        if active_time is None:

            self.active_time_value.setText(
                "--"
            )

        else:

            try:

                seconds = float(
                    active_time
                )

                minutes = int(
                    seconds // 60
                )

                remaining_seconds = int(
                    seconds % 60
                )

                self.active_time_value.setText(
                    (
                        f"{minutes} min "
                        f"{remaining_seconds:02d} sec"
                    )
                )

            except (
                TypeError,
                ValueError,
            ):

                self.active_time_value.setText(
                    str(active_time)
                )

    # ============================================================
    # DEVICE
    # ============================================================

    def load_device(
        self,
        connection,
    ):

        try:

            row = connection.execute(
                """
                SELECT *
                FROM devices
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (
                    self.user_id,
                ),
            ).fetchone()

        except Exception:

            row = None

        self.latest_device = row

        if row is None:

            self.device_name_label.setText(
                "No device registered"
            )

            self.device_type_label.setText(
                "Connect a HealthSync BLE device to begin monitoring."
            )

            self.device_battery_value.setText(
                "--"
            )

            self.device_connection_value.setText(
                "--"
            )

            self.device_updated_value.setText(
                "--"
            )

            return

        device_name = self.get_value(
            row,
            "device_name",
        )

        device_type = self.get_value(
            row,
            "device_type",
        )

        connection_type = self.get_value(
            row,
            "connection_type",
        )

        status = self.get_value(
            row,
            "status",
        )

        last_seen = self.get_value(
            row,
            "last_seen_at",
        )

        if last_seen is None:

            last_seen = self.get_value(
                row,
                "last_seen",
            )

        self.device_name_label.setText(
            device_name
            or
            "HealthSync Device"
        )

        self.device_type_label.setText(
            (
                f"{device_type or 'Wearable'}"
                "  •  "
                f"{self.format_connection_type(connection_type)}"
            )
        )

        self.device_connection_value.setText(
            status
            or
            "UNKNOWN"
        )

        self.device_updated_value.setText(
            self.format_datetime(
                last_seen
            )
        )

        device_id = self.get_value(
            row,
            "id",
        )

        battery = self.get_latest_battery(
            connection,
            device_id,
        )

        if battery is None:

            self.device_battery_value.setText(
                "--"
            )

        else:

            self.device_battery_value.setText(
                (
                    f"{self.format_number(battery)}"
                    "%"
                )
            )

    # ============================================================
    # BATTERY
    # ============================================================

    def get_latest_battery(
        self,
        connection,
        device_id,
    ):

        if device_id is None:
            return None

        try:

            row = connection.execute(
                """
                SELECT battery
                FROM device_telemetry
                WHERE device_id = ?
                ORDER BY recorded_at DESC
                LIMIT 1
                """,
                (
                    device_id,
                ),
            ).fetchone()

            if row is None:
                return None

            return row[0]

        except Exception:

            return None

    # ============================================================
    # LOCATION
    # ============================================================

    def load_location(
        self,
        connection,
    ):

        try:

            row = connection.execute(
                """
                SELECT *
                FROM location_history
                WHERE user_id = ?
                ORDER BY recorded_at DESC, id DESC
                LIMIT 1
                """,
                (
                    self.user_id,
                ),
            ).fetchone()

        except Exception:

            row = None

        self.latest_location = row

        if row is None:

            self.location_value.setText(
                "Location unavailable"
            )

            self.location_coordinates.setText(
                "No location data received."
            )

            self.location_updated.setText(
                "--"
            )

            return

        latitude = self.get_first_value(
            row,
            (
                "latitude",
                "lat",
            ),
        )

        longitude = self.get_first_value(
            row,
            (
                "longitude",
                "lon",
                "lng",
            ),
        )

        recorded_at = self.get_value(
            row,
            "recorded_at",
        )

        if (
            latitude is None
            or longitude is None
        ):

            self.location_value.setText(
                "Location data received"
            )

            self.location_coordinates.setText(
                "Coordinates unavailable."
            )

            self.location_updated.setText(
                self.format_datetime(
                    recorded_at
                )
            )

            return

        try:

            latitude = float(
                latitude
            )

            longitude = float(
                longitude
            )

        except (
            TypeError,
            ValueError,
        ):

            self.location_value.setText(
                "Location unavailable"
            )

            self.location_coordinates.setText(
                "Invalid coordinates."
            )

            return

        # --------------------------------------------------------
        # Show coordinates as secondary information.
        # --------------------------------------------------------

        self.location_coordinates.setText(
            (
                f"{latitude:.5f}, "
                f"{longitude:.5f}"
            )
        )

        self.location_updated.setText(
            self.format_datetime(
                recorded_at
            )
        )

        # --------------------------------------------------------
        # Only reverse-geocode when coordinates change.
        # --------------------------------------------------------

        location_changed = (
            self.last_geocoded_latitude is None
            or
            self.last_geocoded_longitude is None
            or
            abs(
                self.last_geocoded_latitude
                -
                latitude
            ) > 0.001
            or
            abs(
                self.last_geocoded_longitude
                -
                longitude
            ) > 0.001
        )

        if not location_changed:

            return

        self.last_geocoded_latitude = (
            latitude
        )

        self.last_geocoded_longitude = (
            longitude
        )

        self.location_value.setText(
            "Finding location..."
        )

        self.reverse_geocode(
            latitude,
            longitude,
        )

    # ============================================================
    # REVERSE GEOCODING
    # ============================================================

    def reverse_geocode(
        self,
        latitude,
        longitude,
    ):
        """
        Convert GPS coordinates into a human-readable
        locality using OpenStreetMap Nominatim.

        Example:

        18.760500, 73.863600

        becomes something like:

        Chakan, Pune
        """

        if self.location_lookup_running:

            return

        self.location_lookup_running = True

        self.location_geocoder.lookup(
            latitude,
            longitude,
        )

    # ============================================================
    # APPLY GEOCODED LOCATION
    # ============================================================

    def apply_geocoded_location(
        self,
        place_name,
        latitude,
        longitude,
    ):

        # --------------------------------------------------------
        # The lookup has completed.
        # --------------------------------------------------------

        self.location_lookup_running = False

        # --------------------------------------------------------
        # Ignore an old result if the device has moved and a newer
        # coordinate is now being displayed.
        # --------------------------------------------------------

        if (
            self.last_geocoded_latitude != latitude
            or
            self.last_geocoded_longitude != longitude
        ):

            return

        if place_name:

            self.location_value.setText(
                str(place_name)
            )

        else:

            self.location_value.setText(
                "Location identified"
            )

    # ============================================================
    # HEART RATE HISTORY
    # ============================================================

    def load_heart_rate_history(
        self,
        connection,
    ):

        try:

            rows = connection.execute(
                """
                SELECT heart_rate
                FROM vitals
                WHERE user_id = ?
                  AND heart_rate IS NOT NULL
                ORDER BY recorded_at DESC, id DESC
                LIMIT 30
                """,
                (
                    self.user_id,
                ),
            ).fetchall()

        except Exception:

            rows = []

        values = []

        for row in reversed(
            rows
        ):

            try:

                value = row[
                    "heart_rate"
                ]

                if value is not None:

                    values.append(
                        float(value)
                    )

            except (
                TypeError,
                ValueError,
            ):

                continue

        self.heart_rate_graph.set_values(
            values
        )

    # ============================================================
    # MONITORING STATUS
    # ============================================================

    def update_monitoring_state(
        self,
        recorded_at,
    ):

        self.health_status_value.setText(
            "Monitoring"
        )

        self.health_status_indicator.setObjectName(
            "health_indicator"
        )

        self.refresh_widget_style(
            self.health_status_indicator
        )

        self.health_status_time.setText(
            (
                "Last update: "
                +
                self.format_datetime(
                    recorded_at
                )
            )
        )

    # ============================================================
    # METRIC HELPERS
    # ============================================================

    @staticmethod
    def set_metric(
        card,
        value,
        status,
    ):

        card.value_label.setText(
            value
        )

        card.status_label.setText(
            status
        )

    @staticmethod
    def get_value(
        row,
        key,
    ):

        if row is None:
            return None

        try:

            return row[key]

        except (
            KeyError,
            IndexError,
        ):

            return None

    @classmethod
    def get_first_value(
        cls,
        row,
        keys,
    ):

        for key in keys:

            value = cls.get_value(
                row,
                key,
            )

            if value is not None:

                return value

        return None

    @staticmethod
    def format_number(
        value,
        decimals=0,
    ):

        try:

            number = float(
                value
            )

            if decimals == 0:

                return f"{number:.0f}"

            return f"{number:.{decimals}f}"

        except (
            TypeError,
            ValueError,
        ):

            return str(
                value
            )

    @staticmethod
    def format_connection_type(
        connection_type,
    ):

        if connection_type == "BLE":

            return "Bluetooth LE"

        if not connection_type:

            return "--"

        return str(
            connection_type
        )

    @staticmethod
    def format_datetime(
        value,
    ):

        if value is None:

            return "--"

        if isinstance(
            value,
            datetime,
        ):

            return value.strftime(
                "%d %b %Y, %H:%M:%S"
            )

        value = str(
            value
        )

        try:

            parsed = datetime.fromisoformat(
                value.replace(
                    "Z",
                    "+00:00",
                )
            )

            return parsed.strftime(
                "%d %b %Y, %H:%M:%S"
            )

        except ValueError:

            return value

    # ============================================================
    # STYLE REFRESH
    # ============================================================

    @staticmethod
    def refresh_widget_style(
        widget,
    ):

        widget.style().unpolish(
            widget
        )

        widget.style().polish(
            widget
        )

        widget.update()

    # ============================================================
    # PAGE STYLING
    # ============================================================

    def apply_page_styles(
        self,
    ):

        self.setStyleSheet(
            """
            QWidget {
                color: #FFFFFF;
                font-family: "Segoe UI";
            }

            QScrollArea#dashboard_scroll {
                background: transparent;
                border: none;
            }

            QScrollArea#dashboard_scroll > QWidget > QWidget {
                background: transparent;
            }

            QScrollBar:vertical {
                background: #07131F;
                width: 8px;
                margin: 4px 0 4px 0;
                border-radius: 4px;
            }

            QScrollBar::handle:vertical {
                background: #29465A;
                min-height: 40px;
                border-radius: 4px;
            }

            QScrollBar::handle:vertical:hover {
                background: #3D6178;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            /* ==================================================
               HEADER
            ================================================== */

            #welcome_title {
                color: #FFFFFF;
                font-size: 30px;
                font-weight: 700;
            }

            #page_description {
                color: #90C2E7;
                font-size: 14px;
            }

            #monitoring_status {
                color: #39D98A;
                font-size: 11px;
                font-weight: 700;
                padding-top: 4px;
            }

            /* ==================================================
               HEALTH STATUS
            ================================================== */

            #health_status_card {
                background: #0B1D2A;
                border: 1px solid #1C3A4D;
                border-radius: 18px;
            }

            #card_overline {
                color: #6F95AA;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 1px;
            }

            #status_time {
                color: #66869A;
                font-size: 11px;
            }

            #health_indicator {
                color: #39D98A;
                font-size: 17px;
            }

            #health_indicator_waiting {
                color: #66869A;
                font-size: 17px;
            }

            #health_status_value {
                color: #FFFFFF;
                font-size: 18px;
                font-weight: 650;
            }

            #health_status_description {
                color: #6F95AA;
                font-size: 12px;
            }

            /* ==================================================
               SECTIONS
            ================================================== */

            #section_title {
                color: #FFFFFF;
                font-size: 18px;
                font-weight: 650;
            }

            #section_description {
                color: #6F95AA;
                font-size: 12px;
            }

            /* ==================================================
               CURRENT HEALTH
            ================================================== */

            #metric_card {
                background: #0B1D2A;
                border: 1px solid #173044;
                border-radius: 14px;
            }

            #metric_card:hover {
                border: 1px solid #286477;
            }

            #metric_title {
                color: #648398;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.7px;
            }

            #metric_value {
                color: #FFFFFF;
                font-size: 23px;
                font-weight: 700;
            }

            #metric_status {
                color: #66869A;
                font-size: 11px;
            }

            /* ==================================================
               ACTIVITY
            ================================================== */

            #activity_card {
                background: #0B1D2A;
                border: 1px solid #1C3A4D;
                border-radius: 18px;
            }

            #activity_stat {
                background: #071923;
                border: 1px solid #173044;
                border-radius: 10px;
            }

            #activity_stat_title {
                color: #648398;
                font-size: 9px;
                font-weight: 700;
                letter-spacing: 0.6px;
            }

            #activity_stat_value {
                color: #FFFFFF;
                font-size: 17px;
                font-weight: 600;
            }

            /* ==================================================
               GRAPH
            ================================================== */

            #graph_card {
                background: #0B1D2A;
                border: 1px solid #173044;
                border-radius: 16px;
            }

            #graph_current {
                color: #55E7E2;
                font-size: 18px;
                font-weight: 700;
            }

            /* ==================================================
               DEVICE
            ================================================== */

            #device_card {
                background: #0B1D2A;
                border: 1px solid #173044;
                border-radius: 14px;
            }

            #device_icon {
                color: #00A9A5;
                font-size: 20px;
            }

            #device_name {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 600;
            }

            #device_details {
                color: #66869A;
                font-size: 11px;
            }

            #device_stat_title {
                color: #648398;
                font-size: 9px;
                font-weight: 700;
            }

            #device_stat_value {
                color: #DCE6EB;
                font-size: 12px;
                font-weight: 600;
            }

            /* ==================================================
               LOCATION
            ================================================== */

            #location_card {
                background: #0B1D2A;
                border: 1px solid #173044;
                border-radius: 14px;
            }

            #location_icon {
                color: #00A9A5;
                font-size: 21px;
            }

            #location_value {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 600;
            }

            #location_coordinates {
                color: #66869A;
                font-size: 11px;
            }

            #location_updated {
                color: #66869A;
                font-size: 10px;
            }

            /* ==================================================
               BUTTONS
            ================================================== */

            #secondary_button {
                background: #10333E;
                color: #90DAD7;
                border: 1px solid #1A5965;
                border-radius: 9px;
                padding: 0 15px;
                font-size: 12px;
                font-weight: 600;
            }

            #secondary_button:hover {
                background: #00A9A5;
                color: #FFFFFF;
                border: 1px solid #00A9A5;
            }

            #secondary_button:pressed {
                background: #078F8C;
            }
            """
        )