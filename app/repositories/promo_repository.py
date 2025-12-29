from sqlalchemy import select
from sqlalchemy.orm import Session
from collections.abc import Sequence
from models.promo import Promo
from app.schemas.promo_schema import PromoCreate, PromoUpdate


class PromoRepository:

    def create(self, db: Session, data: PromoCreate) -> Promo:
        promo = Promo(**data.model_dump())
        db.add(promo)
        db.commit()
        db.refresh(promo)
        return promo

    def get(self, db: Session, promo_id: int) -> Promo | None:
        stmt = select(Promo).where(
            Promo.id == promo_id,
            Promo.is_deleted.is_(False),
        )
        return db.execute(stmt).scalar_one_or_none()

    def list(self, db: Session) -> Sequence[Promo]:
        stmt = select(Promo).where(Promo.is_deleted.is_(False))
        return db.execute(stmt).scalars().all()

    def update(
        self,
        db: Session,
        promo: Promo,
        data: PromoUpdate,
    ) -> Promo:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(promo, field, value)

        db.commit()
        db.refresh(promo)
        return promo

    def soft_delete(self, db: Session, promo: Promo) -> None:
        promo.is_deleted = True
        db.commit()
