from fastapi import FastAPI, Request
# from starlette.responses import Response
from contextlib import asynccontextmanager
from app.ml.model_manager import ModelManager
import asyncio
import logging

# ---- Core Logging ----
from app.core.logging_config import setup_logging

# ---- Middleware ----
from app.middleware.logging_middleware import RequestLoggingMiddleware
# from starlette.middleware.base import BaseHTTPMiddleware

# ---- Routers ----
from app.api.v1.system.router import router as system_router
from app.api.v1.promo.router import router as promo_router
from app.api.v1.calculator.router import router as calculator_router
from app.api.v1.ml.router import router as ml_router


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
    except Exception as e:
        logger.error(f"Failed to load ML model: {e}")

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
application = FastAPI(
    title="Promo ML API",
    lifespan=lifespan,
)


# ------------------------------------------------------
# Подключение middleware
# ------------------------------------------------------

# noinspection PyTypeChecker
application.add_middleware(RequestLoggingMiddleware)


# ------------------------------------------------------
# Регистрация API v1
# ------------------------------------------------------
application.include_router(system_router, prefix="/api/v1/system")
application.include_router(promo_router, prefix="/api/v1/promo")
application.include_router(calculator_router, prefix="/api/v1/calculator")
application.include_router(ml_router, prefix="/api/v1/ml")


# ------------------------------------------------------
# Root endpoint
# ------------------------------------------------------
@application.get("/", summary="Root endpoint")
async def root():
    """Корневой энд-поинт сервиса."""
    return {"status": "ok", "service": "promo-ml"}





