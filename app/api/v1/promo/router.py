"""
Promo API — операции над промо и расчёт эффективности.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from app.services.promo_calculator_service import PromoCalculatorService


router = APIRouter(tags=["promo"])
service = PromoCalculatorService()


class PromoCalcRequest(BaseModel):
    base_sales: float
    uplift_percent: float


@router.post("/calculate", summary="Расчёт промо-эффективности")
def calculate_promo(payload: PromoCalcRequest):
    """
    Рассчитывает ожидаемую эффективность промо-акции.

    Args:
        payload (PromoCalcRequest): Параметры для расчёта.

    Returns:
        dict: Результаты промо-калькуляции.
    """
    return service.calculate(payload.model_dump())
