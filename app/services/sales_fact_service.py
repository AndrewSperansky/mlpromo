# app/services/sales_fact_service.py

import uuid
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
        batch_id: str = None
    ) -> dict:
        if not records:
            return {"status": "error", "message": "No records provided"}

        batch_id = batch_id or str(uuid.uuid4())
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
                        region, quantity, revenue, batch_id
                    ) VALUES (
                        :date, :sku_code, :sku_name, :store_code, :store_name,
                        :region, :quantity, :revenue, :batch_id
                    )
                """),
                {
                    "date": rec.date,
                    "sku_code": rec.sku_code,
                    "sku_name": rec.sku_name,
                    "store_code": rec.store_code,
                    "store_name": rec.store_name,
                    "region": rec.region,
                    "quantity": rec.quantity,
                    "revenue": rec.revenue,
                    "batch_id": batch_id
                }
            )
            records_loaded += 1

        db.commit()

        return {
            "status": "success",
            "batch_id": batch_id,
            "records_loaded": records_loaded,
            "message": f"Загружено {records_loaded} записей продаж"
        }