# app/api/v1/promo/router.py

"""
Promo API — операции над промо и расчёт эффективности.
POST   /api/v1/promo
GET    /api/v1/promo/{id}
GET    /api/v1/promo
PATCH  /api/v1/promo/{id}
DELETE /api/v1/promo/{id}   (soft delete)
"""


from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.promo_schema import (
    PromoCreate,
    PromoRead,
    PromoUpdate,
)
from app.services.promo_service import PromoService

router = APIRouter(prefix="/promo", tags=["promo"])

service = PromoService()


@router.post("", response_model=PromoRead)
def create_promo(
    data: PromoCreate,
    db: Session = Depends(get_db),
):
    return service.create(db, data)


@router.get("/{promo_id}", response_model=PromoRead)
def get_promo(
    promo_id: int,
    db: Session = Depends(get_db),
):
    return service.get(db, promo_id)


@router.get("", response_model=list[PromoRead])
def list_promos(
    db: Session = Depends(get_db),
):
    return service.list(db)


@router.patch("/{promo_id}", response_model=PromoRead)
def update_promo(
    promo_id: int,
    data: PromoUpdate,
    db: Session = Depends(get_db),
):
    return service.update(db, promo_id, data)


@router.delete("/{promo_id}", status_code=204)
def delete_promo(
    promo_id: int,
    db: Session = Depends(get_db),
):
    service.delete(db, promo_id)

