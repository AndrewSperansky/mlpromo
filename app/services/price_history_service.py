# app/services/price_history_service.py

from typing import List
from sqlalchemy.orm import Session
from datetime import date, timedelta
from sqlalchemy import text


class PriceHistoryService:

    def __init__(self, db: Session):
        self.db = db

    def get_retail_price_history(self, sku: str, days: int = 30) -> list[dict]:
        """Возвращает историю продажных цен за последние N дней"""
        result = self.db.execute(
            text("""
                SELECT date, price
                FROM retail_price_history
                WHERE sku_code = :sku AND date >= CURRENT_DATE - :days
                ORDER BY date
            """),
            {"sku": sku, "days": days}
        )
        return [{"date": row[0], "price": float(row[1])} for row in result.fetchall()]



    def get_purchase_price_history(self, sku: str, supplier: str, days: int = 30) -> list[dict]:
        """Возвращает историю закупочных цен за последние N дней"""
        result = self.db.execute(
            text("""
                SELECT date, price
                FROM purchase_price_history
                WHERE sku = :sku AND supplier = :supplier AND date >= CURRENT_DATE - :days
                ORDER BY date
            """),
            {"sku": sku, "supplier": supplier, "days": days}
        )
        return [{"date": row[0], "price": float(row[1])} for row in result.fetchall()]



    async def process_retail_prices(self, db: Session, records: List[dict]) -> dict:
        """Сохраняет историю розничных цен"""
        records_loaded = 0
        for rec in records:
            db.execute(
                text("""
                    INSERT INTO retail_price_history (date, week, sku_code, sku_name, category, price, created_at, updated_at)
                    VALUES (:date, :week, :sku_code, :sku_name, :category, :price, NOW(), NOW())
                    ON CONFLICT (date, sku_code) DO UPDATE SET
                        week = EXCLUDED.week,
                        sku_name = EXCLUDED.sku_name,
                        category = EXCLUDED.category,
                        price = EXCLUDED.price,
                        updated_at = NOW()
                """),
                {
                    "date": rec["date"],
                    "week": rec["week"],
                    "sku_code": rec["sku_code"],
                    "sku_name": rec.get("sku_name"),
                    "category": rec.get("category"),
                    "price": rec["price"]
                }
            )
            records_loaded += 1

        db.commit()
        return {
            "status": "success",
            "records_loaded": records_loaded,
            "message": f"Загружено {records_loaded} записей розничных цен"
        }



    async def process_purchase_prices(self, db: Session, records: List[dict]) -> dict:
        """Сохраняет историю закупочных цен"""
        records_loaded = 0
        for rec in records:
            db.execute(
                text("""
                    INSERT INTO purchase_price_history (date, sku, supplier, price, created_at, updated_at)
                    VALUES (:date, :sku, :supplier, :price, NOW(), NOW())
                    ON CONFLICT (date, sku, supplier) DO UPDATE SET
                        price = EXCLUDED.price,
                        updated_at = NOW()
                """),
                {
                    "date": rec["date"],
                    "sku": rec["sku"],
                    "supplier": rec["supplier"],
                    "price": rec["price"]
                }
            )
            records_loaded += 1

        db.commit()
        return {
            "status": "success",
            "records_loaded": records_loaded,
            "message": f"Загружено {records_loaded} записей закупочных цен"
        }
