# LSTM Temporal Forecasting — Promo-ML

## Definition

The LSTM temporal forecasting component is an independent PyTorch/LSTM
implementation intended to forecast regular (non-promotional) sales from observed
historical sales data. It is not a CatBoost feature generator.

## Knowledge

### Current implementation facts (2026-11-10 audit)

- **Entry points:** `train_lstm_pipeline` (per-SKU) and `train_lstm_unified`
  (all SKUs) in `app/ml_torch/train/train_pipeline.py`.
- **Model:** `LSTMUpliftModel` with categorical embeddings in
  `app/ml_torch/models/lstm.py`.
- **Target:** next-observation `quantity` (`df['quantity'].shift(-1)`), **not**
  a regular-sales baseline.
- **Split:** `random_split`, **not** chronological.
- **Scaling/normalization:** none applied to numeric inputs.
- **Train/serve parity:** broken — training uses 8 numeric features (per-SKU) or
  6 (unified), while inference uses a fixed 6-feature order.
- **Inference sequence:** synthetic — a single feature vector repeated `seq_len`
  times instead of assembling a real rolling window.
- **Validated regular-sales baseline capability:** **none**.

### Architectural role

Per ADR-0005 §3.1:
- LSTM is responsible for independently forecasting regular sales from observed
  historical sales data.
- The target quantity is the expected sales volume in the absence of the
  evaluated promotional intervention.
- The forecasting methodology must not be constrained by the existing
  `RegularSales_1C` calculation.
- Alternative baseline estimation methods may be evaluated before selecting the
  final temporal model configuration.
- External conditions and economic indicators may be introduced when their
  predictive value and temporal availability have been validated.

### Limitations for baseline work

- The existing LSTM is a next-day quantity forecaster, not a regular-sales
  baseline estimator.
- It must not be treated as already capable of producing `BaselineSales_ML`.
- Its defects must be addressed (or its role reconsidered) before any
  comparative evaluation is trustworthy.
- The existing LSTM implementation is **not** a validated regular-sales baseline
  model.

## Architecture / Usage

The LSTM consumes ordered historical observations associated with products and
stores. Potential input includes historical sales quantities, historical price
dynamics, calendar characteristics, seasonality and trends, external economic
indicators, and other temporally available explanatory variables. External
indicators are optional extensions.

Future information must not leak into historical training examples (ADR-0005
§6.1).

The preferred dataset representation is vertical: One Day × One Product × One
Store × Context (ADR-0005 §6).

## Related Concepts

- [[concepts/prediction-level-composition]]
- [[concepts/baseline-sales-ml]]
- [[concepts/chronological-validation]]
- [[concepts/promotion-period-classification]]
- [[concepts/missing-vs-zero-sales]]
- [[concepts/statistical-evaluation-and-conformal-calibration]]

## Sources

- [[resume/2026-11-10-development-roadmap]]
- [[resume/2026-11-10-implementation-status]]
- [[resume/2026-11-10-temporal-baseline-architecture]]
- ADR-0005 — Hybrid LSTM and CatBoost Forecast Composition