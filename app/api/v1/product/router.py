"""
 POST   /api/v1/product
 GET    /api/v1/product/{id}
 GET    /api/v1/product
 PATCH  /api/v1/product/{id}
 DELETE /api/v1/product/{id}   (soft delete)

"""


from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.product_schema import (
    ProductCreate,
    ProductRead,
    ProductUpdate,
)
from app.services.product_service import ProductService

router = APIRouter(prefix="/product", tags=["product"])

service = ProductService()


@router.post("", response_model=ProductRead)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
):
    return service.create(db, data)


@router.get("/{product_id}", response_model=ProductRead)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    return service.get(db, product_id)


@router.get("", response_model=list[ProductRead])
def list_products(
    db: Session = Depends(get_db),
):
    return service.list(db)


@router.patch("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
):
    return service.update(db, product_id, data)


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    service.delete(db, product_id)
