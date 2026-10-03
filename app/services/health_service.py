from collections.abc import Callable

from app.database.telemetry_repository import TelemetryRepository
from app.models.telemetry import HealthTelemetry


class HealthService:
    """
    Application-level service for health telemetry.

    Responsibilities:
    - Receive complete telemetry from BLEManager.
    - Maintain the latest telemetry snapshot.
    - Save telemetry to the database.
    - Notify other application components when telemetry arrives.

    This class does not know anything about:
    - BLE / Bleak
    - PySide6 UI
    """

    def __init__(
        self,
        user_id: int,
        device_id: int,
        telemetry_repository: TelemetryRepository,
        on_telemetry: Callable[[HealthTelemetry], None] | None = None,
    ):
        self.user_id = user_id
        self.device_id = device_id
        self.telemetry_repository = telemetry_repository
        self.on_telemetry = on_telemetry

        self.latest_telemetry: HealthTelemetry | None = None

    def process_telemetry(
        self,
        telemetry: HealthTelemetry,
    ):
        """
        Process one complete telemetry snapshot.

        The snapshot is:
        1. Stored as the latest in-memory telemetry.
        2. Saved to SQLite.
        3. Forwarded to any registered callback.
        """

        self.latest_telemetry = telemetry

        self.telemetry_repository.save_telemetry(
            user_id=self.user_id,
            device_id=self.device_id,
            telemetry=telemetry,
        )

        if self.on_telemetry is not None:
            self.on_telemetry(telemetry)

    def get_latest_telemetry(self) -> HealthTelemetry | None:
        """
        Return the most recently received telemetry snapshot.
        """

        return self.latest_telemetry

    def clear(self):
        """
        Clear the current telemetry state.
        """

        self.latest_telemetry = None