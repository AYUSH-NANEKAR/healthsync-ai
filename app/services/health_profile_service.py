from datetime import date, datetime

from app.database.health_profile_repository import HealthProfileRepository


class HealthProfileService:
    """
    Business logic for the user's health profile.

    The service keeps validation, normalization, and BMI calculation
    separate from the UI and database repository.
    """

    def __init__(self, repository=None):
        self.repository = repository or HealthProfileRepository()

    # ============================================================
    # PROFILE
    # ============================================================

    def get_profile(self, user_id: int):
        """
        Get the health profile for a specific user.

        Returns:
            dict | None
        """

        self._validate_user_id(user_id)

        profile = self.repository.get_profile(user_id)

        if profile is not None:
            profile["age"] = self.calculate_age(
                profile.get("date_of_birth")
            )

            profile["bmi"] = self.calculate_bmi(
                profile.get("height"),
                profile.get("weight"),
            )

        return profile

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
        Validate, normalize, and save a user's health profile.

        Creates a new profile when one does not exist.
        Updates the existing profile otherwise.
        """

        self._validate_user_id(user_id)

        data = {
            "mobile_number": self._clean_text(mobile_number),
            "date_of_birth": self._normalize_date_of_birth(
                date_of_birth
            ),
            "gender": self._clean_text(gender),
            "blood_group": self._clean_text(blood_group),
            "height": self._normalize_number(height),
            "weight": self._normalize_number(weight),
            "city": self._clean_text(city),
            "allergies": self._clean_text(allergies),
            "medical_conditions": self._clean_text(
                medical_conditions
            ),
            "medications": self._clean_text(medications),
        }

        return self.repository.save_profile(
            user_id=user_id,
            **data,
        )

    # ============================================================
    # BMI
    # ============================================================

    @staticmethod
    def calculate_bmi(height, weight):
        """
        Calculate BMI using height in centimeters and weight in kg.

        Formula:
            BMI = weight / height(m)^2

        Returns:
            float | None
        """

        try:
            height = float(height)
            weight = float(weight)
        except (TypeError, ValueError):
            return None

        if height <= 0 or weight <= 0:
            return None

        height_meters = height / 100

        bmi = weight / (height_meters ** 2)

        return round(bmi, 1)

    @staticmethod
    def get_bmi_category(bmi):
        """
        Return a general BMI category.

        This is informational only and is not a medical diagnosis.
        """

        if bmi is None:
            return "Not available"

        if bmi < 18.5:
            return "Underweight"

        if bmi < 25:
            return "Normal range"

        if bmi < 30:
            return "Overweight"

        return "Obesity range"

    # ============================================================
    # AGE
    # ============================================================

    @staticmethod
    def calculate_age(date_of_birth):
        """
        Calculate the user's current age from date of birth.

        Expected date format:
            YYYY-MM-DD

        Returns:
            int | None
        """

        if not date_of_birth:
            return None

        try:
            if isinstance(date_of_birth, date):
                birth_date = date_of_birth

            else:
                birth_date = datetime.strptime(
                    str(date_of_birth),
                    "%Y-%m-%d",
                ).date()

        except (TypeError, ValueError):
            return None

        today = date.today()

        age = today.year - birth_date.year

        if (
            today.month,
            today.day,
        ) < (
            birth_date.month,
            birth_date.day,
        ):
            age -= 1

        return age if age >= 0 else None

    # ============================================================
    # VALIDATION / NORMALIZATION
    # ============================================================

    @staticmethod
    def _validate_user_id(user_id):
        """
        Ensure a valid authenticated user ID is supplied.
        """

        if user_id is None:
            raise ValueError("user_id is required.")

        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            raise ValueError("user_id must be an integer.")

        if user_id <= 0:
            raise ValueError("user_id must be greater than zero.")

    @staticmethod
    def _clean_text(value):
        """
        Normalize optional text fields.

        Empty strings become None.
        """

        if value is None:
            return None

        value = str(value).strip()

        return value if value else None

    @staticmethod
    def _normalize_number(value):
        """
        Convert numeric input to float.

        Empty values become None.
        """

        if value is None:
            return None

        if isinstance(value, str):
            value = value.strip()

            if not value:
                return None

        try:
            number = float(value)

        except (TypeError, ValueError):
            raise ValueError(
                "Height and weight must contain valid numbers."
            )

        if number <= 0:
            raise ValueError(
                "Height and weight must be greater than zero."
            )

        return number

    @staticmethod
    def _normalize_date_of_birth(value):
        """
        Normalize date-of-birth input to YYYY-MM-DD.

        Accepts:
            YYYY-MM-DD
            datetime.date
            datetime.datetime
        """

        if value is None:
            return None

        if isinstance(value, datetime):
            return value.date().isoformat()

        if isinstance(value, date):
            return value.isoformat()

        value = str(value).strip()

        if not value:
            return None

        try:
            parsed_date = datetime.strptime(
                value,
                "%Y-%m-%d",
            ).date()

        except ValueError:
            raise ValueError(
                "Date of birth must use YYYY-MM-DD format."
            )

        if parsed_date > date.today():
            raise ValueError(
                "Date of birth cannot be in the future."
            )

        return parsed_date.isoformat()
