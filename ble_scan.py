import asyncio

from bleak import BleakScanner


async def scan_devices():
    print("Scanning for BLE devices...")
    print("Make sure the HealthSync Android simulator is running and advertising.")
    print()

    devices = await BleakScanner.discover(timeout=10)

    if not devices:
        print("No BLE devices found.")
        return

    print(f"Found {len(devices)} BLE device(s):")
    print("-" * 60)

    for device in devices:
        print(f"Name:    {device.name}")
        print(f"Address: {device.address}")
        print("-" * 60)


if __name__ == "__main__":
    asyncio.run(scan_devices())