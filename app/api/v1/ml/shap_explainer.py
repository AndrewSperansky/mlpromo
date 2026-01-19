# app/api/v1/ml/shap_explainer.py
def explain(features: dict, model=None):
    return [{'feature':'DiscountPercent','effect':32.1}]
