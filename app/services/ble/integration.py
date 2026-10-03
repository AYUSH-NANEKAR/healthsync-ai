import asyncio

from PySide6.QtCore import QObject, QThread, Signal, Slot

from app.database.device_repository import DeviceRepository
from app.database.telemetry_repository import TelemetryRepository
from app.services.ble.manager import BLEManager
from app.services.health_service import HealthService


class BLEIntegrationWorker(QObject):
    """
    Runs the BLE integration pipeline in a background thread.

    Responsibilities:
    - Maintain the asyncio BLE event loop.
    - Scan for nearby BLE devices.
    - Connect to a selected BLE device.
    - Register HealthSync devices in SQLite.
    - Connect BLE telemetry to HealthService.
    - Forward telemetry and status to the application.
    - Handle manual BLE disconnection.
    - Preserve BLEManager automatic reconnect behavior.

    The worker does not automatically scan or connect when the
    application starts.
    """

    telemetry_received = Signal(object)
    status_changed = Signal(str)
    error_occurred = Signal(str)
    devices_discovered = Signal(object)
    finished = Signal()

    def __init__(self, user_id: int):
        super().__init__()

        self.user_id = user_id

        self.ble_manager = None
        self.health_service = None

        self.device_repository = DeviceRepository()
        self.telemetry_repository = TelemetryRepository()

        self.device_id = None

        self.discovered_devices = {}

        self.loop = None
        self._shutdown_requested = False

        self._connected_device_address = None
        self._connected_device_name = None
        self._is_healthsync_device = False

    # ============================================================
    # WORKER STARTUP
    # ============================================================

    @Slot()
    def run(self):
        """
        Start the worker's asyncio event loop.

        Important:
        The worker starts the BLE system but does NOT scan or
        automatically connect to a device.
        """

        try:

            self.loop = asyncio.new_event_loop()

            asyncio.set_event_loop(
                self.loop
            )

            self.loop.create_task(
                self._startup()
            )

            self.loop.run_forever()

        except Exception as error:

            self.error_occurred.emit(
                f"{type(error).__name__}: {error}"
            )

        finally:

            if self.loop is not None:

                try:
                    pending_tasks = (
                        asyncio.all_tasks(
                            self.loop
                        )
                    )

                    for task in pending_tasks:
                        task.cancel()

                except Exception:
                    pass

                try:
                    self.loop.close()
                except Exception:
                    pass

            self.finished.emit()

    async def _startup(self):
        """
        Initialize BLEManager only.

        No scan and no automatic connection happen here.
        """

        try:

            self.ble_manager = BLEManager(
                on_telemetry=self._handle_ble_telemetry,
                on_status=self._handle_ble_status,
            )

            self.status_changed.emit(
                "BLE service ready. Press Scan for Devices to begin."
            )

        except Exception as error:

            self.error_occurred.emit(
                f"{type(error).__name__}: {error}"
            )

    # ============================================================
    # SCANNING
    # ============================================================

    async def scan_devices(self):
        """
        Scan for all nearby BLE devices.

        The scan is not restricted to HealthSync Band.
        """

        if self.ble_manager is None:

            self.ble_manager = BLEManager(
                on_telemetry=self._handle_ble_telemetry,
                on_status=self._handle_ble_status,
            )

        try:

            self.status_changed.emit(
                "Scanning for nearby BLE devices..."
            )

            devices = await self.ble_manager.scan_devices(
                timeout=5
            )

            self.discovered_devices.clear()

            results = []

            for device in devices:

                address = device.address

                if not address:
                    continue

                self.discovered_devices[
                    address
                ] = device

                results.append(
                    {
                        "name": device.name or "Unknown",
                        "address": address,
                    }
                )

            self.devices_discovered.emit(
                results
            )

            self.status_changed.emit(
                f"BLE scan complete. "
                f"Found {len(results)} device(s)."
            )

        except Exception as error:

            self.error_occurred.emit(
                f"BLE scan error: {error}"
            )

    # ============================================================
    # CONNECTION
    # ============================================================

    async def connect_device(
        self,
        device_address: str,
    ):
        """
        Connect to a device selected by the UI.
        """

        device = self.discovered_devices.get(
            device_address
        )

        if device is None:

            self.error_occurred.emit(
                "Selected BLE device is no longer available."
            )

            return

        try:

            if self.ble_manager is None:

                self.ble_manager = BLEManager(
                    on_telemetry=self._handle_ble_telemetry,
                    on_status=self._handle_ble_status,
                )

            # If another device is connected, manually disconnect
            # it before connecting to the newly selected device.
            if self.ble_manager.is_connected:

                await self._disconnect_current_device()

            # If a reconnect operation is currently active,
            # stop that connection before selecting another device.
            if self.ble_manager.is_reconnecting:

                await self._disconnect_current_device()

            await self._connect_device(
                device
            )

        except Exception as error:

            self.error_occurred.emit(
                f"BLE connection error: {error}"
            )

    async def _connect_device(
        self,
        device,
    ):
        """
        Connect to a BLEDevice.

        HealthSync compatibility is determined after the BLE
        connection is established by inspecting the actual
        HealthSync A001 service.
        """

        device_name = (
            device.name or "Unknown BLE device"
        )

        self.status_changed.emit(
            f"Connecting to {device_name}..."
        )

        self._connected_device_address = None
        self._connected_device_name = None
        self._is_healthsync_device = False

        # The BLE manager performs the actual BLE connection
        # and service discovery.
        connected = await self.ble_manager.connect(
            device
        )

        if not connected:

            self.status_changed.emit(
                f"Failed to connect to {device_name}."
            )

            return

        self._connected_device_address = (
            device.address
        )

        self._connected_device_name = (
            device_name
        )

        self._is_healthsync_device = (
            self.ble_manager.is_healthsync_device
        )

        # --------------------------------------------------------
        # HealthSync device
        # --------------------------------------------------------

        if self._is_healthsync_device:

            await self._configure_healthsync_device(
                device
            )

            if self.device_id is not None:

                self.status_changed.emit(
                    f"HealthSync device connected. "
                    f"Device ID: {self.device_id}"
                )

            return

        # --------------------------------------------------------
        # Generic BLE device
        # --------------------------------------------------------

        self.device_id = None
        self.health_service = None

        self.status_changed.emit(
            f"{device_name} connected. "
            "HealthSync telemetry unavailable."
        )

    async def _configure_healthsync_device(
        self,
        device,
    ):
        """
        Register or restore the user-owned HealthSync device
        and create its HealthService pipeline.

        This method is called only after the actual A001
        HealthSync service has been detected.
        """

        existing_device = (
            self.device_repository.find_by_address(
                self.user_id,
                device.address,
            )
        )

        if existing_device is not None:

            self.device_id = (
                existing_device["id"]
            )

            self.device_repository.mark_connected(
                self.device_id
            )

            self.status_changed.emit(
                f"Using existing device ID "
                f"{self.device_id}"
            )

        else:

            self.device_id = (
                self.device_repository.create(
                    user_id=self.user_id,
                    device_name=(
                        device.name
                        or BLEManager.DEVICE_NAME
                    ),
                    device_address=device.address,
                    device_type="BLE_WEARABLE",
                    connection_type="BLE",
                    service_uuid=BLEManager.SERVICE_UUID,
                )
            )

            self.status_changed.emit(
                f"Registered new device ID "
                f"{self.device_id}"
            )

        if self.device_id is None:

            self.health_service = None

            raise RuntimeError(
                "Unable to create or restore the BLE device record."
            )

        self.health_service = HealthService(
            user_id=self.user_id,
            device_id=self.device_id,
            telemetry_repository=self.telemetry_repository,
            on_telemetry=self._handle_health_telemetry,
        )

    # ============================================================
    # BLE MANAGER STATUS
    # ============================================================

    def _handle_ble_status(
        self,
        status: str,
    ):
        """
        Receive low-level BLE lifecycle status from BLEManager
        and forward it to the Qt application.

        Database state is changed here only when the manager has
        reached a final disconnected state.
        """

        self.status_changed.emit(
            status
        )

        status_lower = status.lower()

        # --------------------------------------------------------
        # Unexpected disconnect
        # --------------------------------------------------------

        if (
            "connection lost unexpectedly"
            in status_lower
        ):

            self.status_changed.emit(
                "BLE connection lost. Attempting automatic reconnect..."
            )

            return

        # --------------------------------------------------------
        # Reconnecting
        # --------------------------------------------------------

        if (
            "reconnecting"
            in status_lower
        ):

            return

        # --------------------------------------------------------
        # Reconnected
        # --------------------------------------------------------

        if (
            "reconnected"
            in status_lower
        ):

            # The existing device ID and HealthService remain
            # associated with this user/device.
            return

        # --------------------------------------------------------
        # Final disconnect
        # --------------------------------------------------------

        if (
            "automatic reconnection failed"
            in status_lower
        ):

            self._mark_current_device_disconnected()

            return

        if (
            status_lower == "ble device disconnected."
        ):

            self._mark_current_device_disconnected()

    def _mark_current_device_disconnected(self):
        """
        Mark the current user-owned HealthSync device as
        disconnected in SQLite.
        """

        if self.device_id is not None:

            try:

                self.device_repository.mark_disconnected(
                    self.device_id
                )

            except Exception as error:

                self.error_occurred.emit(
                    f"Failed to update device status: {error}"
                )

        self.device_id = None
        self.health_service = None

        self._connected_device_address = None
        self._connected_device_name = None
        self._is_healthsync_device = False

    # ============================================================
    # TELEMETRY
    # ============================================================

    def _handle_ble_telemetry(
        self,
        telemetry,
    ):
        """
        Receive complete telemetry from BLEManager.

        Only HealthSync devices are passed to HealthService.
        """

        if not self._is_healthsync_device:

            return

        if self.health_service is None:

            return

        try:

            self.health_service.process_telemetry(
                telemetry
            )

        except Exception as error:

            self.error_occurred.emit(
                f"Telemetry processing error: {error}"
            )

    def _handle_health_telemetry(
        self,
        telemetry,
    ):
        """
        Forward processed telemetry to the Qt application.
        """

        self.telemetry_received.emit(
            telemetry
        )

    # ============================================================
    # MANUAL DISCONNECT
    # ============================================================

    async def disconnect_device(self):
        """
        Manually disconnect the current BLE device.

        This is intentionally separate from shutdown().

        Manual disconnect:
            - disconnects the BLE device
            - marks the saved device disconnected
            - clears HealthService
            - DOES NOT trigger automatic reconnect
            - keeps the BLE worker alive
        """

        if self.ble_manager is None:

            self._mark_current_device_disconnected()

            self.status_changed.emit(
                "BLE device disconnected."
            )

            return

        try:

            await self.ble_manager.disconnect()

        except Exception as error:

            self.error_occurred.emit(
                f"BLE disconnect error: {error}"
            )

        finally:

            self._mark_current_device_disconnected()

            self.status_changed.emit(
                "BLE device disconnected."
            )

    async def _disconnect_current_device(self):
        """
        Disconnect the currently connected BLE device before
        connecting another selected device.
        """

        if self.ble_manager is None:

            return

        if (
            not self.ble_manager.is_connected
            and not self.ble_manager.is_reconnecting
        ):

            return

        current_device_id = (
            self.device_id
        )

        try:

            await self.ble_manager.disconnect()

        finally:

            if current_device_id is not None:

                self.device_repository.mark_disconnected(
                    current_device_id
                )

            self.device_id = None
            self.health_service = None

            self._connected_device_address = None
            self._connected_device_name = None
            self._is_healthsync_device = False

            self.status_changed.emit(
                "BLE device disconnected."
            )

    # ============================================================
    # SHUTDOWN
    # ============================================================

    async def shutdown(self):
        """
        Gracefully stop BLE integration.

        This is different from normal Disconnect.

        Shutdown:
            - manually disconnects BLE
            - prevents automatic reconnect
            - stops the asyncio event loop
        """

        if self._shutdown_requested:

            return

        self._shutdown_requested = True

        try:

            if self.ble_manager is not None:

                await self.ble_manager.disconnect()

            self._mark_current_device_disconnected()

        except Exception as error:

            self.error_occurred.emit(
                f"BLE shutdown error: {error}"
            )

        finally:

            if self.loop is not None:

                self.loop.stop()

    # ============================================================
    # THREAD-SAFE REQUESTS
    # ============================================================

    def request_scan(self):
        """
        Schedule a BLE scan on the worker's asyncio loop.
        """

        if self.loop is None:

            self.error_occurred.emit(
                "BLE worker is not ready."
            )

            return

        if self._shutdown_requested:

            self.error_occurred.emit(
                "BLE service is shutting down."
            )

            return

        asyncio.run_coroutine_threadsafe(
            self.scan_devices(),
            self.loop,
        )

    def request_connect(
        self,
        device_address: str,
    ):
        """
        Schedule a BLE connection on the worker's asyncio loop.
        """

        if self.loop is None:

            self.error_occurred.emit(
                "BLE worker is not ready."
            )

            return

        if self._shutdown_requested:

            self.error_occurred.emit(
                "BLE service is shutting down."
            )

            return

        asyncio.run_coroutine_threadsafe(
            self.connect_device(
                device_address
            ),
            self.loop,
        )

    def request_disconnect(self):
        """
        Schedule a manual BLE disconnect.
        """

        if self.loop is None:

            self.error_occurred.emit(
                "BLE worker is not ready."
            )

            return

        asyncio.run_coroutine_threadsafe(
            self.disconnect_device(),
            self.loop,
        )

    def request_shutdown(self):
        """
        Schedule graceful worker shutdown.
        """

        if self.loop is None:

            return

        asyncio.run_coroutine_threadsafe(
            self.shutdown(),
            self.loop,
        )


class BLEIntegrationService(QObject):
    """
    Application-level controller for BLE.

    UI communicates with this class instead of talking
    directly to BLEManager.
    """

    telemetry_received = Signal(object)
    status_changed = Signal(str)
    error_occurred = Signal(str)
    devices_discovered = Signal(object)

    def __init__(self, user_id: int):
        super().__init__()

        self.user_id = user_id

        self.thread = QThread()

        self.worker = BLEIntegrationWorker(
            user_id=user_id
        )

        self.worker.moveToThread(
            self.thread
        )

        self.thread.started.connect(
            self.worker.run
        )

        self.worker.telemetry_received.connect(
            self.telemetry_received
        )

        self.worker.status_changed.connect(
            self.status_changed
        )

        self.worker.error_occurred.connect(
            self.error_occurred
        )

        self.worker.devices_discovered.connect(
            self.devices_discovered
        )

        self.worker.finished.connect(
            self.thread.quit
        )

        self.worker.finished.connect(
            self.worker.deleteLater
        )

        self.thread.finished.connect(
            self.thread.deleteLater
        )

    # ============================================================
    # SERVICE CONTROL
    # ============================================================

    def start(self):
        """
        Start the BLE background thread.

        Starting the service does NOT scan or connect.
        """

        if not self.thread.isRunning():

            self.thread.start()

    def scan_devices(self):
        """
        Request a nearby BLE scan.
        """

        self.worker.request_scan()

    def connect_device(
        self,
        device_address: str,
    ):
        """
        Request connection to a device selected by the UI.
        """

        self.worker.request_connect(
            device_address
        )

    def disconnect_device(self):
        """
        Manually disconnect the currently connected device.

        The BLE worker remains running so the user can scan
        and connect again without restarting the application.
        """

        self.worker.request_disconnect()

    def stop(self):
        """
        Gracefully stop BLE integration completely.

        This should be used when the application/page lifecycle
        requires shutting down the BLE background service, not
        for the normal Disconnect button.
        """

        self.worker.request_shutdown()