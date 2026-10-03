import asyncio

from bleak import BleakClient, BleakScanner


DEVICE_NAME = "HealthSync Band"


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
        print("Discovering GATT services...")
        print()

        for service in client.services:
            print(f"Service: {service.uuid}")

            for characteristic in service.characteristics:
                print(f"  Characteristic: {characteristic.uuid}")
                print(f"  Properties: {characteristic.properties}")
                print()


if __name__ == "__main__":
    asyncio.run(main())