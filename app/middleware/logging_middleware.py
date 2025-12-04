# app/middleware/logging_middleware.py
import logging
import time
import uuid
from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger("promo_ml")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        start = time.time()
        request.state.correlation_id = correlation_id

        logger.info("request.start", extra={
            "method": request.method,
            "path": request.url.path,
            "correlation_id": correlation_id
        })

        response: Response = await call_next(request)
        elapsed = (time.time() - start) * 1000
        response.headers["X-Correlation-ID"] = correlation_id

        logger.info("request.end", extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "elapsed_ms": elapsed,
            "correlation_id": correlation_id
        })
        return response
