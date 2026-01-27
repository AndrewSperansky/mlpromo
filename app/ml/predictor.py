def predict_from_features(features: dict, model=None):
    """
    Deprecated mock — заменить MLPredictionService.predict
    """
    return {"forecast_total": 100.0, "baseline": 80.0, "uplift": 20.0}


def predict_with_shap(payload, model):
    """
    Deprecated mock SHAP — заменить MLPredictionService
    """
    return {"forecast_total": 100.0, "baseline": 80.0, "uplift": 20.0}
