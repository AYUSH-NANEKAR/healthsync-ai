from app.database.device_repository import DeviceRepository


USER_ID = 1
DEVICE_ADDRESS = "SIMULATOR-001"


def main():
    repository = DeviceRepository()

    print("Finding existing device...")

    device = repository.find_by_address(
        user_id=USER_ID,
        device_address=DEVICE_ADDRESS,
    )

    if device is None:
        print("Device not found.")
        return

    print("Device found.")
    print()

    print("Device ID:", device["id"])
    print("User ID:", device["user_id"])
    print("Device Name:", device["device_name"])
    print("Device Address:", device["device_address"])
    print("Device Type:", device["device_type"])
    print("Connection Type:", device["connection_type"])
    print("Status:", device["status"])
    print("Service UUID:", device["service_uuid"])
    print("Last Seen:", device["last_seen_at"])

    print()
    print("Marking device as connected...")

    repository.mark_connected(
        device_id=device["id"],
    )

    print("Device marked as connected.")

    print()
    print("Checking updated device...")

    updated_device = repository.find_by_address(
        user_id=USER_ID,
        device_address=DEVICE_ADDRESS,
    )

    print("Status:", updated_device["status"])
    print("Last Seen:", updated_device["last_seen_at"])


if __name__ == "__main__":
    main()