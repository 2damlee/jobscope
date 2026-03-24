import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from app.logging import setup_logger

logger = setup_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.time()

        response = await call_next(request)

        duration_ms = round((time.time() - start) * 1000, 2)

        logger.info(
            f"request_id={request_id} method={request.method} path={request.url.path} "
            f"status={response.status_code} duration_ms={duration_ms}"
        )

        response.headers["X-Request-ID"] = request_id
        return response