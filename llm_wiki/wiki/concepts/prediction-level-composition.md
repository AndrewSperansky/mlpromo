# Prediction-Level Composition — Promo-ML

## Definition

Prediction-level composition is the architectural pattern in which independent
temporal and contextual models each produce a forecast, and a composition layer
combines their predictions at inference time to produce the final absolute
promotional sales forecast.

## Knowledge

The composition formula defined by ADR-0005 §3.3:

```
PromoSaleŝ(t,s,p) = BaselineSaleŝ(t,s,p) × K̂_uplift(t,s,p)
```

Where:
- `t` — forecast date
- `s` — store
- `p` — product
- `BaselineSaleŝ` — predicted baseline sales from the temporal model
- `K̂_uplift` — predicted promotional uplift from CatBoost
- `PromoSaleŝ` — predicted absolute sales during promotion

The composition is valid only if both components refer to the **same product,
store, period, and unit of measurement** (ADR-0005 §8).

## Architecture / Usage

The architecture consists of three logical components (ADR-0005 §2):

| Component | Responsibility | Primary Output |
|---|---|---|
| LSTM (temporal) | Model temporal sales dynamics | Baseline sales forecast |
| CatBoost (contextual) | Model promotional response | K-uplift forecast |
| Forecast Composition | Combine compatible predictions | Absolute promotional sales forecast |

The two model families remain independent at the training and model-artifact
levels. The composition layer operates on their predictions rather than their
internal representations (ADR-0005 §4).

### Composition contract (ADR-0005 §8)

Must define:
- Product identifier
- Store identifier
- Forecast date or period
- Unit of measurement
- Baseline forecast value
- Uplift forecast value
- Composed promotional sales forecast
- LSTM model version
- CatBoost model version
- Forecast generation timestamp
- Availability and error status of each component

### Fallback policy (ADR-0005 §8.1)

A missing LSTM prediction must **not** silently be replaced with a constant
such as `1.0`. Fallback behavior requires a separately defined policy. If a
validated alternative baseline is unavailable, the system must report that the
composed forecast cannot be produced. The CatBoost uplift forecast may remain
available independently.

### Independent model lifecycle (ADR-0005 §7)

1. CatBoost retraining must not automatically trigger LSTM retraining.
2. LSTM retraining must not automatically trigger CatBoost retraining.
3. Each model must retain its own version, metrics, and training metadata.
4. The composition layer must identify the exact model versions used.
5. Model failures must be observable and must not be silently hidden by
   fabricated predictions.
6. The existing CatBoost Model Registry must not be restructured without a
   separate approved design.

### Rejected alternative (ADR-0005 §12)

Feature-level LSTM → CatBoost integration (injecting LSTM forecasts as
additional CatBoost features) is explicitly rejected. Reasons: additional
feature-generation dependencies, increased training and inference coupling,
higher computational and operational complexity, need for leakage-safe
historical LSTM predictions during CatBoost training, no demonstrated
improvement over independent composition.

## Related Concepts

- [[concepts/baseline-sales-ml]]
- [[concepts/catboost-uplift-model]]
- [[concepts/lstm-temporal-forecasting]]
- [[concepts/chronological-validation]]
- [[concepts/model-lifecycle-registry]]
- [[concepts/statistical-evaluation-and-conformal-calibration]]

## Sources

- [[resume/2026-11-10-development-roadmap]]
- [[resume/2026-11-10-implementation-status]]
- [[resume/2026-11-10-temporal-baseline-architecture]]
- ADR-0005 — Hybrid LSTM and CatBoost Forecast Composition