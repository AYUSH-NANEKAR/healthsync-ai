from app.database.connection import get_connection
from app.models.telemetry import HealthTelemetry


class TelemetryRepository:
    """
    Stores complete HealthSync telemetry snapshots in SQLite.

    Responsibilities:
    - Save vital measurements.
    - Save activity measurements.
    - Save device battery telemetry.
    - Save location history.

    This class does not know anything about:
    - BLE / Bleak
    - PySide6
    - HealthService
    - AI
    """

    def save_telemetry(
        self,
        user_id: int,
        device_id: int,
        telemetry: HealthTelemetry,
    ):
        """
        Save one complete telemetry snapshot.

        The snapshot is written to:
        - vitals
        - activity_data
        - device_telemetry
        - location_history
        """

        if telemetry.received_at is None:
            raise ValueError(
                "Telemetry must have received_at before it can be saved."
            )

        systolic_bp, diastolic_bp = self._parse_blood_pressure(
            telemetry.blood_pressure
        )

        connection = get_connection()

        try:
            cursor = connection.cursor()

            # ---------------------------------------------------------
            # Vitals
            # ---------------------------------------------------------

            cursor.execute(
                """
                INSERT INTO vitals (
                    user_id,
                    device_id,
                    heart_rate,
                    spo2,
                    temperature,
                    systolic_bp,
                    diastolic_bp,
                    recorded_at,
                    source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    device_id,
                    telemetry.heart_rate,
                    telemetry.spo2,
                    telemetry.temperature,
                    systolic_bp,
                    diastolic_bp,
                    telemetry.received_at,
                    "BLE",
                ),
            )

            # ---------------------------------------------------------
            # Activity
            # ---------------------------------------------------------

            cursor.execute(
                """
                INSERT INTO activity_data (
                    user_id,
                    device_id,
                    movement,
                    steps,
                    distance,
                    calories,
                    active_time,
                    recorded_at,
                    source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    device_id,
                    telemetry.movement,
                    telemetry.steps,
                    telemetry.distance,
                    telemetry.calories,
                    telemetry.active_time,
                    telemetry.received_at,
                    "BLE",
                ),
            )

            # ---------------------------------------------------------
            # Device telemetry
            # ---------------------------------------------------------

            cursor.execute(
                """
                INSERT INTO device_telemetry (
                    device_id,
                    battery,
                    recorded_at
                )
                VALUES (?, ?, ?)
                """,
                (
                    device_id,
                    telemetry.battery,
                    telemetry.received_at,
                ),
            )

            # ---------------------------------------------------------
            # Location
            # ---------------------------------------------------------

            if telemetry.location is not None:
                cursor.execute(
                    """
                    INSERT INTO location_history (
                        user_id,
                        device_id,
                        readable_name,
                        latitude,
                        longitude,
                        recorded_at,
                        source
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        device_id,
                        telemetry.location.readable_name,
                        telemetry.location.latitude,
                        telemetry.location.longitude,
                        telemetry.received_at,
                        "BLE",
                    ),
                )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    @staticmethod
    def _parse_blood_pressure(
        blood_pressure: str | None,
    ) -> tuple[int | None, int | None]:
        """
        Convert '130/85' into (130, 85).

        Returns (None, None) when blood pressure is unavailable.
        """

        if blood_pressure is None:
            return None, None

        try:
            systolic, diastolic = blood_pressure.split("/", 1)

            return int(systolic), int(diastolic)

        except (ValueError, AttributeError) as error:
            raise ValueError(
                f"Invalid blood pressure format: {blood_pressure}"
            ) from error