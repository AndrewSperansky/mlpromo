# app/api/system/router.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/health", tags=["system"])
async def health():
    return {"status": "ok"}
