# Promo-ML — Technology Stack

**Snapshot:** 2026-11-10  
**Project status:** Infrastructure Blocked / Development Paused

## 1. Purpose

Promo-ML is a machine learning platform for predicting the effectiveness of retail promotional campaigns.

The primary regression target is:

`k_uplift = PromoSales / RegularSales`

The current production-oriented baseline uses CatBoost regression.

## 2. Technology stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend | Python, FastAPI, Uvicorn | REST API and ML orchestration |
| ORM / Database access | SQLAlchemy, psycopg2 | PostgreSQL integration |
| ML regression | CatBoost 1.2.5 | Promotional uplift prediction |
| Data processing | Pandas 2.1.4, NumPy 1.26.4 | Dataset preparation |
| ML utilities | scikit-learn 1.5.2, SciPy 1.11.4 | Splitting and metrics |
| Explainability | SHAP 0.45.x | Feature attribution |
| Neural networks | PyTorch 2.x | LSTM direction; integration status requires verification |
| Frontend | Vue 3, TypeScript, Bootstrap, Chart.js | ML management interface |
| Database | PostgreSQL 15 | Datasets and model metadata |
| Cache | Redis | Runtime infrastructure |
| Reverse proxy | Nginx | HTTP routing |
| Monitoring | Prometheus, Grafana | Operational metrics |
| Logging | Loki, Promtail | Log aggregation |
| Containers | Docker, Docker Compose | Deployment and isolation |
| Authentication | JWT, bcrypt | API security |
| Testing | pytest, pytest-asyncio | Python testing |

Version information comes from the available dependency manifest and project README. Actual installed versions may differ and must be verified against the deployed environment.

## 3. Main components

- Dataset Management
- Training Pipeline
- Model Registry
- Model Promotion and Rollback
- Model Lineage
- Prediction Pipeline
- Statistical Metrics
- Conformal Prediction
- SHAP Explainability
- Frontend ML Dashboard
- Monitoring and Logging

## 4. Existing deployment

The observed environment includes:

- `promo_ml_backend`
- `promo_ml_frontend`
- `promo_postgres`
- `promo_redis`
- `promo_nginx`
- `promo_prometheus`
- `promo_grafana`
- `promo_loki`
- `promo_promtail`
- Exporter containers

## 5. Infrastructure limitation

Full-dataset training against 1,038,784 records causes the backend to become unhealthy.

A diagnostic run with 10,000 records completed successfully.

The exact failure mechanism is not yet established.

## 6. Technology evolution

The intended evolution includes:

- Reliable full-volume training
- Isolated training execution where justified
- Hybrid LSTM + CatBoost forecasting
- Contextual and temporal feature engineering
- Better model validation and uncertainty estimation
- Production-grade monitoring and reproducibility

New services must not be introduced before checking whether the existing repository already provides equivalent functionality.