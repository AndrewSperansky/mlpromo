from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.controllers.promo_controller import PromoController
from app.schemas.promo_schema import PromoCreate, PromoRead

router = APIRouter(prefix="/promo", tags=["Promo"])


@router.post("/", response_model=PromoRead)
def create_promo(
    payload: PromoCreate,
    db: Session = Depends(get_db),
):
    try:
        return PromoController(db).create(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{promo_id}", response_model=PromoRead)
def get_promo(
    promo_id: int,
    db: Session = Depends(get_db),
):
    try:
        return PromoController(db).get(promo_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
