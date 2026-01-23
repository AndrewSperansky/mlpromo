from sqlalchemy.orm import Session
from app.services.promo_service import PromoService
from app.schemas.promo_schema import PromoCreate, PromoRead


class PromoController:
    def __init__(self, db: Session):
        self.service = PromoService(db)

    def create(self, data: PromoCreate) -> PromoRead:
        promo = self.service.create_promo(data)
        return PromoRead.model_validate(promo)

    def get(self, promo_id: int) -> PromoRead:
        promo = self.service.get_promo(promo_id)
        return PromoRead.model_validate(promo)


# update, delete