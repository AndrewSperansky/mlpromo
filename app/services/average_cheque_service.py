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

    1С отдаёт JSON массив с агрегированными данными по магазинам.
    """

    async def sync_from_1c(
            self,
            db: Session,
            start_date: date,
            end_date: date,
            batch_id: str = None
    ) -> dict:
        """
        Загружает средние чеки из 1С за период.
        """
        batch_id = batch_id or str(uuid.uuid4())

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

        # Удаляем старые данные за этот период (перед загрузкой)
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
                        total_amount, average_amount, is_total, batch_id
                    ) VALUES (
                        :date, :store_code, :store_name, :cheque_count,
                        :total_amount, :average_amount, :is_total, :batch_id
                    )
                """),
                {
                    "date": rec["date"],
                    "store_code": rec["store_code"],
                    "store_name": rec.get("store_name"),
                    "cheque_count": rec["cheque_count"],
                    "total_amount": rec["total_amount"],
                    "average_amount": rec["average_amount"],
                    "is_total": rec.get("is_total", False),
                    "batch_id": batch_id
                }
            )

        db.commit()

        return {
            "status": "success",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "records_loaded": len(records),
            "batch_id": batch_id
        }



    async def process_push_data(
            self,
            db: Session,
            records: List[dict],
            batch_id: str = None
    ) -> dict:
        """
        Обрабатывает PUSH-данные от 1С.

        1С отправляет массив записей, этот метод:
        1. Удаляет старые данные за те же даты (если нужно)
        2. Вставляет новые
        """
        if not records:
            return {"status": "error", "message": "No records provided"}

        batch_id = batch_id or str(uuid.uuid4())
        records_loaded = 0

        # Опционально: удалить старые данные за эти даты
        dates = list(set([r["date"] for r in records]))

        for dt in dates:
            db.execute(
                text("""
                    DELETE FROM average_cheque
                    WHERE date = :date
                """),
                {"date": dt}
            )

        # Вставляем новые записи
        for rec in records:
            db.execute(
                text("""
                    INSERT INTO average_cheque (
                        date, store_code, store_name, cheque_count,
                        total_amount, average_amount, is_total, batch_id
                    ) VALUES (
                        :date, :store_code, :store_name, :cheque_count,
                        :total_amount, :average_amount, :is_total, :batch_id
                    )
                """),
                {
                    "date": rec["date"],
                    "store_code": rec["store_code"],
                    "store_name": rec["store_name"],
                    "cheque_count": rec["cheque_count"],
                    "total_amount": rec["total_amount"],
                    "average_amount": rec["average_amount"],
                    "is_total": bool(rec.get("is_total", False)),
                    "batch_id": batch_id
                }
            )
            records_loaded += 1

        db.commit()

        return {
            "status": "success",
            "batch_id": batch_id,
            "records_loaded": records_loaded,
            "message": f"Загружено {records_loaded} записей о среднем чеке"
        }