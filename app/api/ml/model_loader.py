import os
def load_model(path=None):
    path = path or os.getenv('MODEL_PATH','app/ml/model_catboost.cbm')
    if os.path.exists(path):
        return path
    return None
