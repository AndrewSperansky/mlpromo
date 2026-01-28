1️⃣ ОФИЦИАЛЬНАЯ DATA CONTRACT СПЕЦИФИКАЦИЯ

Promo-ML Industrial Data Contract v1.0

1.1. Назначение документа

Data Contract определяет:

что именно передаётся из 1С

в каком виде

кто владелец данных

где проходит граница ответственности

какие данные используются для обучения и прогнозов

Контракт обязателен для:

1С

Promo-ML

Data Engineering

ML

1.2. Уровни данных (строго!)
L0 — RAW (as is from 1C)
L1 — CORE (canonical business truth)
L2 — FEATURE (ML-ready)
L3 — INFERENCE (online)


❗ Запрещено:

обучать модель на L0

делать inference напрямую из L0

считать бизнес-логику в 1С для ML

1.3. Каноническая гранулярность (grain)

1 строка = 1 день × 1 SKU × 1 промо × (регион / магазин)

Фиксируется навсегда.

1.4. CORE TRAINING DATASET

promo_ml_training_daily

🔑 Идентификаторы (обязательные)
Поле	Тип	Источник	Описание
promo_id	string	1С	GUID промо
promo_number	string	1С	Номер промо
sku_id	string	1С	GUID SKU
region_id	string	1С	Регион
store_id	string	1С	Магазин (nullable)
📅 Временная ось
Поле	Тип
date	date
week_number	int
day_of_week	int (1–7)
promo_day_index	int
promo_duration_days	int
💰 Цены и экономика
Поле	Тип
regular_price	numeric
promo_price	numeric
purchase_price_before	numeric
purchase_price_promo	numeric
percent_price_drop	numeric
📦 Ассортимент и логистика
Поле	Тип
assortment_quant	int
num_stores_in_promo	int
lead_time_days	int
📣 Механика и маркетинг
Поле	Тип
promo_mechanics	enum
marketing_carrier	string
marketing_material	string
promo_budget_local	numeric
📊 История и контекст
Поле	Тип
hist_sales_promo	numeric
current_regular_volume	numeric
previous_promo_effect	numeric
is_new_sku	boolean
sku_analog	string
prev_promo_id	string

🌦 Сезонность
Поле	Тип
season_coef_week	numeric
season_coef_day	numeric

🏪 Оперативные факторы  
Поле	Тип
store_traffic_index	       |  numeric  
store_area_m2	           | numeric  
stock_on_hand_at_start	   | numeric  
out_of_stock_flag	       | boolean  
competitor_price	       | numeric  

🎯 Целевая переменная  
Поле	Тип
sales_qty_fact	numeric
🧾 Метаданные (обязательно!)
Поле	Тип
record_created_by	string
record_created_ts	timestamp
1.5. INFERENCE DATA CONTRACT (1С → Promo-ML)

Минимальный контракт, не перегружать 1С:

{
  "request_id": "UUID",
  "promo_id": "GUID",
  "sku_id": "GUID",
  "region_id": "CODE",
  "store_id": "CODE",

  "date": "YYYY-MM-DD",

  "price": 100.0,
  "discount": 10.0,
  "avg_sales_7d": 120,
  "promo_days_left": 5
}

2️⃣ ER-ДИАГРАММА (ASCII)
┌──────────────┐  
│ promo        │  
│──────────────│  
│ promo_id PK  │  
│ promo_number │  
│ start_date   │  
│ end_date     │  
└─────┬────────┘  
      │
      │
┌─────▼────────┐
│ promo_pos    │
│──────────────│
│ promo_id FK  │
│ sku_id FK    │
│ region_id    │
│ store_id     │
└─────┬────────┘
      │
      │
┌─────▼──────────────┐
│ promo_ml_training  │
│ _daily             │
│────────────────────│
│ promo_id           │
│ sku_id             │
│ date               │
│ prices, mechanics  │
│ seasonality        │
│ sales_qty_fact     │
└────────┬───────────┘
         │
         │
┌────────▼──────────┐
│ feature_view_v1   │
│───────────────────│
│ engineered feats  │
└────────┬──────────┘
         │
         │
┌────────▼──────────┐
│ ml_model          │
│───────────────────│
│ model_id          │
│ version           │
└────────┬──────────┘
         │
         │
┌────────▼──────────────┐
│ ml_prediction_request │
│───────────────────────│
│ request_id            │
│ payload (jsonb)       │
└────────┬──────────────┘
         │
         │
┌────────▼──────────────┐
│ ml_prediction_result  │
│───────────────────────│
│ prediction            │
│ shap_values           │
│ model_version         │
└───────────────────────┘