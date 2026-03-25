# app/controllers/model_evaluation_controller.py

import logging
import numpy as np
from sqlalchemy.orm import Session
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from models.ml_model import MLModel
from app.ml.predictor import Predictor
from app.ml.train.train_pipeline import load_full_dataset

logger = logging.getLogger(__name__)


class ModelEvaluationController:

    def evaluate_model(
        self,
        model_id: int,
        db: Session
    ) -> dict:
        """
        Оценивает модель на ВСЁМ датасете.
        """
        # 1. Найти модель
        model_record = db.get(MLModel, model_id)
        if not model_record or model_record.is_deleted:
            raise ValueError("Model not found")

        # 2. Загрузить датасет
        df = load_full_dataset(db)
        if df.empty:
            raise ValueError("Dataset is empty")

        # 3. Проверить целевую колонку
        target = model_record.target
        if target not in df.columns:
            raise ValueError(f"Target column '{target}' not found in dataset")

        # 4. Проверить фичи
        features = model_record.features or []
        missing = set(features) - set(df.columns)
        if missing:
            raise ValueError(f"Missing features: {missing}")

        # 5. Подготовить данные
        X = df[features]
        y_true = df[target]

        # 6. Удалить NaN
        X_clean = X.dropna()
        y_clean = y_true[X_clean.index]

        if len(X_clean) == 0:
            raise ValueError("All rows contain NaN values")

        # 7. Загрузить модель
        predictor = Predictor()
        # 🔥 model_record уже проверен на None выше
        if not predictor.load_by_id(model_record):  # type: ignore
            raise ValueError("Failed to load model file")

        # 8. Предсказания
        y_pred = predictor.predict(X_clean, collect_metrics=False)

        # 9. Метрики
        rmse = float(mean_squared_error(y_clean, y_pred, squared=False))
        mae = float(mean_absolute_error(y_clean, y_pred))
        r2 = float(r2_score(y_clean, y_pred))
        mape = float(np.mean(np.abs((y_clean - y_pred) / (y_clean + 1e-10))) * 100)

        metrics = {
            "rmse": round(rmse, 4),
            "mae": round(mae, 4),
            "r2": round(r2, 4),
            "mape": round(mape, 2)
        }

        logger.info(f"Model {model_id} evaluated: {metrics}, rows={len(y_clean)}")

        return {
            "model_id": model_id,
            "rows_evaluated": len(y_clean),
            "metrics": metrics
        }