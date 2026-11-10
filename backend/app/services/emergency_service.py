import math
import time
import httpx
from app.core.constants import resolve_emergency_numbers
from app.schemas.emergency import EmergencyFacilitiesResponse, FacilityItem

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
CACHE_TTL_SECONDS = 3600  # 1 hour
_GRID_CACHE: dict[tuple[float, float], tuple[float, list[FacilityItem]]] = {}


class EmergencyFacilityService:
    """
    Locates nearby 24/7 emergency facilities using OpenStreetMap Overpass API.
    Features:
    - In-memory coarse-grid spatial caching (0.05° ~ 5.5km).
    - Session-independent public access.
    - Resolves local emergency dispatch numbers per country.
    """

    @classmethod
    async def find_nearby(
        cls,
        latitude: float | None = None,
        longitude: float | None = None,
        country_code: str = "US",
        radius_meters: int = 15000,
    ) -> EmergencyFacilitiesResponse:
        emergency_numbers = resolve_emergency_numbers(country_code)

        # Default fallback coordinates (e.g. if city or postal code search is needed, approximate)
        if latitude is None or longitude is None:
            return EmergencyFacilitiesResponse(
                emergency_numbers=emergency_numbers,
                facilities=[],
                cached=False,
            )

        # Round coordinates to 2 decimal places (~1.1km) to preserve privacy & enable grid caching
        rounded_lat = round(latitude, 2)
        rounded_lon = round(longitude, 2)

        # Spatial grid key (~0.05° grid cell)
        grid_key = (round(rounded_lat / 0.05) * 0.05, round(rounded_lon / 0.05) * 0.05)
        now = time.time()

        if grid_key in _GRID_CACHE:
            cached_time, cached_items = _GRID_CACHE[grid_key]
            if now - cached_time < CACHE_TTL_SECONDS:
                return EmergencyFacilitiesResponse(
                    emergency_numbers=emergency_numbers,
                    facilities=cached_items,
                    cached=True,
                )

        query = f"""
        [out:json][timeout:8];
        (
          node["amenity"="hospital"]["emergency"="yes"](around:{radius_meters},{rounded_lat},{rounded_lon});
          way["amenity"="hospital"]["emergency"="yes"](around:{radius_meters},{rounded_lat},{rounded_lon});
          node["emergency"="emergency_ward_entrance"](around:{radius_meters},{rounded_lat},{rounded_lon});
          node["healthcare"="hospital"](around:{radius_meters},{rounded_lat},{rounded_lon});
          node["amenity"="clinic"]["emergency"="yes"](around:{radius_meters},{rounded_lat},{rounded_lon});
        );
        out center 5;
        """

        facilities: list[FacilityItem] = []

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.post(OVERPASS_URL, data={"data": query})
                if response.status_code == 200:
                    data = response.json()
                    elements = data.get("elements", [])

                    for el in elements:
                        tags = el.get("tags", {})
                        name = tags.get("name") or tags.get("operator") or "Emergency Medical Facility"
                        
                        lat = el.get("lat") or el.get("center", {}).get("lat")
                        lon = el.get("lon") or el.get("center", {}).get("lon")
                        
                        if lat and lon:
                            distance = cls._haversine(rounded_lat, rounded_lon, lat, lon)
                            phone = tags.get("phone") or tags.get("contact:phone")
                            street = tags.get("addr:street")
                            city = tags.get("addr:city")
                            address = f"{street}, {city}" if street and city else street or city
                            hours = tags.get("opening_hours")
                            has_ed = tags.get("emergency") == "yes" or "emergency_ward_entrance" in tags.values()
                            f_type = "hospital" if tags.get("amenity") == "hospital" else "urgent_care"

                            maps_url = f"https://www.google.com/maps/search/?api=1&query={round(lat,2)},{round(lon,2)}"

                            facilities.append(
                                FacilityItem(
                                    name=name,
                                    straight_line_distance_km=round(distance, 1),
                                    facility_type=f_type,
                                    has_emergency_department=has_ed,
                                    address=address,
                                    phone=phone,
                                    hours=hours,
                                    hours_verified=False,
                                    maps_url=maps_url,
                                )
                            )

            facilities.sort(key=lambda x: x.straight_line_distance_km)
            top_facilities = facilities[:3]

            # Cache in spatial grid
            _GRID_CACHE[grid_key] = (now, top_facilities)

            return EmergencyFacilitiesResponse(
                emergency_numbers=emergency_numbers,
                facilities=top_facilities,
                cached=False,
            )
        except Exception:
            return EmergencyFacilitiesResponse(
                emergency_numbers=emergency_numbers,
                facilities=[],
                cached=False,
            )

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return r * c


emergency_service = EmergencyFacilityService()
