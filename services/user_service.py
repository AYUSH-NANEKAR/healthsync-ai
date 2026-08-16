"""
HealthSync AI - User Service

Handles user-specific profile operations.

Core rule:
    Every operation is scoped to user_id.

This service does NOT:
    - Handle UI
    - Handle BLE
    - Generate health values
    - Perform AI analysis
    - Store passwords directly

Authentication is handled by AuthService.
"""

from __future__ import annotations

from typing import Optional

from database.database import db
from database.models import HealthProfile, User
from utils.datetime_utils import utc_now_iso
from utils.validators import (
    validate_blood_group,
    validate_phone,
)


class UserService:
    """
    Provides user and health-profile operations.
    """

    # ========================================================
    # GET USER
    # ========================================================

    def get_user(self, user_id: int) -> Optional[User]:
        """
        Retrieve a user by ID.
        """

        connection = db.get_connection()

        try:
            cursor = connection.execute(
                """
                SELECT
                    id,
                    name,
                    email,
                    password_hash,
                    phone,
                    date_of_birth,
                    gender,
                    created_at,
                    updated_at
                FROM users
                WHERE id = ?
                LIMIT 1
                """,
                (user_id,),
            )

            row = cursor.fetchone()

        finally:
            connection.close()

        if row is None:
            return None

        return User(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            password_hash=row["password_hash"],
            phone=row["phone"],
            date_of_birth=row["date_of_birth"],
            gender=row["gender"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    # ========================================================
    # UPDATE USER
    # ========================================================

    def update_user(
        self,
        user_id: int,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        date_of_birth: Optional[str] = None,
        gender: Optional[str] = None,
    ) -> tuple[bool, str]:
        """
        Update basic user information.

        Email and password are intentionally not changed here.
        """

        user = self.get_user(user_id)

        if user is None:
            return False, "User not found."

        if name is not None:

            name = name.strip()

            if not name:
                return False, "Name cannot be empty."

            if len(name) > 100:
                return False, "Name is too long."

        if phone is not None and phone:

            valid, message = validate_phone(phone)

            if not valid:
                return False, message

            phone = phone.strip()

        now = utc_now_iso()

        with db.transaction() as connection:

            connection.execute(
                """
                UPDATE users
                SET
                    name = COALESCE(?, name),
                    phone = COALESCE(?, phone),
                    date_of_birth = COALESCE(?, date_of_birth),
                    gender = COALESCE(?, gender),
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    name,
                    phone,
                    date_of_birth,
                    gender,
                    now,
                    user_id,
                ),
            )

        return True, "User profile updated successfully."

    # ========================================================
    # GET HEALTH PROFILE
    # ========================================================

    def get_health_profile(
        self,
        user_id: int,
    ) -> Optional[HealthProfile]:
        """
        Retrieve the health profile belonging to user_id.
        """

        connection = db.get_connection()

        try:

            cursor = connection.execute(
                """
                SELECT
                    id,
                    user_id,
                    height,
                    weight,
                    blood_group,
                    medical_conditions,
                    allergies,
                    medications,
                    emergency_notes,
                    updated_at
                FROM health_profiles
                WHERE user_id = ?
                LIMIT 1
                """,
                (user_id,),
            )

            row = cursor.fetchone()

        finally:

            connection.close()

        if row is None:
            return None

        return HealthProfile(
            id=row["id"],
            user_id=row["user_id"],
            height=row["height"],
            weight=row["weight"],
            blood_group=row["blood_group"],
            medical_conditions=row["medical_conditions"],
            allergies=row["allergies"],
            medications=row["medications"],
            emergency_notes=row["emergency_notes"],
            updated_at=row["updated_at"],
        )

    # ========================================================
    # CREATE / UPDATE HEALTH PROFILE
    # ========================================================

    def save_health_profile(
        self,
        user_id: int,
        height: Optional[float] = None,
        weight: Optional[float] = None,
        blood_group: Optional[str] = None,
        medical_conditions: Optional[str] = None,
        allergies: Optional[str] = None,
        medications: Optional[str] = None,
        emergency_notes: Optional[str] = None,
    ) -> tuple[bool, str]:
        """
        Create or update the health profile for one user.

        No default/fake health measurements are generated.
        """

        user = self.get_user(user_id)

        if user is None:
            return False, "User not found."

        # ----------------------------------------------------
        # VALIDATE NUMERIC PROFILE VALUES
        # ----------------------------------------------------

        if height is not None:

            try:
                height = float(height)
            except (TypeError, ValueError):
                return False, "Height must be a number."

            if height <= 0:
                return False, "Height must be greater than zero."

        if weight is not None:

            try:
                weight = float(weight)
            except (TypeError, ValueError):
                return False, "Weight must be a number."

            if weight <= 0:
                return False, "Weight must be greater than zero."

        # ----------------------------------------------------
        # VALIDATE BLOOD GROUP
        # ----------------------------------------------------

        if blood_group:

            valid, message = validate_blood_group(
                blood_group
            )

            if not valid:
                return False, message

            blood_group = blood_group.strip().upper()

        # ----------------------------------------------------
        # CHECK EXISTING PROFILE
        # ----------------------------------------------------

        existing = self.get_health_profile(user_id)

        now = utc_now_iso()

        with db.transaction() as connection:

            if existing is None:

                connection.execute(
                    """
                    INSERT INTO health_profiles (
                        user_id,
                        height,
                        weight,
                        blood_group,
                        medical_conditions,
                        allergies,
                        medications,
                        emergency_notes,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        height,
                        weight,
                        blood_group,
                        medical_conditions,
                        allergies,
                        medications,
                        emergency_notes,
                        now,
                    ),
                )

            else:

                connection.execute(
                    """
                    UPDATE health_profiles
                    SET
                        height = COALESCE(?, height),
                        weight = COALESCE(?, weight),
                        blood_group = COALESCE(?, blood_group),
                        medical_conditions =
                            COALESCE(?, medical_conditions),
                        allergies =
                            COALESCE(?, allergies),
                        medications =
                            COALESCE(?, medications),
                        emergency_notes =
                            COALESCE(?, emergency_notes),
                        updated_at = ?
                    WHERE user_id = ?
                    """,
                    (
                        height,
                        weight,
                        blood_group,
                        medical_conditions,
                        allergies,
                        medications,
                        emergency_notes,
                        now,
                        user_id,
                    ),
                )

        return True, "Health profile saved successfully."


# ============================================================
# DEFAULT SERVICE
# ============================================================

user_service = UserService()


__all__ = [
    "UserService",
    "user_service",
]