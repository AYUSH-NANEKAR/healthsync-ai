import asyncio
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
    - Detect HealthSync service availability.
    - Subscribe to HealthSync telemetry characteristics.
    - Pass raw notifications to BLETelemetryParser.
    - Notify the application when telemetry changes.
    - Detect unexpected disconnections.
    - Automatically reconnect after unexpected disconnection.

    This class does not know anything about:
    - SQLite
    - PySide6
    - AI
    - Dashboard pages
    - HealthService
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

    MAX_RECONNECT_ATTEMPTS = 5
    RECONNECT_DELAY = 3.0

    def __init__(
        self,
        on_telemetry: Callable[[HealthTelemetry], None] | None = None,
        on_status: Callable[[str], None] | None = None,
    ):
        self.on_telemetry = on_telemetry
        self.on_status = on_status

        self.client: BleakClient | None = None
        self.device = None

        self.parser = BLETelemetryParser()

        self._running = False
        self._manual_disconnect = False
        self._reconnecting = False
        self._reconnect_task = None

    # ============================================================
    # STATUS
    # ============================================================

    def _emit_status(self, status: str):
        """
        Send a connection status to the integration layer.
        """

        print(f"[BLE] {status}")

        if self.on_status is not None:
            try:
                self.on_status(status)
            except Exception as error:
                print(
                    f"[BLE] Status callback error: {error}"
                )

    # ============================================================
    # SCANNING
    # ============================================================

    async def scan_devices(
        self,
        timeout: float = 5.0,
    ):
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
        Find the HealthSync Band by advertised name.

        This method is retained for compatibility with
        existing code. The normal application workflow
        uses scan_devices() followed by connect(device).
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

    # ============================================================
    # CONNECTION
    # ============================================================

    async def connect(
        self,
        device=None,
    ):
        """
        Connect to a BLE device.

        The device is considered a HealthSync device when
        the actual connected BLE services contain the
        HealthSync A001 service.

        Args:
            device:
                BLEDevice returned by scan_devices().

                If omitted, the method temporarily falls back
                to find_device() for compatibility.
        """

        if device is None:
            device = await self.find_device()

        if device is None:
            return False

        # If an old client exists, clean it up first.
        if self.client is not None:
            if self.client.is_connected:
                await self.disconnect()

        self.device = device

        self._manual_disconnect = False
        self._reconnecting = False
        self._running = False

        self.parser.reset_snapshot()

        device_name = (
            device.name or "Unknown BLE device"
        )

        self._emit_status(
            f"Connecting to {device_name}..."
        )

        print(
            f"Connecting to {device_name}..."
        )

        try:
            self.client = BleakClient(
                device,
                disconnected_callback=self._handle_disconnect,
            )

            await self.client.connect()

            if not self.client.is_connected:
                print(
                    "BLE connection failed."
                )

                await self._clear_connection()

                return False

            print(
                "Connected: True"
            )

            # The actual BLE service is the source of truth.
            if self._is_healthsync_device():

                self._emit_status(
                    "HealthSync telemetry service detected."
                )

                await self._subscribe_to_notifications()

                print(
                    "HealthSync BLE notifications active."
                )

            else:

                self._emit_status(
                    "Connected device does not provide "
                    "HealthSync telemetry."
                )

                print(
                    "Connected device is not a "
                    "HealthSync telemetry device."
                )

            self._running = True
            self._reconnecting = False

            if self._is_healthsync_device():
                self._emit_status(
                    f"{device_name} connected. "
                    "Telemetry ready."
                )
            else:
                self._emit_status(
                    f"{device_name} connected."
                )

            return True

        except Exception as error:

            print(
                f"BLE connection error: {error}"
            )

            await self._clear_connection()

            return False

    # ============================================================
    # HEALTHSYNC SERVICE DETECTION
    # ============================================================

    def _is_healthsync_device(self) -> bool:
        """
        Determine whether the currently connected BLE device
        exposes the HealthSync A001 service.

        This intentionally checks the actual GATT services
        instead of relying on the advertised device name.
        """

        if self.client is None:
            return False

        try:
            services = self.client.services

            for service in services:
                if service.uuid.lower() == self.SERVICE_UUID.lower():
                    return True

        except Exception as error:
            print(
                f"Unable to inspect BLE services: {error}"
            )

        return False

    @property
    def is_healthsync_device(self) -> bool:
        """
        Public property exposing HealthSync service detection.
        """

        return self._is_healthsync_device()

    # ============================================================
    # TELEMETRY SUBSCRIPTIONS
    # ============================================================

    async def _subscribe_to_notifications(self):
        """
        Subscribe to all available HealthSync telemetry
        characteristics.
        """

        if self.client is None:
            raise RuntimeError(
                "BLE client is not connected."
            )

        if not self.client.is_connected:
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

        subscribed_count = 0

        for uuid in self.CHARACTERISTIC_UUIDS:

            characteristic = (
                available_characteristics.get(
                    uuid.lower()
                )
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

            subscribed_count += 1

            print(
                f"Subscribed: {uuid}"
            )

        print(
            f"HealthSync telemetry subscriptions active: "
            f"{subscribed_count}/{len(self.CHARACTERISTIC_UUIDS)}"
        )

    # ============================================================
    # TELEMETRY
    # ============================================================

    def _notification_handler(
        self,
        characteristic,
        data: bytearray,
    ):
        """
        Receive and parse BLE notification data.

        BLETelemetryParser remains responsible for converting
        characteristic data into HealthTelemetry.
        """

        try:
            self.parser.update(
                characteristic.uuid,
                bytes(data),
            )

            if self.parser.is_complete():

                telemetry = (
                    self.parser.get_snapshot()
                )

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

    # ============================================================
    # UNEXPECTED DISCONNECT
    # ============================================================

    def _handle_disconnect(
        self,
        client,
    ):
        """
        Called by Bleak when the BLE connection is lost.

        This callback does not reconnect when the user explicitly
        requested a disconnect.
        """

        print(
            "[BLE] BLE device disconnected."
        )

        self._running = False

        if self._manual_disconnect:
            print(
                "[BLE] Disconnect was requested manually."
            )

            self._emit_status(
                "BLE device disconnected."
            )

            return

        if self.device is None:
            self._emit_status(
                "BLE device disconnected."
            )
            return

        if self._reconnecting:
            return

        self._emit_status(
            "BLE connection lost unexpectedly."
        )

        self._emit_status(
            "RECONNECTING"
        )

        try:
            loop = asyncio.get_running_loop()

            self._reconnect_task = loop.create_task(
                self._attempt_reconnect()
            )

        except RuntimeError:
            print(
                "[BLE] No running asyncio loop available "
                "for reconnect."
            )

            self._emit_status(
                "BLE device disconnected."
            )

    async def _attempt_reconnect(self):
        """
        Attempt to reconnect after an unexpected disconnect.

        The reconnect process is intentionally handled inside
        BLEManager because this class owns the BleakClient.
        """

        if self._manual_disconnect:
            return

        if self.device is None:
            self._emit_status(
                "BLE device disconnected."
            )
            return

        if self._reconnecting:
            return

        self._reconnecting = True

        original_device = self.device
        device_name = (
            original_device.name
            or "Unknown BLE device"
        )

        for attempt in range(
            1,
            self.MAX_RECONNECT_ATTEMPTS + 1,
        ):

            if self._manual_disconnect:
                break

            self._emit_status(
                f"Reconnecting to {device_name} "
                f"({attempt}/{self.MAX_RECONNECT_ATTEMPTS})..."
            )

            print(
                f"[BLE] Reconnect attempt "
                f"{attempt}/{self.MAX_RECONNECT_ATTEMPTS}"
            )

            try:
                reconnect_device = (
                    await BleakScanner.find_device_by_address(
                        original_device.address,
                        timeout=5.0,
                    )
                )

                if reconnect_device is None:
                    reconnect_device = original_device

                self.device = reconnect_device

                if self.client is not None:
                    try:
                        if self.client.is_connected:
                            await self.client.disconnect()
                    except Exception:
                        pass

                self.client = BleakClient(
                    reconnect_device,
                    disconnected_callback=self._handle_disconnect,
                )

                await self.client.connect()

                if (
                    not self.client.is_connected
                ):
                    raise RuntimeError(
                        "BLE client did not become connected."
                    )

                # Check the actual service again after reconnect.
                if self._is_healthsync_device():

                    self._emit_status(
                        "HealthSync telemetry service detected."
                    )

                    await self._subscribe_to_notifications()

                    self.parser.reset_snapshot()

                    self._running = True
                    self._reconnecting = False

                    self._emit_status(
                        f"{device_name} reconnected. "
                        "Telemetry ready."
                    )

                else:

                    self._running = True
                    self._reconnecting = False

                    self._emit_status(
                        f"{device_name} reconnected. "
                        "HealthSync telemetry unavailable."
                    )

                return True

            except Exception as error:

                print(
                    f"[BLE] Reconnect attempt "
                    f"{attempt} failed: {error}"
                )

                if self.client is not None:
                    try:
                        if self.client.is_connected:
                            await self.client.disconnect()
                    except Exception:
                        pass

                self.client = None

                if attempt < self.MAX_RECONNECT_ATTEMPTS:
                    await asyncio.sleep(
                        self.RECONNECT_DELAY
                    )

        self._reconnecting = False
        self._running = False

        self._emit_status(
            "Automatic reconnection failed. "
            "BLE device remains disconnected."
        )

        await self._clear_connection(
            preserve_device=False
        )

        return False

    # ============================================================
    # MANUAL DISCONNECT
    # ============================================================

    async def disconnect(self):
        """
        Manually disconnect the current BLE device.

        Setting _manual_disconnect before disconnecting prevents
        the Bleak disconnected callback from starting the
        automatic reconnect process.
        """

        self._manual_disconnect = True
        self._running = False
        self._reconnecting = False

        if self._reconnect_task is not None:

            current_task = (
                asyncio.current_task()
            )

            if (
                not self._reconnect_task.done()
                and self._reconnect_task != current_task
            ):
                self._reconnect_task.cancel()

            self._reconnect_task = None

        if self.client is None:
            self.device = None
            self.parser.reset_snapshot()

            return

        try:

            if self.client.is_connected:

                print(
                    "Disconnecting from BLE device..."
                )

                await self.client.disconnect()

        except Exception as error:

            print(
                f"BLE disconnect error: {error}"
            )

        finally:

            self.client = None
            self.device = None

            self.parser.reset_snapshot()

            self._emit_status(
                "BLE device disconnected."
            )

            print(
                "Disconnected."
            )

    # ============================================================
    # INTERNAL CLEANUP
    # ============================================================

    async def _clear_connection(
        self,
        preserve_device: bool = False,
    ):
        """
        Clear the BLE client state.

        preserve_device=True is used when the caller needs the
        device reference for another operation.
        """

        self._running = False

        if self.client is not None:

            try:

                if self.client.is_connected:
                    await self.client.disconnect()

            except Exception as error:

                print(
                    f"BLE cleanup error: {error}"
                )

        self.client = None

        if not preserve_device:
            self.device = None

        self.parser.reset_snapshot()

    # ============================================================
    # STATE
    # ============================================================

    @property
    def is_connected(self) -> bool:
        """
        Return the current BLE connection state.
        """

        return (
            self.client is not None
            and self.client.is_connected
        )

    @property
    def is_reconnecting(self) -> bool:
        """
        Return whether automatic reconnect is active.
        """

        return self._reconnecting