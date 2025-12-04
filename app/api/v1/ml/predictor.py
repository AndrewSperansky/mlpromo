def predict_from_features(features: dict, model=None):
    return {"forecast_total": 100.0, "baseline": 80.0, "uplift": 20.0}


def predict_with_shap(payload, model):
    return {"forecast_total": 100.0, "baseline": 80.0, "uplift": 20.0}
