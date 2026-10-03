from collections.abc import Callable

from bleak import BleakClient, BleakScanner

from app.models.telemetry import HealthTelemetry
from app.services.ble.parser import BLETelemetryParser


class BLEManager:
    """
    Handles Bluetooth Low Energy scanning and connections.

    Responsibilities:
    - Scan for nearby BLE devices.
    - Connect to a selected BLE device.
    - Subscribe to HealthSync telemetry characteristics.
    - Pass raw notifications to BLETelemetryParser.
    - Notify the application when telemetry changes.

    This class does not know anything about:
    - SQLite
    - PySide6
    - AI
    - Dashboard pages
    """

    DEVICE_NAME = "HealthSync Band"

    SERVICE_UUID = "0000A001-0000-1000-8000-00805F9B34FB"

    CHARACTERISTIC_UUIDS = [
        "0000A002-0000-1000-8000-00805F9B34FB",
        "0000A003-0000-1000-8000-00805F9B34FB",
        "0000A004-0000-1000-8000-00805F9B34FB",
        "0000A005-0000-1000-8000-00805F9B34FB",
        "0000A006-0000-1000-8000-00805F9B34FB",
        "0000A007-0000-1000-8000-00805F9B34FB",
        "0000A008-0000-1000-8000-00805F9B34FB",
        "0000A009-0000-1000-8000-00805F9B34FB",
        "0000A00A-0000-1000-8000-00805F9B34FB",
        "0000A00B-0000-1000-8000-00805F9B34FB",
        "0000A00C-0000-1000-8000-00805F9B34FB",
    ]

    def __init__(
        self,
        on_telemetry: Callable[[HealthTelemetry], None] | None = None,
    ):
        self.on_telemetry = on_telemetry

        self.client: BleakClient | None = None
        self.device = None

        self.parser = BLETelemetryParser()

        self._running = False

    async def scan_devices(self, timeout: float = 5.0):
        """
        Scan for nearby BLE devices.

        Returns:
            list[BLEDevice]:
                Devices discovered during the scan.
        """

        print(
            f"Scanning for nearby BLE devices "
            f"for {timeout} seconds..."
        )

        devices = await BleakScanner.discover(
            timeout=timeout
        )

        print(
            f"BLE scan complete. "
            f"Found {len(devices)} device(s)."
        )

        for device in devices:
            print(
                f"Found: "
                f"{device.name or 'Unknown'} "
                f"| Address: {device.address}"
            )

        return devices

    async def find_device(self):
        """
        Find the HealthSync Band by name.

        This method is kept temporarily for compatibility
        with the existing integration service.

        The new Devices page will eventually use
        scan_devices() instead.
        """

        print("Searching for HealthSync Band...")

        device = await BleakScanner.find_device_by_name(
            self.DEVICE_NAME,
            timeout=10,
        )

        if device is None:
            print("HealthSync Band not found.")
            return None

        self.device = device

        print(
            f"Found: {device.name}"
        )

        print(
            f"Address: {device.address}"
        )

        return device

    async def connect(self, device=None):
        """
        Connect to a selected BLE device.

        Args:
            device:
                A BLEDevice returned by scan_devices().

                If no device is supplied, the method temporarily
                falls back to finding the HealthSync Band by name.
                This keeps the existing integration service working
                until it is refactored.
        """

        if device is None:
            device = await self.find_device()

        if device is None:
            return False

        self.device = device

        print(
            f"Connecting to "
            f"{device.name or 'Unknown BLE device'}..."
        )

        self.client = BleakClient(device)

        try:
            await self.client.connect()

            if not self.client.is_connected:
                print("Connection failed.")

                self.client = None

                return False

            print("Connected: True")

            if self._is_healthsync_device():
                await self._subscribe_to_notifications()

                print(
                    "HealthSync BLE notifications active."
                )

            else:
                print(
                    "Connected device is not a "
                    "HealthSync telemetry device."
                )

            self._running = True

            return True

        except Exception as error:
            print(
                f"BLE connection error: {error}"
            )

            self.client = None
            self.device = None

            return False

    def _is_healthsync_device(self) -> bool:
        """
        Determine whether the connected BLE device
        exposes the HealthSync service.
        """

        if self.client is None:
            return False

        services = self.client.services

        for service in services:
            if service.uuid.lower() == self.SERVICE_UUID.lower():
                return True

        return False

    async def _subscribe_to_notifications(self):
        """
        Subscribe to all HealthSync telemetry characteristics.
        """

        if self.client is None:
            raise RuntimeError(
                "BLE client is not connected."
            )

        print(
            "Subscribing to HealthSync characteristics..."
        )

        available_characteristics = {
            characteristic.uuid.lower(): characteristic
            for service in self.client.services
            for characteristic in service.characteristics
        }

        for uuid in self.CHARACTERISTIC_UUIDS:
            characteristic = available_characteristics.get(
                uuid.lower()
            )

            if characteristic is None:
                print(
                    f"Characteristic not found: {uuid}"
                )
                continue

            if "notify" not in characteristic.properties:
                print(
                    f"Notifications not supported: {uuid}"
                )
                continue

            await self.client.start_notify(
                characteristic,
                self._notification_handler,
            )

            print(
                f"Subscribed: {uuid}"
            )

    def _notification_handler(
        self,
        characteristic,
        data: bytearray,
    ):
        """
        Receive and parse BLE notification data.
        """

        try:
            self.parser.update(
                characteristic.uuid,
                bytes(data),
            )

            if self.parser.is_complete():
                telemetry = self.parser.get_snapshot()

                if (
                    telemetry is not None
                    and self.on_telemetry is not None
                ):
                    self.on_telemetry(
                        telemetry
                    )

                self.parser.reset_snapshot()

        except Exception as error:
            print(
                "Failed to process BLE notification "
                f"{characteristic.uuid}: {error}"
            )

    async def disconnect(self):
        """
        Disconnect from the currently connected BLE device.
        """

        self._running = False

        if self.client is None:
            return

        if self.client.is_connected:
            print(
                "Disconnecting from BLE device..."
            )

            await self.client.disconnect()

        self.client = None
        self.device = None

        self.parser.reset_snapshot()

        print("Disconnected.")

    @property
    def is_connected(self) -> bool:
        """
        Return the current BLE connection state.
        """

        return (
            self.client is not None
            and self.client.is_connected
        )