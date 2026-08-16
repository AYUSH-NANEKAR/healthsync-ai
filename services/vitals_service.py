"""
HealthSync AI - Vitals Service

Handles storage and retrieval of health vital readings.

Data source:
    BLE simulator currently
    Real ESP32 wearable in the future

The service does not generate sensor values.

Expected vitals:
    - Heart rate
    - SpO2
    - Temperature
    - Steps
    - Movement
    - Systolic pressure
    - Diastolic pressure

All data is associated with:
    user_id
    device_id
    source

This keeps the service independent from the actual
sensor/device implementation.
"""

from __future__ import annotations

from typing import Any, Optional


from database.database import db


class VitalsService:
    """
    Service responsible for health-vital data.
    """

    # ========================================================
    # RECORD VITALS
    # ========================================================

    def record_vitals(
        self,
        user_id: int,
        device_id: Optional[int] = None,
        heart_rate: Optional[float] = None,
        spo2: Optional[float] = None,
        temperature: Optional[float] = None,
        steps: Optional[int] = None,
        movement: Optional[str] = None,
        source: str = "BLE",
        systolic_pressure: Optional[float] = None,
        diastolic_pressure: Optional[float] = None,
        recorded_at: Optional[str] = None,
    ) -> tuple[bool, str, Optional[dict[str, Any]]]:
        """
        Store one vital reading.

        Values are supplied by the caller.
        No sensor values are generated here.
        """

        if user_id is None:
            return (
                False,
                "User ID is required.",
                None,
            )

        source = (
            str(source).strip()
            if source is not None
            else "BLE"
        )

        if not source:
            source = "BLE"

        connection = db.get_connection()

        try:

            if recorded_at is None:

                cursor = connection.execute(
                    """
                    INSERT INTO vitals (
                        user_id,
                        device_id,
                        heart_rate,
                        spo2,
                        temperature,
                        steps,
                        movement,
                        source,
                        systolic_pressure,
                        diastolic_pressure
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        device_id,
                        heart_rate,
                        spo2,
                        temperature,
                        steps,
                        movement,
                        source,
                        systolic_pressure,
                        diastolic_pressure,
                    ),
                )

            else:

                cursor = connection.execute(
                    """
                    INSERT INTO vitals (
                        user_id,
                        device_id,
                        heart_rate,
                        spo2,
                        temperature,
                        steps,
                        movement,
                        recorded_at,
                        source,
                        systolic_pressure,
                        diastolic_pressure
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        device_id,
                        heart_rate,
                        spo2,
                        temperature,
                        steps,
                        movement,
                        recorded_at,
                        source,
                        systolic_pressure,
                        diastolic_pressure,
                    ),
                )

            connection.commit()

            vital_id = cursor.lastrowid

            row = connection.execute(
                """
                SELECT *
                FROM vitals
                WHERE id = ?
                  AND user_id = ?
                LIMIT 1
                """,
                (
                    vital_id,
                    user_id,
                ),
            ).fetchone()

            return (
                True,
                "Vitals recorded successfully.",
                dict(row) if row else None,
            )

        except Exception as exc:

            connection.rollback()

            return (
                False,
                f"Failed to record vitals: {exc}",
                None,
            )

        finally:

            connection.close()

    # ========================================================
    # GET LATEST VITALS
    # ========================================================

    def get_latest_vitals(
        self,
        user_id: int,
    ) -> Optional[dict[str, Any]]:
        """
        Get the latest vital reading for a user.
        """

        connection = db.get_connection()

        try:

            row = connection.execute(
                """
                SELECT *
                FROM vitals
                WHERE user_id = ?
                ORDER BY recorded_at DESC, id DESC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()

            if row is None:
                return None

            return dict(row)

        finally:

            connection.close()

    # ========================================================
    # GET SPECIFIC VITAL
    # ========================================================

    def get_vital(
        self,
        user_id: int,
        vital_id: int,
    ) -> Optional[dict[str, Any]]:
        """
        Get one vital record belonging to a user.
        """

        connection = db.get_connection()

        try:

            row = connection.execute(
                """
                SELECT *
                FROM vitals
                WHERE id = ?
                  AND user_id = ?
                LIMIT 1
                """,
                (
                    vital_id,
                    user_id,
                ),
            ).fetchone()

            if row is None:
                return None

            return dict(row)

        finally:

            connection.close()

    # ========================================================
    # GET VITAL HISTORY
    # ========================================================

    def get_vitals_history(
        self,
        user_id: int,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Get recent vital readings.

        Maximum history returned in one call is 500 records.
        """

        limit = max(
            1,
            min(int(limit), 500),
        )

        connection = db.get_connection()

        try:

            rows = connection.execute(
                f"""
                SELECT *
                FROM vitals
                WHERE user_id = ?
                ORDER BY recorded_at DESC, id DESC
                LIMIT {limit}
                """,
                (user_id,),
            ).fetchall()

            return [
                dict(row)
                for row in rows
            ]

        finally:

            connection.close()

    # ========================================================
    # GET DEVICE VITAL HISTORY
    # ========================================================

    def get_device_vitals(
        self,
        user_id: int,
        device_id: int,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Get vitals produced by a specific device.
        """

        limit = max(
            1,
            min(int(limit), 500),
        )

        connection = db.get_connection()

        try:

            rows = connection.execute(
                f"""
                SELECT *
                FROM vitals
                WHERE user_id = ?
                  AND device_id = ?
                ORDER BY recorded_at DESC, id DESC
                LIMIT {limit}
                """,
                (
                    user_id,
                    device_id,
                ),
            ).fetchall()

            return [
                dict(row)
                for row in rows
            ]

        finally:

            connection.close()

    # ========================================================
    # DELETE VITAL
    # ========================================================

    def delete_vital(
        self,
        user_id: int,
        vital_id: int,
    ) -> tuple[bool, str]:
        """
        Delete one vital record belonging to the user.
        """

        connection = db.get_connection()

        try:

            cursor = connection.execute(
                """
                DELETE FROM vitals
                WHERE id = ?
                  AND user_id = ?
                """,
                (
                    vital_id,
                    user_id,
                ),
            )

            connection.commit()

            if cursor.rowcount == 0:

                return (
                    False,
                    "Vital record not found.",
                )

            return (
                True,
                "Vital record deleted successfully.",
            )

        except Exception as exc:

            connection.rollback()

            return (
                False,
                f"Failed to delete vital: {exc}",
            )

        finally:

            connection.close()


# ============================================================
# DEFAULT SERVICE INSTANCE
# ============================================================

vitals_service = VitalsService()


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "VitalsService",
    "vitals_service",
]