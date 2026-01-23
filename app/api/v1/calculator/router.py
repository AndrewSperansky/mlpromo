# api/v1/calculator/router.py
"""
Calculator API — расширенные финансовые и маркетинговые расчёты.
"""

from fastapi import APIRouter

router = APIRouter(tags=["calculator"])


@router.get("/test")
def test():
    """
    Тестовый endpoint калькулятора.
    Позже внедрим PromoCalculatorService сюда же — если решим разделить функционал
    """
    return {"status": "calculator ok"}
