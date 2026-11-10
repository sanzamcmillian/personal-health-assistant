from pydantic import BaseModel, Field, model_validator


class EmergencyFacilityQuery(BaseModel):
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    city: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    country_code: str = Field(default="US", min_length=2, max_length=2)

    @model_validator(mode="after")
    def validate_coordinates(self):
        has_lat = self.latitude is not None
        has_lon = self.longitude is not None
        if has_lat != has_lon:
            raise ValueError("Both latitude and longitude must be provided together.")
        if not has_lat and not self.city and not self.postal_code:
            raise ValueError("Either coordinates (latitude, longitude) or location (city/postal_code) must be provided.")
        return self


class FacilityItem(BaseModel):
    name: str
    straight_line_distance_km: float
    facility_type: str = "hospital"
    has_emergency_department: bool = True
    address: str | None = None
    phone: str | None = None
    hours: str | None = None
    hours_verified: bool = False
    maps_url: str


class EmergencyFacilitiesResponse(BaseModel):
    emergency_numbers: list[str]
    facilities: list[FacilityItem] = Field(default_factory=list)
    caveat: str = "Always call ahead to confirm emergency capability and current wait times, or call emergency services directly if experiencing life-threatening symptoms."
    cached: bool = False
