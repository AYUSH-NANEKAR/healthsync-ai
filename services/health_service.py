"""
HealthSync AI - Health Service

Responsible for storing and retrieving user health data.

Architecture:

    BLE Simulator / Future ESP32
                ↓
          BLEDataSnapshot
                ↓
          HealthService
                ↓
             SQLite
                ↓
             user_id
                ↓
          HealthSync AI UI

IMPORTANT:
    This service does NOT generate sensor values.

    Values must come from an external source such as:
        - Temporary BLE simulator
        - Future ESP32 wearable
        - Future real sensors

Every health record is associated with a user_id.
"""

from __future__ import annotations

from typing import Optional

from database.database import db
from database.models import (
    ActivityData,
    BLEDataSnapshot,
    DeviceTelemetry,
    Vital,
)
from utils.datetime_utils import utc_now_iso


class HealthService:
    """
    Health data storage and retrieval service.
    """

    # ========================================================
    # SAVE VITALS
    # ========================================================

    def save_vitals(
        self,
        user_id: int,
        snapshot: BLEDataSnapshot,
        device_id: Optional[int] = None,
    ) -> Optional[int]:
        """
        Store vital measurements received from a BLE source.

        No sensor values are generated here.

        Returns:
            Database record ID, or None if nothing was saved.
        """

        if not self._user_exists(user_id):
            return None

        # Only save a vital record if at least one vital
        # measurement was actually received.

        if not self._has_vitals(snapshot):
            return None

        recorded_at = (
            snapshot.received_at
            or utc_now_iso()
        )

        with db.transaction() as connection:

            cursor = connection.execute(
                """
                INSERT INTO vitals (
                    user_id,
                    device_id,
                    heart_rate,
                    spo2,
                    temperature,
                    systolic_pressure,
                    diastolic_pressure,
                    recorded_at,
                    source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    device_id,
                    snapshot.heart_rate,
                    snapshot.spo2,
                    snapshot.temperature,
                    snapshot.systolic_pressure,
                    snapshot.diastolic_pressure,
                    recorded_at,
                    snapshot.device_address,
                ),
            )

            return cursor.lastrowid

    # ========================================================
    # SAVE ACTIVITY
    # ========================================================

    def save_activity(
        self,
        user_id: int,
        snapshot: BLEDataSnapshot,
        device_id: Optional[int] = None,
    ) -> Optional[int]:
        """
        Store activity measurements received from BLE.

        Activity fields:

            movement
            steps
            distance
            calories
            active time
        """

        if not self._user_exists(user_id):
            return None

        if not self._has_activity(snapshot):
            return None

        recorded_at = (
            snapshot.received_at
            or utc_now_iso()
        )

        with db.transaction() as connection:

            cursor = connection.execute(
                """
                INSERT INTO activity_data (
                    user_id,
                    device_id,
                    movement,
                    steps,
                    distance_km,
                    calories_kcal,
                    active_seconds,
                    recorded_at,
                    source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    device_id,
                    snapshot.movement,
                    snapshot.steps,
                    snapshot.distance_km,
                    snapshot.calories_kcal,
                    snapshot.active_seconds,
                    recorded_at,
                    snapshot.device_address,
                ),
            )

            return cursor.lastrowid

    # ========================================================
    # SAVE DEVICE TELEMETRY
    # ========================================================

    def save_device_telemetry(
        self,
        user_id: int,
        snapshot: BLEDataSnapshot,
        device_id: Optional[int] = None,
    ) -> Optional[int]:
        """
        Store device telemetry.

        Currently this includes battery percentage.
        """

        if not self._user_exists(user_id):
            return None

        if snapshot.battery_percent is None:
            return None

        if device_id is None:
            return None

        recorded_at = (
            snapshot.received_at
            or utc_now_iso()
        )

        with db.transaction() as connection:

            cursor = connection.execute(
                """
                INSERT INTO device_telemetry (
                    user_id,
                    device_id,
                    battery_percent,
                    recorded_at,
                    source
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    device_id,
                    snapshot.battery_percent,
                    recorded_at,
                    snapshot.device_address,
                ),
            )

            return cursor.lastrowid

    # ========================================================
    # SAVE COMPLETE SNAPSHOT
    # ========================================================

    def save_snapshot(
        self,
        user_id: int,
        snapshot: BLEDataSnapshot,
        device_id: Optional[int] = None,
    ) -> dict[str, Optional[int]]:
        """
        Store all available health/activity/device data from
        one BLE snapshot.

        A missing value remains None and is not fabricated.

        Returns:
            Dictionary containing inserted record IDs.
        """

        return {
            "vital_id": self.save_vitals(
                user_id,
                snapshot,
                device_id,
            ),
            "activity_id": self.save_activity(
                user_id,
                snapshot,
                device_id,
            ),
            "telemetry_id": self.save_device_telemetry(
                user_id,
                snapshot,
                device_id,
            ),
        }

    # ========================================================
    # GET LATEST VITALS
    # ========================================================

    def get_latest_vitals(
        self,
        user_id: int,
    ) -> Optional[Vital]:
        """
        Retrieve the latest vital record belonging to user_id.
        """

        if not self._user_exists(user_id):
            return None

        connection = db.get_connection()

        try:

            cursor = connection.execute(
                """
                SELECT
                    id,
                    user_id,
                    device_id,
                    heart_rate,
                    spo2,
                    temperature,
                    systolic_pressure,
                    diastolic_pressure,
                    recorded_at,
                    source
                FROM vitals
                WHERE user_id = ?
                ORDER BY recorded_at DESC
                LIMIT 1
                """,
                (user_id,),
            )

            row = cursor.fetchone()

        finally:

            connection.close()

        if row is None:
            return None

        return Vital(
            id=row["id"],
            user_id=row["user_id"],
            device_id=row["device_id"],
            heart_rate=row["heart_rate"],
            spo2=row["spo2"],
            temperature=row["temperature"],
            systolic_pressure=row["systolic_pressure"],
            diastolic_pressure=row["diastolic_pressure"],
            recorded_at=row["recorded_at"],
            source=row["source"],
        )

    # ========================================================
    # GET LATEST ACTIVITY
    # ========================================================

    def get_latest_activity(
        self,
        user_id: int,
    ) -> Optional[ActivityData]:
        """
        Retrieve the latest activity record belonging
        to user_id.
        """

        if not self._user_exists(user_id):
            return None

        connection = db.get_connection()

        try:

            cursor = connection.execute(
                """
                SELECT
                    id,
                    user_id,
                    device_id,
                    movement,
                    steps,
                    distance_km,
                    calories_kcal,
                    active_seconds,
                    recorded_at,
                    source
                FROM activity_data
                WHERE user_id = ?
                ORDER BY recorded_at DESC
                LIMIT 1
                """,
                (user_id,),
            )

            row = cursor.fetchone()

        finally:

            connection.close()

        if row is None:
            return None

        return ActivityData(
            id=row["id"],
            user_id=row["user_id"],
            device_id=row["device_id"],
            movement=row["movement"],
            steps=row["steps"],
            distance_km=row["distance_km"],
            calories_kcal=row["calories_kcal"],
            active_seconds=row["active_seconds"],
            recorded_at=row["recorded_at"],
            source=row["source"],
        )

    # ========================================================
    # GET LATEST BATTERY
    # ========================================================

    def get_latest_battery(
        self,
        user_id: int,
        device_id: Optional[int] = None,
    ) -> Optional[DeviceTelemetry]:
        """
        Retrieve the latest battery reading.

        If device_id is supplied, the result is restricted
        to that device.
        """

        if not self._user_exists(user_id):
            return None

        connection = db.get_connection()

        try:

            if device_id is None:

                cursor = connection.execute(
                    """
                    SELECT
                        id,
                        user_id,
                        device_id,
                        battery_percent,
                        recorded_at,
                        source
                    FROM device_telemetry
                    WHERE user_id = ?
                    ORDER BY recorded_at DESC
                    LIMIT 1
                    """,
                    (user_id,),
                )

            else:

                cursor = connection.execute(
                    """
                    SELECT
                        id,
                        user_id,
                        device_id,
                        battery_percent,
                        recorded_at,
                        source
                    FROM device_telemetry
                    WHERE user_id = ?
                      AND device_id = ?
                    ORDER BY recorded_at DESC
                    LIMIT 1
                    """,
                    (
                        user_id,
                        device_id,
                    ),
                )

            row = cursor.fetchone()

        finally:

            connection.close()

        if row is None:
            return None

        return DeviceTelemetry(
            id=row["id"],
            user_id=row["user_id"],
            device_id=row["device_id"],
            battery_percent=row["battery_percent"],
            recorded_at=row["recorded_at"],
            source=row["source"],
        )

    # ========================================================
    # GET VITAL HISTORY
    # ========================================================

    def get_vital_history(
        self,
        user_id: int,
        limit: int = 100,
    ) -> list[Vital]:
        """
        Return recent vital records for one user.
        """

        if not self._user_exists(user_id):
            return []

        limit = max(1, min(int(limit), 1000))

        connection = db.get_connection()

        try:

            cursor = connection.execute(
                """
                SELECT
                    id,
                    user_id,
                    device_id,
                    heart_rate,
                    spo2,
                    temperature,
                    systolic_pressure,
                    diastolic_pressure,
                    recorded_at,
                    source
                FROM vitals
                WHERE user_id = ?
                ORDER BY recorded_at DESC
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
            Vital(
                id=row["id"],
                user_id=row["user_id"],
                device_id=row["device_id"],
                heart_rate=row["heart_rate"],
                spo2=row["spo2"],
                temperature=row["temperature"],
                systolic_pressure=row["systolic_pressure"],
                diastolic_pressure=row["diastolic_pressure"],
                recorded_at=row["recorded_at"],
                source=row["source"],
            )
            for row in rows
        ]

    # ========================================================
    # GET ACTIVITY HISTORY
    # ========================================================

    def get_activity_history(
        self,
        user_id: int,
        limit: int = 100,
    ) -> list[ActivityData]:
        """
        Return recent activity records for one user.
        """

        if not self._user_exists(user_id):
            return []

        limit = max(1, min(int(limit), 1000))

        connection = db.get_connection()

        try:

            cursor = connection.execute(
                """
                SELECT
                    id,
                    user_id,
                    device_id,
                    movement,
                    steps,
                    distance_km,
                    calories_kcal,
                    active_seconds,
                    recorded_at,
                    source
                FROM activity_data
                WHERE user_id = ?
                ORDER BY recorded_at DESC
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
            ActivityData(
                id=row["id"],
                user_id=row["user_id"],
                device_id=row["device_id"],
                movement=row["movement"],
                steps=row["steps"],
                distance_km=row["distance_km"],
                calories_kcal=row["calories_kcal"],
                active_seconds=row["active_seconds"],
                recorded_at=row["recorded_at"],
                source=row["source"],
            )
            for row in rows
        ]

    # ========================================================
    # PRIVATE USER CHECK
    # ========================================================

    def _user_exists(
        self,
        user_id: int,
    ) -> bool:
        """
        Verify that the target user exists.
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
    # PRIVATE VITAL CHECK
    # ========================================================

    @staticmethod
    def _has_vitals(
        snapshot: BLEDataSnapshot,
    ) -> bool:
        """
        Check whether the snapshot contains at least one
        actual vital measurement.
        """

        return any(
            value is not None
            for value in (
                snapshot.heart_rate,
                snapshot.spo2,
                snapshot.temperature,
                snapshot.systolic_pressure,
                snapshot.diastolic_pressure,
            )
        )

    # ========================================================
    # PRIVATE ACTIVITY CHECK
    # ========================================================

    @staticmethod
    def _has_activity(
        snapshot: BLEDataSnapshot,
    ) -> bool:
        """
        Check whether the snapshot contains actual activity
        information.
        """

        return any(
            value is not None
            for value in (
                snapshot.movement,
                snapshot.steps,
                snapshot.distance_km,
                snapshot.calories_kcal,
                snapshot.active_seconds,
            )
        )


# ============================================================
# DEFAULT SERVICE
# ============================================================

health_service = HealthService()


__all__ = [
    "HealthService",
    "health_service",
]