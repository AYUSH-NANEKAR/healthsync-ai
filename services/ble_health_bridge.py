"""
HealthSync AI - BLE Health Bridge

Connects BLE data to the HealthSync AI database.

Data flow:

    BLE Simulator / ESP32
            ↓
       BLEManager
            ↓
        BLEPayload
            ↓
      BLEHealthBridge
            ↓
    ┌───────┼────────┐
    ↓       ↓        ↓
  Vitals Activity  Telemetry
                    ↓
                 Location
                    ↓
             location_history

The BLE simulator is temporary.

The same architecture will work with the real ESP32
wearable without changing the database layer.
"""

from __future__ import annotations

from typing import Callable, Optional

from database.database import db
from services.ble_data import BLEPayload
from services.location_service import location_service
from utils.datetime_utils import utc_now_iso


class BLEHealthBridge:
    """
    Receives BLEPayload objects and persists their data.
    """

    SOURCE = "BLE"

    def __init__(
        self,
        user_id: int,
        device_id: int,
        on_saved: Optional[
            Callable[[BLEPayload], None]
        ] = None,
    ):
        self.user_id = user_id
        self.device_id = device_id
        self.on_saved = on_saved

    # ========================================================
    # PROCESS COMPLETE PAYLOAD
    # ========================================================

    def process(
        self,
        payload: BLEPayload,
    ) -> bool:
        """
        Process one complete BLE payload.

        Synchronizes:

        - Vitals
        - Activity
        - Battery telemetry
        - Location
        - Device last_seen
        """

        if payload is None:
            return False

        timestamp = (
            payload.timestamp
            or utc_now_iso()
        )

        try:

            with db.transaction() as connection:

                self._save_vitals(
                    connection,
                    payload,
                    timestamp,
                )

                self._save_activity(
                    connection,
                    payload,
                    timestamp,
                )

                self._save_telemetry(
                    connection,
                    payload,
                    timestamp,
                )

                self._save_location(
                    connection,
                    payload,
                    timestamp,
                )

                self._update_device(
                    connection,
                    timestamp,
                )

            if self.on_saved:

                try:

                    self.on_saved(payload)

                except Exception as exc:

                    print(
                        f"BLE saved callback error: {exc}"
                    )

            return True

        except Exception as exc:

            print(
                f"BLE health bridge error: {exc}"
            )

            return False

    # ========================================================
    # VITALS
    # ========================================================

    def _save_vitals(
        self,
        connection,
        payload: BLEPayload,
        timestamp: str,
    ):
        """
        Save health measurements.
        """

        has_vitals = any(
            value is not None
            for value in (
                payload.heart_rate,
                payload.spo2,
                payload.temperature,
                payload.steps,
                payload.movement,
                payload.systolic_pressure,
                payload.diastolic_pressure,
            )
        )

        if not has_vitals:
            return

        connection.execute(
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
                self.user_id,
                self.device_id,
                payload.heart_rate,
                payload.spo2,
                payload.temperature,
                payload.steps,
                payload.movement,
                timestamp,
                self.SOURCE,
                payload.systolic_pressure,
                payload.diastolic_pressure,
            ),
        )

    # ========================================================
    # ACTIVITY
    # ========================================================

    def _save_activity(
        self,
        connection,
        payload: BLEPayload,
        timestamp: str,
    ):
        """
        Save activity measurements.
        """

        has_activity = any(
            value is not None
            for value in (
                payload.movement,
                payload.steps,
                payload.distance_km,
                payload.calories_kcal,
                payload.active_seconds,
            )
        )

        if not has_activity:
            return

        connection.execute(
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
                self.user_id,
                self.device_id,
                payload.movement,
                payload.steps,
                payload.distance_km,
                payload.calories_kcal,
                payload.active_seconds,
                timestamp,
                self.SOURCE,
            ),
        )

    # ========================================================
    # DEVICE TELEMETRY
    # ========================================================

    def _save_telemetry(
        self,
        connection,
        payload: BLEPayload,
        timestamp: str,
    ):
        """
        Save device telemetry.
        """

        if payload.battery_percent is None:
            return

        connection.execute(
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
                self.user_id,
                self.device_id,
                payload.battery_percent,
                timestamp,
                self.SOURCE,
            ),
        )

    # ========================================================
    # LOCATION
    # ========================================================

    def _save_location(
        self,
        connection,
        payload: BLEPayload,
        timestamp: str,
    ):
        """
        Save location directly using the same database
        transaction.

        This avoids creating a second independent database
        transaction.
        """

        if payload.latitude is None:
            return

        if payload.longitude is None:
            return

        if not location_service._valid_coordinates(
            payload.latitude,
            payload.longitude,
        ):
            return

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
                self.user_id,
                self.device_id,
                payload.latitude,
                payload.longitude,
                payload.location_name,
                None,
                self.SOURCE,
                timestamp,
            ),
        )

    # ========================================================
    # DEVICE LAST SEEN
    # ========================================================

    def _update_device(
        self,
        connection,
        timestamp: str,
    ):
        """
        Update device connection information.
        """

        connection.execute(
            """
            UPDATE devices
            SET
                status = 'Connected',
                last_seen = ?
            WHERE id = ?
              AND user_id = ?
            """,
            (
                timestamp,
                self.device_id,
                self.user_id,
            ),
        )


__all__ = [
    "BLEHealthBridge",
]