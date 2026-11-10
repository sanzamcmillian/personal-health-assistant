import pytest
from pydantic import ValidationError
from app.core.constants import resolve_emergency_numbers
from app.schemas.emergency import EmergencyFacilityQuery


def test_emergency_numbers_resolution():
    assert resolve_emergency_numbers("US") == ["911"]
    assert resolve_emergency_numbers("us") == ["911"]
    assert resolve_emergency_numbers("GB") == ["999", "112"]
    assert resolve_emergency_numbers("ZA") == ["10177", "112"]
    assert resolve_emergency_numbers("AU") == ["000"]
    assert resolve_emergency_numbers("XX") == ["112"]
    assert resolve_emergency_numbers(None) == ["112"]


def test_facility_query_coordinates_validation():
    # Both lat and lon provided
    query = EmergencyFacilityQuery(latitude=37.77, longitude=-122.42)
    assert query.latitude == 37.77

    # Missing longitude when latitude provided raises error
    with pytest.raises(ValidationError):
        EmergencyFacilityQuery(latitude=37.77)

    # Missing both coordinates and city/postal_code raises error
    with pytest.raises(ValidationError):
        EmergencyFacilityQuery()

    # City provided without coordinates is valid
    query_city = EmergencyFacilityQuery(city="San Francisco", country_code="US")
    assert query_city.city == "San Francisco"
