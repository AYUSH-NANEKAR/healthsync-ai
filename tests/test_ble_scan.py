import asyncio

from app.services.ble.manager import BLEManager


async def main():
    manager = BLEManager()

    devices = await manager.scan_devices(
        timeout=5
    )

    print()
    print("========== BLE DEVICES ==========")

    for device in devices:
        print(
            f"Name: {device.name or 'Unknown'}"
        )

        print(
            f"Address: {device.address}"
        )

        print("---------------------------------")


if __name__ == "__main__":
    asyncio.run(main())