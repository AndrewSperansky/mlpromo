# app/api/v1/shap.py
# VOID

from fastapi import APIRouter
router = APIRouter()
@router.get('/shap/sample')
def shap_sample():
    return {'shap':[{'feature':'DiscountPercent','effect':32.1}]}
