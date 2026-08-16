"""
HealthSync AI - Database Models

These dataclasses represent normalized application data.

IMPORTANT:
    These models do NOT generate sensor values.

    Data will eventually come from:

        Temporary Android BLE Simulator
                    OR
        Future ESP32 + real sensors
                    ↓
                BLE Layer
                    ↓
                 Parser
                    ↓
                 Models
                    ↓
                Database

The models are intentionally independent of the BLE simulator
so that the simulator can later be replaced by real hardware
without changing the rest of the application.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ============================================================
# USER
# ============================================================

@dataclass
class User:
    """
    Authenticated HealthSync AI user.
    """

    id: Optional[int] = None

    name: str = ""

    email: str = ""

    password_hash: str = ""

    phone: Optional[str] = None

    date_of_birth: Optional[str] = None

    gender: Optional[str] = None

    created_at: Optional[str] = None

    updated_at: Optional[str] = None


# ============================================================
# SESSION
# ============================================================

@dataclass
class Session:
    """
    Persistent login session.

    The session stores a token/identifier, NOT the user's password.
    """

    id: Optional[int] = None

    user_id: int = 0

    session_token: str = ""

    created_at: Optional[str] = None

    last_used_at: Optional[str] = None

    expires_at: Optional[str] = None


# ============================================================
# HEALTH PROFILE
# ============================================================

@dataclass
class HealthProfile:
    """
    Personal health information belonging to a user.
    """

    id: Optional[int] = None

    user_id: int = 0

    height: Optional[float] = None

    weight: Optional[float] = None

    blood_group: Optional[str] = None

    medical_conditions: Optional[str] = None

    allergies: Optional[str] = None

    medications: Optional[str] = None

    emergency_notes: Optional[str] = None

    updated_at: Optional[str] = None


# ============================================================
# DEVICE
# ============================================================

@dataclass
class Device:
    """
    BLE / IoT device registered to a user.

    The device can currently be the temporary BLE simulator
    and later the real ESP32 wearable.
    """

    id: Optional[int] = None

    user_id: int = 0

    device_name: str = ""

    device_address: Optional[str] = None

    device_type: Optional[str] = None

    connection_type: str = "BLE"

    status: str = "Disconnected"

    last_seen: Optional[str] = None

    created_at: Optional[str] = None


# ============================================================
# VITALS
# ============================================================

@dataclass
class Vital:
    """
    Health measurements received from a device.

    BLE data represented here:

        Heart Rate
        SpO2
        Temperature
        Blood Pressure
    """

    id: Optional[int] = None

    user_id: int = 0

    device_id: Optional[int] = None

    heart_rate: Optional[float] = None

    spo2: Optional[float] = None

    temperature: Optional[float] = None

    systolic_pressure: Optional[float] = None

    diastolic_pressure: Optional[float] = None

    recorded_at: Optional[str] = None

    source: Optional[str] = None


# ============================================================
# ACTIVITY DATA
# ============================================================

@dataclass
class ActivityData:
    """
    Activity measurements received from the wearable.

    BLE data represented here:

        Movement
        Steps
        Distance
        Calories
        Active Time
    """

    id: Optional[int] = None

    user_id: int = 0

    device_id: Optional[int] = None

    movement: Optional[str] = None

    steps: Optional[int] = None

    distance_km: Optional[float] = None

    calories_kcal: Optional[float] = None

    active_seconds: Optional[int] = None

    recorded_at: Optional[str] = None

    source: Optional[str] = None


# ============================================================
# DEVICE TELEMETRY
# ============================================================

@dataclass
class DeviceTelemetry:
    """
    Device-level information.

    Currently represented by:

        Battery percentage
    """

    id: Optional[int] = None

    user_id: int = 0

    device_id: int = 0

    battery_percent: Optional[float] = None

    recorded_at: Optional[str] = None

    source: Optional[str] = None


# ============================================================
# LOCATION
# ============================================================

@dataclass
class LocationData:
    """
    Location information associated with a user/device.

    Location can originate from:

        - BLE simulator
        - Future ESP32/GPS hardware
        - Desktop location service
        - Manual user-selected location

    The source field identifies where the value came from.
    """

    id: Optional[int] = None

    user_id: int = 0

    device_id: Optional[int] = None

    latitude: Optional[float] = None

    longitude: Optional[float] = None

    readable_location: Optional[str] = None

    accuracy_meters: Optional[float] = None

    source: Optional[str] = None

    recorded_at: Optional[str] = None


# ============================================================
# EMERGENCY CONTACT
# ============================================================

@dataclass
class EmergencyContact:
    """
    Emergency contact belonging to a user.
    """

    id: Optional[int] = None

    user_id: int = 0

    name: str = ""

    relationship: Optional[str] = None

    country_code: Optional[str] = None

    phone: str = ""

    is_primary: bool = False

    created_at: Optional[str] = None


# ============================================================
# AI REPORT
# ============================================================

@dataclass
class AIReport:
    """
    Stored AI health-analysis result.

    The model stores the result; it does not perform AI analysis.
    """

    id: Optional[int] = None

    user_id: int = 0

    symptoms: str = ""

    analysis: Optional[str] = None

    recommendations: Optional[str] = None

    severity: Optional[str] = None

    created_at: Optional[str] = None


# ============================================================
# HEALTH REPORT
# ============================================================

@dataclass
class HealthReport:
    """
    Health document/report belonging to a user.
    """

    id: Optional[int] = None

    user_id: int = 0

    title: str = ""

    description: Optional[str] = None

    report_type: Optional[str] = None

    file_path: Optional[str] = None

    created_at: Optional[str] = None


# ============================================================
# NORMALIZED BLE SNAPSHOT
# ============================================================

@dataclass
class BLEDataSnapshot:
    """
    Complete normalized snapshot of the BLE data received
    from the wearable.

    This is the bridge between the BLE parser and the
    application services.

    It does NOT contain generated/default sensor readings.

    Any field may be None because a real device may not
    provide a particular value at a particular moment.
    """

    heart_rate: Optional[float] = None

    spo2: Optional[float] = None

    temperature: Optional[float] = None

    movement: Optional[str] = None

    battery_percent: Optional[float] = None

    systolic_pressure: Optional[float] = None

    diastolic_pressure: Optional[float] = None

    steps: Optional[int] = None

    distance_km: Optional[float] = None

    calories_kcal: Optional[float] = None

    active_seconds: Optional[int] = None

    location: Optional[str] = None

    received_at: Optional[str] = None

    device_address: Optional[str] = None


# ============================================================
# BLE PARAMETER NAMES
# ============================================================

BLE_PARAMETER_NAMES = (
    "heart_rate",
    "spo2",
    "temperature",
    "movement",
    "battery_percent",
    "blood_pressure",
    "steps",
    "distance_km",
    "calories_kcal",
    "active_seconds",
    "location",
)


# ============================================================
# MODEL EXPORTS
# ============================================================

__all__ = [
    "User",
    "Session",
    "HealthProfile",
    "Device",
    "Vital",
    "ActivityData",
    "DeviceTelemetry",
    "LocationData",
    "EmergencyContact",
    "AIReport",
    "HealthReport",
    "BLEDataSnapshot",
    "BLE_PARAMETER_NAMES",
]