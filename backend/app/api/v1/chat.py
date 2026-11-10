from fastapi import APIRouter, Cookie, HTTPException, Request, Response, status
from app.core.config import settings
from app.core.rate_limit import rate_limiter
from app.schemas.chat import ChatRequest, TriageResponse
from app.services.session_service import session_service
from app.services.triage_service import triage_service

router = APIRouter(prefix="/chat", tags=["Chat & Triage"])


@router.post("", response_model=TriageResponse)
async def chat(
    request: Request,
    payload: ChatRequest,
    response: Response,
    session_token: str | None = Cookie(default=None, alias=settings.COOKIE_NAME),
) -> TriageResponse:
    rate_limiter.check(request)

    session = await session_service.get_session(session_token)

    # In-flight conflict check: prevent concurrent requests on the same session
    if session.lock.locked():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "REQUEST_ALREADY_IN_FLIGHT", "detail": "A prior message is still being analyzed."},
        )

    async with session.lock:
        if session.terminated:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "SESSION_TERMINATED", "detail": "Session was terminated."},
            )

        triage_result = await triage_service.process_message(payload.message, session)

    # Re-issue refreshed cookie matching rolling 30-minute TTL
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=session.session_id,
        httponly=True,
        samesite="strict",
        secure=settings.COOKIE_SECURE,
        max_age=settings.SESSION_TTL_MINUTES * 60,
    )

    return triage_result