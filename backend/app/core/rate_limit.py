import time
from collections import defaultdict
from fastapi import HTTPException, Request, status
from app.core.config import settings


class IPRateLimiter:
    """
    In-memory rate limiter using sliding window per client IP.
    """

    def __init__(self, requests_per_minute: int = settings.RATE_LIMIT_PER_MINUTE):
        self.rate = requests_per_minute
        self.window = 60.0  # seconds
        self.history: dict[str, list[float]] = defaultdict(list)

    def check(self, request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        # Prune old timestamps
        timestamps = [ts for ts in self.history[client_ip] if now - ts < self.window]
        
        if len(timestamps) >= self.rate:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait a moment before sending another request.",
            )
        
        timestamps.append(now)
        self.history[client_ip] = timestamps


rate_limiter = IPRateLimiter()
