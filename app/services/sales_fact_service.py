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

        # Удаляем старые данные за эти даты (опционально)
        dates = list(set([r.date for r in records]))
        for dt in dates:
            db.execute(
                text("DELETE FROM sales_fact WHERE date = :date"),
                {"date": dt}
            )

        # Вставляем новые записи
        for rec in records:
            db.execute(
                text("""
                    INSERT INTO sales_fact (
                        date, sku_code, sku_name, store_code, store_name,
                        region, oblast, uom, quantity, revenue
                    ) VALUES (
                        :date, :sku_code, :sku_name, :store_code, :store_name,
                        :region, :oblast, :uom, :quantity, :revenue
                    )
                """),
                {
                    "date": rec.date,
                    "sku_code": rec.sku_code,
                    "sku_name": rec.sku_name,
                    "store_code": rec.store_code,
                    "store_name": rec.store_name,
                    "region": rec.region,
                    "oblast": rec.oblast,      # ← добавить
                    "uom": rec.uom,            # ← добавить
                    "quantity": rec.quantity,
                    "revenue": rec.revenue
                }
            )
            records_loaded += 1

        db.commit()

        return {
            "status": "success",
            "records_loaded": records_loaded,
            "message": f"Загружено {records_loaded} записей продаж"
        }