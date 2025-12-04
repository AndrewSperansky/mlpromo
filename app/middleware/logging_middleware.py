import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("promo_ml")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware логирования всех HTTP запросов / ответов.

    Возможности:
    - Генерация correlation_id для каждого запроса
    - Логирование метода, маршрута, времени выполнения
    - Логирование тела запроса (только в DEV)
    - Возврат X-Request-ID в ответах
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # --- CORRELATION ID ---
        correlation_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Добавляем кореляционный ID в контекст логгера
        # Для JSON логгера он попадёт в поле correlation_id
        logging.LoggerAdapter(logger, {"correlation_id": correlation_id})

        # --- LOG REQUEST ---
        try:
            body = await request.body()
            body_str = body.decode("utf-8") if body else None
        except Exception:
            body_str = "<unreadable>"

        logger.info(
            "Incoming request",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "url": str(request.url),
                "client": request.client.host if request.client else None,
                "body": body_str if body_str else None,
            },
        )

        # --- CALL ENDPOINT ---
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error(
                "Handler exception",
                extra={
                    "correlation_id": correlation_id,
                    "error": str(exc),
                },
            )
            raise

        process_time = round((time.time() - start_time) * 1000, 2)

        # --- LOG RESPONSE ---
        logger.info(
            "Response sent",
            extra={
                "correlation_id": correlation_id,
                "status_code": response.status_code,
                "process_time_ms": process_time,
            },
        )

        # Добавляем header в ответ клиенту
        response.headers["X-Request-ID"] = correlation_id
        return response
