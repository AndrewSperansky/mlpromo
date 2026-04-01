# app/services/promo_calculator_service.py

"""
Promo Calculator Service — расчёт эффективности промо.
"""

import logging
from typing import Dict, Any, List
import numpy as np

logger = logging.getLogger("promo_ml")


class PromoCalculatorService:
    """
    Промо-калькулятор: расчёт коэффициента прироста и эффективности.
    """

    @staticmethod
    def interpret_k_uplift(k_uplift: float) -> Dict[str, Any]:
        """
        Интерпретирует коэффициент прироста
        """
        if k_uplift >= 1.3:
            return {
                "level": "high",
                "message": "Very effective promotion (30%+ uplift)",
                "color": "success"
            }
        elif k_uplift >= 1.1:
            return {
                "level": "medium",
                "message": "Moderately effective promotion (10-30% uplift)",
                "color": "info"
            }
        elif k_uplift > 1.0:
            return {
                "level": "low",
                "message": "Low effectiveness promotion (0-10% uplift)",
                "color": "primary"
            }
        elif k_uplift == 1.0:
            return {
                "level": "neutral",
                "message": "No impact on sales",
                "color": "secondary"
            }
        else:
            return {
                "level": "negative",
                "message": "Negative impact on sales",
                "color": "danger"
            }

    @staticmethod
    def compute_item(data: dict) -> dict:
        """
        Выполняет расчёт промо-метрик по одному SKU.
        Ожидаемые поля:
            - SKU: str
            - BasePrice: float
            - PromoPrice: float
            - KUplift: float (коэффициент прироста)
            - BaseSales: float (базовые продажи, опционально)
        """
        try:
            sku = data.get("SKU", "")
            regular_price = float(data.get("BasePrice", 0))
            promo_price = float(data.get("PromoPrice", 0))
            k_uplift = float(data.get("KUplift", 1.0))
            base_sales = float(data.get("BaseSales", 0))

            result = {
                "SKU": sku,
                "regular_price": regular_price,
                "promo_price": promo_price,
                "k_uplift": k_uplift,
                "predicted_sales": base_sales * k_uplift if base_sales > 0 else None,
            }

            logger.info("Promo calculation completed", extra={"SKU": sku})
            return result

        except Exception as exc:
            logger.error("Promo calculation failed", extra={"error": str(exc)})
            raise


    @staticmethod
    def calculate_forecast_accuracy(
        predictions: List[float],
        actuals: List[float]
    ) -> Dict[str, Any]:
        """
        Рассчитывает точность прогноза для k_uplift
        """
        if not predictions or not actuals or len(predictions) != len(actuals):
            return {"mape": None, "mae": None, "rmse": None}

        predictions = np.array(predictions)
        actuals = np.array(actuals)

        mask = actuals != 0
        if np.any(mask):
            mape = np.mean(np.abs((actuals[mask] - predictions[mask]) / actuals[mask])) * 100
        else:
            mape = None

        mae = np.mean(np.abs(actuals - predictions))
        rmse = np.sqrt(np.mean((actuals - predictions) ** 2))

        return {
            "mape": round(mape, 2) if mape is not None else None,
            "mae": round(mae, 4),
            "rmse": round(rmse, 4)
        }