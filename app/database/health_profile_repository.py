from app.database.connection import get_connection


class HealthProfileRepository:
    """
    Handles database operations for user health profiles.

    Every operation is scoped to a specific user_id so that
    one user's health information cannot be accessed through
    another user's profile.
    """

    def get_profile(self, user_id: int):
        """
        Return the health profile belonging to user_id.

        Returns:
            dict | None
        """

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    user_id,
                    mobile_number,
                    date_of_birth,
                    gender,
                    blood_group,
                    height,
                    weight,
                    city,
                    allergies,
                    medical_conditions,
                    medications,
                    created_at,
                    updated_at
                FROM health_profiles
                WHERE user_id = ?
                LIMIT 1
                """,
                (user_id,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return {
                "id": row[0],
                "user_id": row[1],
                "mobile_number": row[2],
                "date_of_birth": row[3],
                "gender": row[4],
                "blood_group": row[5],
                "height": row[6],
                "weight": row[7],
                "city": row[8],
                "allergies": row[9],
                "medical_conditions": row[10],
                "medications": row[11],
                "created_at": row[12],
                "updated_at": row[13],
            }

        finally:
            connection.close()

    def create_profile(
        self,
        user_id: int,
        mobile_number=None,
        date_of_birth=None,
        gender=None,
        blood_group=None,
        height=None,
        weight=None,
        city=None,
        allergies=None,
        medical_conditions=None,
        medications=None,
    ):
        """
        Create a health profile for a user.

        One user can have only one health profile because
        health_profiles.user_id is UNIQUE.
        """

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO health_profiles (
                    user_id,
                    mobile_number,
                    date_of_birth,
                    gender,
                    blood_group,
                    height,
                    weight,
                    city,
                    allergies,
                    medical_conditions,
                    medications
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    mobile_number,
                    date_of_birth,
                    gender,
                    blood_group,
                    height,
                    weight,
                    city,
                    allergies,
                    medical_conditions,
                    medications,
                ),
            )

            connection.commit()

            return cursor.lastrowid

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def update_profile(
        self,
        user_id: int,
        mobile_number=None,
        date_of_birth=None,
        gender=None,
        blood_group=None,
        height=None,
        weight=None,
        city=None,
        allergies=None,
        medical_conditions=None,
        medications=None,
    ):
        """
        Update the health profile belonging to user_id.

        Returns:
            True if the profile was updated.
            False if no profile exists for the user.
        """

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE health_profiles
                SET
                    mobile_number = ?,
                    date_of_birth = ?,
                    gender = ?,
                    blood_group = ?,
                    height = ?,
                    weight = ?,
                    city = ?,
                    allergies = ?,
                    medical_conditions = ?,
                    medications = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (
                    mobile_number,
                    date_of_birth,
                    gender,
                    blood_group,
                    height,
                    weight,
                    city,
                    allergies,
                    medical_conditions,
                    medications,
                    user_id,
                ),
            )

            connection.commit()

            return cursor.rowcount > 0

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def save_profile(
        self,
        user_id: int,
        mobile_number=None,
        date_of_birth=None,
        gender=None,
        blood_group=None,
        height=None,
        weight=None,
        city=None,
        allergies=None,
        medical_conditions=None,
        medications=None,
    ):
        """
        Create a profile if one does not exist.
        Otherwise update the existing profile.

        This gives the UI one simple method for saving data.
        """

        existing_profile = self.get_profile(user_id)

        if existing_profile is None:
            return self.create_profile(
                user_id=user_id,
                mobile_number=mobile_number,
                date_of_birth=date_of_birth,
                gender=gender,
                blood_group=blood_group,
                height=height,
                weight=weight,
                city=city,
                allergies=allergies,
                medical_conditions=medical_conditions,
                medications=medications,
            )

        updated = self.update_profile(
            user_id=user_id,
            mobile_number=mobile_number,
            date_of_birth=date_of_birth,
            gender=gender,
            blood_group=blood_group,
            height=height,
            weight=weight,
            city=city,
            allergies=allergies,
            medical_conditions=medical_conditions,
            medications=medications,
        )

        return existing_profile["id"] if updated else None