# Resume — Promo-ML Implementation Status

**Date:** 2026-11-10

## Summary

The document records the as-built status of Promo-ML components using four
definitions: Implemented, Verified, Partial, and Planned. It distinguishes
functionality that exists from functionality that has been validated. The
central unresolved items are full-dataset training, statistical validity of
confidence and conformal intervals, and the absence of a validated regular-sales
baseline capability.

## Key Points

- Dataset management: implemented / partial. CSV upload, validation, storage,
  and management UI exist. The database contains 1,038,784 rows in
  `industrial_dataset_raw`. Dataset count reporting needs reconciliation.
- CatBoost training: implemented / verified on 10,000 rows. Supports
  categorical and numeric features, train/validation split, early stopping,
  metric history, artifact persistence, and candidate registration. Model ID 29
  completed with validation RMSE 1.573350. Full-dataset training remains
  blocked.
- Model Registry: implemented / partially verified. Registration, candidate and
  active models, promotion policy, rollback, metadata, and lineage exist. The UI
  reported model ID 29 as active while the training API reported
  `promoted: false` and `stage: candidate`.
- Statistical metrics: implemented / validation required. RMSE, RMSE confidence
  interval, uplift, tolerance accuracy, conformal prediction, and coverage
  exist. The diagnostic report showed RMSE 1.573350, RMSE CI [0, 3.895882], and
  coverage 95.325%.
- Conformal prediction: implemented / statistical review required. The
  inspected implementation uses predictions from the full dataset for
  calibration and evaluation, so independent out-of-sample calibration and test
  separation are not established.
- SHAP: implemented / full-volume validation pending; memory and execution cost
  must be profiled.
- LSTM / PyTorch: implemented in isolation, but regular-sales baseline
  capability is not validated.
- Infrastructure: blocked for full-volume training. New functional development
  is paused.
- Hardware: policy approved, upgrade pending (minimum 32 GB RAM, preferred
  64 GB, preferred NVIDIA GPU with at least 16 GB VRAM, no full-scale training
  on the existing 16 GB workstation).

## Important Details

### Negative lower confidence bound

The reported RMSE CI center and margin imply an unconstrained lower bound of
approximately -0.173814, while the API reports zero. Because RMSE is
nonnegative, the implementation may clamp the lower bound. A zero-clamped
symmetric interval is not automatically a valid 95% confidence interval.

The source recommends inspecting the CI implementation, confirming its
statistical assumptions, distinguishing confidence intervals for RMSE from
prediction intervals for individual forecasts, evaluating a nonnegative
interval estimator such as the bootstrap, and testing boundary cases.

### LSTM implementation facts

- Entry points: `train_lstm_pipeline` (per-SKU) and `train_lstm_unified` (all
  SKUs) in `app/ml_torch/train/train_pipeline.py`.
- Model: `LSTMUpliftModel` with categorical embeddings in
  `app/ml_torch/models/lstm.py`.
- Target: next-observation `quantity` (`df['quantity'].shift(-1)`), not a
  regular-sales baseline.
- Split: `random_split`, not chronological.
- Train/serve parity is broken: training uses 8 numeric features (per-SKU) or 6
  (unified), while inference uses a fixed 6-feature order.
- Inference sequence is synthetic: one feature vector repeated `seq_len` times
  instead of a real rolling window.
- No validated regular-sales baseline forecasting capability exists.

Per ADR-0005, LSTM is intended as an independent temporal baseline forecaster,
not a CatBoost feature. The absence of an LSTM-derived feature in the CatBoost
schema is therefore not a CatBoost defect.

### Sales-data limitations (2026-11-10 audit)

- PostgreSQL was unavailable during the audit.
- Data volume, temporal coverage, gaps, and UOM distribution were not measured.
- Promotion history exists in the 1C PROMO module, but schema, completeness,
  extraction, and PostgreSQL integration remain unverified.
- The sales extraction applies a revenue threshold that can create missing
  observations. A missing row must not be assumed to mean zero sales.

## Related Concepts

- [[concepts/catboost-uplift-model]]
- [[concepts/lstm-temporal-forecasting]]
- [[concepts/model-lifecycle-registry]]
- [[concepts/statistical-evaluation-and-conformal-calibration]]
- [[concepts/missing-vs-zero-sales]]
- [[concepts/training-scalability]]

## Source

- [[raw/implementation-status]]
