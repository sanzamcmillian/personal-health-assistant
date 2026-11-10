import asyncio
from contextlib import asynccontextmanager
import glob
import os
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.chat import router as chat_router
from app.api.v1.documents import router as documents_router
from app.api.v1.emergency import router as emergency_router
from app.api.v1.health import router as health_router
from app.api.v1.session import router as session_router
from app.core.config import settings
from app.core.constants import API_PREFIX, APP_VERSION
from app.core.logging import configure_logging, ZeroPHILoggingMiddleware
from app.services.session_service import session_service

configure_logging()


async def periodic_session_cleanup():
    """Background task running every 5 minutes to sweep abandoned sessions."""
    while True:
        await asyncio.sleep(300)
        try:
            await session_service.cleanup_expired_sessions()
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Startup hook: sweep any orphaned files from /tmp
    for orphan in glob.glob("/tmp/*_health_assistant*"):
        try:
            os.remove(orphan)
        except OSError:
            pass

    # 2. Start background cleanup task
    cleanup_task = asyncio.create_task(periodic_session_cleanup())

    yield

    # 3. Shutdown: cancel task
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title=settings.APP_NAME,
    version=APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Zero-PHI logging middleware (strips payload bodies and query params)
app.add_middleware(ZeroPHILoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Sanitized Error Handler: Prevents leaking raw patient inputs/symptoms in 422 errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    sanitized_errors = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "Invalid value")
        # Explicitly omit err.get("input") to ensure PHI/symptoms are never echoed back!
        sanitized_errors.append(f"{loc}: {msg}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": "VALIDATION_ERROR",
            "detail": f"Validation failed: {'; '.join(sanitized_errors)}",
        },
    )


# Standardized HTTPException handler with machine-readable codes
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        content = exc.detail
    else:
        content = {
            "code": f"HTTP_{exc.status_code}",
            "detail": str(exc.detail),
        }
    return JSONResponse(status_code=exc.status_code, content=content)


# Register API v1 Routers
app.include_router(session_router, prefix=API_PREFIX)
app.include_router(chat_router, prefix=API_PREFIX)
app.include_router(documents_router, prefix=API_PREFIX)
app.include_router(emergency_router, prefix=API_PREFIX)
app.include_router(health_router, prefix=API_PREFIX)


@app.get("/")
async def root():
    return {
        "message": "Personal Health Assistant API",
        "version": APP_VERSION,
        "mode": "ephemeral-zero-retention",
    }