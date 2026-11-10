import logging
import sys
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("health_assistant")


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )


class ZeroPHILoggingMiddleware(BaseHTTPMiddleware):
    """
    Ensures that request bodies, query strings, and response payloads
    are NEVER logged, preserving strict health privacy (zero PHI).
    Logs only operational metrics: path, method, status code, duration.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            logger.info(
                f"{request.method} {request.url.path} - Status: {response.status_code} - Duration: {duration_ms:.2f}ms"
            )
            return response
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"{request.method} {request.url.path} - Unhandled Exception - Duration: {duration_ms:.2f}ms: {type(exc).__name__}"
            )
            raise