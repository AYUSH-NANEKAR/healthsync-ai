import asyncio

from bleak import BleakClient, BleakScanner


DEVICE_NAME = "HealthSync Band"

CHARACTERISTICS = {
    "A002": "Heart Rate",
    "A003": "SpO2",
    "A004": "Temperature",
    "A005": "Movement",
    "A006": "Battery",
    "A007": "Blood Pressure",
    "A008": "Steps",
    "A009": "Distance",
    "A00A": "Calories",
    "A00B": "Active Time",
    "A00C": "Location",
}


def get_characteristic_name(uuid):
    uuid_lower = uuid.lower()

    for short_uuid, name in CHARACTERISTICS.items():
        if short_uuid.lower() in uuid_lower:
            return name

    return "Unknown"


def notification_handler(characteristic, data):
    value = data.decode("utf-8")

    name = get_characteristic_name(characteristic.uuid)

    print(f"{name}: {value}")


async def main():
    print("Searching for HealthSync Band...")

    device = await BleakScanner.find_device_by_name(
        DEVICE_NAME,
        timeout=10,
    )

    if device is None:
        print("HealthSync Band was not found.")
        return

    print(f"Found: {device.name}")
    print(f"Address: {device.address}")
    print()

    print("Connecting...")

    async with BleakClient(device) as client:
        print(f"Connected: {client.is_connected}")
        print()
        print("Subscribing to BLE notifications...")
        print("Waiting for live data...")
        print("Press Ctrl+C to stop.")
        print()

        for service in client.services:
            if service.uuid.lower().startswith(
                "0000a001-0000-1000-8000-00805f9b34fb"
            ):
                for characteristic in service.characteristics:
                    if "notify" in characteristic.properties:
                        await client.start_notify(
                            characteristic,
                            notification_handler,
                        )

        try:
            while True:
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print()
        print("BLE receiver stopped.")