import time
from typing import Dict, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from app.core.exceptions import RateLimitError

# Simple sliding window rate limiter
# Key: client_ip -> (request_count, window_start_timestamp)
_RATE_LIMIT_DB: Dict[str, Tuple[int, float]] = {}
WINDOW_SIZE = 60  # seconds
MAX_REQUESTS_PER_WINDOW = 1000  # for general API endpoints
MAX_LOGIN_ATTEMPTS = 5  # for login endpoint


class RateLimitMiddleware(BaseHTTPMiddleware):
    @staticmethod
    def _rate_limited_response(request: Request, retry_after: int) -> JSONResponse:
        """Mirrors app_exception_handler's envelope so clients parse rate-limit
        rejections exactly like every other API error."""
        exc = RateLimitError("Rate limit exceeded. Please try again later.")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "request_id": getattr(request.state, "request_id", None),
                    "details": None,
                }
            },
            headers={"Retry-After": str(max(retry_after, 1))},
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        if request.url.path.endswith("/auth/login") and request.method == "POST":
            limit = MAX_LOGIN_ATTEMPTS
            key = f"login:{client_ip}"
        else:
            limit = MAX_REQUESTS_PER_WINDOW
            key = f"api:{client_ip}"

        if key in _RATE_LIMIT_DB:
            count, start_time = _RATE_LIMIT_DB[key]
            if now - start_time < WINDOW_SIZE:
                if count >= limit:
                    # Returned, not raised: middleware runs *outside* Starlette's
                    # ExceptionMiddleware, so a raised AppException never reaches
                    # app_exception_handler and would surface as a generic 500.
                    return self._rate_limited_response(request, retry_after=int(start_time + WINDOW_SIZE - now) + 1)
                _RATE_LIMIT_DB[key] = (count + 1, start_time)
            else:
                _RATE_LIMIT_DB[key] = (1, now)
        else:
            _RATE_LIMIT_DB[key] = (1, now)

        return await call_next(request)
