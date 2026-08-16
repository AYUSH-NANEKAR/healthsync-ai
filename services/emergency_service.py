"""
HealthSync AI - Emergency Service

Coordinates emergency-related data for the application.

Responsibilities:
    - Retrieve the user's latest stored location
    - Find the nearest hospital
    - Find multiple nearby hospitals
    - Retrieve emergency contacts
    - Provide one clean service for the Emergency UI

Important:
    - No hardcoded user location
    - No hardcoded hospital list
    - No paid APIs
    - Location comes from location_history
    - Hospital lookup is delegated to HospitalService
    - Emergency contacts remain stored in SQLite
"""

from __future__ import annotations

from typing import Optional

from services.location_service import location_service
from services.hospital_service import hospital_service


class EmergencyService:
    """
    Main service for emergency-related functionality.

    The UI should communicate with this service instead of
    directly accessing the database, location service, or
    hospital provider.
    """

    DEFAULT_HOSPITAL_RADIUS_METERS = 5000
    DEFAULT_HOSPITAL_LIMIT = 10

    # ========================================================
    # LOCATION
    # ========================================================

    def get_current_location(
        self,
        user_id: int,
    ) -> Optional[dict]:
        """
        Return the latest stored location for a user.

        The location is retrieved from location_history.

        No coordinates are hardcoded here.
        """

        return location_service.get_latest_location(
            user_id
        )

    # ========================================================
    # NEAREST HOSPITAL
    # ========================================================

    def get_nearest_hospital(
        self,
        user_id: int,
        radius_meters: int = DEFAULT_HOSPITAL_RADIUS_METERS,
    ) -> Optional[dict]:
        """
        Return the closest hospital to the user's
        latest stored location.

        Hospital discovery is delegated to HospitalService.
        """

        return hospital_service.get_nearest_hospital(
            user_id=user_id,
            radius_meters=radius_meters,
        )

    # ========================================================
    # NEARBY HOSPITALS
    # ========================================================

    def get_nearby_hospitals(
        self,
        user_id: int,
        radius_meters: int = DEFAULT_HOSPITAL_RADIUS_METERS,
        limit: int = DEFAULT_HOSPITAL_LIMIT,
    ) -> list[dict]:
        """
        Return nearby hospitals sorted by distance.
        """

        return hospital_service.get_nearest_hospitals(
            user_id=user_id,
            radius_meters=radius_meters,
            limit=limit,
        )

    # ========================================================
    # EMERGENCY LOCATION + HOSPITAL
    # ========================================================

    def get_emergency_location_info(
        self,
        user_id: int,
    ) -> dict:
        """
        Return the user's current location together with
        the nearest hospital.

        This gives the Emergency UI a single method to call.
        """

        location = self.get_current_location(
            user_id
        )

        nearest_hospital = None

        if location is not None:
            nearest_hospital = (
                self.get_nearest_hospital(
                    user_id
                )
            )

        return {
            "location": location,
            "nearest_hospital": nearest_hospital,
        }

    # ========================================================
    # EMERGENCY CONTACTS
    # ========================================================

    def get_emergency_contacts(
        self,
        user_id: int,
    ) -> list[dict]:
        """
        Retrieve the user's emergency contacts.

        Emergency contacts are stored in SQLite.

        This method attempts to use the existing
        emergency-contact service without forcing the
        EmergencyService to own database logic.
        """

        try:
            from services.emergency_contact_service import (
                emergency_contact_service,
            )

            contacts = (
                emergency_contact_service
                .get_user_contacts(user_id)
            )

            return contacts or []

        except ImportError:
            return []

    # ========================================================
    # EMERGENCY SUMMARY
    # ========================================================

    def get_emergency_summary(
        self,
        user_id: int,
    ) -> dict:
        """
        Return the information currently required by the
        Emergency UI.

        This does not automatically send an SOS or contact
        anyone.
        """

        location = self.get_current_location(
            user_id
        )

        contacts = self.get_emergency_contacts(
            user_id
        )

        nearest_hospital = None

        if location is not None:
            nearest_hospital = (
                self.get_nearest_hospital(
                    user_id
                )
            )

        return {
            "user_id": user_id,
            "location": location,
            "nearest_hospital": nearest_hospital,
            "emergency_contacts": contacts,
        }


# ============================================================
# DEFAULT SERVICE INSTANCE
# ============================================================

emergency_service = EmergencyService()


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "EmergencyService",
    "emergency_service",
]