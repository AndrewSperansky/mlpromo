from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter()


class PredictRequest(BaseModel):
    promo_id: str
    sku_id: str
    store_id: str = None
    features: Dict[str, Any] = {}


class DayForecast(BaseModel):
    date: str
    forecast_units: float


class PredictResponse(BaseModel):
    promo_id: str
    sku_id: str
    forecast_total: float
    baseline: float
    uplift: float
    daily: List[DayForecast] = []
    shap: List[Dict[str, Any]] = []


@router.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    try:
        total = req.features.get("regular_sales", 100) * 1.2
        baseline = req.features.get("regular_sales", 100)
        uplift = total - baseline
        daily = []
        days = int(req.features.get("promo_days", 7))
        per = total / days if days > 0 else total
        for i in range(days):
            daily.append({"date": f"day_{i+1}", "forecast_units": per})
        shap = [{"feature": "DiscountPercent", "effect": 32.1}]
        return PredictResponse(
            promo_id=req.promo_id,
            sku_id=req.sku_id,
            forecast_total=total,
            baseline=baseline,
            uplift=uplift,
            daily=daily,
            shap=shap,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
