# app/services/sales_fact_service.py

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date

class SalesFactService:

    async def process_push_data(self, db: Session, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not records:
            return {"status": "error", "message": "No records provided"}

        records_loaded = 0

        for rec in records:
            # Преобразуем дату
            date_val = rec["date"]
            if isinstance(date_val, str):
                date_val = date.fromisoformat(date_val.split('T')[0])
            elif hasattr(date_val, 'date'):
                date_val = date_val.date()
            elif not isinstance(date_val, date):
                raise ValueError(f"Invalid date format: {date_val}")

            db.execute(
                text("""
                    INSERT INTO sales_fact (
                        date, week, sku_code, sku_name, store_code, store_name,
                        region, oblast, uom, quantity, revenue, category
                    ) VALUES (
                        :date, :week, :sku_code, :sku_name, :store_code, :store_name,
                        :region, :oblast, :uom, :quantity, :revenue, :category
                    )
                    ON CONFLICT (date, sku_code, store_code) DO NOTHING
                """),
                {
                    "date": date_val,
                    "week": rec["week"],
                    "sku_code": rec["sku_code"],
                    "sku_name": rec.get("sku_name"),
                    "store_code": rec["store_code"],
                    "store_name": rec.get("store_name"),
                    "region": rec.get("region"),
                    "oblast": rec.get("oblast"),
                    "uom": rec.get("uom"),
                    "quantity": rec["quantity"],
                    "revenue": rec["revenue"],
                    "category": rec.get("category")
                }
            )
            records_loaded += 1

        db.commit()
        return {
            "status": "success",
            "records_loaded": records_loaded,
            "message": f"Загружено {records_loaded} записей продаж"
        }