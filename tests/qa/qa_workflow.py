import requests
import psycopg2
from datetime import datetime
import json
import os
import sys

# ------------------------
# Настройки
# ------------------------
API_BASE = "http://localhost:8000/api/v1/ml"
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "promo",
    "user": "postgres",
    "password": "postgres"
}
MODEL_NAME = "promo_uplift"

# ------------------------
# Helper: DB connection
# ------------------------
def db_connect():
    return psycopg2.connect(**DB_CONFIG)

def fetch_models():
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, version, is_active, metrics
                FROM ml_model
                WHERE name = %s
                ORDER BY created_at DESC;
            """, (MODEL_NAME,))
            return cur.fetchall()

# ------------------------
# Check API availability
# ------------------------
def check_api():
    try:
        r = requests.get(f"{API_BASE}/models")
        if r.status_code != 200:
            print(f"Ошибка: API доступно, но возвращает {r.status_code}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Ошибка подключения к API: {e}")
        sys.exit(1)
    print("✅ API доступно")

# ------------------------
# 1️⃣ Train candidate
# ------------------------
def train_candidate(promote=False):
    print(f"\n[TRAIN] promote={promote}")
    resp = requests.post(
        f"{API_BASE}/train",
        json={"promote": promote}  # <- исправлено
    )
    data = resp.json()
    print(json.dumps(data, indent=2))
    return data

# ------------------------
# 2️⃣ Promote manually
# ------------------------
def promote_model(model_id):
    print(f"\n[PROMOTE] id={model_id}")
    resp = requests.post(f"{API_BASE}/models/{model_id}/promote")
    data = resp.json()
    print(json.dumps(data, indent=2))
    return data

# ------------------------
# 3️⃣ Predict using active model
# ------------------------
def predict(input_data):
    resp = requests.post(f"{API_BASE}/predict", json=input_data)
    print("\n[PREDICT]")
    print(json.dumps(resp.json(), indent=2))
    return resp.json()

# ------------------------
# 4️⃣ Check metrics gating / active count
# ------------------------
def check_active_count():
    models = fetch_models()
    active_count = sum(1 for m in models if m[3])
    print(f"\n[DB] Active versions: {active_count}")
    return active_count

# ------------------------
# 5️⃣ Lineage check
# ------------------------
def fetch_lineage():
    resp = requests.get(f"{API_BASE}/models/lineage")
    print("\n[LINEAGE]")
    print(json.dumps(resp.json(), indent=2))
    return resp.json()

# ------------------------
# Main QA workflow
# ------------------------
if __name__ == "__main__":
    # Проверка API
    check_api()

    # BLOCK 1: Train candidate
    candidate = train_candidate(promote=False)

    # BLOCK 2: Train with promote
    promoted = train_candidate(promote=True)

    # BLOCK 3: Manual promotion (если есть кандидат)
    models = fetch_models()
    for m in models:
        if not m[3]:
            promote_model(m[0])
            break

    # BLOCK 4: Predict
    predict(
        {
         "prediction_date": "2025-01-15",
         "price": 100,
         "discount": 5,
         "avg_discount_7d": 8,
         "avg_sales_7d": 50,
         "promo_days_left": 2,
         "promo_code": "PROMO_TEST",
         "sku": "SKU_TEST"
        }
    )

    # BLOCK 5: Metrics gating / Active versions
    active_count = check_active_count()
    assert active_count == 1, "Ошибка: больше одной active версии!"

    # BLOCK 6: SHAP / files check
    candidate_dir = "./models/_candidate"
    files = os.listdir(candidate_dir) if os.path.exists(candidate_dir) else []
    print("\n[FILES in _candidate]:", files)

    # BLOCK 7: Lineage
    fetch_lineage()

    print("\n✅ QA workflow completed")



    #  python tests/qa/qa_workflow.py