# app/services/sales_fact_service.py

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas.torch_schema import SalesFactRecord


class SalesFactService:
    """Сервис для загрузки продаж"""

    async def process_push_data(
            self,
            db: Session,
            records: List[SalesFactRecord],
    ) -> dict:
        if not records:
            return {"status": "error", "message": "No records provided"}

        records_loaded = 0

        for rec in records:
            db.execute(
                text("""
                    INSERT INTO sales_fact (
                        date, week, sku_code, sku_name, store_code, store_name,
                        region, oblast, uom, quantity, revenue, category
                    ) VALUES (
                        :date, :week, :sku_code, :sku_name, :store_code, :store_name,
                        :region, :oblast, :uom, :quantity, :revenue, :category
                    )
                    ON CONFLICT (date, sku_code, store_code) DO UPDATE SET
                        week = EXCLUDED.week,
                        sku_name = EXCLUDED.sku_name,
                        store_name = EXCLUDED.store_name,
                        region = EXCLUDED.region,
                        oblast = EXCLUDED.oblast,
                        uom = EXCLUDED.uom,
                        quantity = EXCLUDED.quantity,
                        revenue = EXCLUDED.revenue,
                        category = EXCLUDED.category,
                        updated_at = NOW()
                """),
                {
                    "date": rec.date,
                    "week": rec.week,
                    "sku_code": rec.sku_code,
                    "sku_name": rec.sku_name,
                    "store_code": rec.store_code,
                    "store_name": rec.store_name,
                    "region": rec.region,
                    "oblast": rec.oblast,
                    "uom": rec.uom,
                    "quantity": rec.quantity,
                    "revenue": rec.revenue,
                    "category": rec.category
                }
            )
            records_loaded += 1

        db.commit()

        return {
            "status": "success",
            "records_loaded": records_loaded,
            "message": f"Загружено {records_loaded} записей продаж"
        }