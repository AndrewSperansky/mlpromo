"""
Request/Response logging middleware with correlation ID.
"""

import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


logger = logging.getLogger("promo_ml")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware для логирования запросов и ответов.
    Добавляет correlation_id.
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        correlation_id = str(uuid.uuid4())

        # Добавляем correlation_id в request.state
        request.state.correlation_id = correlation_id

        logger.info(
            "Incoming request",
            extra={
                "method": request.method,
                "url": request.url.path,
                "correlation_id": correlation_id,
            },
        )

        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(
                "Unhandled error",
                extra={"correlation_id": correlation_id, "error": str(e)},
            )
            raise

        process_time = round(time.time() - start_time, 4)

        logger.info(
            "Outgoing response",
            extra={
                "status_code": response.status_code,
                "process_time": process_time,
                "correlation_id": correlation_id,
            },
        )

        # Добавляем header для клиентских логов
        response.headers["X-Correlation-ID"] = correlation_id

        return response
