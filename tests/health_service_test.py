from app.models.telemetry import HealthTelemetry, LocationData
from app.services.health_service import HealthService


def handle_telemetry(telemetry: HealthTelemetry):
    print("Telemetry callback received.")
    print(f"Heart Rate: {telemetry.heart_rate}")
    print(f"SpO2: {telemetry.spo2}")
    print(f"Movement: {telemetry.movement}")


service = HealthService(
    on_telemetry=handle_telemetry,
)

telemetry = HealthTelemetry(
    heart_rate=134,
    spo2=97,
    temperature=36.8,
    movement="Running",
    battery=79,
    blood_pressure="129/86",
    steps=1028,
    distance=1.24,
    calories=164.7,
    active_time=250,
    location=LocationData(
        readable_name="Varale, Varale",
        latitude=18.747636,
        longitude=73.697684,
    ),
)

print("Processing telemetry...")
service.process_telemetry(telemetry)

print()
print("Checking latest telemetry...")

latest = service.get_latest_telemetry()

print(f"Heart Rate: {latest.heart_rate}")
print(f"SpO2: {latest.spo2}")
print(f"Temperature: {latest.temperature}")
print(f"Movement: {latest.movement}")
print(f"Battery: {latest.battery}")
print(f"Blood Pressure: {latest.blood_pressure}")
print(f"Steps: {latest.steps}")
print(f"Distance: {latest.distance}")
print(f"Calories: {latest.calories}")
print(f"Active Time: {latest.active_time}")
print(f"Location: {latest.location.readable_name}")

print()
print("Clearing service...")

service.clear()

print(f"After clear: {service.get_latest_telemetry()}")