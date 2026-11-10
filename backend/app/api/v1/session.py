from fastapi import APIRouter, Cookie, Request, Response, status
from app.core.config import settings
from app.core.constants import resolve_emergency_numbers
from app.core.rate_limit import rate_limiter
from app.models.session import EphemeralPatientProfile
from app.schemas.session import (
    EndSessionResponse,
    KeepAliveResponse,
    SessionResponse,
    SessionStatusResponse,
    StartSessionRequest,
)
from app.services.session_service import session_service

router = APIRouter(prefix="/session", tags=["Session"])


@router.post("/start", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def start_session(
    request: Request,
    payload: StartSessionRequest,
    response: Response,
) -> SessionResponse:
    rate_limiter.check(request)

    profile = EphemeralPatientProfile(
        name=payload.name,
        age_years=payload.age_years,
        age_months=payload.age_months,
        biological_sex=payload.biological_sex,
        country_code=payload.country_code.upper(),
    )

    session = await session_service.create_session(profile)

    # Re-issue secure HttpOnly session cookie
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=session.session_id,
        httponly=True,
        samesite="strict",
        secure=settings.COOKIE_SECURE,
        max_age=settings.SESSION_TTL_MINUTES * 60,
    )

    emergency_numbers = resolve_emergency_numbers(session.profile.country_code)

    # Note: session_id is omitted from the JSON body to defeat XSS leakage.
    return SessionResponse(
        age_years=session.profile.age_years,
        biological_sex=session.profile.biological_sex,
        country_code=session.profile.country_code,
        emergency_numbers=emergency_numbers,
        expires_at=session.expires_at,
    )


@router.get("/status", response_model=SessionStatusResponse)
async def get_session_status(
    session_token: str | None = Cookie(default=None, alias=settings.COOKIE_NAME),
) -> SessionStatusResponse:
    # Does NOT refresh the TTL
    status_data = await session_service.get_session_status(session_token)
    return SessionStatusResponse(**status_data)


@router.post("/keep-alive", response_model=KeepAliveResponse)
async def keep_alive(
    response: Response,
    session_token: str | None = Cookie(default=None, alias=settings.COOKIE_NAME),
) -> KeepAliveResponse:
    new_expires_at = await session_service.keep_alive(session_token)

    # Re-issue refreshed cookie
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=session_token,
        httponly=True,
        samesite="strict",
        secure=settings.COOKIE_SECURE,
        max_age=settings.SESSION_TTL_MINUTES * 60,
    )

    return KeepAliveResponse(refreshed=True, expires_at=new_expires_at)


@router.post("/end", response_model=EndSessionResponse)
async def end_session(
    response: Response,
    session_token: str | None = Cookie(default=None, alias=settings.COOKIE_NAME),
) -> EndSessionResponse:
    # Idempotent: terminates immediately and purges
    await session_service.destroy_session(session_token)

    response.delete_cookie(
        key=settings.COOKIE_NAME,
        httponly=True,
        samesite="strict",
        secure=settings.COOKIE_SECURE,
    )

    return EndSessionResponse(
        message="Session terminated and all memory wiped.",
        purged=True,
    )
