from fastapi import FastAPI
from contextlib import asynccontextmanager

# ---- Core Logging ----
from app.core.logging_config import setup_logging

# ---- Middleware ----
from app.middleware.logging_middleware import RequestLoggingMiddleware

# ---- Routers ----
from app.api.v1.system.router import router as system_router
from app.api.v1.promo.router import router as promo_router
from app.api.v1.calculator.router import router as calculator_router
from app.api.v1.ml.router import router as ml_router


logger = None  # Глобальный логгер приложения


@asynccontextmanager
async def lifespan(_app: FastAPI):  # _app обязательный но неиспользуемый
    """
    Глобальный цикл жизни приложения.
    Выполняет инициализацию логирования, загрузку ML-моделей (если нужно),
    а также корректно логирует shutdown.
    """
    global logger

    # --- Startup ---
    logger = setup_logging()
    logger.info("Application starting up...")

    # --- Место для загрузки ML-модели ---
    # from app.models.model_loader import load_model
    # model = load_model()

    yield

    # --- Shutdown ---
    logger.info("Application shutting down...")


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
# ❗ ОСТАВЛЯЕМ только 1 middleware — второго быть НЕ должно
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
    """Корневой эндпоинт сервиса."""
    return {"status": "ok", "service": "promo-ml"}
