# app/ml/runtime_state.py

ML_RUNTIME_STATE = {
    "checked": False,
    "status": "unknown",

    "model_loaded": False,
    "ml_model_id": None,
    "version": None,
    "feature_order": None,

    "checksum_verified": False,

    "errors": [],
    "warnings": [],
}
