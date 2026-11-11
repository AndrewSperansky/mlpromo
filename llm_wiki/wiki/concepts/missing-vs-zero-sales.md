# Missing versus Zero Sales — Promo-ML

## Definition

Missing-versus-zero sales refers to the semantic ambiguity of absent daily
observations in the historical sales data: a missing row does not imply zero
sales.

## Knowledge

### Root cause

The source extraction from the 1C Sales accumulation register applies:
- A revenue threshold that filters low-turnover entities.
- An SKU exclusion list.

Therefore, a missing daily observation can mean one of several things:

1. The entity genuinely had zero sales.
2. The entity fell below the revenue threshold.
3. The entity was excluded by SKU selection.
4. The observation is genuinely absent from the source register.

### Policy

- Missing rows **must not** be automatically imputed as zero.
- Any baseline model must define an explicit reindexing and zero/missing policy
  on a continuous calendar per `(SKU, store)`.
- The policy must be documented and applied consistently across training,
  validation, and inference.
- No specific imputation rule is approved; it is an open decision (temporal
  architecture §11).

### Data audit findings (2026-11-10)

- PostgreSQL was unavailable during the audit.
- Data volume, temporal coverage, gaps, and UOM distribution were not measured.
- The promotion-history source exists in the 1C PROMO module, but its schema,
  completeness, extraction mechanism, and PostgreSQL integration remain
  unverified.

## Architecture / Usage

This distinction directly affects:
- Baseline target definition (`BaselineSales_ML`): whether missing observations
  are treated as zero, interpolated, or explicitly modeled.
- Chronological validation: missing periods must not create leakage or
  artificially inflate coverage.
- Uplift target re-derivation: historical baseline estimates used to reconstruct
  the CatBoost target must handle missing data consistently.

## Related Concepts

- [[concepts/baseline-sales-ml]]
- [[concepts/chronological-validation]]
- [[concepts/promotion-period-classification]]
- [[concepts/lstm-temporal-forecasting]]
- [[concepts/regular-sales-1c]]

## Sources

- [[resume/2026-11-10-implementation-status]]
- [[resume/2026-11-10-temporal-baseline-architecture]]
- ADR-0005 — Hybrid LSTM and CatBoost Forecast Composition