# app/services/historical_data_service.py

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger("promo_ml")


class HistoricalDataService:
    """
    Сервис для получения исторических данных из industrial_dataset_raw
    """

    def __init__(self, db: Session):
        self.db = db

    def get_sku_history(self, sku: str, store_id: str = None) -> Dict[str, Any]:
        """
        Возвращает историческую статистику по SKU (и магазину, если указан)
        """
        try:
            where_clause = '"sku" = :sku'
            params = {"sku": sku}
            if store_id:
                where_clause += ' AND "store_id" = :store_id'
                params["store_id"] = store_id

            # 🔥 Запрос к базе — получаем все недели продаж
            query = text(f"""
                SELECT 
                    reg_sales_qty_week_1, reg_sales_qty_week_2, reg_sales_qty_week_3,
                    reg_sales_qty_week_4, reg_sales_qty_week_5, reg_sales_qty_week_6,
                    reg_sales_qty_week_7, reg_sales_qty_week_8, reg_sales_qty_week_9,
                    reg_sales_qty_week_10, reg_sales_qty_week_11, reg_sales_qty_week_12,
                    reg_sales_qty_week_13, reg_sales_qty_week_14, reg_sales_qty_week_15,
                    reg_sales_qty_week_16, reg_sales_qty_week_17, reg_sales_qty_week_18,
                    reg_sales_qty_week_19, reg_sales_qty_week_20, reg_sales_qty_week_21,
                    reg_sales_qty_week_22, reg_sales_qty_week_23, reg_sales_qty_week_24,
                    reg_sales_qty_week_25, reg_sales_qty_week_26, reg_sales_qty_week_27,
                    reg_sales_qty_week_28, reg_sales_qty_week_29, reg_sales_qty_week_30,
                    reg_sales_qty_week_31, reg_sales_qty_week_32, reg_sales_qty_week_33,
                    reg_sales_qty_week_34, reg_sales_qty_week_35, reg_sales_qty_week_36,
                    reg_sales_qty_week_37, reg_sales_qty_week_38, reg_sales_qty_week_39,
                    reg_sales_qty_week_40, reg_sales_qty_week_41, reg_sales_qty_week_42,
                    reg_sales_qty_week_43, reg_sales_qty_week_44, reg_sales_qty_week_45,
                    reg_sales_qty_week_46, reg_sales_qty_week_47, reg_sales_qty_week_48,
                    reg_sales_qty_week_49, reg_sales_qty_week_50, reg_sales_qty_week_51,
                    reg_sales_qty_week_52,
                    COUNT(*) as total_records
                FROM industrial_dataset_raw
                WHERE {where_clause}
                GROUP BY 
                    reg_sales_qty_week_1, reg_sales_qty_week_2, reg_sales_qty_week_3,
                    reg_sales_qty_week_4, reg_sales_qty_week_5, reg_sales_qty_week_6,
                    reg_sales_qty_week_7, reg_sales_qty_week_8, reg_sales_qty_week_9,
                    reg_sales_qty_week_10, reg_sales_qty_week_11, reg_sales_qty_week_12,
                    reg_sales_qty_week_13, reg_sales_qty_week_14, reg_sales_qty_week_15,
                    reg_sales_qty_week_16, reg_sales_qty_week_17, reg_sales_qty_week_18,
                    reg_sales_qty_week_19, reg_sales_qty_week_20, reg_sales_qty_week_21,
                    reg_sales_qty_week_22, reg_sales_qty_week_23, reg_sales_qty_week_24,
                    reg_sales_qty_week_25, reg_sales_qty_week_26, reg_sales_qty_week_27,
                    reg_sales_qty_week_28, reg_sales_qty_week_29, reg_sales_qty_week_30,
                    reg_sales_qty_week_31, reg_sales_qty_week_32, reg_sales_qty_week_33,
                    reg_sales_qty_week_34, reg_sales_qty_week_35, reg_sales_qty_week_36,
                    reg_sales_qty_week_37, reg_sales_qty_week_38, reg_sales_qty_week_39,
                    reg_sales_qty_week_40, reg_sales_qty_week_41, reg_sales_qty_week_42,
                    reg_sales_qty_week_43, reg_sales_qty_week_44, reg_sales_qty_week_45,
                    reg_sales_qty_week_46, reg_sales_qty_week_47, reg_sales_qty_week_48,
                    reg_sales_qty_week_49, reg_sales_qty_week_50, reg_sales_qty_week_51,
                    reg_sales_qty_week_52
            """)

            result = self.db.execute(query, params).fetchone()

            if not result:
                return {}

            # 🔥 Собираем словарь с историческими данными
            weekly_sales = {}
            for i in range(52):
                week_key = f"reg_sales_qty_week_{i + 1}"
                value = result[i]
                if value is not None:
                    weekly_sales[week_key] = float(value)

            return {
                "sku": sku,
                "store_id": store_id,
                "total_records": result[52] or 0,
                "weekly_sales": weekly_sales,
                "recent_sales": [weekly_sales.get(f"reg_sales_qty_week_{i + 1}", 0) for i in range(12, 0, -1)]
                # последние 12 недель
            }

        except Exception as e:
            logger.error(f"Failed to get SKU history for {sku}: {e}")
            return {}


    def calculate_baseline(self, sku: str, store_id: str, date: str) -> float:
        """
        Рассчитывает baseline (ожидаемые продажи без промо)
        Использует reg_sales_qty_week_N по номеру недели из date
        """
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            week_number = date_obj.isocalendar()[1]  # номер недели в году
            week_number = max(1, min(52, week_number))  # ограничиваем от 1 до 52

            # 🔥 Запрос к базе — берём продажи за указанную неделю
            field_name = f"reg_sales_qty_week_{week_number}"
            query = text(f"""
                SELECT "{field_name}"
                FROM industrial_dataset_raw
                WHERE "sku" = :sku AND "store_id" = :store_id
                AND "{field_name}" IS NOT NULL
                ORDER BY "id" DESC
                LIMIT 1
            """)

            result = self.db.execute(query, {"sku": sku, "store_id": store_id}).fetchone()

            if result and result[0] is not None:
                baseline = float(result[0])
                logger.debug(f"Baseline for {sku}/{store_id} week {week_number}: {baseline}")
                return baseline

            # 🔥 Fallback 1: ищем по предыдущей или следующей неделе
            for offset in [-1, 1, -2, 2]:
                alt_week = week_number + offset
                if 1 <= alt_week <= 52:
                    alt_field = f"reg_sales_qty_week_{alt_week}"
                    alt_query = text(f"""
                        SELECT "{alt_field}"
                        FROM industrial_dataset_raw
                        WHERE "sku" = :sku AND "store_id" = :store_id
                        AND "{alt_field}" IS NOT NULL
                        ORDER BY "id" DESC
                        LIMIT 1
                    """)
                    alt_result = self.db.execute(alt_query, {"sku": sku, "store_id": store_id}).fetchone()
                    if alt_result and alt_result[0] is not None:
                        baseline = float(alt_result[0])
                        logger.info(
                            f"Baseline for {sku}/{store_id}: using week {alt_week} instead of {week_number}, value: {baseline}")
                        return baseline

            # 🔥 Fallback 2: среднее арифметическое по всем неделям (через Python)
            query_all = text("""
                SELECT 
                    reg_sales_qty_week_1, reg_sales_qty_week_2, reg_sales_qty_week_3,
                    reg_sales_qty_week_4, reg_sales_qty_week_5, reg_sales_qty_week_6,
                    reg_sales_qty_week_7, reg_sales_qty_week_8, reg_sales_qty_week_9,
                    reg_sales_qty_week_10, reg_sales_qty_week_11, reg_sales_qty_week_12,
                    reg_sales_qty_week_13, reg_sales_qty_week_14, reg_sales_qty_week_15,
                    reg_sales_qty_week_16, reg_sales_qty_week_17, reg_sales_qty_week_18,
                    reg_sales_qty_week_19, reg_sales_qty_week_20, reg_sales_qty_week_21,
                    reg_sales_qty_week_22, reg_sales_qty_week_23, reg_sales_qty_week_24,
                    reg_sales_qty_week_25, reg_sales_qty_week_26, reg_sales_qty_week_27,
                    reg_sales_qty_week_28, reg_sales_qty_week_29, reg_sales_qty_week_30,
                    reg_sales_qty_week_31, reg_sales_qty_week_32, reg_sales_qty_week_33,
                    reg_sales_qty_week_34, reg_sales_qty_week_35, reg_sales_qty_week_36,
                    reg_sales_qty_week_37, reg_sales_qty_week_38, reg_sales_qty_week_39,
                    reg_sales_qty_week_40, reg_sales_qty_week_41, reg_sales_qty_week_42,
                    reg_sales_qty_week_43, reg_sales_qty_week_44, reg_sales_qty_week_45,
                    reg_sales_qty_week_46, reg_sales_qty_week_47, reg_sales_qty_week_48,
                    reg_sales_qty_week_49, reg_sales_qty_week_50, reg_sales_qty_week_51,
                    reg_sales_qty_week_52
                FROM industrial_dataset_raw
                WHERE "sku" = :sku AND "store_id" = :store_id
                LIMIT 1
            """)

            result_all = self.db.execute(query_all, {"sku": sku, "store_id": store_id}).fetchone()

            if result_all:
                # Собираем все не-NULL значения
                weekly_values = []
                for i in range(52):
                    value = result_all[i]
                    if value is not None:
                        weekly_values.append(float(value))

                if weekly_values:
                    baseline = sum(weekly_values) / len(weekly_values)
                    logger.info(
                        f"Baseline for {sku}/{store_id}: using average of {len(weekly_values)} weeks, value: {baseline}")
                    return baseline

            # 🔥 Fallback 3: вообще нет данных
            logger.warning(f"No baseline data found for SKU={sku}, store={store_id}")
            return 0.0

        except Exception as e:
            logger.error(f"Failed to calculate baseline for {sku}/{store_id}: {e}")
            return 0.0


    def get_promo_effectiveness(self, promo_id: str) -> Dict[str, Any]:
        """
        Анализирует эффективность промо-акции
        """
        try:
            query = text("""
                SELECT 
                    "sku",
                    "store_id",
                    "promo_week1",
                    "promo_week2",
                    "regular_price",
                    "promo_price",
                    "promo_week1_sales_qty",
                    "promo_week2_sales_qty"
                FROM industrial_dataset_raw
                WHERE "promo_id" = :promo_id
                ORDER BY "promo_week1" DESC
            """)
            results = self.db.execute(query, {"promo_id": promo_id}).fetchall()

            if not results:
                return {"effectiveness": "unknown", "message": "No data for this promo"}

            total_sales = 0
            total_baseline = 0
            total_discount = 0
            for row in results:
                week1_sales = float(row[6]) if row[6] else 0
                week2_sales = float(row[7]) if row[7] else 0
                sales = week1_sales + week2_sales
                regular = float(row[4]) if row[4] else 0
                promo = float(row[5]) if row[5] else 0
                # Базовые продажи можно взять из reg_sales_qty_week_N, но пока не усложняем
                baseline = 0  # placeholder
                total_sales += sales
                total_baseline += baseline
                if regular > 0:
                    total_discount += (regular - promo) / regular * 100

            avg_uplift = ((total_sales - total_baseline) / total_baseline * 100) if total_baseline > 0 else 0
            avg_discount = total_discount / len(results) if results else 0

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
                "promo_id": promo_id,
                "total_records": len(results),
                "total_sales": total_sales,
                "total_baseline": total_baseline,
                "avg_uplift": avg_uplift,
                "avg_discount": avg_discount,
                "effectiveness": effectiveness,
                "message": message,
            }

        except Exception as e:
            logger.error(f"Failed to get promo effectiveness: {e}")
            return {}


    def get_sku_details(self, sku: str) -> Dict[str, Any]:
        """
        Получает детальную информацию по SKU
        """
        try:
            query = text("""
                SELECT 
                    "sku_level_2",
                    "sku_level_3",
                    "sku_level_4",
                    "sku_level_5",
                    "category",
                    "is_new_sku",
                    "analog_sku"
                FROM industrial_dataset_raw
                WHERE "sku" = :sku
                LIMIT 1
            """)
            result = self.db.execute(query, {"sku": sku}).fetchone()
            if result:
                return {
                    "sku_level_2": result[0] or "",
                    "sku_level_3": result[1] or "",
                    "sku_level_4": result[2] or "",
                    "sku_level_5": result[3] or "",
                    "category": result[4] or "",
                    "is_new_sku": result[5] or 0,
                    "analog_sku": result[6] or "",
                }
            return {}

        except Exception as e:
            logger.error(f"Failed to get SKU details: {e}")
            return {}