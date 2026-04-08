✅ 1. Health
curl http://localhost:8000/api/v1/system/health


✔ OK

✅ 2. Dataset
curl http://localhost:8000/api/v1/ml/dataset | jq '.count'




✔ число > 0

===================================================================
✅ 3. Predict + SHAP
===================================================================
 curl -X POST http://localhost:8000/api/v1/ml/predict   -H "Content-Type: application/json"   -d '{
    "prediction_date": "2025-01-15",
    "price": 100,
    "discount": 10,
    "avg_sales_7d": 120,
    "avg_discount_7d": 8,
    "promo_days_left": 5,
    "promo_code": "PROMO_TEST",
    "sku": "SKU_TEST"
  }' | jq 

Результат:

{
  "promo_code": "PROMO_TEST",
  "sku": "SKU_TEST",
  "date": "2025-01-15",
  "prediction": 144.55821009751773,
  "baseline": null,
  "uplift": null,
  "ml_model_id": "cb_promo_v1",
  "version": "stage5",
  "trained_at": "2026-01-26T08:10:00Z",
  "features": {
    "price": 100.0,
    "discount": 10.0,
    "avg_sales_7d": 120.0,
    "avg_discount_7d": 8.0,
    "promo_days_left": 5,
    "promo_code": "PROMO_TEST",
    "sku": "SKU_TEST"
  },
  "shap": [
    {
      "feature": "price",
      "effect": 0.5926733401310543
    },
    {
      "feature": "discount",
      "effect": -2.8142934410963494
    },
    {
      "feature": "avg_sales_7d",
      "effect": -1.393764347203805
    },
    {
      "feature": "avg_discount_7d",
      "effect": -6.82642976819754
    },
    {
      "feature": "promo_days_left",
      "effect": 0.0
    },
    {
      "feature": "promo_code",
      "effect": 0.0
    },
    {
      "feature": "sku",
      "effect": 0.0
    }
  ],
  "fallback_used": false,
  "reason": null
}



=============================================================================
✅ Runtime State
=============================================================================


 curl http://localhost:8000/api/v1/system/runtime-state | jq

Результат: 

{
  "status": "ok",
  "model_loaded": true,
  "version": "stage5",
  "errors": [],
  "warnings": [],
  "last_drift_flag": false,
  "last_latency_p95": null,
  "last_decision": null,
  "last_decision_timestamp": null,
  "retrain_requested": false,
  "ml_model_id": "cb_promo_v1",
  "checked": true,
  "contract": {
    "checked": true,
    "status": "ok",
    "model_loaded": true,
    "errors": [],
    "warnings": [],
    "model_path": "/app/models/cb_promo_v1.cbm"
  },
  "feature_order": [
    "price",
    "discount",
    "avg_sales_7d",
    "avg_discount_7d",
    "promo_days_left",
    "promo_code",
    "sku"
  ]
}

==============================================================================

✅ 4. SHAP
curl http://localhost:8000/api/v1/ml/shap/sample

✅ 5. Calculator
curl http://localhost:8000/api/v1/calculator/test

✅ 6. Routes snapshot
curl http://localhost:8000/routes


Фиксируем как Stage 1 API Surface.


curl http://localhost:8000/api/v1/system/metrics

curl -s http://127.0.0.1:8000/api/v1/system/metrics | jq                                                                                                                                                
вывод:
{
  "timestamp": "2026-02-16T07:38:38.184317+00:00",
  "active_model_version": "stage2",
  "model_loaded": true,
  "drift_flag": false,
  "freeze_flag": false,
  "latency_p95_ms": null,
  "predictions_count": 0,
  "errors_count": 0
}

curl http://localhost:8000/api/v1/system/status | jq    
вывод:
{
  "status": "ok",
  "model_loaded": true,
  "active_model_version": "stage2",
  "errors": [],
  "warnings": []
}


 curl http://localhost:8000/api/v1/system/runtime-state | jq '.feature_order'

[
  "RegularPrice",
  "PromoPrice",
  "PurchasePriceBefore",
  "PurchasePricePromo",
  "PercentPriceDrop",
  "VolumeRegular",
  "HistoricalSalesPromo",
  "SalesQty_PrevModel",
  "FM_Regular",
  "FM_Promo",
  "TurnoverBefore",
  "TurnoverPromo",
  "SeasonCoef_Week",
  "ManualCoefficientFlag",
  "IsNewSKU",
  "IsAnalogSKU"
]

(base) asper@00000-WS2:/mnt/d/PycharmProjects/promo-ml$ curl http://localhost:8000/api/v1/system/runtime-state | jq '.ml_model_id'

42


curl -N -X POST "http://localhost:8000/api/v1/ml/dataset/stream"   -H "Content-Type: application/x-ndjson"   --data-binary @data/test_real_record.ndjson | jq .
 

curl http://localhost:8000/api/v1/ml/dataset/stats | jq