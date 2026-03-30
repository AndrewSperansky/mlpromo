# app/services/promo_calculator_service.py

"""
Promo Calculator Service — расчёт эффективности промо.
Включает:
- baseline (базовые продажи без промо)
- uplift (прирост от промо)
- moving average of regular sales (скользящее среднее обычных продаж)
- прогноз продаж
- финансовая эффективность
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime, timedelta

logger = logging.getLogger("promo_ml")


class PromoCalculatorService:
    """
    Промо-калькулятор: расчёт базовых продаж, прироста, эффективности.
    """

    @staticmethod
    def calculate_baseline(
            weekly_sales: List[float],
            weeks: int = 4,
            method: str = "moving_average"
    ) -> float:
        """
        Рассчитывает baseline (ожидаемые продажи без промо) на основе истории.

        Args:
            weekly_sales: список продаж по неделям (последние N недель)
            weeks: количество недель для усреднения
            method: "moving_average" | "median" | "weighted"

        Returns:
            float: базовые продажи
        """
        if not weekly_sales:
            return 0.0

        # Берём последние `weeks` значений
        recent = weekly_sales[-weeks:] if len(weekly_sales) >= weeks else weekly_sales

        if method == "moving_average":
            return float(np.mean(recent))
        elif method == "median":
            return float(np.median(recent))
        elif method == "weighted":
            # Более свежие недели имеют больший вес
            weights = np.arange(1, len(recent) + 1)
            return float(np.average(recent, weights=weights))
        else:
            return float(np.mean(recent))

    @staticmethod
    def calculate_uplift(prediction: float, baseline: float) -> float:
        """
        Рассчитывает uplift (прирост от промо) в процентах.

        Args:
            prediction: прогноз продаж
            baseline: базовые продажи без промо

        Returns:
            float: uplift в процентах (может быть отрицательным)
        """
        if baseline <= 0:
            return 0.0
        return ((prediction - baseline) / baseline) * 100

    @staticmethod
    def calculate_moving_average(
            df: pd.DataFrame,
            column: str,
            window: int = 4
    ) -> pd.Series:
        """
        Рассчитывает скользящее среднее для колонки.

        Args:
            df: DataFrame с данными
            column: имя колонки
            window: размер окна (недель)

        Returns:
            pd.Series: скользящее среднее
        """
        return df[column].rolling(window=window, min_periods=1).mean()

    @staticmethod
    def get_weekly_sales_from_history(
            history: Dict[str, Any],
            weeks: int = 4
    ) -> List[float]:
        """
        Извлекает список продаж за последние N недель из исторических данных.

        Args:
            history: словарь с историческими данными (от HistoricalDataService)
            weeks: количество недель

        Returns:
            List[float]: список продаж (от новых к старым)
        """
        sales = []
        for i in range(1, weeks + 1):
            week_key = f"reg_sales_qty_week_{i}"
            if week_key in history:
                sales.append(history[week_key])
        return sales[::-1]  # реверсируем, чтобы последние недели были в конце

    @staticmethod
    def calculate_promo_effectiveness(
            total_sales: float,
            total_baseline: float,
            total_discount: float,
            records_count: int
    ) -> Dict[str, Any]:
        """
        Рассчитывает эффективность промоакции.

        Args:
            total_sales: суммарные продажи во время промо
            total_baseline: суммарные базовые продажи
            total_discount: суммарный размер скидки (%)
            records_count: количество записей

        Returns:
            Dict: метрики эффективности
        """
        avg_uplift = ((total_sales - total_baseline) / total_baseline * 100) if total_baseline > 0 else 0
        avg_discount = total_discount / records_count if records_count > 0 else 0

        if avg_uplift > 30:
            effectiveness = "high"
            message = "Very effective promotion"
        elif avg_uplift > 10:
            effectiveness = "medium"
            message = "Moderately effective promotion"
        elif avg_uplift > 0:
            effectiveness = "low"
            message = "Low effectiveness promotion"
        else:
            effectiveness = "negative"
            message = "Negative impact on sales"

        return {
            "avg_uplift": round(avg_uplift, 2),
            "avg_discount": round(avg_discount, 2),
            "effectiveness": effectiveness,
            "message": message
        }

    @staticmethod
    def compute_item(data: dict) -> dict:
        """
        Выполняет расчёт промо-метрик по одному SKU.

        Ожидаемые поля в data:
            - SKU: str
            - BasePrice: float (обычная цена)
            - PromoPrice: float (промо-цена)
            - BaseSales: float (базовые продажи)
            - Elasticity: float (эластичность спроса, опционально)
            - CostPerUnit: float (себестоимость, опционально)
        """
        try:
            sku = data["SKU"]
            base = Decimal(str(data["BasePrice"]))
            promo = Decimal(str(data["PromoPrice"]))
            base_sales = Decimal(str(data["BaseSales"]))
            elasticity = Decimal(str(data.get("Elasticity", "0.5")))

            # Новые продажи с учётом эластичности
            if base > 0:
                price_drop = (base - promo) / base
                new_sales = base_sales * (1 + elasticity * price_drop)
            else:
                new_sales = base_sales

            result = {
                "SKU": sku,
                "NewSales": float(new_sales),
            }

            # Опционально: добавляем финансовые метрики
            if "CostPerUnit" in data:
                cost = Decimal(str(data["CostPerUnit"]))
                revenue_before = base_sales * base
                revenue_after = new_sales * promo
                profit_before = base_sales * (base - cost)
                profit_after = new_sales * (promo - cost)

                result.update({
                    "RevenueBefore": float(revenue_before),
                    "RevenueAfter": float(revenue_after),
                    "ProfitBefore": float(profit_before),
                    "ProfitAfter": float(profit_after),
                })

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
        Рассчитывает точность прогноза.

        Args:
            predictions: список прогнозных значений
            actuals: список фактических значений

        Returns:
            Dict: метрики точности
        """
        if not predictions or not actuals or len(predictions) != len(actuals):
            return {"mape": None, "mae": None, "rmse": None}

        predictions = np.array(predictions)
        actuals = np.array(actuals)

        # MAPE (Mean Absolute Percentage Error)
        mask = actuals != 0
        if np.any(mask):
            mape = np.mean(np.abs((actuals[mask] - predictions[mask]) / actuals[mask])) * 100
        else:
            mape = None

        # MAE (Mean Absolute Error)
        mae = np.mean(np.abs(actuals - predictions))

        # RMSE (Root Mean Square Error)
        rmse = np.sqrt(np.mean((actuals - predictions) ** 2))

        return {
            "mape": round(mape, 2) if mape is not None else None,
            "mae": round(mae, 2),
            "rmse": round(rmse, 2)
        }