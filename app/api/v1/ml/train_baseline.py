import joblib
from pathlib import Path

# from catboost import CatBoostRegressor
from sklearn.linear_model import LinearRegression

from sklearn.model_selection import train_test_split

from app.api.v1.ml.dataset import load_dataset


MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)

MODEL_PATH = MODEL_DIR / "baseline_catboost.pkl"


def train():
    df = load_dataset()

    target = "target_sales_qty"

    features = [
        "price",
        "discount",
        "avg_sales_7d",
        "avg_discount_7d",
        "promo_days_left",
    ]

    X = df[features]
    y = df[target]

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # model = CatBoostRegressor(
    #     iterations=200,
    #     learning_rate=0.1,
    #     depth=6,
    #     loss_function="RMSE",
    #     verbose=False,
    # )

    model = LinearRegression()      # just for a smoke-test

    model.fit(X_train, y_train)

    joblib.dump(model, MODEL_PATH)

    print(f"✅ Model saved to {MODEL_PATH}")


if __name__ == "__main__":
    train()


# =========== Запуск =================
# python -m app.ml.train_baseline
# ====================================