Feature Registry v1
Feature Registry = единый источник истины для признаков
(обучение, inference, backtesting)
________________________________________
📁 Структура  
features/  
 ├── core/  
 │     ├── price.yaml  
 │     ├── discount.yaml  
 │     ├── avg_sales_7d.yaml  
 │     └── promo_days_left.yaml  
 ├── derived/  
 │      ├── percent_price_drop.yaml  
 │      └── promo_day_index.yaml    
 └── targets/    
         └── sales_qty_fact.yaml    
________________________________________
📄 Пример feature-spec
name: avg_sales_7d
type: float
source: 1C
entity: sku_id
description: Средние продажи за 7 дней
nullable: false
default: 0
validation:
  min: 0
used_in:
  - training
  - inference
________________________________________
🧩 Принципы
•	🔁 Одинаковая логика для train / inference
•	🧪 Feature = атомарная единица
•	❌ Никакой бизнес-логики в коде модели
•	✅ Версионирование признаков
