"""
Promo Calculator Service — расчёт эффективности промо.
"""

# from typing import Dict
import logging
from decimal import Decimal

logger = logging.getLogger("promo_ml")


class PromoCalculatorService:
    """
    Промо-калькулятор для SKU на основе цены, объёма продаж
    и эластичности (упрощённая модель).
    """

    @staticmethod
    def compute_item(data: dict) -> dict:
        """
        Выполняет расчёт промо-метрик по одному SKU.
        """
        try:
            SKU = data["SKU"]
            base = Decimal(data["BasePrice"])
            promo = Decimal(data["PromoPrice"])
            base_sales = Decimal(data["BaseSales"])
            elasticity = Decimal(data.get("Elasticity", "0.5"))
            cost = Decimal(data.get("CostPerUnit", "0"))

            new_sales = base_sales * (1 + elasticity * ((base - promo) / base))
            revenue_before = base_sales * base
            revenue_after = new_sales * promo
            profit_before = base_sales * (base - cost)
            profit_after = new_sales * (promo - cost)

            result = {
                "SKU": SKU,
                "NewSales": float(new_sales),
                "RevenueBefore": float(revenue_before),
                "RevenueAfter": float(revenue_after),
                "ProfitBefore": float(profit_before),
                "ProfitAfter": float(profit_after),
            }

            logger.info("Promo calculation completed", extra={"SKU": SKU})
            return result

        except Exception as exc:
            logger.error("Promo calculation failed", extra={"error": str(exc)})
            raise
