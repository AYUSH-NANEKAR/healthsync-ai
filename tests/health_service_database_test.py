from datetime import datetime

from app.database.telemetry_repository import TelemetryRepository
from app.models.telemetry import HealthTelemetry, LocationData
from app.services.health_service import HealthService


USER_ID = 1
DEVICE_ID = 2


def display_telemetry(telemetry: HealthTelemetry):
    print()
    print("===== TELEMETRY CALLBACK =====")
    print(f"Heart Rate: {telemetry.heart_rate}")
    print(f"SpO2: {telemetry.spo2}")
    print(f"Temperature: {telemetry.temperature}")
    print(f"Movement: {telemetry.movement}")
    print(f"Battery: {telemetry.battery}")
    print(f"Blood Pressure: {telemetry.blood_pressure}")
    print(f"Steps: {telemetry.steps}")
    print(f"Distance: {telemetry.distance}")
    print(f"Calories: {telemetry.calories}")
    print(f"Active Time: {telemetry.active_time}")

    if telemetry.location is not None:
        print(f"Location: {telemetry.location.readable_name}")
        print(f"Latitude: {telemetry.location.latitude}")
        print(f"Longitude: {telemetry.location.longitude}")

    print("===============================")


def main():
    repository = TelemetryRepository()

    health_service = HealthService(
        user_id=USER_ID,
        device_id=DEVICE_ID,
        telemetry_repository=repository,
        on_telemetry=display_telemetry,
    )

    telemetry = HealthTelemetry(
        heart_rate=82,
        spo2=97,
        temperature=36.7,
        movement="Walking",
        battery=91,
        blood_pressure="118/78",
        steps=120,
        distance=0.080,
        calories=6.5,
        active_time=300,
        location=LocationData(
            readable_name="Pune",
            latitude=18.520400,
            longitude=73.856700,
        ),
        received_at=datetime.now(),
    )

    print("Processing telemetry through HealthService...")
    health_service.process_telemetry(telemetry)

    print()
    print("===== SERVICE STATE =====")

    latest = health_service.get_latest_telemetry()

    if latest is not None:
        print(f"Latest Heart Rate: {latest.heart_rate}")
        print(f"Latest SpO2: {latest.spo2}")
        print(f"Latest Movement: {latest.movement}")

    print("=========================")
    print()
    print("Telemetry successfully processed and saved.")


if __name__ == "__main__":
    main()