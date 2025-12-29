from fastapi import FastAPI
from fastapi import Response
from contextlib import asynccontextmanager
from app.ml.model_manager import ModelManager
import asyncio
from typing import cast, Callable
import logging

# ---- Core Logging ----
from app.core.logging_config import setup_logging

# ---- Middleware ----
from app.middleware.logging_middleware import RequestLoggingMiddleware
# from starlette.middleware.base import BaseHTTPMiddleware

# ---- Routers ----
from app.api.v1.router import router as v1_router
from app.core.config import settings
from starlette.routing import Route, Mount, Router


logger = None  # Глобальный логгер приложения

model_manager = ModelManager("/models/latest_model.pkl", check_interval=5)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Глобальный цикл жизни приложения.
    Выполняет инициализацию логирования, загрузку ML-моделей (если нужно),
    а также корректно логирует shutdown.
    """
    global logger

    # --- Startup ---
    logger = setup_logging()
    logger.info("Application starting up...")

    # Загрузка ML‑модели
    try:
        model_manager.load()
        logger.info("ML model loaded successfully")

    except FileNotFoundError:
        logger.warning("ML model not found yet, running without ML")

    except Exception as e:
        logger.exception("Unexpected error while loading ML model")

    # Запуск watcher в фоновом режиме
    watcher_task = asyncio.create_task(model_manager.watch())
    logger.info("Watcher task started")

    try:
        yield  # Передача управления приложению
    finally:
        # --- Shutdown ---
        logger.info("Application shutting down...")

        # Корректная остановка watcher‑задачи
        if not watcher_task.done():
            watcher_task.cancel()
            try:
                await watcher_task
            except asyncio.CancelledError:
                logger.info("Watcher task cancelled successfully")
            except Exception as e:
                logger.error(f"Error during watcher task cancellation: {e}")




# ------------------------------------------------------
# Создание FastAPI приложения
# ------------------------------------------------------
app = FastAPI(
    title="Promo ML API",
    lifespan=lifespan,
)




# ------------------------------------------------------
# Подключение middleware
# ------------------------------------------------------

# noinspection PyTypeChecker
app.add_middleware(RequestLoggingMiddleware)




# ------------------------------------------------------
# Root endpoint
# ------------------------------------------------------
@app.get("/", summary="Root endpoint")
async def root():
    """Корневой эндпоинт сервиса."""
    return {"status": "ok", "service": "promo-ml"}


# ------------------------------------------------------
# Health endpoint
# ------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}

# ------------------------------------------------------
# Эндпоинт для просмотра всех маршрутов
# ------------------------------------------------------


@app.get("/routes", response_class=Response)
def list_routes_plain():
    lines = []

    for r in app.routes:
        if not isinstance(r, Route):
            continue

        if r.path in {
            "/openapi.json",
            "/docs",
            "/redoc",
            "/docs/oauth2-redirect",
        }:
            continue

        methods = ",".join(sorted(r.methods)) if r.methods else "-"
        name = r.name or "-"

        endpoint = cast(Callable, r.endpoint)
        module = endpoint.__module__

        line = f"{methods:<7} {r.path:<45} → {name} ({module})"
        lines.append(line)

    lines.sort()
    return Response(
        "\n".join(lines),
        media_type="text/plain; charset=utf-8"
    )



# ------------------------------------------------------
# Регистрация API v1
# ------------------------------------------------------

app.include_router(v1_router)