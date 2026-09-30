from app.database.connection import get_connection
from app.security.password import hash_password, verify_password


class AuthService:
    """
    Handles user authentication and registration.
    """

    def register_user(self, name: str, email: str, password: str):
        """
        Register a new user.

        Returns:
            user_id (int) if registration succeeds.
            None if the email already exists.
        """

        name = name.strip()
        email = email.strip().lower()

        password_hash = hash_password(password)

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO users (name, email, password_hash)
                VALUES (?, ?, ?)
                """,
                (name, email, password_hash),
            )

            connection.commit()

            return cursor.lastrowid

        except Exception:
            connection.rollback()
            return None

        finally:
            connection.close()

    def login_user(self, email: str, password: str):
        """
        Authenticate a user.

        Returns:
            User dictionary if credentials are correct.
            None if authentication fails.
        """

        email = email.strip().lower()

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT id, name, email, password_hash
                FROM users
                WHERE email = ?
                """,
                (email,),
            )

            user = cursor.fetchone()

            if user is None:
                return None

            user_id, name, user_email, stored_hash = user

            if not verify_password(password, stored_hash):
                return None

            return {
                "id": user_id,
                "name": name,
                "email": user_email,
            }

        finally:
            connection.close()