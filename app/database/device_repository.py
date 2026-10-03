from datetime import datetime

from app.database.connection import get_connection


class DeviceRepository:
    """
    Handles persistent BLE device records in SQLite.

    Responsibilities:
    - Find a device belonging to a user.
    - Register a new device.
    - Update device connection status.
    - Update the last time the device was seen.

    This class does not know anything about:
    - Bleak
    - PySide6
    - HealthService
    - AI
    """

    def find_by_address(
        self,
        user_id: int,
        device_address: str,
    ):
        """
        Find a device by Bluetooth address for a specific user.

        Returns:
            Device row as a dictionary-like sqlite3.Row,
            or None if the device does not exist.
        """

        connection = get_connection()

        try:
            connection.row_factory = __import__("sqlite3").Row

            return connection.execute(
                """
                SELECT
                    id,
                    user_id,
                    device_name,
                    device_address,
                    device_type,
                    connection_type,
                    status,
                    service_uuid,
                    last_seen_at,
                    created_at,
                    updated_at
                FROM devices
                WHERE user_id = ?
                  AND device_address = ?
                LIMIT 1
                """,
                (
                    user_id,
                    device_address,
                ),
            ).fetchone()

        finally:
            connection.close()

    def create(
        self,
        user_id: int,
        device_name: str,
        device_address: str,
        device_type: str,
        connection_type: str,
        service_uuid: str | None = None,
    ) -> int:
        """
        Create a new device record.

        Returns:
            The newly created device ID.
        """

        connection = get_connection()

        try:
            cursor = connection.execute(
                """
                INSERT INTO devices (
                    user_id,
                    device_name,
                    device_address,
                    device_type,
                    connection_type,
                    status,
                    service_uuid,
                    last_seen_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    device_name,
                    device_address,
                    device_type,
                    connection_type,
                    "CONNECTED",
                    service_uuid,
                    datetime.now(),
                    datetime.now(),
                ),
            )

            connection.commit()

            return cursor.lastrowid

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def mark_connected(
        self,
        device_id: int,
    ):
        """
        Mark a device as connected and update last_seen_at.
        """

        connection = get_connection()

        try:
            now = datetime.now()

            connection.execute(
                """
                UPDATE devices
                SET
                    status = ?,
                    last_seen_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    "CONNECTED",
                    now,
                    now,
                    device_id,
                ),
            )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def mark_disconnected(
        self,
        device_id: int,
    ):
        """
        Mark a device as disconnected.
        """

        connection = get_connection()

        try:
            connection.execute(
                """
                UPDATE devices
                SET
                    status = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    "DISCONNECTED",
                    datetime.now(),
                    device_id,
                ),
            )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()