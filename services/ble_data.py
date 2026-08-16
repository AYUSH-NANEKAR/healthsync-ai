"""
HealthSync AI - BLE Data Contract

Matches the HealthSync Band Simulator BLE protocol.

BLE Service:
    0000A001-0000-1000-8000-00805F9B34FB

Characteristics:

    A002 - Heart Rate
    A003 - SpO2
    A004 - Temperature
    A005 - Movement
    A006 - Battery
    A007 - Blood Pressure
    A008 - Steps
    A009 - Distance
    A00A - Calories
    A00B - Active Time
    A00C - Location

The simulator sends all values as UTF-8 strings.

This module converts those BLE strings into strongly typed
Python values.

IMPORTANT:

The simulator is only one possible source.

Future source:

    Real ESP32
       ↓
    BLE characteristics
       ↓
    Same parser
       ↓
    HealthSync AI
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import re


# ============================================================
# BLE UUIDS
# ============================================================

SERVICE_UUID = (
    "0000A001-0000-1000-8000-00805F9B34FB"
)

HEART_RATE_UUID = (
    "0000A002-0000-1000-8000-00805F9B34FB"
)

SPO2_UUID = (
    "0000A003-0000-1000-8000-00805F9B34FB"
)

TEMPERATURE_UUID = (
    "0000A004-0000-1000-8000-00805F9B34FB"
)

MOVEMENT_UUID = (
    "0000A005-0000-1000-8000-00805F9B34FB"
)

BATTERY_UUID = (
    "0000A006-0000-1000-8000-00805F9B34FB"
)

BLOOD_PRESSURE_UUID = (
    "0000A007-0000-1000-8000-00805F9B34FB"
)

STEPS_UUID = (
    "0000A008-0000-1000-8000-00805F9B34FB"
)

DISTANCE_UUID = (
    "0000A009-0000-1000-8000-00805F9B34FB"
)

CALORIES_UUID = (
    "0000A00A-0000-1000-8000-00805F9B34FB"
)

ACTIVE_TIME_UUID = (
    "0000A00B-0000-1000-8000-00805F9B34FB"
)

LOCATION_UUID = (
    "0000A00C-0000-1000-8000-00805F9B34FB"
)


# ============================================================
# NORMALIZED BLE DATA
# ============================================================

@dataclass
class BLEPayload:
    """
    Normalized health data received from BLE.

    Every field is optional.

    None means that the BLE source did not provide that
    measurement.

    No fake/default health values are generated.
    """

    # -------------------------
    # VITALS
    # -------------------------

    heart_rate: Optional[float] = None

    spo2: Optional[float] = None

    temperature: Optional[float] = None

    systolic_pressure: Optional[float] = None

    diastolic_pressure: Optional[float] = None

    # -------------------------
    # ACTIVITY
    # -------------------------

    movement: Optional[str] = None

    steps: Optional[int] = None

    distance_km: Optional[float] = None

    calories_kcal: Optional[float] = None

    active_seconds: Optional[int] = None

    # -------------------------
    # DEVICE
    # -------------------------

    battery_percent: Optional[float] = None

    # -------------------------
    # LOCATION
    # -------------------------

    location_name: Optional[str] = None

    latitude: Optional[float] = None

    longitude: Optional[float] = None

    # -------------------------
    # METADATA
    # -------------------------

    timestamp: Optional[str] = None

    device_address: Optional[str] = None


# ============================================================
# BLE DATA PARSER
# ============================================================

class BLEDataParser:
    """
    Converts raw BLE characteristic values into BLEPayload.
    """

    # ========================================================
    # PARSE COMPLETE PAYLOAD
    # ========================================================

    @classmethod
    def parse(
        cls,
        data: dict[str, str],
    ) -> BLEPayload:
        """
        Parse a complete dictionary of BLE values.

        Keys can be characteristic UUIDs or normalized field
        names.
        """

        return BLEPayload(

            heart_rate=cls._number(
                cls._get(
                    data,
                    HEART_RATE_UUID,
                    "heart_rate",
                )
            ),

            spo2=cls._number(
                cls._get(
                    data,
                    SPO2_UUID,
                    "spo2",
                )
            ),

            temperature=cls._number(
                cls._get(
                    data,
                    TEMPERATURE_UUID,
                    "temperature",
                )
            ),

            movement=cls._text(
                cls._get(
                    data,
                    MOVEMENT_UUID,
                    "movement",
                )
            ),

            battery_percent=cls._number(
                cls._get(
                    data,
                    BATTERY_UUID,
                    "battery_percent",
                )
            ),

            systolic_pressure=cls._blood_pressure(
                cls._get(
                    data,
                    BLOOD_PRESSURE_UUID,
                    "blood_pressure",
                )
            )[0],

            diastolic_pressure=cls._blood_pressure(
                cls._get(
                    data,
                    BLOOD_PRESSURE_UUID,
                    "blood_pressure",
                )
            )[1],

            steps=cls._integer(
                cls._get(
                    data,
                    STEPS_UUID,
                    "steps",
                )
            ),

            distance_km=cls._number(
                cls._get(
                    data,
                    DISTANCE_UUID,
                    "distance_km",
                )
            ),

            calories_kcal=cls._number(
                cls._get(
                    data,
                    CALORIES_UUID,
                    "calories_kcal",
                )
            ),

            active_seconds=cls._integer(
                cls._get(
                    data,
                    ACTIVE_TIME_UUID,
                    "active_seconds",
                )
            ),

            location_name=cls._location(
                cls._get(
                    data,
                    LOCATION_UUID,
                    "location",
                )
            )[0],

            latitude=cls._location(
                cls._get(
                    data,
                    LOCATION_UUID,
                    "location",
                )
            )[1],

            longitude=cls._location(
                cls._get(
                    data,
                    LOCATION_UUID,
                    "location",
                )
            )[2],

        )

    # ========================================================
    # CHARACTERISTIC VALUE
    # ========================================================

    @staticmethod
    def parse_characteristic(
        uuid: str,
        value: bytes | str,
    ) -> dict[str, object]:
        """
        Parse one BLE characteristic.

        This is the method the future BLE manager will use.

        Example:

            UUID A002
                ↓
            heart_rate
                ↓
            82.0
        """

        uuid = uuid.upper()

        if isinstance(value, bytes):
            value = value.decode(
                "utf-8",
                errors="replace",
            )

        value = value.strip()

        if uuid == HEART_RATE_UUID:
            return {
                "heart_rate": float(value)
            }

        if uuid == SPO2_UUID:
            return {
                "spo2": float(value)
            }

        if uuid == TEMPERATURE_UUID:
            return {
                "temperature": float(value)
            }

        if uuid == MOVEMENT_UUID:
            return {
                "movement": value
            }

        if uuid == BATTERY_UUID:
            return {
                "battery_percent": float(value)
            }

        if uuid == BLOOD_PRESSURE_UUID:

            systolic, diastolic = (
                BLEDataParser._blood_pressure(
                    value
                )
            )

            return {
                "systolic_pressure": systolic,
                "diastolic_pressure": diastolic,
            }

        if uuid == STEPS_UUID:
            return {
                "steps": int(value)
            }

        if uuid == DISTANCE_UUID:
            return {
                "distance_km": float(value)
            }

        if uuid == CALORIES_UUID:
            return {
                "calories_kcal": float(value)
            }

        if uuid == ACTIVE_TIME_UUID:
            return {
                "active_seconds": int(value)
            }

        if uuid == LOCATION_UUID:

            name, latitude, longitude = (
                BLEDataParser._location(
                    value
                )
            )

            return {
                "location_name": name,
                "latitude": latitude,
                "longitude": longitude,
            }

        return {}

    # ========================================================
    # GET VALUE
    # ========================================================

    @staticmethod
    def _get(
        data: dict[str, str],
        uuid: str,
        name: str,
    ) -> Optional[str]:

        return data.get(uuid) or data.get(
            uuid.lower()
        ) or data.get(name)

    # ========================================================
    # NUMBER
    # ========================================================

    @staticmethod
    def _number(
        value: Optional[str],
    ) -> Optional[float]:

        if value is None:
            return None

        try:
            return float(value)

        except (TypeError, ValueError):
            return None

    # ========================================================
    # INTEGER
    # ========================================================

    @staticmethod
    def _integer(
        value: Optional[str],
    ) -> Optional[int]:

        if value is None:
            return None

        try:
            return int(float(value))

        except (TypeError, ValueError):
            return None

    # ========================================================
    # TEXT
    # ========================================================

    @staticmethod
    def _text(
        value: Optional[str],
    ) -> Optional[str]:

        if value is None:
            return None

        value = str(value).strip()

        return value or None

    # ========================================================
    # BLOOD PRESSURE
    # ========================================================

    @staticmethod
    def _blood_pressure(
        value: Optional[str],
    ) -> tuple[
        Optional[float],
        Optional[float],
    ]:

        if not value:
            return None, None

        match = re.match(
            r"^\s*(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)\s*$",
            value,
        )

        if not match:
            return None, None

        return (
            float(match.group(1)),
            float(match.group(2)),
        )

    # ========================================================
    # LOCATION
    # ========================================================

    @staticmethod
    def _location(
        value: Optional[str],
    ) -> tuple[
        Optional[str],
        Optional[float],
        Optional[float],
    ]:

        if not value:
            return None, None, None

        try:

            parts = value.split("|", 1)

            if len(parts) != 2:
                return None, None, None

            location_name = (
                parts[0].strip()
            )

            coordinates = (
                parts[1].strip()
            )

            latitude_text, longitude_text = (
                coordinates.split(",", 1)
            )

            return (
                location_name or None,
                float(latitude_text),
                float(longitude_text),
            )

        except (
            TypeError,
            ValueError,
        ):
            return None, None, None


__all__ = [
    "BLEPayload",
    "BLEDataParser",
    "SERVICE_UUID",
    "HEART_RATE_UUID",
    "SPO2_UUID",
    "TEMPERATURE_UUID",
    "MOVEMENT_UUID",
    "BATTERY_UUID",
    "BLOOD_PRESSURE_UUID",
    "STEPS_UUID",
    "DISTANCE_UUID",
    "CALORIES_UUID",
    "ACTIVE_TIME_UUID",
    "LOCATION_UUID",
]