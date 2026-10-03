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

    def __init__(self, user_id: int):
        super().__init__()

        self.user_id = user_id

        # BLE integration service is injected by the main application.
        self.ble_service = None

        # Database device ID of the currently connected device.
        self.current_device_id = None

        # Address currently being connected/reconnected.
        self.current_device_address = None

        # Used only for UI state.
        self.telemetry_received_at = None
        self.is_scanning = False
        self.is_connecting = False

        self.build_ui()
        self.load_devices()

    # ========================================================
    # UI
    # ========================================================

    def build_ui(self):
        root_layout = QVBoxLayout(self)

        root_layout.setContentsMargins(0, 0, 0, 0)
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

        # ----------------------------------------------------
        # Page heading
        # ----------------------------------------------------

        heading_layout = QVBoxLayout()
        heading_layout.setSpacing(5)

        title = QLabel("Devices")
        title.setObjectName("page_title")

        description = QLabel(
            "Connect and manage the Bluetooth devices "
            "that provide health data to HealthSync AI."
        )

        description.setObjectName("page_description")

        heading_layout.addWidget(title)
        heading_layout.addWidget(description)

        content_layout.addLayout(heading_layout)

        # ----------------------------------------------------
        # Connected device
        # ----------------------------------------------------

        content_layout.addWidget(
            self.create_connected_card()
        )

        # ----------------------------------------------------
        # Nearby devices header
        # ----------------------------------------------------

        nearby_header = QHBoxLayout()

        nearby_heading_layout = QVBoxLayout()
        nearby_heading_layout.setSpacing(3)

        nearby_title = QLabel(
            "Nearby Bluetooth Devices"
        )

        nearby_title.setObjectName("section_title")

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

        # ----------------------------------------------------
        # Scan status
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Nearby device list
        # ----------------------------------------------------

        self.nearby_devices_container = QVBoxLayout()
        self.nearby_devices_container.setSpacing(10)

        content_layout.addLayout(
            self.nearby_devices_container
        )

        # ----------------------------------------------------
        # Saved devices
        # ----------------------------------------------------

        saved_header = QVBoxLayout()
        saved_header.setSpacing(3)

        saved_title = QLabel("Saved Devices")
        saved_title.setObjectName("section_title")

        saved_description = QLabel(
            "Devices previously registered with your HealthSync account."
        )

        saved_description.setObjectName(
            "section_description"
        )

        saved_header.addWidget(saved_title)
        saved_header.addWidget(saved_description)

        content_layout.addLayout(saved_header)

        self.saved_devices_container = QVBoxLayout()
        self.saved_devices_container.setSpacing(10)

        content_layout.addLayout(
            self.saved_devices_container
        )

        content_layout.addStretch()

        scroll_area.setWidget(content)

        root_layout.addWidget(scroll_area)

        self.apply_page_styles()

    # ========================================================
    # CONNECTED DEVICE CARD
    # ========================================================

    def create_connected_card(self):
        card = QFrame()

        card.setObjectName("connected_card")

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

        # ----------------------------------------------------
        # Card header
        # ----------------------------------------------------

        header = QHBoxLayout()

        label = QLabel("CONNECTED DEVICE")
        label.setObjectName("card_overline")

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

        # ----------------------------------------------------
        # Device identity
        # ----------------------------------------------------

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

        identity.addLayout(identity_text)
        identity.addStretch()

        layout.addLayout(identity)

        # ----------------------------------------------------
        # Device statistics
        # ----------------------------------------------------

        statistics = QHBoxLayout()
        statistics.setSpacing(12)

        self.battery_value = self.create_stat_card(
            statistics,
            "BATTERY",
            "--",
        )

        self.updated_value = self.create_stat_card(
            statistics,
            "LAST TELEMETRY",
            "--",
        )

        self.connection_value = self.create_stat_card(
            statistics,
            "CONNECTION",
            "Bluetooth LE",
        )

        layout.addLayout(statistics)

        # ----------------------------------------------------
        # Metadata
        # ----------------------------------------------------

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

        layout.addLayout(metadata)

        # ----------------------------------------------------
        # Telemetry status
        # ----------------------------------------------------

        telemetry_card = QFrame()

        telemetry_card.setObjectName(
            "telemetry_status_card"
        )

        telemetry_layout = QVBoxLayout(
            telemetry_card
        )

        telemetry_layout.setContentsMargins(
            14,
            12,
            14,
            12,
        )

        telemetry_layout.setSpacing(4)

        telemetry_heading = QLabel("TELEMETRY")
        telemetry_heading.setObjectName(
            "telemetry_heading"
        )

        self.telemetry_status = QLabel(
            "○  WAITING FOR DATA"
        )

        self.telemetry_status.setObjectName(
            "telemetry_waiting"
        )

        self.telemetry_detail = QLabel(
            "Connect a HealthSync-compatible device "
            "to receive telemetry."
        )

        self.telemetry_detail.setObjectName(
            "telemetry_detail"
        )

        telemetry_layout.addWidget(
            telemetry_heading
        )

        telemetry_layout.addWidget(
            self.telemetry_status
        )

        telemetry_layout.addWidget(
            self.telemetry_detail
        )

        layout.addWidget(telemetry_card)

        # ----------------------------------------------------
        # Actions
        # ----------------------------------------------------

        actions = QHBoxLayout()
        actions.addStretch()

        self.disconnect_button = QPushButton(
            "Disconnect"
        )

        self.disconnect_button.setObjectName(
            "danger_button"
        )

        self.disconnect_button.setMinimumHeight(40)
        self.disconnect_button.setMinimumWidth(120)

        self.disconnect_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.disconnect_button.setEnabled(False)

        self.disconnect_button.clicked.connect(
            self.disconnect_device
        )

        actions.addWidget(
            self.disconnect_button
        )

        layout.addLayout(actions)

        return card

    def create_stat_card(
        self,
        parent_layout,
        label_text,
        value_text,
    ):
        card = QFrame()

        card.setObjectName("stat_card")

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

        label = QLabel(label_text)
        label.setObjectName("stat_label")

        value = QLabel(value_text)
        value.setObjectName("stat_value")

        card_layout.addWidget(label)
        card_layout.addWidget(value)

        parent_layout.addWidget(card, 1)

        return value

    def create_metadata(
        self,
        parent_layout,
        text,
    ):
        label = QLabel(text)
        label.setObjectName("metadata_label")

        parent_layout.addWidget(label)

        return label

    # ========================================================
    # BLE SERVICE
    # ========================================================

    def set_ble_service(
        self,
        ble_service,
    ):
        """
        Attach the application BLE integration service.

        The BLE service owns the actual BLE worker/thread.
        This page only reacts to its signals and requests actions.
        """

        self.ble_service = ble_service

        if self.ble_service is None:
            self.set_scan_status(
                "BLE service is unavailable.",
                error=True,
            )

            self.disconnect_button.setEnabled(False)
            return

        self._connect_service_signal(
            "status_changed",
            self.handle_ble_status,
        )

        self._connect_service_signal(
            "telemetry_received",
            self.handle_telemetry,
        )

        self._connect_service_signal(
            "error_occurred",
            self.handle_ble_error,
        )

        self._connect_service_signal(
            "devices_discovered",
            self.handle_devices_discovered,
        )

        self.load_devices()

    def _connect_service_signal(
        self,
        signal_name,
        callback,
    ):
        """
        Safely connect a BLE service signal.

        This prevents the UI from crashing if an optional signal
        is not exposed by a particular service implementation.
        """

        signal = getattr(
            self.ble_service,
            signal_name,
            None,
        )

        if signal is None:
            return

        try:
            signal.connect(callback)
        except (AttributeError, TypeError):
            pass

    # ========================================================
    # BLE SCANNING
    # ========================================================

    def scan_devices(self):
        """
        Start a user-requested BLE scan.

        There is intentionally no automatic scan when the page
        or application starts.
        """

        if self.ble_service is None:
            self.set_scan_status(
                "BLE service is unavailable.",
                error=True,
            )
            return

        if self.is_scanning:
            return

        self.is_scanning = True

        self.scan_button.setEnabled(False)
        self.scan_button.setText("Scanning...")

        self.clear_nearby_devices()

        self.set_scan_status(
            "Scanning for nearby Bluetooth devices..."
        )

        try:
            self.ble_service.scan_devices()

        except Exception as exc:
            self.is_scanning = False

            self.scan_button.setEnabled(True)
            self.scan_button.setText(
                "↻  Scan for Devices"
            )

            self.set_scan_status(
                "Unable to start Bluetooth scan.",
                error=True,
            )

            print(
                f"[DEVICES] Scan error: {exc}"
            )

    def handle_devices_discovered(
        self,
        devices,
    ):
        """
        Display every BLE device returned by the BLE service.

        No filtering is performed here. HealthSync compatibility
        is determined by the BLE backend/service discovery process.
        """

        self.is_scanning = False

        self.scan_button.setEnabled(True)
        self.scan_button.setText(
            "↻  Scan for Devices"
        )

        self.clear_nearby_devices()

        if not devices:
            self.set_scan_status(
                "No BLE devices were found nearby."
            )
            return

        self.set_scan_status(
            f"{len(devices)} Bluetooth device(s) found."
        )

        for device in devices:
            self.add_nearby_device(device)

    # ========================================================
    # NEARBY DEVICE CARD
    # ========================================================

    def add_nearby_device(
        self,
        device,
    ):
        """
        Add one discovered BLE device to the nearby list.
        """

        if not isinstance(device, dict):
            return

        device_name = (
            device.get("name")
            or "Unknown Bluetooth Device"
        )

        device_address = (
            device.get("address")
            or device.get("id")
            or "--"
        )

        card = QFrame()
        card.setObjectName("nearby_device_card")

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

        icon = QLabel("◉")
        icon.setObjectName("device_icon")
        icon.setFixedWidth(30)

        layout.addWidget(icon)

        information = QVBoxLayout()
        information.setSpacing(4)

        name = QLabel(device_name)
        name.setObjectName("nearby_device_name")

        address = QLabel(device_address)
        address.setObjectName(
            "nearby_device_address"
        )

        information.addWidget(name)
        information.addWidget(address)

        layout.addLayout(information)
        layout.addStretch()

        type_label = QLabel("Bluetooth LE")
        type_label.setObjectName(
            "device_type_badge"
        )

        layout.addWidget(type_label)

        connect_button = QPushButton("Connect")
        connect_button.setObjectName(
            "connect_button"
        )

        connect_button.setMinimumHeight(38)
        connect_button.setMinimumWidth(105)

        connect_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        connect_button.clicked.connect(
            lambda checked=False,
            address=device_address:
            self.connect_to_device(address)
        )

        layout.addWidget(connect_button)

        self.nearby_devices_container.addWidget(card)

    # ========================================================
    # BLE CONNECTION ACTIONS
    # ========================================================

    def connect_to_device(
        self,
        device_address: str,
    ):
        """
        Request a connection to the selected BLE device.

        The BLE backend decides whether the device exposes the
        HealthSync A001 service.
        """

        if self.ble_service is None:
            self.set_scan_status(
                "BLE service is unavailable.",
                error=True,
            )
            return

        if not device_address or device_address == "--":
            self.set_scan_status(
                "Selected Bluetooth device has no valid address.",
                error=True,
            )
            return

        self.current_device_address = device_address
        self.is_connecting = True

        self.set_connection_state("CONNECTING")

        self.set_scan_status(
            "Connecting to selected Bluetooth device..."
        )

        try:
            self.ble_service.connect_device(
                device_address
            )

        except Exception as exc:
            self.is_connecting = False

            self.set_connection_state(
                "DISCONNECTED"
            )

            self.set_scan_status(
                "Unable to connect to the selected device.",
                error=True,
            )

            print(
                f"[DEVICES] Connection error: {exc}"
            )

    def disconnect_device(self):
        """
        Request a manual BLE disconnect.
        """

        if self.ble_service is None:
            return

        self.is_connecting = False

        self.set_scan_status(
            "Disconnecting from Bluetooth device..."
        )

        try:
            self.ble_service.disconnect_device()

        except Exception as exc:
            self.set_scan_status(
                "Unable to disconnect from the Bluetooth device.",
                error=True,
            )

            print(
                f"[DEVICES] Disconnect error: {exc}"
            )

    # ========================================================
    # BLE STATUS EVENTS
    # ========================================================

    def handle_ble_status(
        self,
        status: str,
    ):
        """
        React to BLE integration state messages.
        """

        if status is None:
            return

        status_text = str(status).strip()

        if not status_text:
            return

        status_lower = status_text.lower()

        # ----------------------------------------------------
        # Scan state
        # ----------------------------------------------------

        if (
            "scanning" in status_lower
            and "complete" not in status_lower
        ):
            self.is_scanning = True

            self.scan_button.setEnabled(False)
            self.scan_button.setText(
                "Scanning..."
            )

            self.set_scan_status(status_text)
            return

        if (
            "scan complete" in status_lower
            or "scan completed" in status_lower
        ):
            self.is_scanning = False

            self.scan_button.setEnabled(True)
            self.scan_button.setText(
                "↻  Scan for Devices"
            )

            self.set_scan_status(status_text)
            return

        # ----------------------------------------------------
        # Connecting
        # ----------------------------------------------------

        if "connecting" in status_lower:
            self.is_connecting = True

            self.set_connection_state(
                "CONNECTING"
            )

            self.set_scan_status(status_text)
            return

        # ----------------------------------------------------
        # Reconnecting
        # ----------------------------------------------------

        if "reconnecting" in status_lower:
            self.is_connecting = True

            self.set_connection_state(
                "RECONNECTING"
            )

            self.set_scan_status(status_text)
            return

        # ----------------------------------------------------
        # Connected
        # ----------------------------------------------------

        if "connected" in status_lower:
            self.is_connecting = False

            self.set_connection_state(
                "CONNECTED"
            )

            self.set_scan_status(status_text)

            self.load_devices()
            return

        # ----------------------------------------------------
        # Disconnected
        # ----------------------------------------------------

        if "disconnected" in status_lower:
            self.is_connecting = False

            self.set_connection_state(
                "DISCONNECTED"
            )

            self.set_scan_status(status_text)

            self.load_devices()
            return

        # ----------------------------------------------------
        # Failed / error
        # ----------------------------------------------------

        if (
            "failed" in status_lower
            or "error" in status_lower
            or "unable" in status_lower
        ):
            self.is_connecting = False

            self.set_connection_state(
                "DISCONNECTED"
            )

            self.set_scan_status(
                status_text,
                error=True,
            )
            return

        self.set_scan_status(status_text)

    def set_connection_state(
        self,
        state: str,
    ):
        """
        Update the connected-device card based on BLE state.
        """

        state_upper = str(state).upper()

        if state_upper == "CONNECTED":
            self.connection_status.setText(
                "●  CONNECTED"
            )

            self.connection_status.setObjectName(
                "status_connected"
            )

            self.disconnect_button.setEnabled(
                self.ble_service is not None
            )

            self.refresh_widget_style(
                self.connection_status
            )

            return

        if state_upper == "CONNECTING":
            self.connection_status.setText(
                "●  CONNECTING"
            )

            self.connection_status.setObjectName(
                "status_connecting"
            )

            self.disconnect_button.setEnabled(False)

            self.refresh_widget_style(
                self.connection_status
            )

            return

        if state_upper == "RECONNECTING":
            self.connection_status.setText(
                "●  RECONNECTING"
            )

            self.connection_status.setObjectName(
                "status_reconnecting"
            )

            self.disconnect_button.setEnabled(False)

            self.refresh_widget_style(
                self.connection_status
            )

            return

        self.connection_status.setText(
            "●  DISCONNECTED"
        )

        self.connection_status.setObjectName(
            "status_disconnected"
        )

        self.disconnect_button.setEnabled(False)

        self.refresh_widget_style(
            self.connection_status
        )

    # ========================================================
    # TELEMETRY EVENTS
    # ========================================================

    def handle_telemetry(
        self,
        telemetry,
    ):
        """
        React to a valid telemetry snapshot.

        No synthetic values are generated.
        """

        self.telemetry_received_at = datetime.now()

        battery = getattr(
            telemetry,
            "battery",
            None,
        )

        if battery is not None:
            self.battery_value.setText(
                f"{battery}%"
            )

        self.telemetry_status.setText(
            "●  LIVE DATA RECEIVING"
        )

        self.telemetry_status.setObjectName(
            "telemetry_live"
        )

        self.telemetry_detail.setText(
            "Telemetry data is being received from the connected device."
        )

        self.refresh_widget_style(
            self.telemetry_status
        )

        self.updated_value.setText(
            "Just now"
        )

        self.set_connection_state(
            "CONNECTED"
        )

    # ========================================================
    # BLE ERRORS
    # ========================================================

    def handle_ble_error(
        self,
        error: str,
    ):
        self.is_scanning = False
        self.is_connecting = False

        self.scan_button.setEnabled(True)
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

    # ========================================================
    # DATABASE
    # ========================================================

    def load_devices(self):
        """
        Load only devices belonging to the authenticated user.

        Existing user isolation is preserved:

            WHERE user_id = ?
        """

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
            self.add_saved_device(row)

    def show_connected_device(
        self,
        row,
    ):
        self.current_device_id = row["id"]

        self.current_device_address = (
            row["device_address"]
        )

        self.set_connection_state(
            "CONNECTED"
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
            self.battery_value.setText("--")
        else:
            self.battery_value.setText(
                f"{battery}%"
            )

        if self.telemetry_received_at is None:
            self.telemetry_status.setText(
                "○  WAITING FOR DATA"
            )

            self.telemetry_status.setObjectName(
                "telemetry_waiting"
            )

            self.telemetry_detail.setText(
                "Connected successfully. Waiting for telemetry..."
            )

            self.refresh_widget_style(
                self.telemetry_status
            )

    def show_no_connected_device(self):
        self.current_device_id = None
        self.current_device_address = None

        self.set_connection_state(
            "DISCONNECTED"
        )

        self.device_name.setText(
            "No device connected"
        )

        self.device_type.setText(
            "Waiting for a HealthSync device..."
        )

        self.battery_value.setText("--")
        self.updated_value.setText("--")
        self.connection_value.setText("Bluetooth LE")

        self.device_id_value.setText(
            "Device ID: --"
        )

        self.service_value.setText(
            "Service: A001"
        )

        self.source_value.setText(
            "Source: BLE"
        )

        self.telemetry_status.setText(
            "○  WAITING FOR DATA"
        )

        self.telemetry_status.setObjectName(
            "telemetry_waiting"
        )

        self.telemetry_detail.setText(
            "Connect a HealthSync-compatible device to receive telemetry."
        )

        self.refresh_widget_style(
            self.telemetry_status
        )

        self.telemetry_received_at = None

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

    # ========================================================
    # SAVED DEVICES
    # ========================================================

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

        layout.setSpacing(10)

        icon = QLabel("◉")
        icon.setObjectName(
            "saved_device_icon"
        )

        icon.setFixedWidth(30)

        layout.addWidget(icon)

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

        information.addWidget(name)
        information.addWidget(details)

        layout.addLayout(information)
        layout.addStretch()

        status_text = row["status"] or "UNKNOWN"

        status = QLabel(status_text)

        status.setObjectName(
            self.get_saved_status_object_name(
                status_text
            )
        )

        layout.addWidget(status)

        self.saved_devices_container.addWidget(card)

    @staticmethod
    def get_saved_status_object_name(
        status: str,
    ) -> str:
        status_upper = str(status).upper()

        if status_upper == "CONNECTED":
            return "saved_device_status"

        if status_upper == "RECONNECTING":
            return "saved_device_status_reconnecting"

        if status_upper == "CONNECTING":
            return "saved_device_status_connecting"

        return "saved_device_status_disconnected"

    # ========================================================
    # HELPERS
    # ========================================================

    def clear_nearby_devices(self):
        while self.nearby_devices_container.count():
            item = self.nearby_devices_container.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def clear_saved_devices(self):
        while self.saved_devices_container.count():
            item = self.saved_devices_container.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def set_scan_status(
        self,
        text,
        error=False,
    ):
        self.scan_status.setText(str(text))

        self.scan_indicator.setText("●")

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

    # ========================================================
    # PAGE STYLING
    # ========================================================

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

            #status_connecting {
                color: #90C2E7;
                font-size: 12px;
                font-weight: 700;
            }

            #status_reconnecting {
                color: #F2C14E;
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

            #telemetry_status_card {
                background: #091A26;
                border: 1px solid #173044;
                border-radius: 10px;
            }

            #telemetry_heading {
                color: #648398;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 1px;
            }

            #telemetry_live {
                color: #39D98A;
                font-size: 12px;
                font-weight: 700;
            }

            #telemetry_waiting {
                color: #90A8B8;
                font-size: 12px;
                font-weight: 700;
            }

            #telemetry_detail {
                color: #6F95AA;
                font-size: 11px;
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

            #saved_device_status_connecting {
                color: #90C2E7;
                background: #102D3D;
                border-radius: 7px;
                padding: 6px 10px;
                font-size: 10px;
                font-weight: 700;
            }

            #saved_device_status_reconnecting {
                color: #F2C14E;
                background: #302A17;
                border-radius: 7px;
                padding: 6px 10px;
                font-size: 10px;
                font-weight: 700;
            }

            #saved_device_status_disconnected {
                color: #90A8B8;
                background: #17242D;
                border-radius: 7px;
                padding: 6px 10px;
                font-size: 10px;
                font-weight: 700;
            }
            """
        )
