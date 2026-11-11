# app/services/calendar_service.py

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas.torch_schema import CalendarRecord


class CalendarService:
    async def process_push_data(
        self,
        db: Session,
        records: List[CalendarRecord],
    ) -> dict:
        if not records:
            return {"status": "error", "message": "No records provided"}

        records_loaded = 0

        for rec in records:
            db.execute(
                text("""
                    INSERT INTO calendar (date, day_type, week, year)
                    VALUES (:date, :day_type, :week, :year)
                    ON CONFLICT (date) DO UPDATE SET
                        day_type = EXCLUDED.day_type,
                        week = EXCLUDED.week,
                        year = EXCLUDED.year,
                        updated_at = NOW()
                """),
                {
                    "date": rec.date,
                    "day_type": rec.day_type,
                    "week": rec.week,
                    "year": rec.year,
                }
            )
            records_loaded += 1

        db.commit()

        return {
            "status": "success",
            "records_loaded": records_loaded,
            "message": f"Загружено {records_loaded} записей производственного календаря"
        }