# app/api/v1/router.py

from fastapi import APIRouter
from app.api.v1.system.router import router as system_router
from app.api.v1.ml.router import router as ml_router
from app.api.v1.auth.router import router as auth_router


router = APIRouter(prefix="/api/v1")


router.include_router(system_router, prefix="/system")
router.include_router(ml_router, prefix="/ml")
router.include_router(auth_router, prefix="/auth")

