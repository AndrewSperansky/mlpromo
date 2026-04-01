# app/services/historical_data_service.py

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text
import json

logger = logging.getLogger("promo_ml")


class HistoricalDataService:
    """
    Сервис для получения данных для инференса.
    Если SKU новый — подставляет данные аналога.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_sku_features(self, sku: str, store_id: str = None) -> Dict[str, Any]:
        """
        Получает признаки SKU для инференса.
        Если SKU нет в базе — ищет аналог и возвращает его признаки.

        Возвращает:
            - features: dict — признаки для модели
            - is_new: bool — новый ли SKU
            - used_analog: bool — использовался ли аналог
            - original_sku: str — исходный SKU
            - effective_sku: str — SKU, чьи данные использованы
            - message: str — пояснение
        """
        try:
            # 1. Пытаемся найти SKU в базе
            query = text("""
                SELECT
                    "promo_id", 
                    "category",
                    "store_location_type",
                    "format_assortment",
                    "region",
                    "analog_sku",
                    "extra_features"
                FROM industrial_dataset_raw
                WHERE "sku" = :sku
                LIMIT 1
            """)

            result = self.db.execute(query, {"sku": sku}).fetchone()

            if result:
                # SKU найден — возвращаем его признаки
                return {
                    "features": {
                        "category": result[0] or "",
                        "store_location_type": result[1] or "",
                        "format_assortment": result[2] or "",
                        "region": result[3] or "",
                        "analog_sku": result[5] if result[5] else [],
                        "extra_features": result[6] if result[6] else {},
                    },
                    "is_new": False,
                    "used_analog": False,
                    "original_sku": sku,
                    "effective_sku": sku,
                    "message": f"Using data for SKU {sku}"
                }

            # 2. SKU не найден — ищем аналог
            analog_sku = self._find_analog(sku)

            if analog_sku:
                # Ищем признаки аналога
                analog_result = self.db.execute(query, {"sku": analog_sku}).fetchone()

                if analog_result:
                    return {
                        "features": {
                            "category": analog_result[0] or "",
                            "store_location_type": analog_result[1] or "",
                            "format_assortment": analog_result[2] or "",
                            "region": analog_result[3] or "",
                            "analog_sku": analog_result[5] if analog_result[5] else [],
                            "extra_features": analog_result[6] if analog_result[6] else {},
                        },
                        "is_new": True,
                        "used_analog": True,
                        "original_sku": sku,
                        "effective_sku": analog_sku,
                        "message": f"SKU {sku} not found, using analog {analog_sku}"
                    }

            # 3. Нет ни SKU, ни аналога — возвращаем пустые признаки
            return {
                "features": {
                    "category": "",
                    "store_location_type": "",
                    "format_assortment": "",
                    "region": "",
                    "analog_sku": [],
                    "extra_features": {},
                },
                "is_new": True,
                "used_analog": False,
                "original_sku": sku,
                "effective_sku": None,
                "message": f"SKU {sku} not found and no analog available, using defaults"
            }

        except Exception as e:
            logger.error(f"Failed to get SKU features for {sku}: {e}")
            return {
                "features": {},
                "is_new": True,
                "used_analog": False,
                "original_sku": sku,
                "effective_sku": None,
                "message": f"Error: {str(e)}"
            }

    def _find_analog(self, sku: str) -> Optional[str]:
        """
        Находит SKU аналог для данного товара.
        Ищет в поле analog_sku (JSONB) или в extra_features.
        """
        try:
            # 1. Ищем в поле analog_sku (JSONB)
            query = text("""
                SELECT "analog_sku"
                FROM industrial_dataset_raw
                WHERE "sku" = :sku
                LIMIT 1
            """)

            result = self.db.execute(query, {"sku": sku}).fetchone()

            if result and result[0]:
                analog_data = result[0]
                if isinstance(analog_data, list) and len(analog_data) > 0:
                    return analog_data[0]
                elif isinstance(analog_data, str):
                    return analog_data
                elif isinstance(analog_data, dict):
                    return analog_data.get("primary") or analog_data.get("main")

            # 2. Ищем в extra_features
            query_extra = text("""
                SELECT "extra_features"->>'analog_sku' as analog
                FROM industrial_dataset_raw
                WHERE "sku" = :sku
                LIMIT 1
            """)

            result_extra = self.db.execute(query_extra, {"sku": sku}).fetchone()
            if result_extra and result_extra[0]:
                return result_extra[0]

            return None

        except Exception as e:
            logger.error(f"Failed to find analog for {sku}: {e}")
            return None

    def get_sku_info(self, sku: str) -> Dict[str, Any]:
        """
        Возвращает информацию о SKU (для отладки)
        """
        return self.get_sku_features(sku)

    def get_promo_effectiveness(self, promo_id: str) -> Dict[str, Any]:
        """
        Анализирует эффективность промоакции по историческим данным
        (только для аналитики, не для инференса!)
        """
        try:
            query = text("""
                SELECT 
                    COUNT(*) as total_records,
                    AVG("k_uplift") as avg_k_uplift,
                    STDDEV("k_uplift") as k_uplift_stddev,
                    MIN("k_uplift") as min_k_uplift,
                    MAX("k_uplift") as max_k_uplift
                FROM industrial_dataset_raw
                WHERE "promo_id" = :promo_id
            """)

            result = self.db.execute(query, {"promo_id": promo_id}).fetchone()

            if not result or result[0] == 0:
                return {
                    "promo_id": promo_id,
                    "total_records": 0,
                    "avg_k_uplift": None,
                    "effectiveness": "unknown",
                    "message": "No historical data for this promo"
                }

            avg_k_uplift = float(result[1]) if result[1] else None

            if avg_k_uplift is None:
                effectiveness = "unknown"
                message = "Insufficient data"
            elif avg_k_uplift > 1.3:
                effectiveness = "high"
                message = "Very effective promotion (30%+ uplift)"
            elif avg_k_uplift > 1.1:
                effectiveness = "medium"
                message = "Moderately effective promotion (10-30% uplift)"
            elif avg_k_uplift > 1.0:
                effectiveness = "low"
                message = "Low effectiveness promotion (0-10% uplift)"
            elif avg_k_uplift == 1.0:
                effectiveness = "neutral"
                message = "No impact on sales"
            else:
                effectiveness = "negative"
                message = "Negative impact on sales"

            return {
                "promo_id": promo_id,
                "total_records": result[0],
                "avg_k_uplift": round(avg_k_uplift, 3) if avg_k_uplift else None,
                "k_uplift_stddev": float(result[2]) if result[2] else 0,
                "min_k_uplift": float(result[3]) if result[3] else 0,
                "max_k_uplift": float(result[4]) if result[4] else 0,
                "effectiveness": effectiveness,
                "message": message,
            }

        except Exception as e:
            logger.error(f"Failed to get promo effectiveness for {promo_id}: {e}")
            return {}

    def get_sku_details(self, sku: str) -> Dict[str, Any]:
        """
        Получает детальную информацию по SKU
        """
        try:
            query = text("""
                SELECT 
                    "category",
                    "analog_sku",
                    "extra_features"
                FROM industrial_dataset_raw
                WHERE "sku" = :sku
                LIMIT 1
            """)

            result = self.db.execute(query, {"sku": sku}).fetchone()

            if result:
                return {
                    "sku": sku,
                    "category": result[0] or "",
                    "analog_sku": result[2] if result[2] else [],
                    "extra_features": result[3] if result[3] else {},
                }
            return {}

        except Exception as e:
            logger.error(f"Failed to get SKU details for {sku}: {e}")
            return {}