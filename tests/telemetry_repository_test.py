from datetime import datetime

from app.database.connection import get_connection
from app.database.telemetry_repository import TelemetryRepository
from app.models.telemetry import HealthTelemetry, LocationData


USER_ID = 1


def get_or_create_test_device():
    connection = get_connection()

    try:
        device = connection.execute(
            """
            SELECT id
            FROM devices
            WHERE user_id = ?
              AND device_address = ?
            """,
            (USER_ID, "SIMULATOR-001"),
        ).fetchone()

        if device is not None:
            return device[0]

        cursor = connection.execute(
            """
            INSERT INTO devices (
                user_id,
                device_name,
                device_address,
                device_type,
                connection_type,
                status,
                service_uuid
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                USER_ID,
                "HealthSync BLE Simulator",
                "SIMULATOR-001",
                "BLE_WEARABLE",
                "BLE",
                "CONNECTED",
                "0000A001-0000-1000-8000-00805F9B34FB",
            ),
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


def main():
    device_id = get_or_create_test_device()

    telemetry = HealthTelemetry(
        heart_rate=132,
        spo2=97,
        temperature=36.9,
        movement="Running",
        battery=75,
        blood_pressure="130/85",
        steps=1590,
        distance=1.871,
        calories=249.5,
        active_time=378,
        location=LocationData(
            readable_name="Kharabwadi, Maharashtra",
            latitude=18.754764,
            longitude=73.857181,
        ),
        received_at=datetime.now(),
    )

    repository = TelemetryRepository()

    print("Saving telemetry...")
    repository.save_telemetry(
        user_id=USER_ID,
        device_id=device_id,
        telemetry=telemetry,
    )

    print("Telemetry saved successfully.")
    print()
    print(f"User ID:   {USER_ID}")
    print(f"Device ID: {device_id}")


if __name__ == "__main__":
    main()