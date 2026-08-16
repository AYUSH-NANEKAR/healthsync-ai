"""
HealthSync AI - Emergency Contact Service

Manages emergency contacts stored in SQLite.

Responsibilities:
    - Add emergency contacts
    - Retrieve user contacts
    - Retrieve a specific contact
    - Update contacts
    - Delete contacts
    - Manage primary emergency contact

Important:
    - Contacts are user-specific
    - No hardcoded contacts
    - Phone country code is stored separately
    - Uses SQLite
    - Does not send SMS/calls
    - Communication actions can be added later
"""

from __future__ import annotations

from typing import Any, Optional

from database.database import db


class EmergencyContactService:
    """
    Service responsible for emergency-contact management.
    """

    # ========================================================
    # CREATE CONTACT
    # ========================================================

    def add_contact(
        self,
        user_id: int,
        name: str,
        phone: str,
        country_code: str = "+91",
        relationship: Optional[str] = None,
        is_primary: bool = False,
    ) -> tuple[bool, str, Optional[dict[str, Any]]]:
        """
        Add an emergency contact for a user.
        """

        name = name.strip()
        phone = phone.strip()
        country_code = country_code.strip()

        if not name:
            return False, "Contact name is required.", None

        if not phone:
            return False, "Phone number is required.", None

        if not country_code:
            return False, "Country code is required.", None

        connection = db.get_connection()

        try:
            if is_primary:
                connection.execute(
                    """
                    UPDATE emergency_contacts
                    SET is_primary = 0
                    WHERE user_id = ?
                    """,
                    (user_id,),
                )

            cursor = connection.execute(
                """
                INSERT INTO emergency_contacts (
                    user_id,
                    name,
                    phone,
                    country_code,
                    relationship,
                    is_primary
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    name,
                    phone,
                    country_code,
                    relationship,
                    1 if is_primary else 0,
                ),
            )

            connection.commit()

            contact_id = cursor.lastrowid

            contact = self.get_contact(
                user_id,
                contact_id,
            )

            return (
                True,
                "Emergency contact added successfully.",
                contact,
            )

        except Exception as exc:

            connection.rollback()

            return (
                False,
                f"Failed to add emergency contact: {exc}",
                None,
            )

        finally:
            connection.close()

    # ========================================================
    # GET ALL CONTACTS
    # ========================================================

    def get_user_contacts(
        self,
        user_id: int,
    ) -> list[dict[str, Any]]:
        """
        Return all emergency contacts belonging to a user.

        Primary contacts are returned first.
        """

        connection = db.get_connection()

        try:
            rows = connection.execute(
                """
                SELECT *
                FROM emergency_contacts
                WHERE user_id = ?
                ORDER BY
                    is_primary DESC,
                    name ASC,
                    id ASC
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
    # GET ONE CONTACT
    # ========================================================

    def get_contact(
        self,
        user_id: int,
        contact_id: int,
    ) -> Optional[dict[str, Any]]:
        """
        Retrieve one contact belonging to the specified user.

        The user_id condition prevents one user from accessing
        another user's contact.
        """

        connection = db.get_connection()

        try:
            row = connection.execute(
                """
                SELECT *
                FROM emergency_contacts
                WHERE id = ?
                  AND user_id = ?
                LIMIT 1
                """,
                (
                    contact_id,
                    user_id,
                ),
            ).fetchone()

            if row is None:
                return None

            return dict(row)

        finally:
            connection.close()

    # ========================================================
    # UPDATE CONTACT
    # ========================================================

    def update_contact(
        self,
        user_id: int,
        contact_id: int,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        country_code: Optional[str] = None,
        relationship: Optional[str] = None,
        is_primary: Optional[bool] = None,
    ) -> tuple[bool, str, Optional[dict[str, Any]]]:
        """
        Update an existing emergency contact.

        Only supplied values are changed.
        """

        existing = self.get_contact(
            user_id,
            contact_id,
        )

        if existing is None:
            return (
                False,
                "Emergency contact not found.",
                None,
            )

        updated_name = (
            name.strip()
            if name is not None
            else existing.get("name")
        )

        updated_phone = (
            phone.strip()
            if phone is not None
            else existing.get("phone")
        )

        updated_country_code = (
            country_code.strip()
            if country_code is not None
            else existing.get("country_code")
        )

        updated_relationship = (
            relationship
            if relationship is not None
            else existing.get("relationship")
        )

        updated_primary = (
            is_primary
            if is_primary is not None
            else bool(existing.get("is_primary"))
        )

        if not updated_name:
            return False, "Contact name is required.", None

        if not updated_phone:
            return False, "Phone number is required.", None

        if not updated_country_code:
            return False, "Country code is required.", None

        connection = db.get_connection()

        try:
            if updated_primary:
                connection.execute(
                    """
                    UPDATE emergency_contacts
                    SET is_primary = 0
                    WHERE user_id = ?
                      AND id != ?
                    """,
                    (
                        user_id,
                        contact_id,
                    ),
                )

            connection.execute(
                """
                UPDATE emergency_contacts
                SET
                    name = ?,
                    phone = ?,
                    country_code = ?,
                    relationship = ?,
                    is_primary = ?
                WHERE id = ?
                  AND user_id = ?
                """,
                (
                    updated_name,
                    updated_phone,
                    updated_country_code,
                    updated_relationship,
                    1 if updated_primary else 0,
                    contact_id,
                    user_id,
                ),
            )

            connection.commit()

            updated = self.get_contact(
                user_id,
                contact_id,
            )

            return (
                True,
                "Emergency contact updated successfully.",
                updated,
            )

        except Exception as exc:

            connection.rollback()

            return (
                False,
                f"Failed to update emergency contact: {exc}",
                None,
            )

        finally:
            connection.close()

    # ========================================================
    # DELETE CONTACT
    # ========================================================

    def delete_contact(
        self,
        user_id: int,
        contact_id: int,
    ) -> tuple[bool, str]:
        """
        Delete an emergency contact belonging to the user.
        """

        existing = self.get_contact(
            user_id,
            contact_id,
        )

        if existing is None:
            return (
                False,
                "Emergency contact not found.",
            )

        connection = db.get_connection()

        try:
            connection.execute(
                """
                DELETE FROM emergency_contacts
                WHERE id = ?
                  AND user_id = ?
                """,
                (
                    contact_id,
                    user_id,
                ),
            )

            connection.commit()

            return (
                True,
                "Emergency contact deleted successfully.",
            )

        except Exception as exc:

            connection.rollback()

            return (
                False,
                f"Failed to delete emergency contact: {exc}",
            )

        finally:
            connection.close()

    # ========================================================
    # SET PRIMARY CONTACT
    # ========================================================

    def set_primary_contact(
        self,
        user_id: int,
        contact_id: int,
    ) -> tuple[bool, str, Optional[dict[str, Any]]]:
        """
        Make a contact the user's primary emergency contact.
        """

        existing = self.get_contact(
            user_id,
            contact_id,
        )

        if existing is None:
            return (
                False,
                "Emergency contact not found.",
                None,
            )

        connection = db.get_connection()

        try:
            connection.execute(
                """
                UPDATE emergency_contacts
                SET is_primary = 0
                WHERE user_id = ?
                """,
                (user_id,),
            )

            connection.execute(
                """
                UPDATE emergency_contacts
                SET is_primary = 1
                WHERE id = ?
                  AND user_id = ?
                """,
                (
                    contact_id,
                    user_id,
                ),
            )

            connection.commit()

            contact = self.get_contact(
                user_id,
                contact_id,
            )

            return (
                True,
                "Primary emergency contact updated.",
                contact,
            )

        except Exception as exc:

            connection.rollback()

            return (
                False,
                f"Failed to set primary contact: {exc}",
                None,
            )

        finally:
            connection.close()

    # ========================================================
    # GET PRIMARY CONTACT
    # ========================================================

    def get_primary_contact(
        self,
        user_id: int,
    ) -> Optional[dict[str, Any]]:
        """
        Return the user's primary emergency contact.
        """

        connection = db.get_connection()

        try:
            row = connection.execute(
                """
                SELECT *
                FROM emergency_contacts
                WHERE user_id = ?
                  AND is_primary = 1
                ORDER BY id ASC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()

            if row is None:
                return None

            return dict(row)

        finally:
            connection.close()


# ============================================================
# DEFAULT SERVICE INSTANCE
# ============================================================

emergency_contact_service = (
    EmergencyContactService()
)


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "EmergencyContactService",
    "emergency_contact_service",
]