from app.services.auth_service import AuthService
from app.services.session_service import SessionService
from app.services.session_storage import (
    clear_session,
    load_session,
    save_session,
)


class AuthManager:
    """
    Coordinates authentication and session management.
    """

    def __init__(self):
        self.auth_service = AuthService()
        self.session_service = SessionService()
        self.current_user = None
        self.session_token = None

    def login(
        self,
        email: str,
        password: str,
        remember_me: bool = True,
    ):
        """
        Authenticate a user and create a session.

        Args:
            email: User email address.
            password: User password.
            remember_me: Whether the session should persist
                         after the application closes.

        Returns:
            User dictionary if login succeeds.
            None if login fails.
        """

        user = self.auth_service.login_user(email, password)

        if user is None:
            return None

        session_token = self.session_service.create_session(
            user["id"]
        )

        self.current_user = user
        self.session_token = session_token

        if remember_me:
            save_session(session_token)
        else:
            clear_session()

        return user

    def restore_saved_session(self):
        """
        Load the locally saved session and restore the user.

        Returns:
            User dictionary if the saved session is valid.
            None otherwise.
        """

        session_token = load_session()

        if session_token is None:
            return None

        user = self.restore_session(session_token)

        if user is None:
            clear_session()

        return user

    def restore_session(self, session_token: str):
        """
        Restore a previously created session.

        Returns:
            User dictionary if the session is valid.
            None otherwise.
        """

        user = self.session_service.get_user_by_session(
            session_token
        )

        if user is None:
            self.current_user = None
            self.session_token = None
            return None

        self.current_user = user
        self.session_token = session_token

        return user

    def logout(self):
        """
        Log out the current user and remove the persistent session.
        """

        if self.session_token is not None:
            self.session_service.logout(
                self.session_token
            )

        clear_session()

        self.current_user = None
        self.session_token = None

    def is_logged_in(self):
        """
        Check whether a user is currently authenticated.
        """

        return self.current_user is not None