"""
HealthSync AI - Session Service

Responsible for managing the currently active persistent
application session.

Responsibilities:
    - Store the current session token locally
    - Restore the session when the application starts
    - Clear the local session on logout
    - Keep session handling separate from authentication logic

IMPORTANT:
    The session token is NOT the user's password.

    Password:
        Stored only as a secure hash in SQLite.

    Session token:
        Used to restore an authenticated login.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from services.auth_service import auth_service
from database.models import User


# ============================================================
# SESSION FILE
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SESSION_FILE = PROJECT_ROOT / ".healthsync_session"


# ============================================================
# SESSION SERVICE
# ============================================================

class SessionService:
    """
    Manages the locally remembered HealthSync AI session.
    """

    # ========================================================
    # SAVE SESSION
    # ========================================================

    def save_session(self, session_token: str) -> bool:
        """
        Save the session token locally.

        Only the session token is stored.
        No password is stored.
        """

        if not session_token:
            return False

        try:

            SESSION_FILE.write_text(
                json.dumps(
                    {
                        "session_token": session_token
                    }
                ),
                encoding="utf-8",
            )

            return True

        except OSError:
            return False

    # ========================================================
    # LOAD SESSION TOKEN
    # ========================================================

    def load_session_token(self) -> Optional[str]:
        """
        Load the locally stored session token.
        """

        if not SESSION_FILE.exists():
            return None

        try:

            content = SESSION_FILE.read_text(
                encoding="utf-8"
            )

            data = json.loads(content)

            token = data.get("session_token")

            if not isinstance(token, str):
                return None

            if not token:
                return None

            return token

        except (
            OSError,
            json.JSONDecodeError,
            TypeError,
        ):
            return None

    # ========================================================
    # RESTORE USER
    # ========================================================

    def restore_user(self) -> Optional[User]:
        """
        Restore the authenticated user from the locally
        remembered session.

        If the session is invalid or expired, the local
        session file is removed.
        """

        token = self.load_session_token()

        if not token:
            return None

        success, user = auth_service.restore_session(token)

        if not success or user is None:

            self.clear_session()

            return None

        return user

    # ========================================================
    # LOGIN
    # ========================================================

    def login(
        self,
        email: str,
        password: str,
        remember_me: bool = True,
    ) -> tuple[bool, str, Optional[User]]:
        """
        Authenticate the user and optionally remember
        the session.
        """

        success, message, user, session_token = (
            auth_service.login(
                email,
                password,
                remember_me=remember_me,
            )
        )

        if not success or user is None:
            return success, message, None

        if remember_me and session_token:

            if not self.save_session(session_token):

                # If the session could not be saved locally,
                # immediately invalidate the database session.
                auth_service.logout(session_token)

                return (
                    False,
                    "Login succeeded, but the session could "
                    "not be saved.",
                    None,
                )

        return True, message, user

    # ========================================================
    # LOGOUT
    # ========================================================

    def logout(self) -> bool:
        """
        Logout the currently remembered session.
        """

        token = self.load_session_token()

        database_logout = True

        if token:

            database_logout = auth_service.logout(token)

        local_logout = self.clear_session()

        return database_logout and local_logout

    # ========================================================
    # CLEAR LOCAL SESSION
    # ========================================================

    def clear_session(self) -> bool:
        """
        Remove the locally stored session token.
        """

        if not SESSION_FILE.exists():
            return True

        try:

            SESSION_FILE.unlink()

            return True

        except OSError:
            return False

    # ========================================================
    # IS AUTHENTICATED
    # ========================================================

    def is_authenticated(self) -> bool:
        """
        Check whether a valid persistent session exists.
        """

        user = self.restore_user()

        return user is not None


# ============================================================
# DEFAULT SESSION SERVICE
# ============================================================

session_service = SessionService()


# ============================================================
# MODULE EXPORTS
# ============================================================

__all__ = [
    "SessionService",
    "session_service",
    "SESSION_FILE",
]