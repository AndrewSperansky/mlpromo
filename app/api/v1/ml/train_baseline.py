# app/api/v1/ml/train_baseline.py   (c логикой time-based split)
# файл нигде не используется VOID

import pandas as pd
from pathlib import Path


from catboost import CatBoostRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sqlalchemy.orm import Session
from sqlalchemy import update

from app.api.v1.ml.dataset import load_dataset
from app.db.session import SessionLocal
from models.ml_model import MLModel
from app.core.settings import settings

from app.ml.runtime_state import ML_RUNTIME_STATE



FEATURES = [
    "price",
    "discount",
    "avg_sales_7d",
    "promo_days_left",
]

TARGET = "target_sales_qty"

# функции PANDA
def time_train_val_split(df: pd.DataFrame, val_days: int = 4):
    df["date"] = pd.to_datetime(df["date"])
    max_date = df["date"].max()
    split_date = max_date - pd.Timedelta(days=val_days)

    train_df = df[df["date"] <= split_date]
    val_df = df[df["date"] > split_date]

    return train_df, val_df


def train() -> dict:
    df = load_dataset(limit=10_000)

    train_df, val_df = time_train_val_split(df, val_days=4)

    x_train = train_df[FEATURES]
    y_train = train_df[TARGET]

    x_val = val_df[FEATURES]
    y_val = val_df[TARGET]

    model = CatBoostRegressor(
        iterations=300,
        learning_rate=0.1,
        depth=6,
        loss_function="RMSE",
        random_seed=42,
        verbose=50,
    )

    model.fit(
        x_train,
        y_train,
        eval_set=(x_val, y_val),
        use_best_model=True,
    )

    preds = model.predict(x_val)

    rmse = mean_squared_error(y_val, preds, squared=False)
    mae = mean_absolute_error(y_val, preds)

    print(f"📊 Validation RMSE: {rmse:.2f}")
    print(f"📊 Validation MAE: {mae:.2f}")

    model_id = ML_RUNTIME_STATE.get("ml_model_id", "baseline_catboost")
    model_path = Path(settings.ML_MODEL_DIR) / f"{model_id}.cbm"

    model_path.parent.mkdir(parents=True, exist_ok=True)


    # 🔒 ML FILE CONTRACT
    model.save_model(str(model_path), format="cbm")  # ВАЖНО: format="cbm"

    print(f"✅ Model saved to {model_path}")

    return {
        "rmse": rmse,
        "mae": mae,
        "model_path": str(model_path),
    }


def register_model(
    db: Session,
    *,
    name: str,
    algorithm: str,
    version: str,
    model_type: str,
    target: str,
    model_path: str,
    features: list[str],
    metrics: dict | None = None,
    ):

    # деактивируем старые модели с таким же именем
    db.execute(
        update(MLModel)
        .where(MLModel.name == name)
        .values(is_active=False)
    )

    ml_model = MLModel(
        name=name,
        algorithm=algorithm,
        version=version,
        model_type=model_type,
        target=target,
        features=features,
        metrics=metrics,
        model_path=model_path,
        is_active=True,
    )

    db.add(ml_model)
    db.commit()
    db.refresh(ml_model)

    return ml_model

if __name__ == "__main__":
    training_metrics = train()

    session = SessionLocal()

    try:
        register_model(
            db=session,
            name="baseline_catboost",
            algorithm="catboost",
            version="v1",
            model_type="regression",
            target="sales_qty",
            model_path=training_metrics["model_path"],
            features=FEATURES,
            metrics=training_metrics,
        )
        print("✅ Model registered in ml_model")
    finally:
        session.close()


