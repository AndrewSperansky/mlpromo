# Promo-ML Project (VS Code)

This is a ready-to-use skeleton for the PROMO forecasting ML service.
Structure includes FastAPI app, ML module, Docker and postgres compose.
Use this package as the starting point — fill with your code and models.

## Dependency management

- Docker does NOT resolve Python dependencies
- All dependencies must be prebuilt as wheels
- Source of truth: requirements/*.txt
- Runtime source: offline_wheels/

Workflow:
1. Edit requirements/*.txt
2. Build wheels on host
3. Rebuild Docker image

- requirements = спецификация
- offline_wheels = артефакт
- Docker = тупо runtime

🧾 Зафиксируем ML File Contract (как документ)
ML FILE CONTRACT v1

1. Model type: CatBoost
2. Model format: .cbm
3. Save: CatBoostRegressor.save_model(format="cbm")
4. Load: CatBoostRegressor.load_model()
5. joblib — ЗАПРЕЩЁН для CatBoost
6. Path → всегда str()