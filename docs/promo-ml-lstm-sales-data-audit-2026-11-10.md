# Promo-ML — LSTM Pipeline and Historical Sales Data Audit

**Date:** 2026-11-10
**Mode:** STRICT READ-ONLY (no code, DB data/schema, model artifacts, containers, or env changes)
**Report path:** `docs/promo-ml-lstm-sales-data-audit-2026-11-10.md`
**Authoritative documents:** `.adr/0005-hybrid-lstm-catboost.md` (authority), `docs/promo-ml-architecture-codebase-audit-2026-11-10.md`, other ADRs, `llm_wiki/` materials.

---

## 1. Executive Summary

ADR-0005 defines a **prediction-level composition** architecture: LSTM independently forecasts `BaselineSales_ML` from observed historical sales; CatBoost forecasts `K_uplift`; a composition layer multiplies them into absolute promotional sales. Feature-level LSTM→CatBoost integration is **explicitly rejected** (ADR-0005 §12).

This audit establishes four things with high confidence:

1. **The LSTM pipeline exists and is executable end-to-end** (train → checkpoint → register → activate → predict), but it was built for **per-SKU forecasting of the next day's `quantity`** (`sales_fact`), and its target, feature set, splitting, and scaling are **inconsistent with the ADR-0005 baseline-forecasting role**. In particular, its training/inference feature parity is broken, and the inference path fabricates a `seq_len` window by replication.

2. **The historical sales data source is present and well-defined in the 1C extraction scripts, but is not loadable/verifiable today.** The `sales_fact` table (daily aggregation by `date × sku_code × store_code`, columns `quantity`, `revenue`, `uom`, `region`, `oblast`, `category`) is confirmed in the schema dump and in the 1C `data_set_loader.os` query — including the `HAVING SUM(СтоимостьОборот) >= 3000` revenue threshold and SKU exclusions. **There is no live PostgreSQL available in this environment**, so row counts, date range, distinct SKU/store counts, and gap/null statistics **cannot be measured**; only schema-level facts are verifiable.

3. **RegularSales_1C / `regular_sales_qty` / `historical_sales_qty_promo` / `k_uplift` semantics are defined in the 1C PROMO module** (not in Promo-ML backend code): `k_uplift = historical_sales_qty_promo / regular_sales_qty` (0 if either is 0). `regular_sales_qty` = `ПозицииПромоАкции.ТекущийРегулярныйОбъемШт` (1C's own "current regular volume" — i.e., RegularSales_1C). Promo-ML's backend only stores the resulting `k_uplift`; it never stores or recomputes the numerator/denominator. This has direct consequences for ADR-0005's requirement to independently re-derive the CatBoost uplift target (see §7).

4. **No temporal leakage proof can be completed on the LSTM data pipeline because it is not operational**, but source inspection confirms several **confirmed** leakage/parity defects (random split on a shifted target, sequence build across product/store boundaries, no scaling/normalization, and a broken inference `seq_len` path), plus **potential** risks (promotion contamination unhandled; `revenue` and `quantity` enter the feature set without promotion/missing-value semantics).

The LSTM component, as written, is **not ready** to serve as the independent `BaselineSales_ML` forecaster without redesign of its target, feature, train/serve parity, and validation strategy. This is a research-phase gap, not a defect in CatBoost.

---

## 2. Audit Scope and Sources

### 2.1 Scope
Read-only architectural research into (a) the existing PyTorch/LSTM implementation, (b) the PostgreSQL historical-sales data structures and their 1C provenance, (c) promotion-period identification, (d) RegularSales/target semantics, (e) temporal leakage, (f) baseline readiness, (g) resource risks, and (h) ADR-0005 compliance.

### 2.2 Sources inspected

| Source | Path |
|---|---|
| Authoritative ADR | `.adr/0005-hybrid-lstm-catboost.md` |
| Prior audit | `docs/promo-ml-architecture-codebase-audit-2026-11-10.md` |
| ADRs | `.adr/0001…0004`, `.adr/README.md` |
| Wiki raw | `llm_wiki/raw/development-roadmap.md`, `technology-stack.md`, `implementation-status.md`, `Promo-ML.md` (empty) |
| Wiki derived | `llm_wiki/wiki/index.md`, `concepts/training-scalability.md`, `resume/2026-11-10-training-diagnostic.md`, `log.md` |
| LSTM impl | `app/ml_torch/**` (models, data, features, train, inference, utils) |
| LSTM API | `app/api/v1/ml_torch/router.py`, `app/schemas/torch_schema.py` |
| Sales data services | `app/services/sales_fact_service.py`, `price_history_service.py`, `average_cheque_service.py`, `calendar_service.py`, `historical_data_service.py` |
| ORM/schema | `app/models/*.py`, `app/db/*.py`, `backup/schema_v1.5.sql`, `backup/schema*.sql` |
| 1C extraction | `1c_scripts/data_set_loader.os`, `1c_scripts/get_forecast.os` (UTF-8 OScript) |
| CatBoost pipeline (unchanged) | `app/ml/train/train_pipeline.py`, `app/services/ml_prediction_service.py`, `app/ml/model_registry/**` |

### 2.3 Review basis
No application code, DB, model artifacts, containers, or environment were modified. The only repository write is this report.

---

## 3. Existing LSTM Architecture

All paths are repository-relative. The LSTM stack lives under `app/ml_torch/` plus two integration points (`app/api/v1/ml_torch/router.py`, and the dormant baseline hook in `app/services/ml_prediction_service.py`).

### 3.1 Modules, classes, functions

#### Models
- **`app/ml_torch/models/base.py`** — `BaseTorchModel(nn.Module)` abstract (`forward`, `get_config`); `save()` writes `{model_state_dict, config}`; `load()` rebuilds from config.
- **`app/ml_torch/models/lstm.py`** — `LSTMUpliftModel(BaseTorchModel)`:
  - `__init__(numeric_features, categorical_dims, embedding_dim=16, hidden_size=64, num_layers=2, seq_len=30, dropout=0.2)` (`:33-78`).
  - Embeddings via `nn.ModuleDict` per categorical feature (`:54-57`); `lstm_input_size = numeric_features + len(categorical_dims)*embedding_dim` (`:61-62`).
  - `nn.LSTM(batch_first=True, dropout=…)` (`:64-70`); head `fc = Linear(hidden,32)→ReLU→Dropout→Linear(32,1)` (`:73-78`).
  - `forward(x_numeric[bs,seq,nf], x_categorical[bs,seq,nc])` returns `[bs]` — the **last timestep** hidden state through `fc` (`:80-114`).
  - `get_config`/`from_config` round-trip model shape (`:116-137`).
- **`app/ml_torch/models/mlp.py`** — `MLPUpliftModel(BaseTorchModel)`; **note:** `from ml_torch.models.base import BaseTorchModel` (`:5`) is an invalid absolute import (module is `app.ml_torch`), so this file fails import as-is. Not part of the LSTM path but a latent defect.

#### Trainer
- **`app/ml_torch/train/trainer.py`** — `TorchTrainer` (no embeddings; trains on single `X` tensor, `train_epoch`/`validate_epoch`/`train`/`save_checkpoint`/`load_checkpoint`).
- **`app/ml_torch/train/trainer_with_embeddings.py`** — `TorchTrainerWithEmbeddings` (3-tensor: numeric, categorical, target). Used by the LSTM pipelines. No checkpoint-before-rollback; `save_checkpoint("best_model.pt")` writes a literally **fixed filename** (`:78`) each time a new best val loss occurs, which collides with the per-SKU artifact naming in the pipeline (§3.7).

#### Data
- **`app/ml_torch/data/dataset.py`** — `UpliftTimeSeriesDataset(Dataset)`:
  - `_encode_categorical` uses `sklearn.preprocessing.LabelEncoder` fit on the **whole passed DataFrame** (`:49-57`).
  - `_build_sequences` builds `[i:i+seq_len] → target[i+seq_len]` windows over the DataFrame row order (`:78-81`).
- **`app/ml_torch/data/sequence_builder.py`** — `SequenceBuilder` (sliding window, multi-feature sequence, `pad_sequence`). **Not imported** by the LSTM pipelines (dead/parallel utility).

#### Features
- **`app/ml_torch/features/feature_builder.py`** — `FeatureBuilder(db)`:
  - `numeric_features = [regular_price, quantity, revenue, sales_lag_1, sales_lag_2, sales_lag_3, avg_weekly_sales, average_cheque]` (**8**) (`:30-39`).
  - `categorical_features = [sku_code, category, day_type, store_code, region, oblast]` (**6**) (`:42-49`).
  - `build_features_for_sku(sku, days)` / `build_features_for_all_skus(days)` run SQL `SELECT … FROM sales_fact s LEFT JOIN retail_price_history … calendar … average_cheque` with `LAG(quantity, k) OVER (PARTITION BY sku_code, store_code ORDER BY date)` for lags and a `WHERE s.date >= CURRENT_DATE - :days` filter (`:66-91`, `:112-142`). **Hard-coded `ORDER BY s.date` and uses `s.week` join key to `retail_price_history` / `average_cheque`** — see §3.6 and §3.7 parity findings.

#### Training entry points
- **`app/ml_torch/train/train_pipeline.py`**:
  - `train_lstm_pipeline(sku, days=365, seq_len=30, hidden_size=64, num_layers=2, embedding_dim=16, lr=0.001, batch=32, epochs=50, promote=False)` (`:27-212`).
    - target: `df['target'] = df['quantity'].shift(-1)` (`:59`).
    - split: `random_split(dataset, [0.8, 0.2])` (`:81-83`).
    - model registry `algorithm="pytorch_lstm_with_embeddings"`, `model_type="time_series"`, `target="quantity"` (`:125-134`).
    - artifact `{id}.pt` (`:139-141`); meta `{id}.meta.json` includes `model_config` with `label_encoders` (`:144-176`).
  - `train_lstm_unified(days=365, …)` (`:217-392`): same pattern for all SKUs; hard-codes numeric features to **6** (`regular_price, sales_lag_1..3, avg_weekly_sales, average_cheque`, `:256-263`) and categorical to 6 (`:247-254`); writes `lstm_training_metrics.json`.

#### Inference entry points and API
- **`app/api/v1/ml_torch/router.py`**:
  - `POST /ml/torch/train/lstm` — declared **twice** (`:58` and `:358`); the second shadows the first (dead duplicate).
  - `POST /ml/torch/train/lstm/unified` (`:90`).
  - `POST /ml/torch/predict/lstm` (`:129-215`): resolves active LSTM model, loads `model_config` from meta, then `TorchPredictor.predict_for_day` per day.
  - HITL `GET /ml/torch/status`, `POST /ml/torch/activate`, `POST /ml/torch/deactivate` (all gated by `settings.USE_LSTM`, default `False`, `:573,639`).
  - `GET /ml/torch/training/metrics` (`:682`).
  - `GET /ml/torch/compare/catboost` (`:393`).

- **`app/ml_torch/inference/predictor.py`** — `TorchPredictor(db)` (`:18`):
  - `load_model(model_path, config)` builds `LSTMUpliftModel` then `load_state_dict(…, strict=False)` (`:33-50`).
  - `predict_for_day(sku, date, store_id, …)` assembles features and calls `_prepare_input_tensors` (`:56-110`), returns `{"predicted_quantity", "interval", "confidence", …}`.
  - **`_prepare_input_tensors`** hard-codes numeric order to 6 features (`regular_price, sales_lag_1..3, avg_weekly_sales, average_cheque`) and categorical order to 6 (`sku_code, category, day_type, store_code, region, oblast`) (`:392-446`). **Repeats a single-day vector `seq_len` times** (`:440-442`) instead of building a real window.

### 3.2 Model input features
- Training (`train_lstm_unified`): **6 numeric** + **6 categorical** (`train_pipeline.py:247-263`).
- Single-SKU (`train_lstm_pipeline`): uses `feature_builder.numeric_features` (8) + `categorical_features` (6) (`feature_builder.py:30-49`).
- Inference (`predictor._prepare_input_tensors`): 6 numeric + 6 categorical.
This yields a **train/serve schema mismatch** (§5.6, §3.7).

### 3.3 Output and target
- Target = `quantity` forecast (next row's `sales_fact.quantity`), `target` column via `.shift(-1)` (`train_pipeline.py:59, 243`). **Not `k_uplift`, not `RegularSales`, and not a cleaned "regular demand" quantity** — it is raw observed quantity, which includes promotional effects.

### 3.4 Sequence length and horizon
- `seq_len` default 30 (`lstm.py` default, schema `TrainLSTMRequest.seq_len=30`). Forecast horizon is **1 step** (the single next row). The API `predict/lstm` iterates `days_ahead` calls but each call predicts one day using replicated history (§3.2).

### 3.5 Scaling and normalization
- **None.** No scaler/min-max/standardization anywhere in `ml_torch`. `regular_price`, `quantity`, `revenue`, `average_cheque` are fed raw. `avg_weekly_sales` is raw. Implication: model effectively must learn scale per SKU/store; the single-SKU vs unified variant differ in this exposure.

### 3.6 Train/validation/test split
- `random_split` (shuffle) for both pipelines (`train_pipeline.py:83, 288`). No chronological holdout, no test set, no grouped split. **Confirmed leakage risk** (§8).

### 3.7 Serialization and versioning
- Checkpoint `{id}.pt` + `{id}.meta.json` (`train_pipeline.py:139-176`). Trainer's internal `save_checkpoint("best_model.pt")` writes a fixed-name file (`trainer_with_embeddings.py:78`) never consumed by the registry path — **orphan + cross-run collision risk**.
- Registry `model_type="time_series"`, independent of CatBoost (`registry_service.get_active_lstm_model`, `model_loader._load_torch_model`). No promotion-policy application beyond manual `promote` boolean.

### 3.8 Integration with FastAPI / frontend
- Routers under `/api/v1/ml/torch/*` (`app/api/v1/router.py:16`). Frontend: `LSTMPredictForm.vue`, `LSTMTrainingChart.vue`, `Models.vue` LSTM HITL card, `Predict.vue` LSTM mode (`frontend/src/services/api.ts:368-438`). These are UI affordances only; the model feeds no composed forecast today.

### 3.9 Dormant CatBoost-side hook
- `app/services/ml_prediction_service.py:457-549` `_get_lstm_baseline(…)` returns `predicted_quantity` as a scalar **`baseline`** for `prediction_absolute` computation when `USE_LSTM=True` (`:275-299`). It is **not** a CatBoost feature and is disabled by default.

**Distinction (inference vs actual behavior):** The code files, comments, and UI exist; the actual trained LSTM models are **not present in `models/`** (only CatBoost model 29 exists). No LSTM `.pt`/`.meta.json` artifact exists in the repo (`models/current` has `29.cbm`, `29.meta.json`; `models/candidate` empty of `.pt`). So the LSTM is implemented but **never verified trained or served** in this repository state.

---

## 4. PostgreSQL Sales Data Inventory

### 4.1 Tables and views
Schema found in `backup/schema_v1.5.sql` (PostgreSQL dump). Relevant tables:

| Table | Purpose | Key/PK | Verified? |
|---|---|---|---|
| `sales_fact` | Daily sales observation | `(date, sku_code, store_code)` (`schema_v1.5.sql:901`) | schema-only |
| `retail_price_history` | Retail price per week | `(date, sku)` (`:893`) | schema-only |
| `purchase_price_history` | Purchase price | `(date, sku, supplier)` (`:885`) | schema-only |
| `average_cheque` | Average cheque per store/date | `(date, store_code, is_total)` (`:797`) | schema-only |
| `calendar` | Production calendar | `(date)` (`:805`) | schema-only |
| `exchange_rates` | FX rates | `(currency, date)` (`:821`) | schema-only |
| `industrial_dataset_raw` | Promo uplift dataset (CatBoost) | `(id)` bigint seq (`:136-188, 829`) | schema-only |

### 4.2 `sales_fact` columns and types
From `backup/schema_v1.5.sql:434-448`:
```
date date NOT NULL,
sku_code varchar(50) NOT NULL,
sku_name varchar(200),
store_code varchar(50) NOT NULL,
store_name varchar(200),
region varchar(100),
oblast varchar(100),
uom varchar(20),
quantity integer NOT NULL,
revenue numeric(15,2) NOT NULL,
created_at, updated_at, batch_id uuid
```
Indexes: `idx_sales_sku_date (sku_code, date)`, `idx_sales_store_date (store_code, date)`, `idx_sales_region_date (region, date)` (`:1129-1143`).

### 4.3 ORM models / migrations
- **No Alembic/migration dir** exists (searched; only `.venv` paths matched). The ORM layer in `app/models/` has **no** `sales_fact`, `retail_price_history`, `average_cheque`, `calendar`, or `exchange_rates` model — those tables are accessed only via **raw SQL `text()`** in `app/services/*_service.py` and `app/ml_torch/features/feature_builder.py` & `inference/predictor.py`. The only ORM models are `industrial_dataset.py`, `ml_model.py`, `ml_prediction.py`, `prediction.py`, user/activity/activation/upload-history. This means the temporal tables are **not managed by the ORM/migrations in source**; they are created by the DB dumps.

### 4.4 Primary/foreign keys
- `sales_fact` PK is composite `(date, sku_code, store_code)`. **No foreign keys** are declared for these temporal tables (dump shows only PKs/unique indexes). Referential integrity is by convention only.

### 4.5 Date range / row counts / distinct counts / duplicates / gaps / nulls / negatives / UOM
**Not measurable — no live DB.** Port 5432 is closed; Docker daemon is not running; `.env` points to `postgres:5432` (container-internal hostname). Row counts would be ~1,038,784 for `industrial_dataset_raw` (per ADR-0002), but `sales_fact` cardinality is **unknown** and I will not fabricate it.

The **1C extraction logic** (which defines the shape of incoming `sales_fact`) is confirmed in `data_set_loader.os`:
- Daily aggregation: `НАЧАЛОПЕРИОДА(ПродажиОбороты.ДокументПродажи.Дата, ДЕНЬ)` (`dl:500`).
- Group by `sku_code, uom, store_code, store_name, oblast, region, sku_name, date, week, store_name` (`dl:524-532`).
- `SUM(КоличествоОборот) AS quantity`, `SUM(СтоимостьОборот) AS revenue` (`dl:516-517`).
- `HAVING СУММА(ПродажиОбороты.СтоимостьОборот) >= 3000` (`dl:542`) — **revenue threshold** (see §5).
- `WHERE НЕ ПродажиОбороты.Номенклатура.Код В (&Исключения)` (`dl:521`) — **SKU exclusions**.

The task's caveat is verified: **the `HAVING >= 3000` threshold can drop low-sales entities entirely and create gaps**; a missing date×SKU×store row must not be interpreted as zero sales.

### 4.6 Is sales_data already used by LSTM?
**Yes, at feature-generation only.** `feature_builder.py` reads `sales_fact` (lags, `avg_weekly_sales`, `quantity`, `revenue`). It is used by `train_lstm_pipeline`/`train_lstm_unified`. The LSTM **predictor** also reads `sales_fact` for `_get_sales_history` (lags + 7-day average, `predictor.py:178-247`) and `retail_price_history`/`average_cheque`/`calendar`.

---

## 5. Sales Data Quality and Coverage

Verifiable **structure** facts (no measured statistics):

1. **Revenue threshold preserved in extraction (CONFIRMED).** `HAVING SUM(СтоимостьОборот) >= 3000` (`data_set_loader.os:542`). Backend does **not** re-apply any revenue filter (no such WHERE in `sales_fact_service`/`feature_builder`) — so any historical completeness gap is **already baked into the ingested rows**.

2. **SKU exclusion preserved (CONFIRMED).** `НЕ … Номенклатура.Код В (&Исключения)` (`dl:521`). The exclusion list itself is a runtime parameter (`&Исключения`), not visible in the script default.

3. **Missing dates / gaps:** the daily-aggregation + threshold design means **absence of a row ≠ zero sales**. The current LSTM (and any future baseline model) must explicitly re-index to a continuous calendar dense per (SKU, store) and decide a zero-vs-missing policy. No such logic exists.

4. **Null/zero quantities:** `quantity integer NOT NULL` and `revenue numeric NOT NULL` in schema — the loader always emits SUM aggregates (never null for surviving rows, but the loader validation in `dataset_streaming_service.py:120-128` drops `k_uplift <= 0` records). Sales-table null handling is not enforced in the backend LSTM path.

5. **Negative quantities / returns:** the 1C register `Продажи.Обороты` may include returns/reversals; no sign-normalization or return-exclusion is present in `sales_fact_service` or `feature_builder`. **Not verifiable** against data.

6. **UOM consistency:** `uom varchar(20)` is loaded from `Номенклатура.ЕдиницаИзмерения` (`dl:515`) but is **grouping key** only in the loader; the LSTM **never uses `uom`** to normalize quantity — so mixed-unit quantities may be summed as if commensurable. **CONFIRMED risk** (feature builder ignores `uom`).

7. **Revenue and prices availability:** `revenue` is present (`sales_fact`); `retail_price_history.price` exists; `purchase_price_history` exists. `regular_price`/`promo_price` live in `industrial_dataset_raw` (from the PROMO module), **not** in `sales_fact`. There is no unified price series linked per (SKU, store, date).

8. **Duplicate prevented by PK:** `sales_fact` PK `(date, sku_code, store_code)` and `ON CONFLICT … DO NOTHING` in the push service (`sales_fact_service.py:35`) make duplicates structurally impossible for identical keys — though this also silently drops any second daily row for the same key whose values might be corrected data.

---

## 6. Promotion Period Identification

Findings:

1. **Promotional observations exist only in `industrial_dataset_raw`**, and that table stores an aggregated `k_uplift` and promo context (promo_id, promo_mechanics, adv_*, marketing_type, prices, analog_sku) — **no per-day promotion flag and no promotion start/end dates**. There is **no** `promo_start`/`promo_end` column in `industrial_dataset_raw` (`schema_v1.5.sql:136-188`).

2. The only date-like field in the promo path is `РасчетПрогнозаПозицийПромоАкций.ДатаПромо` (`data_set_loader.os:1155`) = "promo date", mapped to `month`/`week`. It is **not exposed** in the Promo-ML DB as a range; it is collapsed to month/week features in `industrial_dataset_raw`.

3. Therefore there is **no join/mapping between `sales_fact` (daily observations) and promotions** in the repository. A day×SKU×store row in `sales_fact` **cannot** be classified as promotional vs non-promotional with current data structures.

4. `ml_prediction_service._get_lstm_baseline` and the LSTM pipelines do **not** consult any promotion table; the LSTM trains on raw `quantity` with **no promotion-period masking/flagging**.

**Implication:** ADR-0005 §6.3 and §13 Q1 ("how are promotional periods identified?") is **unresolved and unsupported by current data**. This is a P0 blocker for leakage-safe baseline estimation because training on promo-inflated quantities without flagging promo periods biases the baseline upward.

---

## 7. RegularSales and Target Semantics

### 7.1 Origin and construction (CONFIRMED from 1C scripts)

`k_uplift` is constructed entirely in the **1C PROMO module** (`data_set_loader.os`), not in Promo-ML:

```text
regular_sales_qty        = ПозицииПромоАкции.ТекущийРегулярныйОбъемШт        (dl:1076)
historical_sales_qty_promo = ПозицииПромоАкции.ИсторияПродажВПромо           (dl:1077)

k_uplift = CASE
    WHEN ЕСТЬNULL(regular_sales_qty,0) = 0 OR ЕСТЬNULL(historical_sales_qty_promo,0) = 0
        THEN 1
    ELSE ОКР(historical_sales_qty_promo / regular_sales_qty, 3)
END                                                                        (dl:1183-1188)
```

### 7.2 How they enter PostgreSQL
Only the computed `k_uplift` (and the promo context features) are POSTed to `industrial_dataset_raw` (`data_set_loader.os:945-982, 1250-1352`). **`regular_sales_qty` (RegularSales_1C) and `historical_sales_qty_promo` are NOT persisted** in the Promo-ML schema. `industrial_dataset_raw` has `k_uplift` but no `regular_sales_qty`/`historical_sales_qty_promo` columns (schema `:136-188`). The backend read-only `avg_regular_sales` in `prediction_schema.py:86`/`prediction_controller.py:138` is a response placeholder, not a stored source.

### 7.3 What this means for ADR-0005
- **RegularSales_1C is not stored** — it cannot be used directly for a denominator or for comparison without re-extraction from 1C.
- **`k_uplift = PromoSales_1C / RegularSales_1C`**, both from the 1C PROMO module. The current CatBoost target is therefore anchored to the 1C RegularSales methodology (which ADR-0005 §6.3 explicitly refuses to treat as authoritative).
- **Special treatment of zero:** any zero numerator **or** denominator maps `k_uplift → 1` (`dl:1184-1186`). This means the training target contains a **mass of synthetic "no-effect" (1.0) values** that do not correspond to a real ratio — a target-definition inconsistency that will propagate to any CatBoost retraining against a new baseline.
- **Time-period consistency:** `regular_sales_qty` is described as "current" regular volume; `historical_sales_qty_promo` is the promo history; whether they represent the **same time period** is not determinable from the script and must be confirmed with the 1C module owner.

### 7.4 What the LSTM target actually is
`target = quantity` (`sales_fact`), next-row (`train_pipeline.py:59, 243`). This is **raw observed quantity including promo effects**, not regular/baseline demand. It does **not** use `RegularSales_1C` as a target, which is *consistent* with ADR-0005's "do not use RegularSales_1C as ground truth" — but it also is **not yet** the regular-sales estimate either (no promo removal), so it is not yet a valid `BaselineSales_ML` target either.

---

## 8. Temporal Leakage Assessment

Classification legend: **Confirmed issue** / **Potential risk** / **Not observed** / **Insufficient evidence**.

| # | Item | Evidence | Classification |
|---|---|---|---|
| L1 | Random (non-chronological) train/val split | `train_pipeline.py:83, 288` `random_split` | **Confirmed issue** |
| L2 | Target built by `shift(-1)` then random split → validation examples adjacent to training examples | `:59` + `:83` | **Confirmed issue** (sequence overlap across split) |
| L3 | Sequences span product/store boundaries (no `PARTITION`/reset at group edges in `_build_sequences`) | `dataset.py:78-81` iterates DataFrame row order; grouping only at SQL `LAG` level | **Confirmed issue** (cross-series window contamination) |
| L4 | Normalization fitted on full data | No normalization exists at all | **Not observed** (but no scaler → no leakage, yet also no scaling) |
| L5 | Future values entering historical features (lags/rolling) | `LAG(quantity,k)` and `AVG(quantity) OVER (… week)` use `ORDER BY date` ascending, no future values — but `avg_weekly_sales` window is **current week incl. the target day** (`feature_builder.py:80`) | **Potential risk** (weekly mean is not strictly historical at day granularity) |
| L6 | Promotion-period contamination | No promo flag joins sales; target `quantity` includes promo sales | **Confirmed issue** (baseline bias, no masking) |
| L7 | Target leakage via `revenue`/`quantity` features | `revenue` is in numeric features (`feature_builder.py:33`) and is highly collinear with target `quantity` | **Potential risk** (revenue may act as a near-target proxy) |
| L8 | Train/serve feature parity | Training numeric = 8 (single-SKU) / 6 (unified) vs inference numeric = 6; order differs; `avg_weekly_sales` repurposed | **Confirmed issue** |
| L9 | Inference `seq_len` fabricated by replication | `predictor.py:440-442` `X.repeat(1, seq_len, 1)` | **Confirmed issue** (vanishes temporal modeling at inference) |
| L10 | LabelEncoder fit on full corpus vs per-split | `dataset.py:52` fits before split | **Potential risk** (encoder sees validation categories) |

---

## 9. Baseline Estimation Readiness

Readiness to support independent `BaselineSales_ML`:

**A. Simple statistical baselines** — **Ready, with data prerequisite.** Naive, seasonal-naive, moving-average, and calendar-adjusted baselines can be computed from `sales_fact` (once accessible) using plain SQL/NumPy. Nothing in code blocks this. No BS/normalization required. **Required:** dense calendar reindexing + promo-period flag to avoid bias.

**B. Seasonal historical baselines** — **Partially ready.** Week/day-of-week seasonality derivable from `date`/`week` columns; `calendar.day_type` available. **Missing:** a verified promo flag, holiday/region alignment, and multi-week-of-year history depth (unknown).

**C. Existing LSTM forecasting** — **Not ready (as-is).** Target is raw `quantity`, split is random, feature parity broken, no scaling, no chronological holdout, no promo masking, inference window fabricated. It can be *salvaged* into a baseline forecaster only after the defects in §8 are corrected and a chronological validation strategy is adopted.

**D. Future external economic indicators** — **Not present.** `exchange_rates` and `average_cheque` exist; no macro/economic features are consumed by any model. Extension is possible (`average_cheque`, `exchange_rates`, price history) but requires availability/timing validation per ADR-0005 §3.1.

**Minimum data/validation requirements for a controlled comparison:**
1. Dense per-(SKU, store) daily time series with explicit zero-vs-missing policy.
2. Promotion-period flag per (SKU, store, date) — the single most critical missing element.
3. Chronological train/validation/test split with a real held-out recent period.
4. Common evaluation period for baseline, CatBoost, and composed forecast.
5. Explicit unit-of-measure normalization (or single-UOM subset) so quantities are commensurable.
6. Recorded dataset version/hash and sample configuration (ADR-0003 follow-up).

---

## 10. Resource and Execution Risks

Docker daemon is not running and no live infra is reachable, so this is **source-level** analysis only.

1. **Synchronous training inside API requests (CONFIRMED).** `train_lstm_pipeline`/`train_lstm_unified` run in-process from `POST /ml/torch/train/...` (`router.py:58,90`). Same pattern and risk as the CatBoost blocker (ADR-0004). No queue/worker isolation.

2. **CPU/GPU selection:** `device = "cuda" if torch.cuda.is_available() else "cpu"` (`train_pipeline.py:89, 275`). In the container (CPU-only torch wheel install, `Dockerfile:16`), this is always CPU.

3. **Sequence materialization:** `_build_sequences` constructs three full NumPy arrays (`X_num`, `X_cat`, `y`) of `(n_rows - seq_len)` windows in RAM at once (`dataset.py:59-87`). For "all SKUs" with many rows this is O(rows×seq_len×features) — a memory multiplier analogous to the CatBoost blocker.

4. **Batch sizes:** 32 (single) / 64 (unified) defaults; not memory-optimized.

5. **No checkpointing for recovery.** `save_checkpoint` only writes on new best val loss (`trainer_with_embeddings.py:75-78`) with a fixed path `best_model.pt`; final artifact `{id}.pt` is written once at end. A mid-training failure loses progress; no resume path.

6. **No timeout/retry/backoff** on the train endpoints; they rely on uvicorn keep-alive 7200s set in compose (`docker-compose.prod.yml:37-38`).

7. **No resource isolation config** for the backend service (previously noted in the prior audit §8.3).

**No OOM claim is made.** These are structural risks consistent with the already-observed CatBoost failure mode, not evidence of a specific LSTM failure.

---

## 11. ADR-0005 Compliance Matrix

| # | ADR-0005 requirement | Existing implementation | Evidence | Gap | Severity |
|---|---|---|---|---|---|
| 1 | LSTM independently forecasts regular sales | LSTM forecasts raw `quantity` (incl. promo) | `train_pipeline.py:59,243` | Target is not "regular demand" | P0 |
| 2 | Historical sales as primary source | `sales_fact` read by LSTM feature builder | `feature_builder.py:61-142` | Present; data availability unverified | — |
| 3 | Promotion periods accounted for | None (no promo join/flag) | grep: no promo in ml_torch | Missing | P0 |
| 4 | RegularSales_1C retained, not ground truth | Not stored in DB at all; only `k_uplift` persisted | `industrial_dataset_raw` schema `:136-188` | Numerator/denominator not persisted | P1 |
| 5 | CatBoost 14-feature schema unchanged | 14 features; no LSTM feature | `train_pipeline.py:152-174`, `29.meta.json` | **Compliant** | — |
| 6 | No feature-level LSTM→CatBoost integration | None | prior audit F-6.1 | **Compliant (expected)** | — |
| 7 | Independent model lifecycles | separate `algorithm`/`model_type`; `get_active_lstm_model` | `registry_service.py:514` | Partial (same registry table) | P2 |
| 8 | Composition contract (id/store/date/UoM/versions/timestamps) | Absent | grep: no composition module | Missing | P1 |
| 9 | Fallback ≠ constant 1.0 | `_get_lstm_baseline` returns `None`; `predict` falls back to `1.0` | `ml_prediction_service.py:288-294` | **Violates** ADR-0005 §8.1 | P1 |
| 10 | Chronological, leakage-safe validation | `random_split` | `train_pipeline.py:83,288` | Violates | P0 |
| 11 | Uncertainty not silently conflated | LSTM interval via `ML_RUNTIME_STATE.conformal_q_hat` (CatBoost's) | `predictor.py:452-465` | Cross-model reuse of q_hat | P2 |
| 12 | Find owner service for composition | Undecided, no module | — | Open decision | P2 |

---

## 12. Findings and Severity

**P0 — Blocks safe baseline research or threatens data integrity**

- **F-L1** — No promotion-period identification in sales data (target trains on promo-inflated `quantity` without masking). Evidence: `feature_builder.py`, no promo joins; §6.
- **F-L2** — LSTM target is raw `quantity`, not regular/baseline demand; not aligned to ADR-0005 baseline semantic. Evidence: `train_pipeline.py:59,243`.
- **F-L3** — Random (non-chronological) split + `shift(-1)` target ⇒ leakage; no chronological holdout. Evidence: `train_pipeline.py:83,288`.

**P1 — Blocks reliable evaluation or composition readiness**

- **F-L4** — Train/serve feature parity broken (8 vs 6 numeric; order differs; unified vs single-SKU differ). Evidence: `feature_builder.py:30-49` vs `train_pipeline.py:256-263` vs `predictor.py:395-402`.
- **F-L5** — Inference fabricates `seq_len` window by replication. Evidence: `predictor.py:440-442`.
- **F-L6** — Fallback to constant `1.0` baseline contradicts ADR-0005 §8.1. Evidence: `ml_prediction_service.py:288-294`.
- **F-L7** — `regular_sales_qty`/`historical_sales_qty_promo` (RegularSales_1C) not persisted; cannot reconstruct CatBoost target independently. Evidence: schema + `data_set_loader.os:1183-1188`.
- **F-L8** — `k_uplift → 1.0` guard for any zero numerator/denominator injects synthetic non-ratio targets. Evidence: `data_set_loader.os:1184-1186`.

**P2 — Improvement or optional extension**

- **F-L9** — `HAVING revenue >= 3000` + SKU exclusions create gaps; missing ≠ zero. Evidence: `data_set_loader.os:521,542`.
- **F-L10** — UOM ignored; mixed-unit quantity.sum risk. Evidence: `feature_builder.py` (no uom), schema `uom`.
- **F-L11** — `revenue` in numeric features collinear with `quantity` target (near-target proxy). Evidence: `feature_builder.py:33`.
- **F-L12** — No scaling/normalization. Evidence: absent.
- **F-L13** — Trainer writes fixed `best_model.pt` (collision), no recovery/resume. Evidence: `trainer_with_embeddings.py:75-78`.
- **F-L14** — Duplicate `POST /train/lstm` route. Evidence: `router.py:58` & `:358`.
- **F-L15** — `mlp.py` invalid absolute import `from ml_torch.models.base import …`. Evidence: `mlp.py:5`.
- **F-L16** — `SequenceBuilder` (dedicated sequence util) is not used; `_build_sequences` re-implements it inside the dataset. Evidence: `sequence_builder.py` vs `dataset.py:59-87`.

---

## 13. Recommended Experimental Plan

This is a **research plan, not an implementation plan**. No code changes are authorized.

### Stage A — Data quality and coverage validation **[requires DB access]**
- Restore/connect to PostgreSQL (read-only) and run bounded SELECT diagnostics on `sales_fact`: row count, min/max date, distinct `sku_code`/`store_code`, per-week density, null/zero/negative `quantity` and `revenue`, UOM histogram, duplicate check already enforced by PK.
- **Proposed SQL (for later execution, not executed in this audit):**
```sql
SELECT count(*)                 AS n,
       min(date)                AS min_date,
       max(date)                AS max_date,
       count(DISTINCT sku_code) AS distinct_sku,
       count(DISTINCT store_code) AS distinct_store,
       count(DISTINCT uom)      AS distinct_uom
FROM public.sales_fact;

SELECT count(*) FILTER (WHERE quantity < 0)   AS negative_qty,
       count(*) FILTER (WHERE quantity = 0)   AS zero_qty,
       count(*) FILTER (WHERE revenue < 0)    AS negative_rev,
       count(*) FILTER (WHERE revenue = 0)    AS zero_rev
FROM public.sales_fact;
```
(plus `EXPLAIN` on the extraction join in `feature_builder.py`, no `ANALYZE`). No prior DB access existed, so these are proposals.

### Stage B — Promotion-period identification **[requires decision + 1C data]**
- Determine whether 1C exposes promotion start/end dates (or a promo-period flag) per (SKU, store). Decide the mapping between `РасчетПрогнозаПозицийПромоАкций.ДатаПромо` and observational dates.
- Classify each sales observation as promotional / non-promotional / unknown; do **not** assume non-promo outside known datasets.

### Stage C — Regular-sales target definition **[requires architectural decision]**
- Declare the `BaselineSales_ML` target: masked regular sales (excluding promo periods) vs statistical decomposition. Decide how zero `regular_sales_qty`/`historical_sales_qty_promo` should be treated (the current `→1` rule must be reconsidered for any future CatBoost re-target).

### Stage D — Chronological validation strategy **[decision]**
- Adopt ordered train/validation/test with a held-out recent period; grouped time split (walk-forward or fixed horizon). Applied to both baseline and CatBoost workloads.

### Stage E — Simple statistical baseline comparison **[possible with existing code + DB]**
- Implement/run naive, seasonal-naive, moving-average baselines on `sales_fact` (pure SQL/NumPy) as the reference. No model training required.

### Stage F — Existing LSTM evaluation **[requires fixes]**
- After fixing F-L3/F-L4/F-L5/F-L12, retrain the LSTM on the leakage-safe split and evaluate baseline forecast accuracy. Compare vs Stage E baselines using the same holdout.

### Stage G — Leakage-safe historical baseline generation **[decision]**
- Define the procedure to generate past baseline forecasts (used only later for CatBoost target re-derivation) without future leakage (e.g., rolling origin).

### Stage H — CatBoost uplift target alignment + final PromoSales evaluation **[decision + retraining]**
- Decide whether CatBoost target must be re-derived against `BaselineSales_ML`. If yes, separate retraining experiment with the preserved CatBoost as comparison. Evaluate absolute PromoSales accuracy end-to-end.

**Classification of each stage:**
- Existing code only: E (partially A analysis-query formulation).
- Requires missing data: A, B.
- Requires architectural decision: B, C, D, G, H.
- Requires implementation: F (fixes), H (retraining), composition layer (ADR-0005 §10 Stage 3-4).

---

## 14. Open Architectural Questions

1. **Promotion identification** — what 1C data can flag promo periods per (SKU, store, date)? (ADR-0005 Q1)
2. **Regular-sales target** — should `BaselineSales_ML` be promo-masked observed quantity, or a statistical decomposition? (Q2/Q3)
3. **CatBoost target reconstruction** — how to produce a leakage-safe denominator from the selected ML baseline, and is a retraining experiment in scope now? (Q4)
4. **Forecast horizon/aggregation** — daily per (SKU, store), weekly, or store-level? (Q5)
5. **Constant-1.0 fallback** — explicit fallback policy required by ADR-0005 §8.1; what should replace it? (Q6)
6. **Uncertainty of composition** — separate statistical design needed; current LSTM reuses CatBoost `conformal_q_hat`. (Q7)
7. **Composition owner service** — which existing service, or a thin new layer? (Q8)
8. **UOM / mixed units** — how to normalize quantities before any model consumes them?
9. **Missing-vs-zero sales** — policy for gaps caused by `HAVING >= 3000` and SKU exclusions.
10. **Data versioning** — record dataset version/sample in baseline-model metadata (ADR-0003 follow-up).

---

## 15. Evidence and References

- `.adr/0005-hybrid-lstm-catboost.md` — architectural authority (§3, §6.3, §8.1, §9, §12).
- `docs/promo-ml-architecture-codebase-audit-2026-11-10.md` — prior audit (F-6.1, statistical findings, infrastructure).
- `app/ml_torch/models/lstm.py`, `base.py`, `mlp.py`; `data/dataset.py`, `sequence_builder.py`; `features/feature_builder.py`; `train/train_pipeline.py`, `trainer.py`, `trainer_with_embeddings.py`; `inference/predictor.py`; `api/v1/ml_torch/router.py`; `schemas/torch_schema.py`.
- `app/services/sales_fact_service.py`, `price_history_service.py`, `average_cheque_service.py`, `calendar_service.py`, `historical_data_service.py`, `ml_prediction_service.py`.
- `app/models/*.py`, `app/db/base.py`, `backup/schema_v1.5.sql` (line refs cited inline), `backup/schema*.sql`.
- `1c_scripts/data_set_loader.os` and `get_forecast.os` (decoded UTF-8; line refs `dl:`/`gf:` correspond to `\n`-split of the decoded file).

---

## 16. Final Audit Verdict

**The LSTM pipeline and the historical-sales data layer are partially implemented but not ready to serve the ADR-0005 independent `BaselineSales_ML` role.**

- **Data readiness:** structurally sound schema + confirmed 1C extraction; but **no live DB access** prevented any quantitative verification, and the source-level revenue threshold / SKU exclusions / UOM / missing-vs-zero issues create concrete data-quality work before safe baseline research.
- **Model readiness:** the LSTM is a **functional per-SKU next-day `quantity` forecaster** with confirmed train/serve parity, leakage, and scaling defects; its target and validation strategy are **not aligned** to regular-sales forecasting.
- **Decision readiness:** the single most critical missing artifact for baseline estimation is a **promotion-period identifier**, which is currently neither in `sales_fact` nor in the promo dataset link, and must be resolved with 1C before leakage-safe experiments can proceed.

No application code, database data/schema, model artifacts, containers, or environment were modified. The only repository write is this report.

---

*Returned to the Architecture Center (Andrey + ChatGPT) for review and FINAL ACCEPTANCE. No recommendations have been implemented.*