# app/services/product_schema.py
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.product_repository import ProductRepository
from app.schemas.product_schema import ProductCreate, ProductUpdate
from models.product import Product


class ProductService:

    def __init__(self):
        self.repo = ProductRepository()

    def create(self, db: Session, data: ProductCreate) -> Product:
        if self.repo.get_by_sku(db, data.sku):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product with this SKU already exists",
            )
        return self.repo.create(db, data)

    def get(self, db: Session, product_id: int) -> Product:
        product = self.repo.get(db, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        return product

    def list(self, db: Session) -> list[Product]:
        return self.repo.list(db)

    def update(
        self,
        db: Session,
        product_id: int,
        data: ProductUpdate,
    ) -> Product:
        product = self.get(db, product_id)
        return self.repo.update(db, product, data)

    def delete(self, db: Session, product_id: int) -> None:
        product = self.get(db, product_id)
        self.repo.soft_delete(db, product)
