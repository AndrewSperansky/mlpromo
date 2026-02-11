# app/ml/predictor.py

import time

from app.ml.monitoring.inference_metrics import collect_inference_metrics

def predict(self, X):

    start = time.perf_counter()

    preds = self.model.predict(X)

    latency_ms = (time.perf_counter() - start) * 1000

    collect_inference_metrics(
        ml_model_id=self.meta["ml_model_id"],
        inputs=X,
        outputs=preds,
        latency_ms=latency_ms,
    )

    return preds

