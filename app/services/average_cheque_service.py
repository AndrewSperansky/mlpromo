# app/services/average_cheque_service.py

import httpx
import json
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
import uuid

class AverageChequeService:
    """
    Сервис для загрузки данных о среднем чеке из 1С.
    """

    async def sync_from_1c(
        self,
        db: Session,
        start_date: date,
        end_date: date
    ) -> dict:
        """Загружает средние чеки из 1С за период."""
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "http://1c-service/api/average-cheque",
                json={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            )
            response.raise_for_status()
            data = response.json()

        records = data.get("records", [])

        # Удаляем старые данные за этот период
        db.execute(
            text("""
                DELETE FROM average_cheque
                WHERE date BETWEEN :start_date AND :end_date
            """),
            {"start_date": start_date, "end_date": end_date}
        )

        # Вставляем новые
        for rec in records:
            db.execute(
                text("""
                    INSERT INTO average_cheque (
                        date, store_code, store_name, cheque_count,
                        total_amount, average_amount, week
                    ) VALUES (
                        :date, :store_code, :store_name, :cheque_count,
                        :total_amount, :average_amount, :week
                    )
                """),
                {
                    "date": rec["date"],
                    "store_code": rec["store_code"],
                    "store_name": rec.get("store_name"),
                    "cheque_count": rec["cheque_count"],
                    "total_amount": rec["total_amount"],
                    "average_amount": rec["average_amount"],
                    "week": rec.get("week")
                }
            )

        db.commit()

        return {
            "status": "success",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "records_loaded": len(records)
        }

    async def process_push_data(
        self,
        db: Session,
        records: List[dict]
    ) -> dict:
        """Обрабатывает PUSH-данные от 1С."""
        if not records:
            return {"status": "error", "message": "No records provided"}

        records_loaded = 0

        for rec in records:
            db.execute(
                text("""
                    INSERT INTO average_cheque (
                        date, store_code, store_name, cheque_count,
                        total_amount, average_amount, week
                    ) VALUES (
                        :date, :store_code, :store_name, :cheque_count,
                        :total_amount, :average_amount, :week
                    )
                    ON CONFLICT (date, store_code) DO UPDATE SET
                        cheque_count = EXCLUDED.cheque_count,
                        total_amount = EXCLUDED.total_amount,
                        average_amount = EXCLUDED.average_amount,
                        week = EXCLUDED.week,
                        updated_at = NOW()
                """),
                {
                    "date": rec["date"],
                    "store_code": rec["store_code"],
                    "store_name": rec.get("store_name"),
                    "cheque_count": rec["cheque_count"],
                    "total_amount": rec["total_amount"],
                    "average_amount": rec["average_amount"],
                    "week": rec["week"]
                }
            )
            records_loaded += 1

        db.commit()

        return {
            "status": "success",
            "records_loaded": records_loaded,
            "message": f"Загружено {records_loaded} записей о среднем чеке"
        }