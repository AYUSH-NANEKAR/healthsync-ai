from datetime import datetime

from app.models.telemetry import HealthTelemetry, LocationData


class BLETelemetryParser:
    CHARACTERISTICS = {
        "a002": "heart_rate",
        "a003": "spo2",
        "a004": "temperature",
        "a005": "movement",
        "a006": "battery",
        "a007": "blood_pressure",
        "a008": "steps",
        "a009": "distance",
        "a00a": "calories",
        "a00b": "active_time",
        "a00c": "location",
    }

    REQUIRED_FIELDS = {
        "heart_rate",
        "spo2",
        "temperature",
        "movement",
        "battery",
        "blood_pressure",
        "steps",
        "distance",
        "calories",
        "active_time",
        "location",
    }

    def __init__(self):
        self.telemetry = HealthTelemetry()
        self.received_fields: set[str] = set()

    def update(self, characteristic_uuid: str, raw_data: bytes) -> HealthTelemetry:
        value = raw_data.decode("utf-8").strip()

        characteristic_id = self._get_characteristic_id(characteristic_uuid)

        if characteristic_id is None:
            raise ValueError(
                f"Unknown HealthSync characteristic: {characteristic_uuid}"
            )

        field_name = self.CHARACTERISTICS[characteristic_id]

        parser = getattr(self, f"_parse_{field_name}")
        parser(value)

        self.received_fields.add(field_name)
        self.telemetry.received_at = datetime.now()

        return self.telemetry

    def is_complete(self) -> bool:
        return self.REQUIRED_FIELDS.issubset(self.received_fields)

    def get_snapshot(self) -> HealthTelemetry | None:
        if not self.is_complete():
            return None

        return self.telemetry

    def reset_snapshot(self):
        self.telemetry = HealthTelemetry()
        self.received_fields.clear()

    def _get_characteristic_id(self, characteristic_uuid: str) -> str | None:
        uuid_lower = characteristic_uuid.lower()

        for characteristic_id in self.CHARACTERISTICS:
            if f"0000{characteristic_id}" in uuid_lower:
                return characteristic_id

        return None

    def _parse_heart_rate(self, value: str):
        self.telemetry.heart_rate = int(value)

    def _parse_spo2(self, value: str):
        self.telemetry.spo2 = int(value)

    def _parse_temperature(self, value: str):
        self.telemetry.temperature = float(value)

    def _parse_movement(self, value: str):
        self.telemetry.movement = value

    def _parse_battery(self, value: str):
        self.telemetry.battery = int(value)

    def _parse_blood_pressure(self, value: str):
        self.telemetry.blood_pressure = value

    def _parse_steps(self, value: str):
        self.telemetry.steps = int(value)

    def _parse_distance(self, value: str):
        self.telemetry.distance = float(value)

    def _parse_calories(self, value: str):
        self.telemetry.calories = float(value)

    def _parse_active_time(self, value: str):
        self.telemetry.active_time = int(value)

    def _parse_location(self, value: str):
        try:
            readable_name, coordinates = value.split("|", 1)
            latitude, longitude = coordinates.split(",", 1)

            self.telemetry.location = LocationData(
                readable_name=readable_name,
                latitude=float(latitude),
                longitude=float(longitude),
            )

        except ValueError as error:
            raise ValueError(
                f"Invalid location format: {value}"
            ) from error