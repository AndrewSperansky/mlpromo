from datetime import date
from sqlalchemy.orm import Session
from models.promo import Promo
from app.seeds.base import get_or_create


PROMOS = [
    {
        "code": "PROMO_DAIRY_JAN",
        "name": "Январская молочная акция",
        "start_date": date(2025, 1, 1),
        "end_date": date(2025, 1, 31),
    }
]


def seed_promos(db: Session) -> dict[str, Promo]:
    result = {}

    for data in PROMOS:
        promo, _ = get_or_create(
            db,
            Promo,
            filters={"code": data["code"]},   # ← теперь поле реально существует
            defaults={
                "code": data["code"],
                "start_date": data["start_date"],
                "end_date": data["end_date"],
            },
        )
        result[data["code"]] = promo

    db.commit()
    return result
