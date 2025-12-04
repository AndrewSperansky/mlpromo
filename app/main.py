from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.logging_config import setup_logging
from app.middleware.logging_middleware import RequestLoggingMiddleware

# ------------ РОУТЕРЫ ---------------
from app.api.v1.system.router import router as system_router
from app.api.v1.promo.router import router as promo_router
from app.api.v1.calculator.router import router as calculator_router
from app.api.v1.ml.router import router as ml_router


# Глобальные объекты
logger = None


@asynccontextmanager
async def lifespan(_app: FastAPI):  # _app обязательный но неиспользуемый
    global logger

    # --------- startup ----------
    logger = setup_logging()
    logger.info("Application starting up...")

    # ============ Здесь можно загрузить ML-модель =========================

    # from app.models.model_loader import load_model
    # model = load_model()

    yield

    # --- shutdown ---
    logger.info("Application shutting down...")


application = FastAPI(title="Promo ML API", lifespan=lifespan)

application.add_middleware(RequestLoggingMiddleware)


# Регистрируем маршруты API v1 ---------------------------------------
application.include_router(system_router, prefix="/api/v1/system")
application.include_router(promo_router, prefix="/api/v1/promo")
application.include_router(calculator_router, prefix="/api/v1/calculator")
application.include_router(ml_router, prefix="/api/v1/ml")
# --------------------------------------------------------------------


@application.get("/", summary="Root")
async def root():
    """Service root endpoint"""
    return {"status": "ok", "service": "promo-ml"}
