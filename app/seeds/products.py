from sqlalchemy.orm import Session
from models.product import Product
from app.seeds.base import get_or_create


PRODUCTS = [
    {
        "sku": "MILK_1L",
        "name": "Молоко 1л",
        "category": "dairy",
        "price": 89.90,
    },
    {
        "sku": "CHEESE_200G",
        "name": "Сыр 200г",
        "category": "dairy",
        "price": 159.90,
    },
]


def seed_products(db: Session) -> dict[str, Product]:
    result = {}

    for data in PRODUCTS:
        product, _ = get_or_create(
            db,
            Product,
            filters={"sku": data["sku"]},
            defaults={"name": data["name"]},
        )
        result[data["sku"]] = product

    db.commit()
    return result
