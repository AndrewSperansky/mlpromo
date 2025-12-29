# app/services/promo_service.py
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from collections.abc import Sequence
from app.repositories.promo_repository import PromoRepository
from app.schemas.promo_schema import PromoCreate, PromoUpdate
from models.promo import Promo


class PromoService:

    def __init__(self):
        self.repo = PromoRepository()

    def create(self, db: Session, data: PromoCreate) -> Promo:
        return self.repo.create(db, data)

    def get(self, db: Session, promo_id: int) -> Promo:
        promo = self.repo.get(db, promo_id)
        if not promo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Promo not found",
            )
        return promo

    def list(self, db: Session) -> Sequence[Promo]:
        stmt = select(Promo).where(Promo.is_deleted.is_(False))
        return db.execute(stmt).scalars().all()

    def update(
        self,
        db: Session,
        promo_id: int,
        data: PromoUpdate,
    ) -> Promo:
        promo = self.get(db, promo_id)
        return self.repo.update(db, promo, data)

    def delete(self, db: Session, promo_id: int) -> None:
        promo = self.get(db, promo_id)
        self.repo.soft_delete(db, promo)
