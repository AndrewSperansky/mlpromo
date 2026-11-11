# Chronological Validation — Promo-ML

## Definition

Chronological validation is the evaluation protocol that enforces temporal
ordering of training, validation, and test periods to prevent future-data
leakage and produce trustworthy out-of-sample performance estimates for
time-series forecasting.

## Knowledge

### Principles (ADR-0005 §8, temporal architecture §8)

1. **Chronological splits only.** Training, validation, and test periods are
   ordered in time; no random shuffle across the time axis.
2. **No future information in historical features.** Lags and rolling statistics
   must be strictly backward-looking at the target date.
3. **Leakage-safe sequence boundaries.** Validation and test targets must remain
   strictly within their respective chronological periods. Historical
   observations from earlier periods **may be used** as input context for later
   predictions, provided they would have been available at prediction time. No
   future target values or unavailable future features may enter the training or
   inference pipeline.
4. **Original splitters recomputed per split.** Encoders/scalers must be fit on
   training data only.
5. **Promotion-aware evaluation.** The evaluation must distinguish `PROMO` from
   `REGULAR` observations.
6. **Leakage-safe historical baseline generation.** Any historical baseline used
   to re-derive the CatBoost target must be generated without using future data
   (e.g., rolling-origin generation).
7. **Common test period.** Baseline, CatBoost, and composed forecasts are
   compared on a single temporally valid holdout (ADR-0005 §9.3).

### Current violations

- The existing LSTM implementation uses `random_split`, not chronological
  splits.
- Conformal calibration uses predictions from the full dataset for calibration
  and evaluation, lacking independent out-of-sample calibration and test
  separation.

### Scope

These principles apply to:
- Baseline estimation research (statistical baselines and Global LSTM
  comparison)
- CatBoost uplift evaluation (when target is re-derived against
  `BaselineSales_ML`)
- Composed forecast evaluation (final PromoSales accuracy as the primary
  criterion)

## Architecture / Usage

The primary system-level objective is the predictive accuracy of absolute
promotional sales. Component-level accuracy alone is insufficient to establish
the accuracy of the composed forecast (ADR-0005 §9).

The final evaluation must use a common, temporally valid test period and
compare results against a defined baseline forecasting approach.

Prediction intervals and confidence intervals must be treated as distinct
statistical concepts. Uncertainty propagation through forecast composition
requires a separate statistical design (ADR-0005 §9).

## Related Concepts

- [[concepts/prediction-level-composition]]
- [[concepts/baseline-sales-ml]]
- [[concepts/catboost-uplift-model]]
- [[concepts/lstm-temporal-forecasting]]
- [[concepts/promotion-period-classification]]
- [[concepts/statistical-evaluation-and-conformal-calibration]]

## Sources

- [[resume/2026-11-10-development-roadmap]]
- [[resume/2026-11-10-implementation-status]]
- [[resume/2026-11-10-temporal-baseline-architecture]]
- ADR-0005 — Hybrid LSTM and CatBoost Forecast Composition