from fastapi import APIRouter, Request
from app.core.rate_limit import rate_limiter
from app.schemas.emergency import EmergencyFacilitiesResponse, EmergencyFacilityQuery
from app.services.emergency_service import emergency_service

router = APIRouter(prefix="/emergency", tags=["Emergency"])


@router.post("/facilities", response_model=EmergencyFacilitiesResponse)
async def get_nearby_facilities(
    request: Request,
    payload: EmergencyFacilityQuery,
) -> EmergencyFacilitiesResponse:
    # Public, rate-limited endpoint - DOES NOT REQUIRE A SESSION!
    rate_limiter.check(request)

    return await emergency_service.find_nearby(
        latitude=payload.latitude,
        longitude=payload.longitude,
        country_code=payload.country_code,
    )
