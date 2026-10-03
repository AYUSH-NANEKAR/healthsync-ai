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

    @Slot()
    def run(self):
        """
        Start the worker's asyncio event loop.
        """

        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

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
                self.loop.close()

            self.finished.emit()

    async def _startup(self):
        """
        Preserve the existing application behavior:
        automatically connect to HealthSync Band at startup.
        """

        try:
            self.ble_manager = BLEManager(
                on_telemetry=self._handle_ble_telemetry
            )

            self.status_changed.emit(
                "Searching for HealthSync Band..."
            )

            device = await self.ble_manager.find_device()

            if device is None:
                self.status_changed.emit(
                    "HealthSync Band not found."
                )
                return

            await self._connect_device(device)

        except Exception as error:
            self.error_occurred.emit(
                f"{type(error).__name__}: {error}"
            )

    async def scan_devices(self):
        """
        Scan for nearby BLE devices.
        """

        if self.ble_manager is None:
            self.ble_manager = BLEManager(
                on_telemetry=self._handle_ble_telemetry
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

    async def connect_device(
        self,
        device_address: str,
    ):
        """
        Connect to a device discovered by scan_devices().
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
                    on_telemetry=self._handle_ble_telemetry
                )

            if self.ble_manager.is_connected:
                await self._disconnect_current_device()

            await self._connect_device(device)

        except Exception as error:
            self.error_occurred.emit(
                f"BLE connection error: {error}"
            )

    async def _connect_device(self, device):
        """
        Connect a BLEDevice and configure HealthSync
        application services when applicable.
        """

        device_name = device.name or "Unknown BLE device"

        self.status_changed.emit(
            f"Connecting to {device_name}..."
        )

        is_healthsync = (
            device.name == BLEManager.DEVICE_NAME
        )

        if is_healthsync:
            existing_device = (
                self.device_repository.find_by_address(
                    self.user_id,
                    device.address,
                )
            )

            if existing_device is not None:
                self.device_id = existing_device["id"]

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
                        device_name=device_name,
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

            self.health_service = HealthService(
                user_id=self.user_id,
                device_id=self.device_id,
                telemetry_repository=self.telemetry_repository,
                on_telemetry=self._handle_health_telemetry,
            )

        connected = await self.ble_manager.connect(
            device
        )

        if not connected:
            if (
                is_healthsync
                and self.device_id is not None
            ):
                self.device_repository.mark_disconnected(
                    self.device_id
                )

            self.status_changed.emit(
                f"Failed to connect to {device_name}."
            )

            return

        if is_healthsync:
            self.status_changed.emit(
                "HealthSync Band connected."
            )
        else:
            self.status_changed.emit(
                f"{device_name} connected."
            )

    def _handle_ble_telemetry(
        self,
        telemetry,
    ):
        """
        Receive complete telemetry from BLEManager.

        HealthSync telemetry is passed through HealthService
        before reaching the application.
        """

        if self.health_service is None:
            return

        self.health_service.process_telemetry(
            telemetry
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

    async def _disconnect_current_device(self):
        """
        Disconnect the currently connected BLE device.
        """

        if self.ble_manager is None:
            return

        if not self.ble_manager.is_connected:
            return

        current_device_id = self.device_id

        await self.ble_manager.disconnect()

        if current_device_id is not None:
            self.device_repository.mark_disconnected(
                current_device_id
            )

        self.device_id = None
        self.health_service = None

        self.status_changed.emit(
            "BLE device disconnected."
        )

    async def shutdown(self):
        """
        Gracefully stop the BLE worker.
        """

        if self._shutdown_requested:
            return

        self._shutdown_requested = True

        try:
            await self._disconnect_current_device()

        finally:
            if self.loop is not None:
                self.loop.stop()

    def request_scan(self):
        """
        Schedule a BLE scan on the worker's asyncio loop.
        """

        if self.loop is None:
            self.error_occurred.emit(
                "BLE worker is not ready."
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
        Schedule a BLE connection on the worker's
        asyncio loop.
        """

        if self.loop is None:
            self.error_occurred.emit(
                "BLE worker is not ready."
            )
            return

        asyncio.run_coroutine_threadsafe(
            self.connect_device(
                device_address
            ),
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

    def start(self):
        """
        Start the BLE background thread.
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
        Connect to a device selected by the UI.
        """

        self.worker.request_connect(
            device_address
        )

    def stop(self):
        """
        Gracefully stop BLE integration.
        """

        self.worker.request_shutdown()