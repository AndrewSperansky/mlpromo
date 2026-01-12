# app/api/v1/ml/train_baseline.py   (c логикой time-based split)
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
from pathlib import Path
from sqlalchemy.orm import Session

from app.api.v1.ml.dataset import load_dataset
from models import MLModel

MODEL_PATH = Path("models/baseline_catboost.pkl")

FEATURES = [
    "price",
    "discount",
    "avg_sales_7d",
    "promo_days_left",
]

TARGET = "target_sales_qty"


def time_train_val_split(df: pd.DataFrame, val_days: int = 4):
    df["date"] = pd.to_datetime(df["date"])
    max_date = df["date"].max()
    split_date = max_date - pd.Timedelta(days=val_days)

    train_df = df[df["date"] <= split_date]
    val_df = df[df["date"] > split_date]

    return train_df, val_df


def train():
    df = load_dataset(limit=10_000)

    train_df, val_df = time_train_val_split(df, val_days=4)

    X_train = train_df[FEATURES]
    y_train = train_df[TARGET]

    X_val = val_df[FEATURES]
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
        X_train,
        y_train,
        eval_set=(X_val, y_val),
        use_best_model=True,
    )

    preds = model.predict(X_val)

    rmse = mean_squared_error(y_val, preds, squared=False)
    mae = mean_absolute_error(y_val, preds)

    print(f"📊 Validation RMSE: {rmse:.2f}")
    print(f"📊 Validation MAE: {mae:.2f}")

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    print(f"✅ Model saved to {MODEL_PATH}")

def register_model(
    db: Session,
    *,
    name: str,
    version: str,
    model_type: str,
    model_path: str,
    features: list[str],
    metrics: dict | None = None,
    ):
    # deactivate old
    db.query(MLModel).filter(
        MLModel.name == name,
        MLModel.is_active == True,
    ).update({"is_active": False})

    model = MLModel(
        name=name,
        version=version,
        model_type=model_type,
        target="sales_qty",
        features=features,
        metrics=metrics,
        model_path=model_path,
        is_active=True,
    )

    db.add(model)
    db.commit()



if __name__ == "__main__":
    train()
