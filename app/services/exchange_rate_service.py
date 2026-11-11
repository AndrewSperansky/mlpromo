# app/services/exchange_rate_service.py

import uuid
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas.torch_schema import ExchangeRateRecord


class ExchangeRateService:
    async def process_push_data(
        self,
        db: Session,
        records: List[ExchangeRateRecord],
    ) -> dict:
        if not records:
            return {"status": "error", "message": "No records provided"}

        records_loaded = 0

        for rec in records:
            db.execute(
                text("""
                    INSERT INTO exchange_rates (date, currency, rate)
                    VALUES (:date, :currency, :rate)
                    ON CONFLICT (date, currency) DO UPDATE SET
                        rate = EXCLUDED.rate,
                        updated_at = NOW()
                """),
                {
                    "date": rec.date,
                    "currency": rec.currency,
                    "rate": rec.rate
                }
            )
            records_loaded += 1

        db.commit()

        return {
            "status": "success",
            "records_loaded": records_loaded,
            "message": f"Загружено {records_loaded} записей курсов валют"
        }