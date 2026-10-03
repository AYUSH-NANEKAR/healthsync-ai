import asyncio

from app.database.device_repository import DeviceRepository
from app.services.ble.manager import BLEManager


USER_ID = 1


async def main():
    print("Searching for HealthSync Band...")

    ble_manager = BLEManager()

    device = await ble_manager.find_device()

    if device is None:
        print("HealthSync Band not found.")
        return

    print()
    print("===== BLE DEVICE =====")
    print(f"Name: {device.name}")
    print(f"Address: {device.address}")
    print("======================")

    repository = DeviceRepository()

    existing_device = repository.find_by_address(
        USER_ID,
        device.address,
    )

    if existing_device is not None:
        print()
        print("Device already exists in database.")

        device_id = existing_device["id"]

        repository.mark_connected(device_id)

    else:
        print()
        print("Device not found in database.")
        print("Creating device record...")

        device_id = repository.create(
            user_id=USER_ID,
            device_name=device.name or "HealthSync Band",
            device_address=device.address,
            device_type="BLE_WEARABLE",
            connection_type="BLE",
            service_uuid=BLEManager.SERVICE_UUID,
        )

    print()
    print("===== DATABASE DEVICE =====")
    print(f"Device ID: {device_id}")
    print(f"User ID: {USER_ID}")
    print(f"Device Name: {device.name}")
    print(f"Device Address: {device.address}")
    print("Status: CONNECTED")
    print("===========================")


if __name__ == "__main__":
    asyncio.run(main())