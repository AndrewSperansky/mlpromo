# Promo-ML — Implementation Status

**Date:** 2026-11-10

## Status definitions

- **Implemented:** Code or functionality is present.
- **Verified:** Functionality has been demonstrated in the current diagnostic environment.
- **Partial:** Implementation exists, but full operational validation is incomplete.
- **Planned:** Architectural direction without confirmed end-to-end implementation.

## 1. Dataset Management

**Status: Implemented / Partial**

Available functionality includes CSV dataset upload, validation, dataset storage and management UI.

Current database contains 1,038,784 rows in `industrial_dataset_raw`.

Dataset count reporting requires reconciliation between the training response and the actual training sample.

## 2. CatBoost Training

**Status: Implemented / Verified on 10,000 rows**

The pipeline supports:

- Categorical and numeric features
- Train/validation split
- Early stopping
- Training metric history
- Model artifact persistence
- Candidate registration

The diagnostic model ID 29 completed training with validation RMSE 1.573350.

Full-dataset training remains blocked.

## 3. Model Registry

**Status: Implemented / Partially verified**

Existing functionality includes:

- Model registration
- Candidate and active model concepts
- Promotion policy
- Rollback
- Model metadata
- Lineage

The UI reported model ID 29 as active.

The training API reported `promoted: false` and `stage: candidate`. This discrepancy requires investigation.

## 4. Statistical Metrics

**Status: Implemented / Validation required**

Available calculations include:

- RMSE
- RMSE confidence interval
- Uplift
- Accuracy with tolerance
- Conformal Prediction
- Coverage

The latest diagnostic report showed:

- RMSE: 1.573350
- Reported RMSE CI: [0, 3.895882]
- Coverage: 95.325%

### Known issue — negative lower confidence bound

The reported confidence interval center and margin imply an unconstrained lower bound of approximately -0.173814.

The API reports zero instead.

Since RMSE is nonnegative, the implementation may clamp the lower bound to zero.

This behavior requires review.

A zero-clamped symmetric interval is not automatically a statistically valid 95% confidence interval.

Recommended investigation:

1. Inspect the CI implementation.
2. Confirm the underlying statistical assumptions.
3. Distinguish confidence intervals for RMSE from prediction intervals for individual forecasts.
4. Evaluate bootstrap or another suitable nonnegative interval estimator.
5. Test boundary cases explicitly.

## 5. Conformal Prediction

**Status: Implemented / Statistical review required**

The pipeline calculates prediction intervals and empirical coverage.

However, the inspected training implementation uses predictions from the full dataset for subsequent calibration and evaluation.

Independent out-of-sample calibration and test separation have not been established.

Reported coverage should not be treated as fully independent performance evidence until this is corrected.

## 6. SHAP Explainability

**Status: Implemented / Full-volume validation pending**

The pipeline computes and saves SHAP artifacts.

Its memory and execution cost must be profiled during blocker investigation.

## 7. LSTM / PyTorch

**Status: Implemented (isolated) / Regular-sales baseline capability not validated**

Per ADR-0005, LSTM is intended as an independent temporal baseline
forecaster, not as a CatBoost feature. The 2026-11-10 LSTM audit confirmed
the implementation state below.

### Confirmed LSTM implementation

- Per-SKU and unified training entry points exist
  (`app/ml_torch/train/train_pipeline.py`: `train_lstm_pipeline`,
  `train_lstm_unified`).
- An LSTM model with categorical embeddings exists
  (`app/ml_torch/models/lstm.py`: `LSTMUpliftModel`).
- The current target is the next-observation `quantity`
  (`df['quantity'].shift(-1)`), not a regular-sales baseline.
- Training and validation use a random split (`random_split`), not a
  chronological split.
- Train/serve feature parity is broken: training uses 8 (per-SKU) or 6
  (unified) numeric features, while inference uses a fixed 6-feature order.
- The inference sequence is synthetic: a single feature vector is repeated
  `seq_len` times instead of assembling a real rolling window.
- There is no validated regular-sales baseline forecasting capability.

### Sales-data limitations (2026-11-10 audit)

- PostgreSQL was unavailable during the audit.
- Data volume, temporal coverage, gaps, and UOM distribution were not
  measured.
- The promotion-history source exists in the 1C PROMO module, but its
  schema, completeness, extraction mechanism, and PostgreSQL integration
  remain unverified.
- The existing sales extraction applies a revenue threshold that can create
  missing observations; a missing row must not be assumed to mean zero
  sales.

The CatBoost training feature list still contains no LSTM-derived feature.
This is consistent with ADR-0005's rejection of feature-level integration
and is not a defect in the CatBoost implementation.

## 8. Infrastructure

**Status: Blocked for full-volume training**

The current backend cannot reliably complete full-dataset training in the observed local environment.

Development of new functionality is paused pending root-cause analysis and operational acceptance.

## 9. Hardware and Training Infrastructure

**Status: Policy approved — hardware upgrade pending**

Approved hardware policy (see
`llm_wiki/raw/promo-ml-hardware-requirements.md`):

- Minimum 32 GB RAM.
- Preferred 64 GB RAM.
- Preferred NVIDIA GPU with at least 16 GB VRAM.
- No full-scale training on the existing 16 GB workstation.

Operational constraints remain in force: full-dataset training must not run
inside the primary API worker and must not compromise backend availability.