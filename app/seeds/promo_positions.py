# 🔥 ML-ядро
# 📌 Это важно
# бизнес-ключ = (promo_id, product_id, date)
# можно добавлять новые дни → временной ряд для ML

from datetime import date, timedelta
from sqlalchemy.orm import Session
from models.promo_position import PromoPosition
from app.seeds.base import get_or_create


START_DATE = date(2025, 1, 1)
DAYS = 14  # 2 недели — достаточно для baseline


PROMO_POSITIONS = [
    {
        "promo_code": "PROMO_DAIRY_JAN",
        "product_sku": "MILK_1L",
        "date": date(2025, 1, 5),
        "price": 79.90,
        "discount": 10.0,
        "sales_qty": 120,
    },
    {
        "promo_code": "PROMO_DAIRY_JAN",
        "product_sku": "CHEESE_200G",
        "date": date(2025, 1, 5),
        "price": 139.90,
        "discount": 12.5,
        "sales_qty": 60,
    },
]


def seed_promo_positions(
    db: Session,
    promos: dict,
    products: dict,
) -> None:

    for cfg in PROMO_POSITIONS:
        promo = promos[cfg["promo_code"]]
        product = products[cfg["product_sku"]]

        for day in range(DAYS):
            current_date = START_DATE + timedelta(days=day)

            # простая детерминированная динамика
            sales_qty = cfg["sales_qty"] + day * 3
            discount = cfg["discount"] + (day % 3) * 0.5
            price = cfg["price"] - discount

            get_or_create(
                db,
                PromoPosition,
                filters={
                    "promo_id": promo.id,
                    "product_id": product.id,
                    "date": current_date,
                },
                defaults={
                    "price": round(price, 2),
                    "discount": round(discount, 2),
                    "sales_qty": sales_qty,
                },
            )




# def seed_promo_positions(
#     db: Session,
#     promos: dict,
#     products: dict,
# ):
#     for row in PROMO_POSITIONS:
#         promo = promos[row["promo_code"]]
#         product = products[row["product_sku"]]
#
#         get_or_create(
#             db,
#             PromoPosition,
#             filters={
#                 "promo_id": promo.id,
#                 "product_id": product.id,
#                 "date": row["date"],
#             },
#             defaults={
#                 "price": row["price"],
#                 "discount": row["discount"],
#                 "sales_qty": row["sales_qty"],
#             },
#         )

    db.commit()
