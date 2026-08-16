"""
HealthSync AI - BLE Manager

Handles communication between HealthSync AI and a BLE wearable.

Current source:
    HealthSync BLE Android Simulator

Future source:
    Real ESP32 wearable

BLE service:
    0000A001-0000-1000-8000-00805F9B34FB

Characteristics:
    A002 Heart Rate
    A003 SpO2
    A004 Temperature
    A005 Movement
    A006 Battery
    A007 Blood Pressure
    A008 Steps
    A009 Distance
    A00A Calories
    A00B Active Time
    A00C Location

The BLE manager does NOT create health values.
It only receives and forwards them.
"""

from __future__ import annotations

import asyncio
import threading
from typing import Callable, Optional

from services.ble_data import (
    BLEDataParser,
    BLEPayload,
    SERVICE_UUID,
    HEART_RATE_UUID,
    SPO2_UUID,
    TEMPERATURE_UUID,
    MOVEMENT_UUID,
    BATTERY_UUID,
    BLOOD_PRESSURE_UUID,
    STEPS_UUID,
    DISTANCE_UUID,
    CALORIES_UUID,
    ACTIVE_TIME_UUID,
    LOCATION_UUID,
)


try:
    from bleak import BleakClient, BleakScanner
except ImportError:
    BleakClient = None
    BleakScanner = None


class BLEManager:
    """
    Manages BLE scanning, connection and notifications.
    """

    CHARACTERISTIC_UUIDS = {
        HEART_RATE_UUID,
        SPO2_UUID,
        TEMPERATURE_UUID,
        MOVEMENT_UUID,
        BATTERY_UUID,
        BLOOD_PRESSURE_UUID,
        STEPS_UUID,
        DISTANCE_UUID,
        CALORIES_UUID,
        ACTIVE_TIME_UUID,
        LOCATION_UUID,
    }

    def __init__(
        self,
        on_data: Optional[
            Callable[[BLEPayload], None]
        ] = None,
        on_status: Optional[
            Callable[[str], None]
        ] = None,
    ):
        self.on_data = on_data
        self.on_status = on_status

        self.client = None

        self.device_address: Optional[str] = None

        self.connected = False

        self.running = False

        self._loop: Optional[asyncio.AbstractEventLoop] = None

        self._thread: Optional[threading.Thread] = None

        self._values: dict[str, str] = {}

    # ========================================================
    # CHECK BLE LIBRARY
    # ========================================================

    @staticmethod
    def is_available() -> bool:
        """
        Check whether Bleak is installed.
        """

        return (
            BleakClient is not None
            and BleakScanner is not None
        )

    # ========================================================
    # SCAN
    # ========================================================

    async def scan(
        self,
        timeout: float = 5.0,
    ):
        """
        Scan for nearby BLE devices.

        Returns a list of discovered devices.
        """

        if not self.is_available():
            raise RuntimeError(
                "Bleak is not installed. "
                "Run: pip install bleak"
            )

        self._notify_status(
            "Scanning for BLE devices..."
        )

        devices = await BleakScanner.discover(
            timeout=timeout
        )

        self._notify_status(
            f"BLE scan complete: {len(devices)} device(s)"
        )

        return devices

    # ========================================================
    # FIND HEALTHSYNC DEVICE
    # ========================================================

    async def find_healthsync_device(
        self,
        timeout: float = 8.0,
    ):
        """
        Search for the HealthSync BLE service.
        """

        devices = await self.scan(timeout)

        for device in devices:

            try:

                advertisement = (
                    device.metadata
                    .get("uuids", [])
                )

                uuids = {
                    str(uuid).upper()
                    for uuid in advertisement
                }

                if SERVICE_UUID.upper() in uuids:
                    return device

            except Exception:
                continue

        return None

    # ========================================================
    # CONNECT
    # ========================================================

    async def connect(
        self,
        address: str,
    ) -> bool:
        """
        Connect to a BLE device.
        """

        if not self.is_available():
            self._notify_status(
                "Bleak is not installed."
            )
            return False

        if self.connected:
            await self.disconnect()

        self.device_address = address

        self._notify_status(
            f"Connecting to {address}..."
        )

        try:

            self.client = BleakClient(
                address,
                disconnected_callback=self._on_disconnect,
            )

            await self.client.connect()

            if not self.client.is_connected:

                self._notify_status(
                    "BLE connection failed."
                )

                return False

            self.connected = True

            self._notify_status(
                f"Connected to {address}"
            )

            await self._subscribe_to_characteristics()

            return True

        except Exception as exc:

            self.connected = False

            self._notify_status(
                f"BLE connection error: {exc}"
            )

            return False

    # ========================================================
    # SUBSCRIBE
    # ========================================================

    async def _subscribe_to_characteristics(
        self,
    ):
        """
        Subscribe to all HealthSync health characteristics.
        """

        if not self.client:
            return

        services = self.client.services

        found = 0

        for service in services:

            for characteristic in service.characteristics:

                uuid = characteristic.uuid.upper()

                if uuid not in self.CHARACTERISTIC_UUIDS:
                    continue

                if "notify" not in characteristic.properties:
                    continue

                try:

                    await self.client.start_notify(
                        characteristic.uuid,
                        self._notification_handler,
                    )

                    found += 1

                    self._notify_status(
                        f"Subscribed: {uuid}"
                    )

                except Exception as exc:

                    self._notify_status(
                        f"Subscription failed "
                        f"for {uuid}: {exc}"
                    )

        self._notify_status(
            f"BLE subscriptions active: {found}"
        )

    # ========================================================
    # NOTIFICATION
    # ========================================================

    def _notification_handler(
        self,
        sender,
        data: bytearray,
    ):
        """
        Called whenever a BLE characteristic sends
        a notification.
        """

        uuid = str(sender).upper()

        try:

            value = bytes(data).decode(
                "utf-8",
                errors="replace",
            ).strip()

        except Exception:

            return

        if not value:
            return

        self._values[uuid] = value

        self._process_values()

    # ========================================================
    # PROCESS VALUES
    # ========================================================

    def _process_values(self):
        """
        Convert the received BLE values into BLEPayload.

        Values are processed only when received.

        No values are generated here.
        """

        payload = BLEDataParser.parse(
            self._values
        )

        if self.on_data:
            try:
                self.on_data(payload)
            except Exception as exc:
                self._notify_status(
                    f"BLE data callback error: {exc}"
                )

    # ========================================================
    # DISCONNECT
    # ========================================================

    async def disconnect(self):
        """
        Disconnect from the current BLE device.
        """

        if self.client:

            try:

                if self.client.is_connected:
                    await self.client.disconnect()

            except Exception:
                pass

        self.client = None

        self.connected = False

        self._notify_status(
            "BLE disconnected."
        )

    # ========================================================
    # DISCONNECT CALLBACK
    # ========================================================

    def _on_disconnect(
        self,
        client,
    ):
        """
        Called when the BLE device disconnects.
        """

        self.connected = False

        self._notify_status(
            "BLE device disconnected."
        )

    # ========================================================
    # START BACKGROUND LOOP
    # ========================================================

    def start_background(
        self,
        address: str,
    ):
        """
        Start BLE connection in a background thread.

        This prevents BLE operations from blocking the
        PySide6 UI thread.
        """

        if self.running:
            return

        self.running = True

        self._thread = threading.Thread(
            target=self._run_background,
            args=(address,),
            daemon=True,
        )

        self._thread.start()

    # ========================================================
    # BACKGROUND RUNNER
    # ========================================================

    def _run_background(
        self,
        address: str,
    ):
        """
        Run an asyncio BLE loop in a background thread.
        """

        try:

            self._loop = asyncio.new_event_loop()

            asyncio.set_event_loop(
                self._loop
            )

            self._loop.run_until_complete(
                self.connect(address)
            )

            self._loop.run_until_complete(
                self._wait_until_stopped()
            )

        except Exception as exc:

            self._notify_status(
                f"BLE background error: {exc}"
            )

        finally:

            try:

                if self._loop:
                    self._loop.run_until_complete(
                        self.disconnect()
                    )

            except Exception:
                pass

            if self._loop:
                self._loop.close()

            self._loop = None

            self.running = False

    # ========================================================
    # WAIT
    # ========================================================

    async def _wait_until_stopped(self):
        """
        Keep the BLE event loop alive.
        """

        while self.running:
            await asyncio.sleep(0.2)

    # ========================================================
    # STOP
    # ========================================================

    def stop(self):
        """
        Stop background BLE communication.
        """

        self.running = False

        if self._loop:

            try:

                asyncio.run_coroutine_threadsafe(
                    self.disconnect(),
                    self._loop,
                )

            except Exception:
                pass

    # ========================================================
    # STATUS CALLBACK
    # ========================================================

    def _notify_status(
        self,
        message: str,
    ):
        """
        Send status information to the UI/application.
        """

        if self.on_status:

            try:
                self.on_status(message)

            except Exception:
                pass


__all__ = [
    "BLEManager",
]