# BaselineSales_ML — Promo-ML

## Definition

`BaselineSales_ML` is the independent regular-sales estimate produced by
Promo-ML from observed historical sales observations. It represents the expected
sales quantity for a product, store, and period in the absence of the evaluated
promotion.

## Knowledge

### Distinction from RegularSales_1C

| Concept | Definition | Status |
|---|---|---|
| `RegularSales_1C` | Regular-sales estimate produced by the 1C PROMO module | Current CatBoost uplift denominator derives from it |
| `BaselineSales_ML` | Independent regular-sales estimate produced by Promo-ML from observed history | To be established by research |

Both describe the same business concept but may differ numerically because their
estimation methodologies differ. `RegularSales_1C` is retained for
compatibility, traceability, and comparison, and is **not** an authoritative
training target for the new baseline model (ADR-0005 §6.3).

The primary historical data source is the 1C Sales accumulation register.
Observed sales may include promotional effects. The training methodology must
therefore account for promotional periods without assuming that all observed
quantities represent regular demand.

### Semantic requirements

- The preferred baseline estimation method will be selected through temporally
  valid experiments, with priority given to the accuracy of final promotional
  sales forecasts (ADR-0005 §9.3).
- A revised CatBoost uplift target must use a denominator consistent with the
  selected ML baseline methodology.
- The existing CatBoost target must not be silently combined with an
  incompatible ML baseline estimate (ADR-0005 §6.3).

### Current status

- Not yet established; research pending.
- Selection of baseline method (statistical baselines vs Global LSTM) is an
  open architectural decision.
- `BaselineSales_ML` target definition (promo-masked observed sales vs
  statistical decomposition) is unresolved.

## Architecture / Usage

The temporal model (`BaselineSales_ML`) and the uplift model (`K_uplift`) are
composed at prediction level:

```
PromoSaleŝ = BaselineSaleŝ_ML × K̂_uplift
```

This composition is valid only if both components refer to the same product,
store, period, and unit of measurement.

## Related Concepts

- [[concepts/regular-sales-1c]]
- [[concepts/prediction-level-composition]]
- [[concepts/catboost-uplift-model]]
- [[concepts/chronological-validation]]
- [[concepts/promotion-period-classification]]
- [[concepts/missing-vs-zero-sales]]
- [[concepts/lstm-temporal-forecasting]]

## Sources

- [[resume/2026-11-10-development-roadmap]]
- [[resume/2026-11-10-implementation-status]]
- [[resume/2026-11-10-temporal-baseline-architecture]]
- ADR-0005 — Hybrid LSTM and CatBoost Forecast Composition