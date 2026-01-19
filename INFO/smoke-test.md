✅ 1. Health
curl http://localhost:8000/api/v1/system/health


✔ OK

✅ 2. Dataset
curl http://localhost:8000/api/v1/dataset | jq '.count'


✔ число > 0

✅ 3. Predict (КЛЮЧЕВОЕ)
curl -X POST http://localhost:8000/api/v1/ml/predict \
  -H "Content-Type: application/json" \
  -d '{
    "prediction_date": "2025-01-15",
    "price": 100,
    "discount": 10,
    "avg_sales_7d": 120,
    "promo_days_left": 5,
    "promo_code": "PROMO_TEST",
    "sku": "SKU_TEST"
  }'

✔ ОЖИДАЕМ:
{
  "promo_code": "PROMO_TEST",
  "sku": "SKU_TEST",
  "date": "2025-01-15",
  "prediction": 120.0,
  "model_id": "dummy-model",
  "version": "dev",
  "trained_at": "...",
  "features": {...},
  "fallback_used": true
}

✅ 4. SHAP
curl http://localhost:8000/api/v1/ml/shap/sample

✅ 5. Calculator
curl http://localhost:8000/api/v1/calculator/test

✅ 6. Routes snapshot
curl http://localhost:8000/routes


Фиксируем как Stage 1 API Surface.