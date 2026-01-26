# ML API Contract (Stage 2)

Документ фиксирует **внешний контракт** между системой **1С** и сервисом **promo-ml**.
Контракт считается стабильным в рамках Stage 2.

---

## 1. Общие принципы

- Контракт **строго JSON**
- Только **плоские поля** (без вложенных структур во входе)
- Все ответы **HTTP 200**, ошибки сигнализируются через `fallback_used`
- 1С **не обрабатывает исключения**, только анализирует тело ответа
- Версия контракта: **ml-predict.v1**

---

## 2. Endpoint

```
POST /api/v1/ml/predict
```

Content-Type:
```
application/json
```

---

## 3. Контракт запроса (Request)

### Формат

```json
{
  "prediction_date": "2025-01-15",
  "promo_code": "PROMO_123",
  "sku": "SKU_456",

  "price": 100.0,
  "discount": 10.0,
  "avg_sales_7d": 120.0,
  "promo_days_left": 5
}
```

### Поля

| Поле | Тип | Обязательное | Описание |
|---|---|---|---|
| prediction_date | string (YYYY-MM-DD) | да | Дата прогноза |
| promo_code | string | да | Код промо-акции |
| sku | string | да | SKU товара |
| price | number | да | Цена |
| discount | number | да | Скидка (%) |
| avg_sales_7d | number | да | Средние продажи за 7 дней |
| promo_days_left | integer | да | Осталось дней промо |

---

## 4. Контракт ответа (Response)

### 4.1 Успешный ответ

```json
{
  "promo_code": "PROMO_123",
  "sku": "SKU_456",
  "date": "2025-01-15",

  "prediction": 134.7,

  "model_id": "cb_v1",
  "version": "stage2",
  "trained_at": "2026-01-20T08:11:45Z",

  "features": {
    "price": 100.0,
    "discount": 10.0,
    "avg_sales_7d": 120.0,
    "promo_days_left": 5
  },

  "fallback_used": false,
  "shap": [
    {"feature": "discount", "effect": 12.4},
    {"feature": "price", "effect": -3.1}
  ]
}
```

---

### 4.2 Деградированный ответ (fallback)

```json
{
  "promo_code": "PROMO_123",
  "sku": "SKU_456",
  "date": "2025-01-15",

  "prediction": null,

  "model_id": "unknown",
  "version": "stage1",
  "trained_at": "2026-01-20T08:11:45Z",

  "features": null,

  "fallback_used": true,
  "reason": "ml_contract_degraded",
  "shap": []
}
```

---

## 5. Семантика fallback

Поле `fallback_used = true` означает, что:

- модель недоступна
- контракт нарушен
- признаки некорректны

В этом случае поле `prediction` всегда равно `null`.

1С **НЕ должна** считать это ошибкой интеграции.

---

## 6. Гарантии совместимости

- Stage 2: контракт **не меняется**
- Новые поля могут добавляться **только как optional**
- Удаление / переименование полей запрещено

---

## 7. Контакт

Ответственный за контракт: promo-ml service

