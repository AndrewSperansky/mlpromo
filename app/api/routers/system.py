# app/api/routers/system.py
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import settings

router = APIRouter(prefix="/system", tags=["system"])

@router.get("/healthcheck")
def healthcheck(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "checks": {
            "database": "ok",
            "config": "ok",
        },
        "environment": settings.ENV,
        "version": settings.VERSION,
    }

# повторяет --> app/api/v1/system/router.py
