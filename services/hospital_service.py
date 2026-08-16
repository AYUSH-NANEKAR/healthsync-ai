from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import Optional

import requests

from services.location_service import location_service


class HospitalProvider(ABC):
    """Common interface for hospital providers."""

    @abstractmethod
    def search_nearby(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int,
        limit: int,
    ) -> list[dict]:
        raise NotImplementedError


class OverpassHospitalProvider(HospitalProvider):
    """Free OpenStreetMap / Overpass hospital provider."""

    API_URLS = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.private.coffee/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    ]

    USER_AGENT = "HealthSyncAI/1.0 (academic project)"
    REQUEST_TIMEOUT = 45

    def search_nearby(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int,
        limit: int,
    ) -> list[dict]:

        query = f"""
[out:json][timeout:45];

(
    nwr["amenity"="hospital"]
    (around:{radius_meters},{latitude},{longitude});
);

out center tags;
"""

        data: Optional[dict] = None
        last_error: Optional[Exception] = None

        for api_url in self.API_URLS:
            try:
                print(
                    f"Trying hospital provider: {api_url}"
                )

                response = requests.post(
                    api_url,
                    data=query.encode("utf-8"),
                    headers={
                        "User-Agent": self.USER_AGENT,
                        "Accept": "application/json",
                    },
                    timeout=self.REQUEST_TIMEOUT,
                )

                response.raise_for_status()
                data = response.json()

                print(
                    f"Hospital provider succeeded: {api_url}"
                )

                break

            except requests.RequestException as exc:
                last_error = exc

                print(
                    f"Hospital provider failed: {api_url}"
                )
                print(f"Reason: {exc}")

        if data is None:
            raise RuntimeError(
                "All free hospital providers failed. "
                f"Last error: {last_error}"
            )

        hospitals: list[dict] = []

        for element in data.get("elements", []):
            coordinates = self._extract_coordinates(element)

            if coordinates is None:
                continue

            hospital_latitude, hospital_longitude = coordinates
            tags = element.get("tags", {})

            distance = calculate_distance_km(
                latitude,
                longitude,
                hospital_latitude,
                hospital_longitude,
            )

            hospitals.append(
                {
                    "id": element.get("id"),
                    "osm_type": element.get("type"),
                    "provider": "OpenStreetMap",
                    "name": tags.get(
                        "name",
                        "Unnamed Hospital",
                    ),
                    "latitude": hospital_latitude,
                    "longitude": hospital_longitude,
                    "distance_km": round(distance, 3),
                    "distance_meters": round(
                        distance * 1000
                    ),
                    "address": build_address(tags),
                    "phone": (
                        tags.get("phone")
                        or tags.get("contact:phone")
                    ),
                    "website": (
                        tags.get("website")
                        or tags.get("contact:website")
                    ),
                    "emergency": tags.get("emergency"),
                    "opening_hours": tags.get(
                        "opening_hours"
                    ),
                    "source": "OpenStreetMap",
                }
            )

        hospitals.sort(
            key=lambda hospital: hospital["distance_km"]
        )

        return hospitals[:limit]

    @staticmethod
    def _extract_coordinates(
        element: dict,
    ) -> Optional[tuple[float, float]]:

        if "lat" in element and "lon" in element:
            return (
                float(element["lat"]),
                float(element["lon"]),
            )

        center = element.get("center")

        if center is not None:
            if "lat" in center and "lon" in center:
                return (
                    float(center["lat"]),
                    float(center["lon"]),
                )

        return None


class HealthSyncAPIHospitalProvider(HospitalProvider):
    """
    Future provider for the HealthSync AI custom API.

    Not implemented yet.

    The rest of the application will not need to change
    when this provider is eventually introduced.
    """

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def search_nearby(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int,
        limit: int,
    ) -> list[dict]:

        raise NotImplementedError(
            "HealthSync API provider is not implemented yet."
        )


class HospitalService:
    """Main hospital service used by HealthSync AI."""

    DEFAULT_RADIUS_METERS = 5000
    DEFAULT_LIMIT = 10

    def __init__(
        self,
        provider: Optional[HospitalProvider] = None,
    ):
        if provider is None:
            self.provider = OverpassHospitalProvider()
        else:
            self.provider = provider

    def set_provider(
        self,
        provider: HospitalProvider,
    ) -> None:

        if not isinstance(provider, HospitalProvider):
            raise TypeError(
                "Provider must implement HospitalProvider."
            )

        self.provider = provider

    def get_user_location(
        self,
        user_id: int,
    ) -> Optional[dict]:

        return location_service.get_latest_location(
            user_id
        )

    def get_nearest_hospitals(
        self,
        user_id: int,
        radius_meters: int = DEFAULT_RADIUS_METERS,
        limit: int = DEFAULT_LIMIT,
    ) -> list[dict]:

        location = self.get_user_location(user_id)

        if location is None:
            return []

        latitude = location.get("latitude")
        longitude = location.get("longitude")

        if latitude is None or longitude is None:
            return []

        return self.search_nearby_hospitals(
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            limit=limit,
        )

    def search_nearby_hospitals(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int = DEFAULT_RADIUS_METERS,
        limit: int = DEFAULT_LIMIT,
    ) -> list[dict]:

        validate_coordinates(latitude, longitude)

        radius_meters = max(
            100,
            min(int(radius_meters), 50000),
        )

        limit = max(
            1,
            min(int(limit), 50),
        )

        return self.provider.search_nearby(
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            limit=limit,
        )

    def get_nearest_hospital(
        self,
        user_id: int,
        radius_meters: int = DEFAULT_RADIUS_METERS,
    ) -> Optional[dict]:

        hospitals = self.get_nearest_hospitals(
            user_id=user_id,
            radius_meters=radius_meters,
            limit=1,
        )

        if not hospitals:
            return None

        return hospitals[0]


def calculate_distance_km(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float,
    longitude_2: float,
) -> float:

    earth_radius_km = 6371.0088

    lat1 = math.radians(latitude_1)
    lat2 = math.radians(latitude_2)

    delta_lat = math.radians(
        latitude_2 - latitude_1
    )

    delta_lon = math.radians(
        longitude_2 - longitude_1
    )

    a = (
        math.sin(delta_lat / 2) ** 2
        +
        math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a),
    )

    return earth_radius_km * c


def build_address(
    tags: dict,
) -> Optional[str]:

    parts: list[str] = []

    for key in (
        "addr:housenumber",
        "addr:street",
        "addr:suburb",
        "addr:city",
        "addr:postcode",
    ):

        value = tags.get(key)

        if value:
            parts.append(str(value))

    if not parts:
        return None

    return ", ".join(parts)


def validate_coordinates(
    latitude: float,
    longitude: float,
) -> None:

    if not -90 <= float(latitude) <= 90:
        raise ValueError(
            "Latitude must be between -90 and 90."
        )

    if not -180 <= float(longitude) <= 180:
        raise ValueError(
            "Longitude must be between -180 and 180."
        )


hospital_service = HospitalService()


__all__ = [
    "HospitalProvider",
    "OverpassHospitalProvider",
    "HealthSyncAPIHospitalProvider",
    "HospitalService",
    "hospital_service",
    "calculate_distance_km",
    "build_address",
    "validate_coordinates",
]
