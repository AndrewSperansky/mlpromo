from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.logging_config import setup_logging

# Глобальные объекты
logger = None
model = None


@asynccontextmanager
async def lifespan(_app: FastAPI):  # _app обязательныый но неиспол
    global logger, model

    # --- startup ---
    logger = setup_logging()
    logger.info("Application starting up...")

    # Здесь можно загрузить ML-модель
    # from app.models.model_loader import load_model
    # model = load_model()

    yield

    # --- shutdown ---
    logger.info("Application shutting down...")


application = FastAPI(
    title="Promo ML API",
    lifespan=lifespan
)

# ------------ РОУТЕРЫ ---------------
from app.api.system.router import router as system_router
from app.api.promo.router import router as promo_router
from app.api.ml.router import router as ml_router

application.include_router(system_router, prefix="/api/v1/system")
application.include_router(promo_router, prefix="/api/v1/promo")
application.include_router(ml_router, prefix="/api/v1/ml")
# -------------------------------------


@application.get("/")
async def root():
    return {"status": "ok", "service": "promo-ml"}
