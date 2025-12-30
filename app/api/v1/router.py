
from fastapi import APIRouter

from app.api.v1.system.router import router as system_router
from app.api.v1.promo.router import router as promo_router
from app.api.v1.product.router import router as product_router
from app.api.v1.ml.router import router as ml_router



router = APIRouter(prefix="/api/v1")

router.include_router(system_router, prefix="/system")
router.include_router(promo_router, prefix="/promo")
router.include_router(product_router, prefix="/product")
router.include_router(ml_router)



