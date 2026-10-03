from dataclasses import dataclass
from datetime import datetime


@dataclass
class LocationData:
    readable_name: str
    latitude: float
    longitude: float


@dataclass
class HealthTelemetry:
    heart_rate: int | None = None
    spo2: int | None = None
    temperature: float | None = None
    movement: str | None = None
    battery: int | None = None
    blood_pressure: str | None = None
    steps: int | None = None
    distance: float | None = None
    calories: float | None = None
    active_time: int | None = None
    location: LocationData | None = None
    received_at: datetime | None = None