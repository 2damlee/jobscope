import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from app.logging import setup_logger

logger = setup_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        start = time.time()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.time() - start) * 1000, 2)
            logger.exception(
                "request_id=%s method=%s path=%s status=500 duration_ms=%s",
                request_id,
                request.method,
                request.url.path,
                duration_ms,
            )
            raise

        duration_ms = round((time.time() - start) * 1000, 2)
        logger.info(
            "request_id=%s method=%s path=%s status=%s duration_ms=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        response.headers["X-Request-ID"] = request_id
        return response