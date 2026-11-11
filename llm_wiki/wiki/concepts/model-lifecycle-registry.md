# Model Lifecycle and Registry — Promo-ML

## Definition

The Model Registry manages the lifecycle of CatBoost and (future) LSTM models
from candidate registration through promotion, activation, rollback, and
lineage tracking.

## Knowledge

### Implemented capabilities

- Model registration
- Candidate and active model concepts
- Promotion policy
- Rollback
- Model metadata
- Lineage

### Current status (2026-11-10)

The UI reported model ID 29 as active. The training API reported
`promoted: false` and `stage: candidate`. This discrepancy requires
investigation.

### Independent lifecycle principle (ADR-0005 §7)

1. CatBoost retraining must not automatically trigger LSTM retraining.
2. LSTM retraining must not automatically trigger CatBoost retraining.
3. Each model must retain its own version, metrics, and training metadata.
4. The composition layer must identify the exact model versions used.
5. Model failures must be observable and must not be silently hidden by
   fabricated predictions.
6. The existing CatBoost Model Registry must not be restructured without a
   separate approved design.

### Composition contract versioning (ADR-0005 §8)

The composition layer must record:
- LSTM model version
- CatBoost model version
- Forecast generation timestamp
- Availability and error status of each component

## Architecture / Usage

The Model Registry is part of Phase 1 (functionally implemented). Its
extension to support independent LSTM model lifecycles and composition-layer
version pinning is a planned architectural evolution, not a current
implementation.

The existing CatBoost model lifecycle remains unchanged during baseline
research. If CatBoost target redefinition is required, a leakage-safe
historical baseline generation procedure and a separate CatBoost retraining
experiment will be designed, preserving the existing CatBoost model as a
comparison baseline (ADR-0005 §10 Stage 3).

## Related Concepts

- [[concepts/prediction-level-composition]]
- [[concepts/catboost-uplift-model]]
- [[concepts/lstm-temporal-forecasting]]
- [[concepts/statistical-evaluation-and-conformal-calibration]]
- [[concepts/training-scalability]]

## Sources

- [[resume/2026-11-10-development-roadmap]]
- [[resume/2026-11-10-implementation-status]]
- [[resume/2026-11-10-temporal-baseline-architecture]]
- ADR-0005 — Hybrid LSTM and CatBoost Forecast Composition