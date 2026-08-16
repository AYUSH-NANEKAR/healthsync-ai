"""
HealthSync AI - Device Service

Manages wearable / IoT devices associated with a HealthSync AI user.

The current BLE simulator is temporary.
The same device layer will later work with the real ESP32 wearable.

Architecture:

    BLE Simulator
          OR
       Real ESP32
          ↓
    DeviceService
          ↓
       device_id
          ↓
    HealthService
          ↓
        SQLite

IMPORTANT:
    DeviceService does not generate health values.
    It manages device identity and connection state only.
"""

from __future__ import annotations

from typing import Optional

from database.database import db
from database.models import Device
from utils.datetime_utils import utc_now_iso


class DeviceService:
    """
    Manages HealthSync AI wearable devices.
    """

    # ========================================================
    # REGISTER DEVICE
    # ========================================================

    def register_device(
        self,
        user_id: int,
        device_name: str,
        device_address: Optional[str],
        device_type: str = "Wearable",
        connection_type: str = "BLE",
    ) -> tuple[bool, str, Optional[Device]]:
        """
        Register a device for a specific user.

        The BLE address identifies the physical device.

        Returns:

            success
            message
            Device object
        """

        if not self._user_exists(user_id):
            return False, "User not found.", None

        device_name = device_name.strip()

        if device_address:
            device_address = device_address.strip()

        device_type = device_type.strip()
        connection_type = connection_type.strip()

        if not device_name:
            return False, "Device name is required.", None

        if not connection_type:
            connection_type = "BLE"

        # ----------------------------------------------------
        # CHECK EXISTING DEVICE
        # ----------------------------------------------------

        if device_address:

            existing = self.get_device_by_address(
                user_id,
                device_address,
            )

            if existing is not None:
                return (
                    True,
                    "Device already registered.",
                    existing,
                )

        # ----------------------------------------------------
        # INSERT DEVICE
        # ----------------------------------------------------

        now = utc_now_iso()

        with db.transaction() as connection:

            cursor = connection.execute(
                """
                INSERT INTO devices (
                    user_id,
                    device_name,
                    device_address,
                    device_type,
                    connection_type,
                    status,
                    last_seen,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    device_name,
                    device_address,
                    device_type,
                    connection_type,
                    "Disconnected",
                    None,
                    now,
                ),
            )

            device_id = cursor.lastrowid

        device = self.get_device(
            device_id,
            user_id,
        )

        return (
            True,
            "Device registered successfully.",
            device,
        )

    # ========================================================
    # GET DEVICE
    # ========================================================

    def get_device(
        self,
        device_id: int,
        user_id: int,
    ) -> Optional[Device]:
        """
        Retrieve a device belonging to the specified user.
        """

        connection = db.get_connection()

        try:

            cursor = connection.execute(
                """
                SELECT
                    id,
                    user_id,
                    device_name,
                    device_address,
                    device_type,
                    connection_type,
                    status,
                    last_seen,
                    created_at
                FROM devices
                WHERE id = ?
                  AND user_id = ?
                LIMIT 1
                """,
                (
                    device_id,
                    user_id,
                ),
            )

            row = cursor.fetchone()

        finally:

            connection.close()

        if row is None:
            return None

        return self._row_to_device(row)

    # ========================================================
    # GET DEVICE BY BLE ADDRESS
    # ========================================================

    def get_device_by_address(
        self,
        user_id: int,
        device_address: str,
    ) -> Optional[Device]:
        """
        Find a user's device using its BLE address.
        """

        connection = db.get_connection()

        try:

            cursor = connection.execute(
                """
                SELECT
                    id,
                    user_id,
                    device_name,
                    device_address,
                    device_type,
                    connection_type,
                    status,
                    last_seen,
                    created_at
                FROM devices
                WHERE user_id = ?
                  AND device_address = ?
                LIMIT 1
                """,
                (
                    user_id,
                    device_address,
                ),
            )

            row = cursor.fetchone()

        finally:

            connection.close()

        if row is None:
            return None

        return self._row_to_device(row)

    # ========================================================
    # GET USER DEVICES
    # ========================================================

    def get_user_devices(
        self,
        user_id: int,
    ) -> list[Device]:
        """
        Return all devices belonging to one user.
        """

        if not self._user_exists(user_id):
            return []

        connection = db.get_connection()

        try:

            cursor = connection.execute(
                """
                SELECT
                    id,
                    user_id,
                    device_name,
                    device_address,
                    device_type,
                    connection_type,
                    status,
                    last_seen,
                    created_at
                FROM devices
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id,),
            )

            rows = cursor.fetchall()

        finally:

            connection.close()

        return [
            self._row_to_device(row)
            for row in rows
        ]

    # ========================================================
    # UPDATE STATUS
    # ========================================================

    def update_connection_status(
        self,
        user_id: int,
        device_id: int,
        status: str,
    ) -> bool:
        """
        Update the device connection status.

        Allowed:

            Connected
            Disconnected
            Connecting
            Error
        """

        allowed_statuses = {
            "Connected",
            "Disconnected",
            "Connecting",
            "Error",
        }

        normalized_status = status.strip().capitalize()

        if normalized_status not in allowed_statuses:
            return False

        if not self.get_device(
            device_id,
            user_id,
        ):
            return False


        with db.transaction() as connection:

            connection.execute(
                """
                UPDATE devices
                SET
                    status = ?
                WHERE id = ?
                AND user_id = ?
                """,
                (
                    normalized_status,
                    device_id,
                    user_id,
                ),
            )
        return True

    # ========================================================
    # UPDATE LAST SEEN
    # ========================================================

    def update_last_seen(
        self,
        user_id: int,
        device_id: int,
    ) -> bool:
        """
        Update the last time data was received.
        """

        if not self.get_device(
            device_id,
            user_id,
        ):
            return False

        now = utc_now_iso()

        with db.transaction() as connection:

            connection.execute(
                """
                UPDATE devices
                SET
                    last_seen = ?
                WHERE id = ?
                  AND user_id = ?
                """,
                (
                    now,
                    device_id,
                    user_id,
                ),
            )

        return True

    # ========================================================
    # MARK CONNECTED
    # ========================================================

    def mark_connected(
        self,
        user_id: int,
        device_id: int,
    ) -> bool:
        """
        Mark device connected and update last_seen.
        """

        if not self.update_connection_status(
            user_id,
            device_id,
            "Connected",
        ):
            return False

        return self.update_last_seen(
            user_id,
            device_id,
        )

    # ========================================================
    # MARK DISCONNECTED
    # ========================================================

    def mark_disconnected(
        self,
        user_id: int,
        device_id: int,
    ) -> bool:
        """
        Mark device disconnected.
        """

        return self.update_connection_status(
            user_id,
            device_id,
            "Disconnected",
        )

    # ========================================================
    # REMOVE DEVICE
    # ========================================================

    def remove_device(
        self,
        user_id: int,
        device_id: int,
    ) -> bool:
        """
        Remove a device belonging to the specified user.
        """

        with db.transaction() as connection:

            cursor = connection.execute(
                """
                DELETE FROM devices
                WHERE id = ?
                  AND user_id = ?
                """,
                (
                    device_id,
                    user_id,
                ),
            )

            return cursor.rowcount > 0

    # ========================================================
    # PRIVATE USER CHECK
    # ========================================================

    def _user_exists(
        self,
        user_id: int,
    ) -> bool:
        """
        Verify that a user exists.
        """

        connection = db.get_connection()

        try:

            cursor = connection.execute(
                """
                SELECT 1
                FROM users
                WHERE id = ?
                LIMIT 1
                """,
                (user_id,),
            )

            return cursor.fetchone() is not None

        finally:

            connection.close()

    # ========================================================
    # ROW → DEVICE
    # ========================================================

    @staticmethod
    def _row_to_device(row) -> Device:
        """
        Convert a SQLite row into a Device model.
        """

        return Device(
            id=row["id"],
            user_id=row["user_id"],
            device_name=row["device_name"],
            device_address=row["device_address"],
            device_type=row["device_type"],
            connection_type=row["connection_type"],
            status=row["status"],
            last_seen=row["last_seen"],
            created_at=row["created_at"],
        )


# ============================================================
# DEFAULT SERVICE
# ============================================================

device_service = DeviceService()


__all__ = [
    "DeviceService",
    "device_service",
]