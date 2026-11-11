# Statistical Evaluation and Conformal Calibration — Promo-ML

## Definition

Statistical evaluation and conformal calibration cover the metrics, confidence
intervals, conformal prediction intervals, and validation methodology used to
assess model quality in Promo-ML.

## Knowledge

### Available calculations (implemented)

- RMSE
- RMSE confidence interval
- Uplift
- Accuracy with tolerance
- Conformal Prediction
- Coverage

### Diagnostic results (Model ID 29, 10k sample)

- RMSE: 1.573350
- Reported RMSE CI: [0, 3.895882]
- Coverage: 95.325%

### Known issues

#### Negative lower confidence bound

The reported CI center and margin imply an unconstrained lower bound of
approximately -0.173814, while the API reports zero. Because RMSE is
nonnegative, the implementation may clamp the lower bound. A zero-clamped
symmetric interval is not automatically a statistically valid 95% confidence
interval.

Recommended investigation:
1. Inspect the CI implementation.
2. Confirm the underlying statistical assumptions.
3. Distinguish confidence intervals for RMSE from prediction intervals for
   individual forecasts.
4. Evaluate a nonnegative interval estimator such as the bootstrap.
5. Test boundary cases explicitly.

#### Conformal calibration leakage

The inspected training implementation uses predictions from the full dataset
for subsequent calibration and evaluation. Independent out-of-sample calibration
and test separation have not been established. Reported coverage should not be
treated as fully independent performance evidence until this is corrected.

### Evaluation architecture (ADR-0005 §9)

- **CatBoost evaluation:** regression metrics (RMSE, MAE) on uplift forecast.
- **LSTM evaluation:** baseline sales forecast against a temporally valid
  reference; validation must account for time ordering and avoid future-data
  leakage.
- **Composition evaluation:** final absolute promotional sales forecast against
  observed promotional sales. The primary system-level objective is predictive
  accuracy of absolute promotional sales. Accuracy against the 1C PROMO module's
  `RegularSales` estimates is **not** the optimization objective.

Baseline estimation methods must be compared using both component-level
diagnostics and their contribution to final PromoSales forecast accuracy.
Candidate approaches must be evaluated on consistent, temporally separated
datasets. Component-level accuracy alone is insufficient.

Prediction intervals and confidence intervals must be treated as distinct
statistical concepts. Uncertainty propagation through forecast composition
requires a separate statistical design.

## Architecture / Usage

Phase 3 (planned) objectives include:
- Validate confidence interval construction.
- Resolve negative lower-bound handling.
- Establish independent conformal calibration.
- Review random versus temporal/grouped validation.
- Verify dataset representativeness.
- Reconcile API and UI model status.
- Correct training row-count metadata.
- Establish reproducible model comparisons.

## Related Concepts

- [[concepts/catboost-uplift-model]]
- [[concepts/lstm-temporal-forecasting]]
- [[concepts/chronological-validation]]
- [[concepts/prediction-level-composition]]
- [[concepts/model-lifecycle-registry]]
- [[concepts/training-scalability]]

## Sources

- [[resume/2026-11-10-development-roadmap]]
- [[resume/2026-11-10-implementation-status]]
- [[resume/2026-11-10-temporal-baseline-architecture]]
- ADR-0005 — Hybrid LSTM and CatBoost Forecast Composition