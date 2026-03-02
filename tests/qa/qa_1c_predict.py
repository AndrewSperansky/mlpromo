# tests/qa/qa_1c_predict.py

import pytest
import requests
from uuid import uuid4
from datetime import date

BASE_URL = "http://localhost:8000/api/v1/ml/1c/predict/"

# --- Тестовые кейсы ---
test_cases = [
    (
        "valid_request",
        {
            "request_id": str(uuid4()),
            "data": {
                "prediction_date": str(date(2025, 1, 15)),
                "price": 100,
                "discount": 10,
                "avg_sales_7d": 120,
                "avg_discount_7d": 8,
                "promo_days_left": 5,
                "promo_code": "PROMO_TEST",
                "sku": "SKU_TEST"
            }
        },
        200,
        None
    ),
    (
        "missing_fields",
        {
            "request_id": str(uuid4()),
            "data": {
                "price": 100,
                "discount": 5
            }
        },
        422,
        ["prediction_date", "avg_sales_7d", "avg_discount_7d", "promo_days_left", "promo_code", "sku"]
    )
]

@pytest.mark.parametrize("name,payload,expected_status,expected_missing", test_cases)
def test_1c_predict(name, payload, expected_status, expected_missing):
    resp = requests.post(BASE_URL, json=payload)
    assert resp.status_code == expected_status, f"[{name}] Unexpected status: {resp.status_code}"

    if expected_status == 200:
        data = resp.json()
        # Проверяем базовые поля ответа
        assert data["request_id"] == payload["request_id"]
        assert "prediction" in data
        assert isinstance(data["prediction"], (int, float))
        assert "ml_model_id" in data
        assert "version" in data
        print(f"✅ [{name}] 1C predict works")
    elif expected_status == 422:
        errors = resp.json()["detail"]
        missing_fields = [e["loc"][-1] for e in errors if e["type"] == "missing"]
        assert set(missing_fields) == set(expected_missing), f"[{name}] Unexpected missing fields: {missing_fields}"
        print(f"✅ [{name}] 1C validation catches missing fields")