#!/usr/bin/env bash
set -e

BASE_URL="http://localhost:8000"

echo "== Health =="
curl -sf $BASE_URL/health
echo -e "\n"

echo "== System health =="
curl -sf $BASE_URL/api/v1/system/health
echo -e "\n"

echo "== ML model status =="
curl -sf $BASE_URL/api/v1/ml/model-status
echo -e "\n"

echo "== ML predict =="
curl -sf -X POST $BASE_URL/api/v1/ml/predict \
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
echo -e "\n"

echo "SMOKE TEST OK"


# ЗАПУСК
# Дать права на исполнение
# chmod +x scripts/smoke_test.sh
# выполнение
# ./scripts/smoke_test.sh