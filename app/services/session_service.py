import secrets

from app.database.connection import get_connection


class SessionService:
    """
    Handles creation, retrieval, and removal of user login sessions.
    """

    def create_session(self, user_id: int):
        """
        Create a new session for a user.

        Returns:
            A unique session token.
        """

        session_token = secrets.token_urlsafe(32)

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO sessions (user_id, session_token)
                VALUES (?, ?)
                """,
                (user_id, session_token),
            )

            connection.commit()

            return session_token

        finally:
            connection.close()

    def get_user_by_session(self, session_token: str):
        """
        Retrieve the user associated with a session token.

        Returns:
            User dictionary if the session exists.
            None if the session does not exist.
        """

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT users.id, users.name, users.email
                FROM sessions
                INNER JOIN users ON users.id = sessions.user_id
                WHERE sessions.session_token = ?
                """,
                (session_token,),
            )

            user = cursor.fetchone()

            if user is None:
                return None

            return {
                "id": user[0],
                "name": user[1],
                "email": user[2],
            }

        finally:
            connection.close()

    def logout(self, session_token: str):
        """
        Delete a session from the database.

        Returns:
            True if the session was removed.
            False if the session did not exist.
        """

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                DELETE FROM sessions
                WHERE session_token = ?
                """,
                (session_token,),
            )

            connection.commit()

            return cursor.rowcount > 0

        finally:
            connection.close()