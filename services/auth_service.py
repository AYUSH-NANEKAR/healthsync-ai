"""
HealthSync AI - Authentication Service

Handles:

    - User registration
    - Password verification
    - Persistent login sessions
    - Session restoration
    - Logout
    - Current authenticated user lookup

Architecture:

    UI
      ↓
    AuthService
      ↓
    Security Utilities
      ↓
    SQLite Database

IMPORTANT:
    - Passwords are never stored as plaintext.
    - Authentication is user-specific.
    - Sessions are stored locally in SQLite.
    - No external/paid authentication service is required.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Optional

from database.database import db
from database.models import Session, User
from utils.datetime_utils import utc_now, utc_now_iso
from utils.security import (
    generate_session_token,
    hash_password,
    validate_password,
    verify_password,
)
from utils.validators import (
    validate_email,
    validate_name,
    validate_phone,
)


# ============================================================
# SESSION CONFIGURATION
# ============================================================

# Persistent login session duration.
#
# The user remains signed in across application restarts
# until the session expires or the user explicitly logs out.
#
# This is NOT a password-storage mechanism.

SESSION_DURATION_DAYS = 30


# ============================================================
# AUTHENTICATION SERVICE
# ============================================================

class AuthService:
    """
    Authentication and persistent-session service.
    """

    # ========================================================
    # REGISTER
    # ========================================================

    def register_user(
        self,
        name: str,
        email: str,
        password: str,
        phone: Optional[str] = None,
        date_of_birth: Optional[str] = None,
        gender: Optional[str] = None,
    ) -> tuple[bool, str, Optional[User]]:
        """
        Register a new HealthSync AI user.

        Returns:

            (True, message, User)
                Registration successful.

            (False, message, None)
                Registration failed.
        """

        # ----------------------------------------------------
        # VALIDATE NAME
        # ----------------------------------------------------

        valid, message = validate_name(name)

        if not valid:
            return False, message, None

        # ----------------------------------------------------
        # VALIDATE EMAIL
        # ----------------------------------------------------

        valid, message = validate_email(email)

        if not valid:
            return False, message, None

        # ----------------------------------------------------
        # VALIDATE PASSWORD
        # ----------------------------------------------------

        valid, message = validate_password(password)

        if not valid:
            return False, message, None

        # ----------------------------------------------------
        # VALIDATE PHONE
        # ----------------------------------------------------

        if phone:
            valid, message = validate_phone(phone)

            if not valid:
                return False, message, None

        # ----------------------------------------------------
        # NORMALIZE BASIC INPUT
        # ----------------------------------------------------

        name = name.strip()

        email = email.strip().lower()

        if phone:
            phone = phone.strip()

        # ----------------------------------------------------
        # HASH PASSWORD
        # ----------------------------------------------------

        password_hash = hash_password(password)

        # ----------------------------------------------------
        # INSERT USER
        # ----------------------------------------------------

        try:

            with db.transaction() as connection:

                cursor = connection.execute(
                    """
                    INSERT INTO users (
                        name,
                        email,
                        password_hash,
                        phone,
                        date_of_birth,
                        gender,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        name,
                        email,
                        password_hash,
                        phone,
                        date_of_birth,
                        gender,
                        utc_now_iso(),
                        utc_now_iso(),
                    ),
                )

                user_id = cursor.lastrowid

        except Exception as error:

            error_text = str(error).lower()

            if "unique constraint" in error_text:
                return (
                    False,
                    "An account with this email already exists.",
                    None,
                )

            return (
                False,
                "Registration failed.",
                None,
            )

        # ----------------------------------------------------
        # CREATE USER OBJECT
        # ----------------------------------------------------

        user = User(
            id=user_id,
            name=name,
            email=email,
            password_hash=password_hash,
            phone=phone,
            date_of_birth=date_of_birth,
            gender=gender,
            created_at=utc_now_iso(),
            updated_at=utc_now_iso(),
        )

        return (
            True,
            "Registration successful.",
            user,
        )

    # ========================================================
    # LOGIN
    # ========================================================

    def login(
        self,
        email: str,
        password: str,
        remember_me: bool = True,
    ) -> tuple[bool, str, Optional[User], Optional[str]]:
        """
        Authenticate a user.

        Returns:

            (
                success,
                message,
                user,
                session_token
            )

        When remember_me=True, a persistent session is created.
        """

        if not isinstance(email, str):
            return False, "Invalid email.", None, None

        if not isinstance(password, str):
            return False, "Invalid password.", None, None

        email = email.strip().lower()

        if not email or not password:
            return (
                False,
                "Email and password are required.",
                None,
                None,
            )

        # ----------------------------------------------------
        # FIND USER
        # ----------------------------------------------------

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
                WHERE email = ?
                LIMIT 1
                """,
                (email,),
            )

            row = cursor.fetchone()

        finally:

            connection.close()

        if row is None:
            return (
                False,
                "Invalid email or password.",
                None,
                None,
            )

        # ----------------------------------------------------
        # VERIFY PASSWORD
        # ----------------------------------------------------

        if not verify_password(
            password,
            row["password_hash"],
        ):
            return (
                False,
                "Invalid email or password.",
                None,
                None,
            )

        # ----------------------------------------------------
        # CREATE USER OBJECT
        # ----------------------------------------------------

        user = User(
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

        # ----------------------------------------------------
        # SESSION
        # ----------------------------------------------------

        session_token = None

        if remember_me:

            session_token = self._create_session(
                user_id=user.id,
            )

        return (
            True,
            "Login successful.",
            user,
            session_token,
        )

    # ========================================================
    # CREATE SESSION
    # ========================================================

    def _create_session(
        self,
        user_id: int,
    ) -> str:
        """
        Create a persistent login session.
        """

        session_token = generate_session_token()

        created_at = utc_now()

        expires_at = (
            created_at
            + timedelta(days=SESSION_DURATION_DAYS)
        )

        with db.transaction() as connection:

            # Remove older sessions for the same user.

            connection.execute(
                """
                DELETE FROM sessions
                WHERE user_id = ?
                """,
                (user_id,),
            )

            connection.execute(
                """
                INSERT INTO sessions (
                    user_id,
                    session_token,
                    created_at,
                    last_used_at,
                    expires_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    session_token,
                    created_at.isoformat(),
                    created_at.isoformat(),
                    expires_at.isoformat(),
                ),
            )

        return session_token

    # ========================================================
    # RESTORE SESSION
    # ========================================================

    def restore_session(
        self,
        session_token: str,
    ) -> tuple[bool, Optional[User]]:
        """
        Restore a previously created persistent session.

        This is what the application will use when it starts
        again after being closed.
        """

        if not session_token:
            return False, None

        connection = db.get_connection()

        try:

            cursor = connection.execute(
                """
                SELECT
                    s.id AS session_id,
                    s.user_id,
                    s.session_token,
                    s.expires_at,

                    u.id,
                    u.name,
                    u.email,
                    u.password_hash,
                    u.phone,
                    u.date_of_birth,
                    u.gender,
                    u.created_at,
                    u.updated_at

                FROM sessions s

                INNER JOIN users u
                    ON u.id = s.user_id

                WHERE s.session_token = ?

                LIMIT 1
                """,
                (session_token,),
            )

            row = cursor.fetchone()

        finally:

            connection.close()

        if row is None:
            return False, None

        # ----------------------------------------------------
        # CHECK EXPIRATION
        # ----------------------------------------------------

        expires_at_text = row["expires_at"]

        if expires_at_text:

            try:
                from datetime import datetime

                expires_at = datetime.fromisoformat(
                    expires_at_text
                )

                if utc_now() >= expires_at:

                    self.logout(session_token)

                    return False, None

            except ValueError:

                self.logout(session_token)

                return False, None

        # ----------------------------------------------------
        # UPDATE LAST USED
        # ----------------------------------------------------

        now = utc_now_iso()

        connection = db.get_connection()

        try:

            connection.execute(
                """
                UPDATE sessions
                SET last_used_at = ?
                WHERE session_token = ?
                """,
                (
                    now,
                    session_token,
                ),
            )

            connection.commit()

        finally:

            connection.close()

        # ----------------------------------------------------
        # CREATE USER
        # ----------------------------------------------------

        user = User(
            id=row["user_id"],
            name=row["name"],
            email=row["email"],
            password_hash=row["password_hash"],
            phone=row["phone"],
            date_of_birth=row["date_of_birth"],
            gender=row["gender"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

        return True, user

    # ========================================================
    # LOGOUT
    # ========================================================

    def logout(
        self,
        session_token: str,
    ) -> bool:
        """
        Destroy a persistent login session.
        """

        if not session_token:
            return False

        with db.transaction() as connection:

            cursor = connection.execute(
                """
                DELETE FROM sessions
                WHERE session_token = ?
                """,
                (session_token,),
            )

            return cursor.rowcount > 0

    # ========================================================
    # LOGOUT ALL SESSIONS
    # ========================================================

    def logout_all(
        self,
        user_id: int,
    ) -> int:
        """
        Remove all active sessions belonging to a user.

        Returns the number of sessions removed.
        """

        with db.transaction() as connection:

            cursor = connection.execute(
                """
                DELETE FROM sessions
                WHERE user_id = ?
                """,
                (user_id,),
            )

            return cursor.rowcount

    # ========================================================
    # GET USER BY ID
    # ========================================================

    def get_user_by_id(
        self,
        user_id: int,
    ) -> Optional[User]:
        """
        Retrieve a user using the authenticated user's ID.
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


# ============================================================
# DEFAULT AUTH SERVICE
# ============================================================

auth_service = AuthService()


# ============================================================
# MODULE EXPORTS
# ============================================================

__all__ = [
    "AuthService",
    "auth_service",
    "SESSION_DURATION_DAYS",
]