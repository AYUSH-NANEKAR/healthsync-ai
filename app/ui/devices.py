from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.database.connection import get_connection


class DevicesPage(QWidget):
    """
    Devices management page.

    Responsibilities:
    - Display the currently connected device.
    - Display nearby BLE devices.
    - Start BLE scans.
    - Request connection to a selected BLE device.
    - Display saved devices from SQLite.
    - Display latest battery information.

    BLE communication is handled by BLEIntegrationService.
    """

    def __init__(self, user_id: int):
        super().__init__()

        self.user_id = user_id
        self.ble_service = None
        self.current_device_id = None

        self.build_ui()
        self.load_devices()

    # ============================================================
    # UI
    # ============================================================

    def build_ui(self):
        root_layout = QVBoxLayout(self)

        root_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        root_layout.setSpacing(0)

        scroll_area = QScrollArea()

        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        content = QWidget()

        content_layout = QVBoxLayout(content)

        content_layout.setContentsMargins(
            10,
            8,
            10,
            30,
        )

        content_layout.setSpacing(22)

        # --------------------------------------------------------
        # Page heading
        # --------------------------------------------------------

        heading_layout = QVBoxLayout()
        heading_layout.setSpacing(5)

        title = QLabel("Devices")
        title.setObjectName("page_title")

        description = QLabel(
            "Connect and manage the Bluetooth devices "
            "that provide health data to HealthSync AI."
        )

        description.setObjectName(
            "page_description"
        )

        heading_layout.addWidget(title)
        heading_layout.addWidget(description)

        content_layout.addLayout(
            heading_layout
        )

        # --------------------------------------------------------
        # Connected device
        # --------------------------------------------------------

        content_layout.addWidget(
            self.create_connected_card()
        )

        # --------------------------------------------------------
        # Nearby devices header
        # --------------------------------------------------------

        nearby_header = QHBoxLayout()

        nearby_heading_layout = QVBoxLayout()
        nearby_heading_layout.setSpacing(3)

        nearby_title = QLabel(
            "Nearby Bluetooth Devices"
        )

        nearby_title.setObjectName(
            "section_title"
        )

        nearby_description = QLabel(
            "Devices currently visible through Bluetooth Low Energy."
        )

        nearby_description.setObjectName(
            "section_description"
        )

        nearby_heading_layout.addWidget(
            nearby_title
        )

        nearby_heading_layout.addWidget(
            nearby_description
        )

        nearby_header.addLayout(
            nearby_heading_layout
        )

        nearby_header.addStretch()

        self.scan_button = QPushButton(
            "↻  Scan for Devices"
        )

        self.scan_button.setObjectName(
            "primary_button"
        )

        self.scan_button.setMinimumHeight(42)
        self.scan_button.setMinimumWidth(170)

        self.scan_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.scan_button.clicked.connect(
            self.scan_devices
        )

        nearby_header.addWidget(
            self.scan_button
        )

        content_layout.addLayout(
            nearby_header
        )

        # --------------------------------------------------------
        # Scan status
        # --------------------------------------------------------

        scan_status_container = QFrame()

        scan_status_container.setObjectName(
            "scan_status_card"
        )

        scan_status_layout = QHBoxLayout(
            scan_status_container
        )

        scan_status_layout.setContentsMargins(
            14,
            10,
            14,
            10,
        )

        self.scan_indicator = QLabel("●")

        self.scan_indicator.setObjectName(
            "scan_indicator"
        )

        self.scan_status = QLabel(
            "Press Scan for Devices to search nearby."
        )

        self.scan_status.setObjectName(
            "scan_status"
        )

        scan_status_layout.addWidget(
            self.scan_indicator
        )

        scan_status_layout.addWidget(
            self.scan_status
        )

        scan_status_layout.addStretch()

        content_layout.addWidget(
            scan_status_container
        )

        # --------------------------------------------------------
        # Nearby device list
        # --------------------------------------------------------

        self.nearby_devices_container = QVBoxLayout()

        self.nearby_devices_container.setSpacing(
            10
        )

        content_layout.addLayout(
            self.nearby_devices_container
        )

        # --------------------------------------------------------
        # Saved devices
        # --------------------------------------------------------

        saved_header = QVBoxLayout()
        saved_header.setSpacing(3)

        saved_title = QLabel(
            "Saved Devices"
        )

        saved_title.setObjectName(
            "section_title"
        )

        saved_description = QLabel(
            "Devices previously registered with your HealthSync account."
        )

        saved_description.setObjectName(
            "section_description"
        )

        saved_header.addWidget(
            saved_title
        )

        saved_header.addWidget(
            saved_description
        )

        content_layout.addLayout(
            saved_header
        )

        self.saved_devices_container = QVBoxLayout()

        self.saved_devices_container.setSpacing(
            10
        )

        content_layout.addLayout(
            self.saved_devices_container
        )

        content_layout.addStretch()

        scroll_area.setWidget(
            content
        )

        root_layout.addWidget(
            scroll_area
        )

        self.apply_page_styles()

    def create_connected_card(self):
        card = QFrame()

        card.setObjectName(
            "connected_card"
        )

        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        layout = QVBoxLayout(card)

        layout.setContentsMargins(
            24,
            22,
            24,
            22,
        )

        layout.setSpacing(18)

        # --------------------------------------------------------
        # Card header
        # --------------------------------------------------------

        header = QHBoxLayout()

        label = QLabel(
            "CONNECTED DEVICE"
        )

        label.setObjectName(
            "card_overline"
        )

        header.addWidget(label)

        header.addStretch()

        self.connection_status = QLabel(
            "●  DISCONNECTED"
        )

        self.connection_status.setObjectName(
            "status_disconnected"
        )

        header.addWidget(
            self.connection_status
        )

        layout.addLayout(header)

        # --------------------------------------------------------
        # Device identity
        # --------------------------------------------------------

        identity = QHBoxLayout()

        identity.setSpacing(20)

        identity_text = QVBoxLayout()
        identity_text.setSpacing(5)

        self.device_name = QLabel(
            "No device connected"
        )

        self.device_name.setObjectName(
            "connected_device_name"
        )

        self.device_type = QLabel(
            "Waiting for a HealthSync device..."
        )

        self.device_type.setObjectName(
            "connected_device_type"
        )

        identity_text.addWidget(
            self.device_name
        )

        identity_text.addWidget(
            self.device_type
        )

        identity.addLayout(
            identity_text
        )

        identity.addStretch()

        layout.addLayout(identity)

        # --------------------------------------------------------
        # Device statistics
        # --------------------------------------------------------

        statistics = QHBoxLayout()

        statistics.setSpacing(12)

        self.battery_value = self.create_stat_card(
            statistics,
            "BATTERY",
            "--",
        )

        self.updated_value = self.create_stat_card(
            statistics,
            "LAST UPDATED",
            "--",
        )

        self.connection_value = self.create_stat_card(
            statistics,
            "CONNECTION",
            "Bluetooth LE",
        )

        layout.addLayout(
            statistics
        )

        # --------------------------------------------------------
        # Metadata
        # --------------------------------------------------------

        metadata = QHBoxLayout()

        self.device_id_value = self.create_metadata(
            metadata,
            "Device ID: --",
        )

        self.service_value = self.create_metadata(
            metadata,
            "Service: A001",
        )

        self.source_value = self.create_metadata(
            metadata,
            "Source: BLE",
        )

        metadata.addStretch()

        layout.addLayout(
            metadata
        )

        # --------------------------------------------------------
        # Actions
        # --------------------------------------------------------

        actions = QHBoxLayout()

        actions.addStretch()

        self.disconnect_button = QPushButton(
            "Disconnect"
        )

        self.disconnect_button.setObjectName(
            "danger_button"
        )

        self.disconnect_button.setMinimumHeight(
            40
        )

        self.disconnect_button.setMinimumWidth(
            120
        )

        self.disconnect_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.disconnect_button.setEnabled(
            False
        )

        self.disconnect_button.clicked.connect(
            self.disconnect_device
        )

        actions.addWidget(
            self.disconnect_button
        )

        layout.addLayout(
            actions
        )

        return card

    def create_stat_card(
        self,
        parent_layout,
        label_text,
        value_text,
    ):
        card = QFrame()

        card.setObjectName(
            "stat_card"
        )

        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        card_layout = QVBoxLayout(card)

        card_layout.setContentsMargins(
            16,
            13,
            16,
            13,
        )

        card_layout.setSpacing(5)

        label = QLabel(
            label_text
        )

        label.setObjectName(
            "stat_label"
        )

        value = QLabel(
            value_text
        )

        value.setObjectName(
            "stat_value"
        )

        card_layout.addWidget(label)
        card_layout.addWidget(value)

        parent_layout.addWidget(
            card,
            1,
        )

        return value

    def create_metadata(
        self,
        parent_layout,
        text,
    ):
        label = QLabel(text)

        label.setObjectName(
            "metadata_label"
        )

        parent_layout.addWidget(
            label
        )

        return label

    # ============================================================
    # BLE CONNECTION
    # ============================================================

    def set_ble_service(
        self,
        ble_service,
    ):
        self.ble_service = ble_service

        if self.ble_service is None:
            return

        self.ble_service.status_changed.connect(
            self.handle_ble_status
        )

        self.ble_service.telemetry_received.connect(
            self.handle_telemetry
        )

        self.ble_service.error_occurred.connect(
            self.handle_ble_error
        )

        self.ble_service.devices_discovered.connect(
            self.handle_devices_discovered
        )

        self.load_devices()

    def scan_devices(self):
        if self.ble_service is None:
            self.set_scan_status(
                "BLE service is unavailable.",
                error=True,
            )
            return

        self.scan_button.setEnabled(
            False
        )

        self.scan_button.setText(
            "Scanning..."
        )

        self.set_scan_status(
            "Scanning nearby Bluetooth devices..."
        )

        self.ble_service.scan_devices()

    def handle_devices_discovered(
        self,
        devices,
    ):
        self.clear_nearby_devices()

        self.scan_button.setEnabled(
            True
        )

        self.scan_button.setText(
            "↻  Scan for Devices"
        )

        if not devices:
            self.set_scan_status(
                "No BLE devices were found nearby."
            )
            return

        self.set_scan_status(
            f"{len(devices)} Bluetooth device(s) found."
        )

        for device in devices:
            self.add_nearby_device(
                device
            )

    def add_nearby_device(
        self,
        device,
    ):
        card = QFrame()

        card.setObjectName(
            "nearby_device_card"
        )

        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        layout = QHBoxLayout(card)

        layout.setContentsMargins(
            18,
            14,
            18,
            14,
        )

        layout.setSpacing(15)

        # --------------------------------------------------------
        # Device icon
        # --------------------------------------------------------

        icon = QLabel("◉")

        icon.setObjectName(
            "device_icon"
        )

        icon.setFixedWidth(30)

        layout.addWidget(
            icon
        )

        # --------------------------------------------------------
        # Device information
        # --------------------------------------------------------

        information = QVBoxLayout()

        information.setSpacing(4)

        name = QLabel(
            device["name"]
        )

        name.setObjectName(
            "nearby_device_name"
        )

        address = QLabel(
            device["address"]
        )

        address.setObjectName(
            "nearby_device_address"
        )

        information.addWidget(
            name
        )

        information.addWidget(
            address
        )

        layout.addLayout(
            information
        )

        layout.addStretch()

        # --------------------------------------------------------
        # Device type
        # --------------------------------------------------------

        type_label = QLabel(
            "Bluetooth LE"
        )

        type_label.setObjectName(
            "device_type_badge"
        )

        layout.addWidget(
            type_label
        )

        # --------------------------------------------------------
        # Connect button
        # --------------------------------------------------------

        connect_button = QPushButton(
            "Connect"
        )

        connect_button.setObjectName(
            "connect_button"
        )

        connect_button.setMinimumHeight(
            38
        )

        connect_button.setMinimumWidth(
            105
        )

        connect_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        connect_button.clicked.connect(
            lambda checked=False,
            address=device["address"]:
            self.connect_to_device(
                address
            )
        )

        layout.addWidget(
            connect_button
        )

        self.nearby_devices_container.addWidget(
            card
        )

    def connect_to_device(
        self,
        device_address: str,
    ):
        if self.ble_service is None:
            return

        self.set_scan_status(
            "Connecting to selected device..."
        )

        self.ble_service.connect_device(
            device_address
        )

    def disconnect_device(self):
        if self.ble_service is None:
            return

        self.ble_service.stop()

    # ============================================================
    # BLE EVENTS
    # ============================================================

    def handle_ble_status(
        self,
        status: str,
    ):
        status_lower = status.lower()

        if "scan complete" in status_lower:
            self.scan_button.setEnabled(
                True
            )

            self.scan_button.setText(
                "↻  Scan for Devices"
            )

        self.set_scan_status(
            status
        )

        if (
            "connected" in status_lower
            or "disconnected" in status_lower
        ):
            self.load_devices()

    def handle_telemetry(
        self,
        telemetry,
    ):
        if self.current_device_id is None:
            self.load_devices()
            return

        if telemetry.battery is not None:
            self.battery_value.setText(
                f"{telemetry.battery}%"
            )

        self.updated_value.setText(
            "Just now"
        )

        self.connection_status.setText(
            "●  CONNECTED"
        )

        self.connection_status.setObjectName(
            "status_connected"
        )

        self.refresh_widget_style(
            self.connection_status
        )

    def handle_ble_error(
        self,
        error: str,
    ):
        self.scan_button.setEnabled(
            True
        )

        self.scan_button.setText(
            "↻  Scan for Devices"
        )

        self.set_scan_status(
            "Bluetooth error. Check the device and try again.",
            error=True,
        )

        print(
            f"[DEVICES] BLE Error: {error}"
        )

    # ============================================================
    # DATABASE
    # ============================================================

    def load_devices(self):
        connection = get_connection()

        try:
            connection.row_factory = __import__(
                "sqlite3"
            ).Row

            rows = connection.execute(
                """
                SELECT
                    id,
                    device_name,
                    device_address,
                    device_type,
                    connection_type,
                    status,
                    service_uuid,
                    last_seen_at
                FROM devices
                WHERE user_id = ?
                ORDER BY updated_at DESC
                """,
                (self.user_id,),
            ).fetchall()

        finally:
            connection.close()

        self.clear_saved_devices()

        connected_device = None

        for row in rows:
            if row["status"] == "CONNECTED":
                if connected_device is None:
                    connected_device = row

        if connected_device is not None:
            self.show_connected_device(
                connected_device
            )
        else:
            self.show_no_connected_device()

        for row in rows:
            self.add_saved_device(
                row
            )

    def show_connected_device(
        self,
        row,
    ):
        self.current_device_id = row["id"]

        self.connection_status.setText(
            "●  CONNECTED"
        )

        self.connection_status.setObjectName(
            "status_connected"
        )

        self.refresh_widget_style(
            self.connection_status
        )

        self.device_name.setText(
            row["device_name"]
        )

        self.device_type.setText(
            row["device_type"]
        )

        self.connection_value.setText(
            self.format_connection_type(
                row["connection_type"]
            )
        )

        self.device_id_value.setText(
            f"Device ID: {row['id']}"
        )

        self.service_value.setText(
            self.format_service_uuid(
                row["service_uuid"]
            )
        )

        self.updated_value.setText(
            self.format_datetime(
                row["last_seen_at"]
            )
        )

        battery = self.get_latest_battery(
            row["id"]
        )

        if battery is None:
            self.battery_value.setText(
                "--"
            )
        else:
            self.battery_value.setText(
                f"{battery}%"
            )

        self.disconnect_button.setEnabled(
            self.ble_service is not None
        )

    def show_no_connected_device(self):
        self.current_device_id = None

        self.connection_status.setText(
            "●  DISCONNECTED"
        )

        self.connection_status.setObjectName(
            "status_disconnected"
        )

        self.refresh_widget_style(
            self.connection_status
        )

        self.device_name.setText(
            "No device connected"
        )

        self.device_type.setText(
            "Waiting for a HealthSync device..."
        )

        self.battery_value.setText(
            "--"
        )

        self.updated_value.setText(
            "--"
        )

        self.connection_value.setText(
            "Bluetooth LE"
        )

        self.device_id_value.setText(
            "Device ID: --"
        )

        self.service_value.setText(
            "Service: A001"
        )

        self.source_value.setText(
            "Source: BLE"
        )

        self.disconnect_button.setEnabled(
            False
        )

    def get_latest_battery(
        self,
        device_id: int,
    ):
        connection = get_connection()

        try:
            row = connection.execute(
                """
                SELECT battery
                FROM device_telemetry
                WHERE device_id = ?
                ORDER BY recorded_at DESC
                LIMIT 1
                """,
                (device_id,),
            ).fetchone()

            if row is None:
                return None

            return row[0]

        finally:
            connection.close()

    # ============================================================
    # SAVED DEVICES
    # ============================================================

    def add_saved_device(
        self,
        row,
    ):
        card = QFrame()

        card.setObjectName(
            "saved_device_card"
        )

        layout = QHBoxLayout(card)

        layout.setContentsMargins(
            18,
            14,
            18,
            14,
        )

        icon = QLabel("◉")

        icon.setObjectName(
            "saved_device_icon"
        )

        icon.setFixedWidth(30)

        layout.addWidget(
            icon
        )

        information = QVBoxLayout()

        information.setSpacing(4)

        name = QLabel(
            row["device_name"]
        )

        name.setObjectName(
            "saved_device_name"
        )

        details = QLabel(
            f"{row['device_type']}  •  "
            f"{self.format_connection_type(row['connection_type'])}"
        )

        details.setObjectName(
            "saved_device_details"
        )

        information.addWidget(
            name
        )

        information.addWidget(
            details
        )

        layout.addLayout(
            information
        )

        layout.addStretch()

        status = QLabel(
            row["status"]
        )

        status.setObjectName(
            "saved_device_status"
        )

        layout.addWidget(
            status
        )

        self.saved_devices_container.addWidget(
            card
        )

    # ============================================================
    # HELPERS
    # ============================================================

    def clear_nearby_devices(self):
        while self.nearby_devices_container.count():
            item = (
                self.nearby_devices_container.takeAt(
                    0
                )
            )

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def clear_saved_devices(self):
        while self.saved_devices_container.count():
            item = (
                self.saved_devices_container.takeAt(
                    0
                )
            )

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def set_scan_status(
        self,
        text,
        error=False,
    ):
        self.scan_status.setText(
            text
        )

        self.scan_indicator.setText(
            "●"
        )

        if error:
            self.scan_indicator.setObjectName(
                "scan_indicator_error"
            )
        else:
            self.scan_indicator.setObjectName(
                "scan_indicator"
            )

        self.refresh_widget_style(
            self.scan_indicator
        )

    @staticmethod
    def refresh_widget_style(
        widget,
    ):
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    @staticmethod
    def format_connection_type(
        connection_type: str | None,
    ) -> str:
        if connection_type == "BLE":
            return "Bluetooth LE"

        if not connection_type:
            return "--"

        return connection_type

    @staticmethod
    def format_service_uuid(
        service_uuid: str | None,
    ) -> str:
        if not service_uuid:
            return "Service: A001"

        if "A001" in service_uuid.upper():
            return "Service: A001"

        return f"Service: {service_uuid}"

    @staticmethod
    def format_datetime(
        value,
    ) -> str:
        if value is None:
            return "--"

        if isinstance(value, datetime):
            return value.strftime(
                "%d %b %Y, %H:%M"
            )

        return str(value)

    # ============================================================
    # PAGE STYLING
    # ============================================================

    def apply_page_styles(self):
        self.setStyleSheet(
            """
            QWidget {
                color: #FFFFFF;
                font-family: "Segoe UI";
            }

            QScrollArea {
                background: transparent;
                border: none;
            }

            QScrollArea > QWidget > QWidget {
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

            #page_title {
                color: #FFFFFF;
                font-size: 30px;
                font-weight: 700;
            }

            #page_description {
                color: #90C2E7;
                font-size: 14px;
            }

            #connected_card {
                background: #0B1D2A;
                border: 1px solid #1C3A4D;
                border-radius: 18px;
            }

            #card_overline {
                color: #6F95AA;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1px;
            }

            #status_connected {
                color: #39D98A;
                font-size: 12px;
                font-weight: 700;
            }

            #status_disconnected {
                color: #90A8B8;
                font-size: 12px;
                font-weight: 700;
            }

            #connected_device_name {
                color: #FFFFFF;
                font-size: 24px;
                font-weight: 700;
            }

            #connected_device_type {
                color: #90C2E7;
                font-size: 13px;
            }

            #stat_card {
                background: #071923;
                border: 1px solid #173044;
                border-radius: 12px;
            }

            #stat_label {
                color: #648398;
                font-size: 10px;
                font-weight: 700;
            }

            #stat_value {
                color: #FFFFFF;
                font-size: 17px;
                font-weight: 600;
            }

            #metadata_label {
                color: #6F95AA;
                font-size: 11px;
            }

            #section_title {
                color: #FFFFFF;
                font-size: 18px;
                font-weight: 650;
            }

            #section_description {
                color: #6F95AA;
                font-size: 12px;
            }

            #scan_status_card {
                background: #091A26;
                border: 1px solid #173044;
                border-radius: 10px;
            }

            #scan_status {
                color: #90C2E7;
                font-size: 12px;
            }

            #scan_indicator {
                color: #00A9A5;
                font-size: 10px;
            }

            #scan_indicator_error {
                color: #E56B6F;
                font-size: 10px;
            }

            #nearby_device_card {
                background: #0B1D2A;
                border: 1px solid #173044;
                border-radius: 13px;
            }

            #nearby_device_card:hover {
                border: 1px solid #286477;
            }

            #device_icon {
                color: #00A9A5;
                font-size: 19px;
            }

            #nearby_device_name {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 600;
            }

            #nearby_device_address {
                color: #66869A;
                font-size: 11px;
            }

            #device_type_badge {
                background: #102D3D;
                color: #90C2E7;
                border-radius: 7px;
                padding: 6px 9px;
                font-size: 10px;
            }

            #primary_button {
                background: #00A9A5;
                color: #FFFFFF;
                border: none;
                border-radius: 9px;
                padding: 0 15px;
                font-weight: 600;
            }

            #primary_button:hover {
                background: #00BDB8;
            }

            #primary_button:disabled {
                background: #24505B;
                color: #7894A1;
            }

            #connect_button {
                background: #103E4A;
                color: #65DDD8;
                border: 1px solid #176775;
                border-radius: 8px;
                padding: 0 14px;
                font-weight: 600;
            }

            #connect_button:hover {
                background: #00A9A5;
                color: #FFFFFF;
            }

            #danger_button {
                background: transparent;
                color: #E58B8F;
                border: 1px solid #704347;
                border-radius: 8px;
                padding: 0 14px;
                font-weight: 600;
            }

            #danger_button:hover {
                background: #3A2025;
                color: #FFFFFF;
            }

            #saved_device_card {
                background: #091A26;
                border: 1px solid #173044;
                border-radius: 12px;
            }

            #saved_device_icon {
                color: #52788D;
                font-size: 17px;
            }

            #saved_device_name {
                color: #FFFFFF;
                font-size: 13px;
                font-weight: 600;
            }

            #saved_device_details {
                color: #66869A;
                font-size: 11px;
            }

            #saved_device_status {
                color: #39D98A;
                background: #102C25;
                border-radius: 7px;
                padding: 6px 10px;
                font-size: 10px;
                font-weight: 700;
            }
            """
        )