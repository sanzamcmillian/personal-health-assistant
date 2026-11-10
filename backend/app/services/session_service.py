import asyncio
from datetime import datetime, timezone, timedelta
import secrets
from fastapi import HTTPException, status
from app.core.config import settings
from app.models.session import EphemeralPatientProfile, EphemeralSession


class SessionService:
    """
    Manages ephemeral in-memory sessions with rolling TTL,
    concurrency locks, in-flight cancellation, and resource quotas.
    """

    def __init__(self):
        self._sessions: dict[str, EphemeralSession] = {}
        self._global_lock = asyncio.Lock()

    async def create_session(self, profile: EphemeralPatientProfile) -> EphemeralSession:
        async with self._global_lock:
            # Check global capacity
            if len(self._sessions) >= settings.MAX_ACTIVE_SESSIONS:
                self._sweep_expired_unlocked()
                if len(self._sessions) >= settings.MAX_ACTIVE_SESSIONS:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail={"code": "CAPACITY_EXCEEDED", "detail": "Demo capacity reached. Please try again shortly."},
                    )

            session_id = secrets.token_urlsafe(32)
            session = EphemeralSession(
                session_id=session_id,
                profile=profile,
            )
            self._sessions[session_id] = session
            return session

    async def get_session(self, session_id: str | None) -> EphemeralSession:
        if not session_id or session_id not in self._sessions:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "SESSION_EXPIRED", "detail": "Active session required. Please start a session first."},
            )

        session = self._sessions[session_id]

        if session.terminated:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "SESSION_TERMINATED", "detail": "Session has been terminated."},
            )

        now = datetime.now(timezone.utc)
        if now > session.expires_at:
            await self.destroy_session(session_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "SESSION_EXPIRED", "detail": "Session expired due to inactivity. Please start a new session."},
            )

        session.refresh_ttl()
        return session

    async def get_session_status(self, session_id: str | None) -> dict:
        """Inspects session status without refreshing TTL."""
        if not session_id or session_id not in self._sessions:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "SESSION_EXPIRED", "detail": "Session does not exist or has expired."},
            )

        session = self._sessions[session_id]
        if session.terminated:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "SESSION_TERMINATED", "detail": "Session has been terminated."},
            )

        now = datetime.now(timezone.utc)
        if now > session.expires_at:
            await self.destroy_session(session_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "SESSION_EXPIRED", "detail": "Session has expired."},
            )

        remaining = max(0, int((session.expires_at - now).total_seconds()))
        return {
            "active": True,
            "expires_at": session.expires_at,
            "seconds_remaining": remaining,
            "highest_triage_level": session.highest_triage_level,
            "documents_count": len(session.documents),
        }

    async def keep_alive(self, session_id: str | None) -> datetime:
        """Explicitly extends session TTL by another 30 minutes."""
        session = await self.get_session(session_id)
        session.refresh_ttl()
        return session.expires_at

    async def destroy_session(self, session_id: str | None) -> bool:
        """Idempotent session destruction with immediate termination flag."""
        if not session_id:
            return True

        session = self._sessions.get(session_id)
        if not session:
            return True

        # Set terminated immediately to signal in-flight requests to abort
        session.terminated = True

        async with session.lock:
            session.chat_history.clear()
            session.documents.clear()
            self._sessions.pop(session_id, None)

        return True

    async def cleanup_expired_sessions(self) -> int:
        async with self._global_lock:
            return self._sweep_expired_unlocked()

    def _sweep_expired_unlocked(self) -> int:
        now = datetime.now(timezone.utc)
        expired_ids = [
            sid
            for sid, s in self._sessions.items()
            if s.terminated or now > s.expires_at
        ]
        for sid in expired_ids:
            self._sessions.pop(sid, None)
        return len(expired_ids)


session_service = SessionService()
