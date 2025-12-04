"""
Promo Calculator Service — расчёт эффективности промо.
"""

from typing import Dict


class PromoCalculatorService:
    """
    Сервис бизнес-логики калькуляции промо.
    """

    def calculate(self, data: Dict) -> Dict:
        """
        Выполняет расчёт промо-эффективности.

        Args:
            data (dict): Параметры промо.

        Returns:
            dict: Результаты расчёта.
        """

        # _TODO: добавить формулы и бизнес-логику
        base_sales = data.get("base_sales", 0)
        uplift = data.get("uplift_percent", 0)

        predicted_sales = base_sales * (1 + uplift / 100)

        return {
            "base_sales": base_sales,
            "uplift_percent": uplift,
            "predicted_sales": predicted_sales,
        }
