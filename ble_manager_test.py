import asyncio

from app.models.telemetry import HealthTelemetry
from app.services.ble.manager import BLEManager
from app.services.health_service import HealthService


def display_telemetry(telemetry: HealthTelemetry):
    print()
    print("===== HEALTH SERVICE UPDATE =====")
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

    print("=================================")


async def main():
    health_service = HealthService(
        on_telemetry=display_telemetry,
    )

    ble_manager = BLEManager(
        on_telemetry=health_service.process_telemetry,
    )

    connected = await ble_manager.connect()

    if not connected:
        print("Could not connect to HealthSync Band.")
        return

    try:
        print()
        print("BLE → HealthService pipeline is active.")
        print("Receiving complete telemetry snapshots...")
        print("Press Ctrl+C to stop.")

        while True:
            await asyncio.sleep(1)

    finally:
        await ble_manager.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print()
        print("BLE → HealthService test stopped.")