# CatBoost Uplift Model — Promo-ML

## Definition

The CatBoost uplift model estimates the promotional uplift coefficient
`K_uplift = PromoSales / RegularSales` from product, store, pricing, and
promotional context features.

## Knowledge

### Feature schema (14 features)

**Numerical:**
- `month`
- `week`
- `regular_price`
- `promo_price`

**Categorical:**
- `sku`
- `store_id`
- `category`
- `region`
- `store_location_type`
- `format_assortment`
- `promo_mechanics`
- `adv_carrier`
- `adv_material`
- `marketing_type`

### Target definition

Current target: `K_uplift` derived using `RegularSales_1C` (the 1C PROMO module
estimate) as denominator. Per ADR-0005 §6.3, this target must be reviewed and,
where necessary, redefined against `BaselineSales_ML` once an independently
validated baseline method is selected. Historical baseline estimates used to
construct the revised uplift target must be generated without future-data
leakage.

### Lifecycle

Implemented functionality includes model registration, candidate and active
model concepts, promotion policy, rollback, model metadata, and lineage. The
existing CatBoost Model Registry must not be restructured without a separate
approved design (ADR-0005 §7).

### Status

- Implemented / Verified on 10,000 rows (Model ID 29, validation RMSE 1.573350)
- Full-dataset training blocked
- LSTM-derived features are absent by design (ADR-0005 §12 rejects
  feature-level integration; this is not a defect in the CatBoost
  implementation — ADR-0005 §14 disposition of audit finding F-6.1)

### Architecture invariants

- The 14-feature schema must not be modified merely to connect LSTM and CatBoost
  components (ADR-0005 §6.2).
- LSTM output is not required as an input feature for CatBoost (ADR-0005 §3.2).
- CatBoost and LSTM have independent training and activation lifecycles
  (ADR-0005 §7).

## Architecture / Usage

The CatBoost pipeline supports categorical and numeric features, train/validation
split, early stopping, training metric history, model artifact persistence, and
candidate registration.

Conformal prediction calculates prediction intervals and empirical coverage, but
the inspected implementation uses predictions from the full dataset for
calibration and evaluation — independent out-of-sample calibration and test
separation are not established.

SHAP artifacts are computed and saved; their memory and execution cost must be
profiled during blocker investigation.

## Related Concepts

- [[concepts/prediction-level-composition]]
- [[concepts/regular-sales-1c]]
- [[concepts/baseline-sales-ml]]
- [[concepts/model-lifecycle-registry]]
- [[concepts/statistical-evaluation-and-conformal-calibration]]
- [[concepts/chronological-validation]]

## Sources

- [[resume/2026-11-10-development-roadmap]]
- [[resume/2026-11-10-implementation-status]]
- [[resume/2026-11-10-temporal-baseline-architecture]]
- ADR-0005 — Hybrid LSTM and CatBoost Forecast Composition