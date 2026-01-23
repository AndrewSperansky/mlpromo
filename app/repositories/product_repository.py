# app/repositories/product_schema.py
from sqlalchemy.orm import Session
from sqlalchemy import select
from collections.abc import Sequence
from models.product import Product
from app.schemas.product_schema import ProductCreate, ProductUpdate


class ProductRepository:

    def create(self, db: Session, data: ProductCreate) -> Product:
        product = Product(**data.model_dump())
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    def get(self, db: Session, product_id: int) -> Product | None:
        return (
            db.query(Product)
            .filter(Product.id == product_id, Product.is_deleted.is_(False))
            .first()
        )

    def get_by_sku(self, db: Session, sku: str) -> Product | None:
        return (
            db.query(Product)
            .filter(Product.sku == sku, Product.is_deleted.is_(False))
            .first()
        )

    def list(self, db: Session) -> Sequence[Product]:
        stmt = (
            select(Product)
            .where(Product.is_deleted.is_(False))
            .order_by(Product.created_at.desc())
        )
        return db.execute(stmt).scalars().all()

    def update(
        self,
        db: Session,
        product: Product,
        data: ProductUpdate,
    ) -> Product:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(product, field, value)

        db.commit()
        db.refresh(product)
        return product

    def soft_delete(self, db: Session, product: Product) -> None:
        product.is_deleted = True
        db.commit()
