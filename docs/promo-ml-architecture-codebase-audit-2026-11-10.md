# Promo-ML — Architecture & Implementation Audit

**Date:** 2026-11-10
**Mode:** Read-only analysis (no code, config, DB, model, or dataset changes)
**Authorized report path:** `docs/promo-ml-architecture-codebase-audit-2026-11-10.md`

---

## 1. Executive Summary

Promo-ML is a FastAPI + Vue 3 platform for **promotional uplift regression** whose primary model is a **CatBoost regressor** targeting `k_uplift = PromoSales / RegularSales`. The repository is a functional prototype that successfully trained a 10,000-row diagnostic model (Model ID 29), but is **suspended by a P0 infrastructure blocker** (ADR-0002): full-dataset training (~1,038,784 rows) made the backend container unhealthy while PostgreSQL and Redis stayed healthy.

Key verified conclusions from this audit:

1. **CatBoost pipeline is real and executable** — `train_pipeline()` in `app/ml/train/train_pipeline.py` implements load → feature assembly (14 features) → random split → train → metrics → conformal → registry → SHAP → optional promotion. It is **synchronous and runs inside the FastAPI process** (`POST /api/v1/ml/train`).

2. **LSTM → CatBoost integration is ABSENT at the feature level.** LSTM code (PyTorch) is present and trainable/executable, and there is a *baseline* wire that *could* source LSTM output at inference time, but the trained CatBoost model's feature schema (confirmed in `models/current/29.meta.json`) contains **no LSTM-derived feature**. `USE_LSTM` defaults to `False`. The LSTM output never enters the CatBoost feature vector. Classification: **ABSENT (feature-level)**; the surrounding plumbing is **PARTIAL**.

3. **Statistical correctness defects are confirmed in code.** The RMSE confidence interval divides the standard deviation of squared errors by √n, producing `lower = max(0, rmse − margin)`; the observed `[0.0, 3.89588]` with center `1.86103` and margin `2.03485` implies an unconstrained lower bound of **≈ −0.1738**, clamped to zero (verified in `models/current/29.meta.json`, which pairs `rmse_ci.lower = 0.0` with `rmse_ci.rmse = 1.86103`, `margin = 2.03485`). Conformal calibration is computed on **in-sample** full-dataset predictions, so reported coverage (~0.953) is not out-of-sample evidence.

4. **Root cause of the infrastructure blocker is UNKNOWN** — memory is a hypothesis only. Evidence: `pd.read_sql` full materialization (`train_pipeline.py:96`), full-data `model.predict(X)` (`:273`), full-data SHAP (`shap_utils.py:88`), and a single uvicorn worker. **No OOM event is proven**; Docker Compose dev sets `postgres` memory 1G and `redis` 512M, but **the backend service has no resource limit and no worker/queue isolation**.

5. **Lifecycle consistency defects are confirmed.** `models/current/` holds only model 29 while `models/candidate/` holds none (the promotion moved the artifact); lineage and `29.meta.json` agree that model 29 was promoted, but its `meta.json` `stage` field reads `"candidate"` (stale). The API "dataset count" (`total_rows`) is a live `COUNT(*)` while training metrics reflect the 10,000-row diagnostic sample — the exact discrepancy ADR-0003 flagged.

No code was modified. No tests, model artifacts, datasets, or containers were changed. The only repository write is this report (see §15).

---

## 2. Repository and Git Baseline

| Item | Value |
|---|---|
| Current branch | `v1.5` |
| HEAD revision | `7000eef922f1a5c68a2d0767762c38c86845066b` |
| HEAD message | `v1.5: Ammends in the docker-compose.prod.yml` |
| HEAD committed | 2026-11-09 11:22:03 +0300 |
| Working tree | Pre-existing changes (staged, not authored by this audit) |

### Pre-existing working-tree changes (preserved)

```
AM .adr/0001-training-baseline.md
AM .adr/0002-infrastructure-blocker.md
AM .adr/0003-diagnostic-sampling.md
AM .adr/0004-training-isolation.md
AM .adr/0005-hybrid-lstm-catboost.md
AM .adr/README.md
A  1c_scripts/data_set_loader.os
A  1c_scripts/get_forecast.os
 M app/ml/train/train_pipeline.py
AM docs/blocker-evidence.md
AM docs/restart-checklist.md
R  llm-wiki/... -> llm_wiki/...            (directory rename)
A  llm_wiki/raw/development-roadmap.md
A  llm_wiki/raw/implementation-status.md
A  llm_wiki/raw/technology-stack.md
A  llm_wiki/wiki/...                        (new wiki layer files)
```

The only *content* modification to `train_pipeline.py` (staged and pre-existing) is the diagnostic SQL limit commented out:

```diff
         WHERE k_uplift IS NOT NULL
+        --ORDER BY id
+        --LIMIT 10000
```

This confirms ADR-0003 was honored in source (the hardcoded limit was removed and left as documentation). The rest of the staged changes are ADRs, docs, and the `llm_wiki` rename/new files created during the 2026-11-10 handover.

### Instructions hierarchy noted

`AGENTS.md` at the repo root is the common agent contract. Note: `AGENTS.md:1.2` references the **`D:\JS_Projects\3dsonet\admin`** working directory, which **does not match this repository** (`D:\PycharmProjects\promo-ml`). This rule appears copied from a different project (3D SoNet) and is not applicable to Promo-ML; it is a documentation provenance artifact, not an implementation defect. `./SKILLS` referenced by the task does **not exist** in this repository (verified); the only local skill material is `llm_wiki/schema` (present) and a user-level Graphify skill outside the repo.

---

## 3. Architecture Inventory and Dependency Map

### 3.1 Backend (FastAPI, `app/`)

**Application entry:** `app/main.py` — lifespan loads active model from DB, runs `check_ml_contract()`, starts `ModelManager.watch()` task (self-healing worker is defined but `start()` is commented out, so only the watcher runs).

**API routers** (`app/api/v1/`):

| Router | Prefix | Responsibilities |
|---|---|---|
| `system/router.py` | `/api/v1/system` | health, status, metrics, runtime admin, freeze/retrain, Docker status |
| `ml/router.py` | `/api/v1/ml` | train, predict, predict/batch, dataset upload/stream, model CRUD, promote/activate, rollback, lineage, compare, drift |
| `ml_torch/router.py` | `/api/v1/ml/torch` | LSTM train/predict, 1C push endpoints, HITL activate/deactivate |
| `auth/router.py` | `/api/v1/auth` | login/register |

**Key services (`app/services/`):** `ml_training_service` (wraps `train_pipeline`), `ml_prediction_service` (CatBoost inference + SHAP + optional LSTM baseline), `registry_service` (promote/rollback/activate), `dataset_service`, `dataset_streaming_service`, `system_service`, and 1C-data services (`sales_fact`, `price_history`, `average_cheque`, `calendar`, `exchange_rate`).

**ML core (`app/ml/`):** `train/train_pipeline.py`, `train/shap_utils.py`, `statistical_metrics.py`, `conformal.py`, `model_loader.py`, `model_manager.py`, `predictor.py`, `feature_pipeline.py` + `feature_config.yaml`, `decision_engine.py`, `telemetry.py`, `audit_logger.py`, `runtime_state.py`; subpackages `model_registry/` (promotion/tradeoff/rollback/lineage), `monitoring/` (drift, latency, retrain, shadow), `self_healing/`.

**PyTorch / LSTM (`app/ml_torch/`):** `models/lstm.py`, `models/mlp.py`, `train/train_pipeline.py`, `train/trainer.py`, `train/trainer_with_embeddings.py`, `inference/predictor.py`, `data/dataset.py`, `data/sequence_builder.py`, `features/feature_builder.py`.

**Data access (`app/db/`, `app/models/`):** SQLAlchemy 2.0, `industrial_dataset_raw` (core table), `ml_model` (registry), `ml_prediction`, `activation_history`, `dataset_upload_history`, `user`, `user_activity`.

**Persistence dirs** (`app/core/settings.py`): `/app/models/{current,candidate,archive,history,metrics}`.

**Dependency map (execution flow):**

```
POST /api/v1/ml/train (ml/router.py:195)
  └─ MLTrainingService.train (ml_training_service.py:22)
       ├─ COUNT(*) industrial_dataset_raw   (row-count reporting, live)
       └─ train_pipeline (train_pipeline.py:107)
            ├─ load_full_dataset (pd.read_sql, no chunking)  :96
            ├─ dropna(target), fillna(categorical)           :136,:197
            ├─ train_test_split(random_state=42)             :204
            ├─ CatBoostRegressor.fit(early stopping)         :244
            ├─ model.predict(X) full data (in-sample)        :273
            ├─ StatisticalMetrics.calculate_confidence_interval :319
            ├─ ConformalPredictor fit/predict/coverage       :351-358
            ├─ ModelRegistryService.register_model           :421
            ├─ compute_shap_catboost(full X)                 :475
            ├─ decide_promotion (if promote)                 :503
            └─ comparison block for UI                       :521-593

POST /api/v1/ml/predict (ml/router.py:428)
  └─ MLPredictionService.predict (ml_prediction_service.py:221)
       ├─ contract gate (contract["status"]=="ok")           :235
       ├─ baseline: manual > LSTM (if USE_LSTM) > fallback  :272-299
       ├─ _build_feature_vector (Pool)                       :302-320
       ├─ model.predict                                      :323
       └─ CatBoost native SHAP (get_feature_importance)      :331-370
```

### 3.2 Feature schema (verified)

`train_pipeline.py:152-174` defines the training schema (14 features), confirmed identical in `models/current/29.meta.json:5-19`:

```text
numeric (4):     month, week, regular_price, promo_price
categorical (10): sku, store_id, category, region, store_location_type,
                  format_assortment, promo_mechanics, adv_carrier,
                  adv_material, marketing_type
```

`feature_config.yaml` and `feature_pipeline.py` define a parallel inference-time config that also computes `price_drop_percent` (computed feature). **Discrepancy:** `price_drop_percent` is not in the model feature list and there is no evidence it is injected during training; `feature_pipeline.py` appears disconnected from the CatBoost training path (no caller in the training pipeline). The inference path (`ml_prediction_service`) does **not** use `feature_pipeline` at all — it builds the vector directly from `feature_order`. This is dead/duplicated feature-configuration logic.

### 3.3 Frontend (Vue 3 + TypeScript, `frontend/src/`)

Pages: `Dashboard`, `Datasets`, `Models`, `ModelDetails`, `Lineage`, `Predict`, `Audit`, `RuntimeAdmin`, `Login`, `Register`, `LandingPage`. Components: `TrainModal`, `RetrainPanel`, `TrainingResultCard`, `ActivateModal`, `DeactivateModal`, `CompareModelsModal`, `LSTMTrainingChart`, `LSTMPredictForm`, `ModelTable`, `DriftCoverageChart`, etc. The training workflow is in `RetrainPanel.vue`.

### 3.4 Dataset management and versioning

- Upload: CSV (`POST /ml/dataset/upload`) and 1C stream (`POST /ml/dataset/stream`, NDJSON) via `dataset_streaming_service.py`.
- **Versioning: not implemented.** No dataset snapshot/hash/version is recorded in model metadata; lineage enrichment (`lineage.py:59-71`) only adds `parent_model_id` and `trigger`. ADR-0003 follow-up ("record training dataset version") remains open.

### 3.5 Model Registry, promotion, rollback, lineage

- Registry in PostgreSQL `ml_model`; `registry_service.py` implements `register_model`, `promote_model` (deactivate all → activate → archive old → cleanup candidate → move files), `force_promote_model`, `deactivate_model`, `validate_promotion`.
- Promotion decision gates in `promotion_policy.py` (freeze → drift → tradeoff → shadow → statistical checks).
- Rollback: two mechanisms exist — (a) DB-based rollback in `ml/router.py:252` (uses `activation_history`), and (b) file-based `rollback.py:22` (`rollback_current_to_archive`) which references `settings.ML_ARCYIVE_DIR` (a **typo**; the setting is `ML_ARCHIVE_DIR`, `settings.py:29`), so `rollback.py` would raise `AttributeError`/`PydanticUndefinedAnnotation` if executed. See §5/§9.
- Lineage: event log written to `models/history/lineage_events.json` via `record_lineage_event`.

### 3.6 Infrastructure (Docker, workers, queues, cache, observability)

- `docker-compose.yml` (dev) and `docker-compose.prod.yml`; `Dockerfile` (python:3.10-slim + CPU torch; note the `--extra-index-url .../whl/cpu` install). `docker/Dockerfile.ml`, `entrypoint.sh`, `redis.conf`, postgres/nginx/prometheus/promtail/loki/grafana configs.
- **No dedicated training worker or task queue exists.** Training runs synchronously inside the uvicorn worker. Redis is present but used only via `REDIS_URL` (no queue usage verified). `self_healing/self_healing_worker.py` exists but is **not started** (`main.py:143` `# self_healing_worker.start()`). See §5.

### 3.7 Tests and project knowledge

- `tests/smoke/*.py` (22 files), `tests/qa/*.py`, `pytest.ini` (`pythonpath=.`, `testpaths=tests`).
- Knowledge layers: `.adr/` (5 ADRs + README), `docs/` (blocker-evidence, restart-checklist), `llm_wiki/raw/` (immutable), `llm_wiki/wiki/` (derived), `INFO/` (misc diagnostics).

---

## 4. Verified Implementation Matrix

| Feature | Documentation claim (source) | Source evidence | Implementation status | Gap / note |
|---|---|---|---|---|
| CatBoost regression, target `k_uplift` | ADR-0001; README | `train_pipeline.py:34,244` | **Verified** on 10k rows | Full-volume unverified |
| 14 features (4 num + 10 cat) | ADR-0001 | `train_pipeline.py:152-171`; `29.meta.json` | **Implemented** | No LSTM feature |
| Train/val split 20%, random | ADR-0001 | `train_pipeline.py:204` | **Implemented** | Random, not temporal/grouped (§6) |
| Early stopping | ADR-0001 | `train_pipeline.py:223` | **Implemented** | `best_iteration=209` recorded |
| RMSE | README/ADR | `statistical_metrics.py:30` | **Implemented** | CI formula defective (§7) |
| 95% prediction interval (conformal) | README; ADR | `conformal.py` | **Implemented** | In-sample calibration (§7) |
| SHAP explanations | README/ADR-0001 | `shap_utils.py`; `ml_prediction_service.py:331` | **Implemented** | Full-data SHAP in training is memory-heavy (§5) |
| Model registry (candidate/active) | ADR-0003 w. "Partial" | `registry_service.py` | **Implemented / Partial** | `stage` field stale (§9) |
| Promotion policy (multi-gate) | `promotion_policy.py` | `promotion_policy.py` | **Implemented** | Gates largely inert in training path (§9) |
| Rollback | `rollback.py`; `ml/router.py:252` | both files | **Partial** | `ML_ARCYIVE_DIR` typo; two divergent mechanisms |
| LSTM (PyTorch) train/infer | `ml_torch/` | `train_pipeline.py`, `predictor.py` | **Implemented (isolated)** | Not integrated into CatBoost (§6) |
| LSTM output = CatBoost input feature | ADR-0005 ("Proposed — pending verification") | no injection point in `train_pipeline.py` | **ABSENT** | Confirmed §6 |
| Confidence vs prediction interval distinction | raw/implementation-status.md §4 | `statistical_metrics.py` | **Not distinguished correctly** | §7 |
| Dataset versioning/sampling config in metadata | ADR-0003 follow-up | `train_pipeline.py` meta block | **Absent** | `total_rows` vs `sample` mismatch (§5/§9) |
| Isolated/worker training | ADR-0004 (Proposed) | no worker; synchronous | **Absent** | §5 |

---

## 5. CatBoost Pipeline Findings

**F-5.1 (P1) — Training is synchronous inside the API worker.**
`train_pipeline()` executes in-process within `POST /api/v1/ml/train` (`ml/router.py:195` → `ml_training_service.py:50`). There is no background task, queue, or process isolation. A long-running training blocks that uvicorn worker, and the Docker healthcheck (`curl /api/v1/system/health`, `docker-compose.prod.yml:52-60`, timeout 10s) can time out while the event loop is saturated — consistent with the observed "running but unhealthy" symptom. Evidence: `docker-compose.prod.yml:33-38` (single `uvicorn ... --port 8000`, no `--workers`), `main.py:44` (`model_manager`), no worker/queue module imported in `train_pipeline.py`.

**F-5.2 (P1) — Full materialization and repeated full-data copies.** `load_full_dataset` uses `pd.read_sql(query, db.bind)` with no `chunksize` (`train_pipeline.py:96`). Then multiple full-data artifacts are allocated/held: `X`, `y`, `X_train/X_val`, `preds = model.predict(X)` (`:273`, full 1M predictions), `errors_array` negative/positive `y - preds` (`:316`), `np.random.permutation(len(y))` (`:330`), and finally SHAP over the full `X` (`shap_utils.py:78-91` returns a `(n_samples, n_features)` float matrix ≈ 1M × 15 × 8 bytes ≈ ~120 MB, plus CatBoost internal tree SHAP buffers). This is a **supported hypothesis** for memory pressure, not a confirmed OOM.

**F-5.3 (P1) — SHAP on the full dataset in every training run.** `compute_shap_catboost(model, X, ...)` computes ShapValues for the entire dataset (`train_pipeline.py:475`), and `save_full_shap=False` only skips writing the `.npy`, not the computation. CatBoost `get_feature_importance(type="ShapValues")` is O(ntrees×nrows×fdepth) and memory-intensive. For 1M rows this is a prime suspect for the health failure. Distinguish from memory-hypothesis: this is **confirmed expensive and O(n)**; whether it exceeded the container limit is **unconfirmed**.

**F-5.4 (P2) — Row-count reporting inconsistency (confirmed, ADR-0003).** `MLTrainingService.train` reports `total_rows = db.query(...).count()` of the full table (`ml_training_service.py:41`), while `train_pipeline` reports `rows_used = len(cleaned df)` (the diagnostic sample) and `meta["metrics"]["sample_size"]`. The API `TrainResponse.total_rows` therefore reflects the whole DB, not the trained sample — exactly the discrepancy documented in ADR-0003 and `raw/implementation-status.md`.

**F-5.5 (P2) — Duplicated feature logic / dead config.** `feature_pipeline.py` + `feature_config.yaml` define an inference feature contract (including computed `price_drop_percent`) that is **not used** by the CatBoost training path (`train_pipeline.py` hardcodes `FEATURES`) nor by the inference path (`ml_prediction_service.py` builds vectors directly). This is orphaned/duplicated logic with divergence risk.

**F-5.6 (P3) — Hidden coupling / in-source Russian comments.** Numerous emoji-laden Russian comments and debug `logger.info` logs (e.g. `train_pipeline.py:49-52, 539-598`) are informational but violate the AGENTS.md "English identifiers and English string literals" convention. Not a functional defect; a maintainability note.

**F-5.7 (P3) — Partial-state risk on exception.** Between registration (`register_model` commits a DB row, `:421`) and artifact writes (`meta.json`, `.cbm`, SHAP), a failure leaves a DB registration without matching artifacts (or vice versa). `save_model`/SHAP failures are not rolled back. `register_model` uses a `name+version` idempotency check (`registry_service.py:42-51`) that returns the existing row, which can alias a previously registered candidate on timestamp-collision.

---

## 6. LSTM Integration Findings

**F-6.1 (P0) — LSTM → CatBoost feature integration is ABSENT (verify).** The intended flow in ADR-0005 is `Historical Sales → LSTM → Derived Feature → CatBoost → Uplift Forecast`. Evidence that the feature does **not** exist in the CatBoost schema:

- Training feature list has only 14 features, none LSTM/LSTM-forecast related (`train_pipeline.py:152-174`).
- Active model metadata confirms the same 14 features (`models/current/29.meta.json:5-19`) — no `lstm_forecast`, `baseline`, or equivalent.
- `baseline` exists only in the *prediction request* DTO (`prediction_schema.py:39`) and is used to compute a downstream absolute prediction, but it is **not** a CatBoost feature: `_build_feature_vector`/`predict` iterate over `self.feature_order`, which excludes `baseline` (`ml_prediction_service.py:302-320`).

What exists is a **parallel, gated baseline source**: `MLPredictionService._get_lstm_baseline` (`ml_prediction_service.py:457-549`) can call `TorchPredictor.predict_for_day` to obtain a scalar `predicted_quantity`. This value, when `USE_LSTM=True`, substitutes the *baseline* field used for `prediction_absolute = k_uplift × baseline` — it is **not** fed into CatBoost.

**F-6.2 (P0) — `USE_LSTM` defaults to `False`.** `app/core/settings.py:35-38`. The HITL activate/deactivate endpoints explicitly return `"not_implemented"` when `USE_LSTM=False` (`ml_torch/router.py:573-579, 639-645`). So even the baseline-substitution path is dormant by default.

**F-6.3 (P1) — LSTM training/inference entrypoints exist and are executable.** `POST /ml/torch/train/lstm` and `/ml/torch/train/lstm/unified` (`ml_torch/router.py:58,90`) → `train_lstm_pipeline` / `train_lstm_unified` (`ml_torch/train/train_pipeline.py:27,217`); inference `/ml/torch/predict/lstm` (`router.py:129`). Model persistence: `.pt` checkpoint + `{id}.meta.json` with `model_config` (including `label_encoders`). Target: `quantity` (shifted `sales_fact.quantity`), **not** `k_uplift`. This is a distinct forecasting model, not a CatBoost feature producer.

**F-6.4 (P1) — Training/inference feature parity risk in LSTM itself.** Training numeric features in `feature_builder.py:30-39` (8: `regular_price, quantity, revenue, sales_lag_1..3, avg_weekly_sales, average_cheque`) differ from the inferred input order in `predictor.py:395-402` (6: `regular_price, sales_lag_1..3, avg_weekly_sales, average_cheque`), which omits `quantity` and `revenue` and reorders. `_prepare_input_tensors` also **repeats a single-day vector `seq_len` times** (`predictor.py:436-442`) rather than assembling a real rolling window, and `_get_sales_history` hardcodes `days >= date - interval '3 days'` for lags, so the declared `seq_len=30` is effectively filled by replication. This is a latent train/serve skew.

**F-6.5 (P2) — Temporal leakage risk.** `feature_builder` uses `LAG(quantity, n)` partitioned by `(sku_code, store_code) ORDER BY date` (`feature_builder.py:77-80`) and `train_lstm_pipeline` sets `df['target'] = df['quantity'].shift(-1)` then `random_split` for train/val (`train_lstm/train_pipeline.py:59,83`). A random split over an ordered time series leaks future information into validation; there is no temporal or grouped split.

**F-6.6 (P2) — Fallback behavior.** In the CatBoost prediction path, when `USE_LSTM=True` but no LSTM result, the code falls back to a manual baseline or `1.0` (`ml_prediction_service.py:288-291`); LSTM errors are swallowed and return `None` (`:545-547`). There is **no** schema-level fallback for a missing LSTM *feature* because no such feature exists.

**F-6.7 (P2) — Duplicate LSTM route definition.** `ml_torch/router.py` defines `POST /train/lstm` twice (`:58` and `:358`). FastAPI registers the first; the second is dead code shadowing.

**Integration classification: ABSENT (feature-level).** The executable code for a full `Historical Sales → LSTM → Derived Feature → CatBoost` chain does **not** exist. The components exist independently (LSTM train/infer, CatBoost train), and a dormant scalar-baseline substitution path exists, but the LSTM output is never a CatBoost input feature. This matches ADR-0005's own "implementation and integration require verification" status and `raw/implementation-status.md §7` ("Partial / Integration unverified").

---

## 7. Statistical Correctness Findings

**F-7.1 (P0) — RMSE CI formula is mathematically incorrect and zero-clamped (confirmed).**
`statistical_metrics.py:28-44`:

```python
squared_errors = errors ** 2
rmse = np.sqrt(np.mean(squared_errors))
std = np.std(squared_errors)          # std of SQUARED errors, not errors
n = len(squared_errors)
z = stats.norm.ppf((1 + confidence) / 2)
margin = z * (std / np.sqrt(n))       # se of squared-errors mean, not of rmse
return {"lower": float(max(0, rmse - margin)), ...}
```

The standard error of `rmse` is **not** `std(squared_errors)/√n`; the CI is computed on the wrong quantity (squared errors) and with a normal approximation that ignores the skew of squared errors. The `max(0, …)` clamp then enforces non-negativity post-hoc.

Confirmed in the artifact `models/current/29.meta.json:46-52`:
```json
"rmse_ci": { "rmse": 1.861034, "lower": 0.0, "upper": 3.895882, "margin": 2.034848 }
```
`rmse − margin = 1.861034 − 2.034848 = −0.173814`, exactly the "negative unconstrained lower bound" the task flagged (also noted in `raw/implementation-status.md:75-93`). The reported `lower = 0.0` is the clamp.

**F-7.2 (P1) — Confidence interval vs prediction interval are conflated.** The `rmse_ci` is labeled a confidence interval (for the population RMSE estimate), but it is stored alongside `coverage` and a `"95% prediction interval"` narrative (README §"Доверительные интервалы"). `calculate_prediction_interval` (`statistical_metrics.py:46-61`) computes a separate `preds ± z·std(errors)` interval. These are conceptually different quantities but are not kept distinct in the metrics/metadata; `promotion_policy.py:171-182` uses `rmse_ci` bounds (a CI on RMSE) to test model overlap, which is a category error.

**F-7.3 (P1) — Conformal calibration is not out-of-sample.** `train_pipeline.py:316` builds `errors_array = y - preds` where `preds = model.predict(X)` is the **full (including training) data** prediction (`:273`). The calibration/test split at `:330-348` is a random partition of those **in-sample** predictions. `cp.fit(y_calib, preds_calib)` therefore calibrates with scores the model already saw; the resulting `coverage ≈ 0.953` (`29.meta.json:55`) is not valid out-of-sample coverage. The independent validation holdout (`X_val`) exists but is not used for conformal calibration.

**F-7.4 (P2) — Random split, not temporal/grouped.** `train_test_split(..., random_state=42)` (`:204`) with no temporal ordering or grouping by store/SKU/time → potential leakage across the split and inflated validation RMSE.

**F-7.5 (P2) — Reported `rmse` vs CI base mismatch.** `meta["metrics"]["rmse"]` = `val_rmse_final` (hold-out RMSE, `:280`), but `rmse_ci.rmse` = 1.861034 (in-sample RMSE from `errors_array`). The UI may display the CI of a *different* quantity than the reported RMSE. Confirmed by `29.meta.json` where `rmse=1.573350` while `rmse_ci.rmse=1.861034`.

**F-7.6 (P3) — `accuracy_eps` interpretation.** `accuracy_with_tolerance(epsilon=5.0)` (`statistical_metrics.py:74-83`) counts `|err| < 5` on an uplift-ratio target (RMSE ~1.57), yielding ~0.994 — effectively a trivial threshold, not a meaningful accuracy.

Note: no replacement method is prescribed here; any correction to the CI/interval methodology (e.g., bootstrap or profile-likelihood intervals for RMSE, out-of-sample conformal) requires Architecture Center approval and an explicit discussion of the distributional assumptions.

---

## 8. Infrastructure Blocker Findings

**F-8.1 (P0) — Root cause NOT CONFIRMED.** Status per evidence:
- **CONFIRMED:** full-data training reached "Loading full dataset" then produced no completion in the available logs (`docs/blocker-evidence.md:17-26`); backend container `running` but `unhealthy`; postgres/redis healthy.
- **SUPPORTED HYPOTHESIS (memory/exhaustion):** full `pd.read_sql` (no chunking), repeated full-data allocations, full-data `model.predict`, full-data SHAP, and single-worker uvicorn are all confirmed memory- and CPU-heavy O(n) operations (§5.2, §5.3). The observed snapshot (backend mem 1.738 GiB / 2.842 GiB) is **not** a peak measurement and **does not prove OOM** (`blocker-evidence.md:36-41`).
- **UNKNOWN:** which specific stage or resource limit caused the health failure.

**F-8.2 (P1) — No training isolation; healthcheck coupling.** Training shares the uvicorn worker with HTTP serving. The Docker healthcheck curls a Django/FastAPI endpoint with a 10s timeout (`docker-compose.prod.yml:52-60`). A saturated worker causes health failures even without OOM. No queue/worker exists; Redis is unused for work dispatch; `SelfHealingWorker` not started (`main.py:143`).

**F-8.3 (P2) — Backend resource config asymmetry.** In `docker-compose.yml` (dev), `postgres` has `deploy.resources.limits.memory: 1G` (`:113-116`) and `redis` 512M (`:162-165`), `nginx` 512M/0.5 CPU (`:203-207`), loki 1G, grafana 512M. **The `backend` service has no `deploy.resources` block** (`:5-58`) — no memory/CPU limit enforced. In `docker-compose.prod.yml` the backend also has no resource limit (`:7-60`). This means the backend can consume unbounded memory and push the host/other containers into contention.

**F-8.4 (P2) — Healthcheck endpoint choice.** `/api/v1/system/health` (`system/router.py:27`) is static and does not touch DB/ML, which is good for liveness, but it runs in the same event loop; under CPU-bound synchronous training, even a trivial async handler can be starved, producing the "unhealthy but running" state. `/health` (`main.py:244`) is a duplicate bare endpoint.

**F-8.5 (P3) — Observability present but partial.** Prometheus (Instrumentator), Loki/Promtail, Grafana, and exporters are configured (`docker-compose.prod.yml`). Training-stage instrumentation (memory/time per load/transform/train/metrics/SHAP) is **absent** — this is listed as a required diagnostic in `blocker-evidence.md:66-71` and `restart-checklist.md`.

**F-8.6 (P3) — `docker-compose.backup.yml` / `docker/Dockerfile.ml`.** These exist; `Dockerfile.ml` and `docker-compose.backup.yml` were not inspected in depth beyond listing. No evidence of an ML training worker in the active compose files.

**Conclusion:** The blocker is real but un-diagnosed. The correct next step (per ADR-0002/0004) is measurement (per-stage profiling) and confirming whether OOM vs event-loop starvation vs DB-throughput is the true cause; do **not** pre-commit to a specific fix or to new infrastructure before evidence.

---

## 9. Model Lifecycle and UI Consistency

**F-9.1 (P1) — `stage` field stale after promotion.** `train_pipeline.py` writes `meta["stage"]="candidate"` initially (`:293`), and only sets `meta["stage"]="current"` inside the `if promote:` branch (`:511`). Promoted model 29's `meta.json` still shows `"stage": "candidate"` (`29.meta.json:39`) while its lineage shows a `"promoted"` event (`lineage_events.json:12-21`) and the file exists in `models/current/`. The stage is not reconciled when promotion happens via the **frontend's** manual `/models/{id}/promote` endpoint (which calls `ModelActivationController` → `registry.promote_model`, and never rewrites `meta.json` stage).

**F-9.2 (P1) — API vs UI activation discrepancy (confirmed root).** ADR-0003 and `raw/implementation-status.md §3` report that the UI showed model 29 active while the train API returned `promoted:false`/`stage:candidate`. Evidence:
- The train API defaults `promote=False` (`TrainRequest.promote` default `False`, `dataset_schema_csv.py:9`).
- The frontend `RetrainPanel.vue` calls `trainModel({promote:false})` then **separately** calls `/ml/models/{id}/promote` (or `/activate`) when metrics improved or no active model (`RetrainPanel.vue:149-196`).
- Therefore the "activated" state is established by a **second, frontend-orchestrated call**, not reflected in the train API's `promoted/stage` fields. The training response and the activation path are decoupled, producing the observed inconsistency.

**F-9.3 (P1) — `total_rows` vs `trained_rows_count` semantics.** API reports live `COUNT(*)` (`ml_training_service.py:41,102`), while the model's `trained_rows_count` = `rows_used` (10,000) and `meta.total_rows` = 10,000. UI row-count reporting for the dataset derives from the live count. Confirmed discrepancy.

**F-9.4 (P2) — Candidate directory emptied on promotion.** After promotion, `registry.promote_model` calls `_cleanup_candidate_models(keep_last=3)` (`registry_service.py:115,148`) and `_move_model_files` moves the `.cbm`/`.meta.json` to `current`. Observed state: `models/candidate/` contains only SHAP files (no `.cbm`/`.meta.json`); `models/current/` contains `29.cbm` + `29.meta.json`. This is expected cleanup, but it means the "candidate" artifact and the `stage=candidate` metadata diverge (combined with F-9.1).

**F-9.5 (P2) — Promotion gates inert in the training path.** `train_pipeline.py:503` calls `decide_promotion(candidate_metrics=..., current_metrics=...)` with `inference_metrics`, `drift_report`, and `slo_config` all `None`. In `promotion_policy.py`, the backward-compat branch (`:80-100`) short-circuits to a simple RMSE comparison **without** the statistical gates (CI overlap, uplift, coverage, accuracy, p-value at `:167-229`). Those advanced gates only run when a Decision Engine with drift/inference context invokes them (e.g., `decision_engine.py:126`), which is not part of the simple train flow. So the elaborate governance logic is effectively bypassed during ordinary training.

**F-9.6 (P2) — Two divergent rollback implementations.** `ml/router.py:252` (DB `activation_history`-based) vs `rollback.py:22` (filesystem-based) implement different semantics. `rollback.py:37` references `settings.ML_ARCYIVE_DIR` (typo), so the filesystem rollback cannot execute as-is.

**F-9.7 (P3) — Lineage vs registry consistency.** `record_lineage_event` writes to a file keyed by string `model_id`; registry uses integer primary key; `get_current_model_id()` (`lineage.py:33-56`) reads the first `.meta.json` in `current`, which is fragile with multiple files. `get_current_metrics()` (`lineage.py:91-97`) reads `metrics/training_metrics.json` (an array of iteration traces), not model metrics — an apparent semantic mismatch when used by `ml/router.py:171` (`get_current_metrics()` returned into `decide_promotion`).

---

## 10. Documentation Discrepancies

| Doc | Claim | Source vs Implementation | Verdict |
|---|---|---|---|
| README §Проект | "PyTorch модели" under "Дальнейшее развитие" | PyTorch/LSTM is implemented but not integrated | Doc understates (LSTM exists, not wired) |
| README §ML stack | no LSTM/PyTorch in table | `ml_torch/` + `torch` dependency present | Doc omission |
| README "prediction intervals ... Conformal" | 95% intervals | in-sample calibration | Doc overstates validity (see §7) |
| ADR-0001 limitation | "pd.read_sql without chunking; random split; no independent conformal calibration" | matches code | **Consistent** |
| ADR-0003 | diagnostic `LIMIT 10000` removed/commented | `train_pipeline.py` has `--LIMIT 10000` commented | **Consistent** |
| ADR-0005 | LSTM integration "not yet confirmed" | no LSTM-derived CatBoost feature | **Consistent (absent)** |
| .adr/README register | lists only ADR-0001..0004 | ADR-0005 exists but not in table | Table stale (missing ADR-0005) |
| raw/implementation-status.md §4 | CI lower bound clamped to zero, "review required" | code confirms `max(0, …)` | **Consistent** |
| raw/implementation-status.md §5 | "in-sample calibration" | code confirms | **Consistent** |
| llm_wiki/index.md | "raw/Promo-ML.md was empty" | (not re-verified here; noted as-is) | — |
| AGENTS.md §1.2 | canonical working dir `D:\JS_Projects\3dsonet\admin` | irrelevant to promo-ml | Provenance artifact |
| docs/restart-checklist.md | diagnostic checklist | no measurement has yet been performed | Un-resolved |

No direct contradiction with the accepted ADRs was found; the two open items to reconcile are (1) `.adr/README.md` missing ADR-0005, and (2) README's ML stack omitting PyTorch/LSTM while LSTM code and `torch` dependency are present.

---

## 11. Test Evidence and Limitations

**Treatment of tests in this audit:**
- No tests were **executed**, because `tests/smoke/conftest.py:15-33` registers a session-scoped **`autouse`** fixture that calls **`train_pipeline()`** (a real `pd.read_sql` against `industrial_dataset_raw` + CatBoost training + SHAP + DB registration) simply to prepare SHAP artifacts. Running the smoke suite could trigger a live full-dataset training and DB mutations against a reachable DB — a violation of the read-only scope and a repeat of the P0 risk. The test would run even for unrelated tests via `autouse`.
- `tests/smoke/test_train_pipeline.py` hardcodes `MODELS_DIR = models/_smoke` and asserts artifacts there, but (a) the pipeline now honors `settings.ML_*_DIR`, not `MODELS_DIR`; (b) `train_pipeline()` reads the real DB, not a fixture.

**Coverage boundaries observed (static):**
- `tests/smoke/` covers promotion policy, rollback, lineage, telemetry, drift, latency SLO, SHAP artifacts, audit logger (22 test modules). These are logic-level tests; no dedicated tests for `statistical_metrics.py` (CI formula), `conformal.py` (independence), LSTM feature parity, or dataset loading/streaming were observed in the smoke list.
- Unsafe test dependencies: real DB access (conftest `train_pipeline`, `SessionLocal`), real filesystem (`models/_smoke`), real model artifacts.

**Recommendation:** treat `RuntimeError`-style execution of smoke tests as requiring explicit approval; first refactor the `autouse` fixture to mock the DB/dataset or use a committed tiny fixture.

---

## 12. Prioritized Findings

| ID | Severity | Finding |
|---|---|---|
| F-6.1 | P0 | LSTM → CatBoost feature integration ABSENT (no LSTM-derived CatBoost feature) |
| F-7.1 | P0 | RMSE CI formula incorrect + zero-clamped (confirmed −0.1738 unconstrained lower bound) |
| F-8.1 | P0 | Infrastructure blocker root cause UNKNOWN (memory is hypothesis only) |
| F-5.1 | P1 | Training synchronous inside API worker (no isolation/queue) |
| F-5.2 | P1 | Full `pd.read_sql` + full-data predict + full-data SHAP allocations |
| F-5.3 | P1 | Full-dataset SHAP computed every training run (O(n) memory/CPU) |
| F-6.3 | P1 | LSTM train/infer executable but isolated (target `quantity`, not `k_uplift`) |
| F-6.4 | P1 | LSTM train/serve feature parity risk (numeric order/count mismatch, seq replication) |
| F-7.2 | P1 | CI vs prediction interval conflation |
| F-7.3 | P1 | Conformal calibration not out-of-sample |
| F-8.2 | P1 | Healthcheck coupled to worker saturation |
| F-9.1 | P1 | `stage` field stale after promotion |
| F-9.2 | P1 | API vs UI activation discrepancy (frontend orchestrates promotion post-train) |
| F-9.3 | P1 | `total_rows` vs `trained_rows_count` semantics mismatch |
| F-5.4 | P2 | Row-count reporting inconsistency (ADR-0003) |
| F-5.5 | P2 | Orphaned `feature_pipeline`/`feature_config` logic |
| F-6.5 | P2 | LSTM temporal leakage (random split on shifted target) |
| F-6.6 | P2 | LSTM fallback swallows errors / scalar 1.0 default |
| F-6.7 | P2 | Duplicate `POST /train/lstm` route |
| F-7.4 | P2 | Random (non-temporal/grouped) split for CatBoost |
| F-7.5 | P2 | `rmse` vs `rmse_ci.rmse` different quantities |
| F-8.3 | P2 | Backend has no resource limit (asymmetric with other services) |
| F-8.4 | P2 | Healthcheck endpoint / event-loop starvation |
| F-9.4 | P2 | Candidate dir emptied on promotion vs stale `stage` |
| F-9.5 | P2 | Promotion statistical gates inert in simple train flow |
| F-9.6 | P2 | Divergent rollback mechanisms + `ML_ARCYIVE_DIR` typo |
| F-5.6 | P3 | Non-English comments/logs violate convention |
| F-5.7 | P3 | Partial-state risk on training exception |
| F-7.6 | P3 | `accuracy_eps` epsilon threshold not meaningful |
| F-8.5 | P3 | No per-stage training profiling/observability |
| F-9.7 | P3 | Lineage `model_id` string vs int; `get_current_metrics` mismatch |

---

## 13. Recommendations Requiring Architecture Center Approval

These require explicit approval before implementation; they are **not** prescribed here:

1. **Training isolation strategy** (ADR-0004). Choose between optimizing the existing synchronous pipeline, extending existing infra (none found suitable), or introducing isolated training execution. Requires per-stage profiling evidence first (ADR-0002).

2. **LSTM integration contract** (ADR-0005). Define the LSTM-derived CatBoost feature name, semantic, versioning, lineage, and fallback before wiring. Confirm whether the intended architecture is "LSTM forecast as a CatBoost feature" (as currently documented) vs "LSTM only as a baseline scalar for absolute-sales scaling" (as currently gated by `USE_LSTM`). Remove or repurpose the dormant `_get_lstm_baseline` path accordingly.

3. **Statistical methodology correction.** Decide how RMSE confidence intervals should be estimated (e.g., bootstrap/profile-likelihood) and how prediction intervals (conformal, out-of-sample calibration) should be computed and reported — after discussing the underlying distributional assumptions (non-negativity, skew, heteroscedasticity). No replacement is mandated by this audit.

4. **Row-count/status contract.** Define a single source of truth for `total_rows` vs `sample_size` vs `trained_rows_count`, and reconcile `stage`/`promoted` semantics between training response and model metadata.

5. **Dataset versioning & sampling configuration.** Approve recording dataset version/hash and explicit sample configuration in model metadata (ADR-0003 follow-up).

6. **Test-safety refactor.** Approve de-coupling the `autouse` DB-training smoke fixture from mere artifact assertions before any test run is deemed safe.

---

## 14. Open Questions

1. Which stage exactly caused full-dataset backend health failure (load/transform/train/metrics/SHAP)? No per-stage measurement exists.
2. Is the failure OOM, event-loop starvation, or DB throughput? Evidence is insufficient to conclude.
3. What is the peak memory/time of CatBoost `get_feature_importance(ShapValues)` at 1M rows? Unmeasured.
4. Should the LSTM output replace the `baseline` scalar or become a genuine CatBoost feature? Unresolved (F-6.1 vs ADR-0005).
5. What is the intended feature-parity contract for LSTM `seq_len=30` given replication in `_prepare_input_tensors`? Unresolved.
6. Are the advanced promotion gates (CI-overlap, uplift, coverage, p-value) intended to run in the simple train flow? Currently bypassed (F-9.5).
7. Is `models/current` expected to contain only the active model's artifacts, or is the archive/lineage expected to retain history? Cleanup policy unclear.

---

## 15. Final Repository Change Manifest

**Verification completed:**

- No source or configuration files were modified.
- No tests, model artifacts, or datasets were changed.
- No containers were restarted.
- No training was launched.
- The only newly created file is this authorized report:
  `docs/promo-ml-architecture-codebase-audit-2026-11-10.md`

**Pre-existing working-tree changes were preserved intact** (see §2). The staged ADR/docs/wiki changes and the commented diagnostic `LIMIT` in `train_pipeline.py` are exactly as found before this audit began.

### Working-tree change made by the human (Andrey) during the audit window

While preparing the final manifest, a **new, unstaged modification** to `app/ml/model_registry/rollback.py` appeared that was **not present** in the baseline `git status` captured at the start of this audit. It was **not made by any tool call in this audit**.

```diff
-    archive_dir = Path(settings.ML_ARCYIVE_DIR)
+    archive_dir = Path(settings.ML_ARCHIVE_DIR)
```

- File mtime: 2026-11-10 13:34:00 (inside the audit window).
- Attribution: **Authored by the human (Andrey)**, not by this audit. This audit did not create, stage, or revert it.
- Effect: it fixes the `ML_ARCYIVE_DIR` typo described in F-9.6. The report's F-9.6 finding and its line reference (`rollback.py:37`) reflect the **source as read during analysis**; the current working-tree file now contains `ML_ARCHIVE_DIR`. The finding should therefore be read as "`ML_ARCYIVE_DIR` typo present at audit time, corrected by Andrey during the audit window" and is effectively **addressed**.

**This report was not committed**, in accordance with the instruction that commits require explicit request.

---

*Returned to Architecture Center (Andrey + ChatGPT) for review and FINAL ACCEPTANCE. No recommendations have been implemented.*