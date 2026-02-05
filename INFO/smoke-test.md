✅ 1. Health
curl http://localhost:8000/api/v1/system/health


✔ OK

✅ 2. Dataset
curl http://localhost:8000/api/v1/ml/dataset | jq '.count'

{
  "count": 28,
  "items": [
    {
      "date": "2025-01-01",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "CHEESE_200G",
      "price": 127.4,
      "discount": 12.5,
      "target_sales_qty": 60,
      "avg_sales_7d": 60,
      "avg_discount_7d": 12.5,
      "promo_days_left": 30
    },
    {
      "date": "2025-01-01",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "MILK_1L",
      "price": 69.9,
      "discount": 10,
      "target_sales_qty": 120,
      "avg_sales_7d": 120,
      "avg_discount_7d": 10,
      "promo_days_left": 30
    },
    {
      "date": "2025-01-02",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "CHEESE_200G",
      "price": 126.9,
      "discount": 13,
      "target_sales_qty": 63,
      "avg_sales_7d": 61.5,
      "avg_discount_7d": 12.75,
      "promo_days_left": 29
    },
    {
      "date": "2025-01-02",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "MILK_1L",
      "price": 69.4,
      "discount": 10.5,
      "target_sales_qty": 123,
      "avg_sales_7d": 121.5,
      "avg_discount_7d": 10.25,
      "promo_days_left": 29
    },
    {
      "date": "2025-01-03",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "CHEESE_200G",
      "price": 126.4,
      "discount": 13.5,
      "target_sales_qty": 66,
      "avg_sales_7d": 63,
      "avg_discount_7d": 13,
      "promo_days_left": 28
    },
    {
      "date": "2025-01-03",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "MILK_1L",
      "price": 68.9,
      "discount": 11,
      "target_sales_qty": 126,
      "avg_sales_7d": 123,
      "avg_discount_7d": 10.5,
      "promo_days_left": 28
    },
    {
      "date": "2025-01-04",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "CHEESE_200G",
      "price": 127.4,
      "discount": 12.5,
      "target_sales_qty": 69,
      "avg_sales_7d": 64.5,
      "avg_discount_7d": 12.875,
      "promo_days_left": 27
    },
    {
      "date": "2025-01-04",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "MILK_1L",
      "price": 69.9,
      "discount": 10,
      "target_sales_qty": 129,
      "avg_sales_7d": 124.5,
      "avg_discount_7d": 10.375,
      "promo_days_left": 27
    },
    {
      "date": "2025-01-05",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "CHEESE_200G",
      "price": 126.9,
      "discount": 13,
      "target_sales_qty": 72,
      "avg_sales_7d": 66,
      "avg_discount_7d": 12.9,
      "promo_days_left": 26
    },
    {
      "date": "2025-01-05",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "MILK_1L",
      "price": 69.4,
      "discount": 10.5,
      "target_sales_qty": 132,
      "avg_sales_7d": 126,
      "avg_discount_7d": 10.4,
      "promo_days_left": 26
    },
    {
      "date": "2025-01-06",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "CHEESE_200G",
      "price": 126.4,
      "discount": 13.5,
      "target_sales_qty": 75,
      "avg_sales_7d": 67.5,
      "avg_discount_7d": 13,
      "promo_days_left": 25
    },
    {
      "date": "2025-01-06",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "MILK_1L",
      "price": 68.9,
      "discount": 11,
      "target_sales_qty": 135,
      "avg_sales_7d": 127.5,
      "avg_discount_7d": 10.5,
      "promo_days_left": 25
    },
    {
      "date": "2025-01-07",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "CHEESE_200G",
      "price": 127.4,
      "discount": 12.5,
      "target_sales_qty": 78,
      "avg_sales_7d": 69,
      "avg_discount_7d": 12.9285714285714,
      "promo_days_left": 24
    },
    {
      "date": "2025-01-07",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "MILK_1L",
      "price": 69.9,
      "discount": 10,
      "target_sales_qty": 138,
      "avg_sales_7d": 129,
      "avg_discount_7d": 10.4285714285714,
      "promo_days_left": 24
    },
    {
      "date": "2025-01-08",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "CHEESE_200G",
      "price": 126.9,
      "discount": 13,
      "target_sales_qty": 81,
      "avg_sales_7d": 72,
      "avg_discount_7d": 13,
      "promo_days_left": 23
    },
    {
      "date": "2025-01-08",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "MILK_1L",
      "price": 69.4,
      "discount": 10.5,
      "target_sales_qty": 141,
      "avg_sales_7d": 132,
      "avg_discount_7d": 10.5,
      "promo_days_left": 23
    },
    {
      "date": "2025-01-09",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "CHEESE_200G",
      "price": 126.4,
      "discount": 13.5,
      "target_sales_qty": 84,
      "avg_sales_7d": 75,
      "avg_discount_7d": 13.0714285714286,
      "promo_days_left": 22
    },
    {
      "date": "2025-01-09",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "MILK_1L",
      "price": 68.9,
      "discount": 11,
      "target_sales_qty": 144,
      "avg_sales_7d": 135,
      "avg_discount_7d": 10.5714285714286,
      "promo_days_left": 22
    },
    {
      "date": "2025-01-10",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "CHEESE_200G",
      "price": 127.4,
      "discount": 12.5,
      "target_sales_qty": 87,
      "avg_sales_7d": 78,
      "avg_discount_7d": 12.9285714285714,
      "promo_days_left": 21
    },
    {
      "date": "2025-01-10",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "MILK_1L",
      "price": 69.9,
      "discount": 10,
      "target_sales_qty": 147,
      "avg_sales_7d": 138,
      "avg_discount_7d": 10.4285714285714,
      "promo_days_left": 21
    },
    {
      "date": "2025-01-11",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "CHEESE_200G",
      "price": 126.9,
      "discount": 13,
      "target_sales_qty": 90,
      "avg_sales_7d": 81,
      "avg_discount_7d": 13,
      "promo_days_left": 20
    },
    {
      "date": "2025-01-11",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "MILK_1L",
      "price": 69.4,
      "discount": 10.5,
      "target_sales_qty": 150,
      "avg_sales_7d": 141,
      "avg_discount_7d": 10.5,
      "promo_days_left": 20
    },
    {
      "date": "2025-01-12",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "CHEESE_200G",
      "price": 126.4,
      "discount": 13.5,
      "target_sales_qty": 93,
      "avg_sales_7d": 84,
      "avg_discount_7d": 13.0714285714286,
      "promo_days_left": 19
    },
    {
      "date": "2025-01-12",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "MILK_1L",
      "price": 68.9,
      "discount": 11,
      "target_sales_qty": 153,
      "avg_sales_7d": 144,
      "avg_discount_7d": 10.5714285714286,
      "promo_days_left": 19
    },
    {
      "date": "2025-01-13",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "CHEESE_200G",
      "price": 127.4,
      "discount": 12.5,
      "target_sales_qty": 96,
      "avg_sales_7d": 87,
      "avg_discount_7d": 12.9285714285714,
      "promo_days_left": 18
    },
    {
      "date": "2025-01-13",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "MILK_1L",
      "price": 69.9,
      "discount": 10,
      "target_sales_qty": 156,
      "avg_sales_7d": 147,
      "avg_discount_7d": 10.4285714285714,
      "promo_days_left": 18
    },
    {
      "date": "2025-01-14",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "CHEESE_200G",
      "price": 126.9,
      "discount": 13,
      "target_sales_qty": 99,
      "avg_sales_7d": 90,
      "avg_discount_7d": 13,
      "promo_days_left": 17
    },
    {
      "date": "2025-01-14",
      "promo_code": "PROMO_DAIRY_JAN",
      "sku": "MILK_1L",
      "price": 69.4,
      "discount": 10.5,
      "target_sales_qty": 159,
      "avg_sales_7d": 150,
      "avg_discount_7d": 10.5,
      "promo_days_left": 17
    }
  ]
}


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

=========================================================================
  curl -X POST http://localhost:8000/api/v1/ml/1c/predict   -H "Content-Type: application/json"   -d '{
    "request_id": "33333333-3333-3333-3333-333333333341",
    "data": {
      "price": 120,
      "discount": 15,
      "avg_sales_7d": 95,
      "promo_days_left": 7
    }
  }'

{
    "request_id":"33333333-3333-3333-3333-333333333333",
    "prediction":151.81549452722453,
    "ml_model_id":"cb_promo_v1",
    "version":"stage2"
}



✅ 4. SHAP
curl http://localhost:8000/api/v1/ml/shap/sample

✅ 5. Calculator
curl http://localhost:8000/api/v1/calculator/test

✅ 6. Routes snapshot
curl http://localhost:8000/routes


Фиксируем как Stage 1 API Surface.