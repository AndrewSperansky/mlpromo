from fastapi import FastAPI
from api.system.router import router as system_router
from app.promo.router import router as promo_router
from api.calculator.router import router as calculator_router
from api.system.router import router as ml_router
from core.logging_config import setup_logging

def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title="ML Promo Backend")

    app.include_router(system_router, prefix="/system")
    app.include_router(promo_router, prefix="/promo")
    app.include_router(calculator_router, prefix="/calculator")
    app.include_router(ml_router, prefix="/ml")

    return app

app = create_app()
