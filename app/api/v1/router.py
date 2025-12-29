
from fastapi import APIRouter

from app.api.v1.system.router import router as system_router
from app.api.v1.promo.router import router as promo_router
from app.api.v1.product.router import router as product_router



router = APIRouter(prefix="/api/v1")

router.include_router(system_router, prefix="/system")
router.include_router(promo_router, prefix="/promo")
router.include_router(product_router, prefix="/product")

#=================================
# БЫВШИЙ health.py !!!!
#=================================
# from fastapi import APIRouter
# router = APIRouter()
# @router.get('/health')
# def health():
#     return {'status':'ok'}

# curl http://localhost:8000/api/v1/system/health
# curl http://localhost:8000/api/v1/system/health/server
# curl http://localhost:8000/api/v1/system/health/bd

