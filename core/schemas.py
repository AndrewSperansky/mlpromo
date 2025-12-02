from pydantic import BaseModel
class ForecastRow(BaseModel):
    promo_id: str
    sku_id: str
    forecast_units: float
