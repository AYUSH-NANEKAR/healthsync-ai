"""
HealthSync AI - Location Service

Handles location data received from BLE devices.

Current source:
    HealthSync BLE Simulator

Future source:
    ESP32 / GPS module / phone GPS / other location source

Responsibilities:
    - Store location history
    - Retrieve latest location
    - Retrieve location history
    - Validate coordinates

This service NEVER creates fake coordinates.
"""

from __future__ import annotations

from typing import Optional

from database.database import db
from services.ble_data import BLEPayload
from utils.datetime_utils import utc_now_iso


class LocationService:
    """
    Manages user location data.
    """

    SOURCE = "BLE"

    # ========================================================
    # SAVE BLE LOCATION
    # ========================================================

    def save_ble_location(
        self,
        user_id: int,
        device_id: int,
        payload: BLEPayload,
    ) -> bool:
        """
        Save location received from a BLE payload.

        Location is stored only when valid latitude and
        longitude are actually supplied by the BLE source.
        """

        if payload is None:
            return False

        if payload.latitude is None:
            return False

        if payload.longitude is None:
            return False

        if not self._valid_coordinates(
            payload.latitude,
            payload.longitude,
        ):
            return False

        timestamp = (
            payload.timestamp
            or utc_now_iso()
        )

        readable_location = (
            payload.location_name
        )

        try:

            with db.transaction() as connection:

                connection.execute(
                    """
                    INSERT INTO location_history (
                        user_id,
                        device_id,
                        latitude,
                        longitude,
                        readable_location,
                        accuracy_meters,
                        source,
                        recorded_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        device_id,
                        payload.latitude,
                        payload.longitude,
                        readable_location,
                        None,
                        self.SOURCE,
                        timestamp,
                    ),
                )

            return True

        except Exception as exc:

            print(
                f"Location save error: {exc}"
            )

            return False

    # ========================================================
    # SAVE RAW LOCATION
    # ========================================================

    def save_location(
        self,
        user_id: int,
        device_id: int,
        latitude: float,
        longitude: float,
        readable_location: Optional[str] = None,
        accuracy_meters: Optional[float] = None,
        source: str = "BLE",
        recorded_at: Optional[str] = None,
    ) -> bool:
        """
        Save a location independently of BLEPayload.

        Useful for future GPS/location providers.
        """

        if not self._valid_coordinates(
            latitude,
            longitude,
        ):
            return False

        timestamp = (
            recorded_at
            or utc_now_iso()
        )

        try:

            with db.transaction() as connection:

                connection.execute(
                    """
                    INSERT INTO location_history (
                        user_id,
                        device_id,
                        latitude,
                        longitude,
                        readable_location,
                        accuracy_meters,
                        source,
                        recorded_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        device_id,
                        latitude,
                        longitude,
                        readable_location,
                        accuracy_meters,
                        source,
                        timestamp,
                    ),
                )

            return True

        except Exception as exc:

            print(
                f"Location save error: {exc}"
            )

            return False

    # ========================================================
    # GET LATEST LOCATION
    # ========================================================

    def get_latest_location(
        self,
        user_id: int,
    ) -> Optional[dict]:
        """
        Return the latest location for a user.
        """

        connection = db.get_connection()

        try:

            cursor = connection.execute(
                """
                SELECT
                    id,
                    user_id,
                    device_id,
                    latitude,
                    longitude,
                    readable_location,
                    accuracy_meters,
                    source,
                    recorded_at
                FROM location_history
                WHERE user_id = ?
                ORDER BY recorded_at DESC, id DESC
                LIMIT 1
                """,
                (user_id,),
            )

            row = cursor.fetchone()

        finally:

            connection.close()

        if row is None:
            return None

        return self._row_to_dict(row)

    # ========================================================
    # LOCATION HISTORY
    # ========================================================

    def get_location_history(
        self,
        user_id: int,
        limit: int = 100,
    ) -> list[dict]:
        """
        Return recent location history.

        Newest locations are returned first.
        """

        limit = max(
            1,
            min(limit, 1000),
        )

        connection = db.get_connection()

        try:

            cursor = connection.execute(
                """
                SELECT
                    id,
                    user_id,
                    device_id,
                    latitude,
                    longitude,
                    readable_location,
                    accuracy_meters,
                    source,
                    recorded_at
                FROM location_history
                WHERE user_id = ?
                ORDER BY recorded_at DESC, id DESC
                LIMIT ?
                """,
                (
                    user_id,
                    limit,
                ),
            )

            rows = cursor.fetchall()

        finally:

            connection.close()

        return [
            self._row_to_dict(row)
            for row in rows
        ]

    # ========================================================
    # DELETE LOCATION HISTORY
    # ========================================================

    def clear_user_location_history(
        self,
        user_id: int,
    ) -> int:
        """
        Delete all stored location history for a user.

        Returns the number of deleted records.
        """

        with db.transaction() as connection:

            cursor = connection.execute(
                """
                DELETE FROM location_history
                WHERE user_id = ?
                """,
                (user_id,),
            )

            return cursor.rowcount

    # ========================================================
    # VALIDATE COORDINATES
    # ========================================================

    @staticmethod
    def _valid_coordinates(
        latitude: float,
        longitude: float,
    ) -> bool:
        """
        Validate geographic coordinate ranges.

        Latitude:
            -90 to +90

        Longitude:
            -180 to +180
        """

        try:

            latitude = float(latitude)
            longitude = float(longitude)

        except (
            TypeError,
            ValueError,
        ):

            return False

        return (
            -90.0 <= latitude <= 90.0
            and
            -180.0 <= longitude <= 180.0
        )

    # ========================================================
    # ROW → DICT
    # ========================================================

    @staticmethod
    def _row_to_dict(row) -> dict:
        """
        Convert SQLite row to dictionary.
        """

        return {
            "id": row["id"],
            "user_id": row["user_id"],
            "device_id": row["device_id"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "readable_location": row["readable_location"],
            "accuracy_meters": row["accuracy_meters"],
            "source": row["source"],
            "recorded_at": row["recorded_at"],
        }


location_service = LocationService()


__all__ = [
    "LocationService",
    "location_service",
]