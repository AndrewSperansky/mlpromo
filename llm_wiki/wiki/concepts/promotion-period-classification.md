# Promotion Period Classification — Promo-ML

## Definition

Promotion period classification assigns each daily sales observation a promotion
status: `PROMO`, `REGULAR`, or `UNKNOWN`. This classification is the critical
input for leakage-safe baseline research and correct uplift target derivation.

## Knowledge

### Classification schema

| Class | Meaning |
|---|---|
| `PROMO` | The date falls inside a known promotion period for that SKU and store. |
| `REGULAR` | The date is confirmed outside any promotion period. |
| `UNKNOWN` | Promotion status cannot be determined from available data. |

### Principles

- Do **not** assume that observations outside any available promotion dataset are
  regular. If coverage is incomplete, the observation is `UNKNOWN`.
- `UNKNOWN` observations must not be silently treated as `REGULAR`.
- Promotion classification is the critical input for leakage-safe baseline
  research (ADR-0005 §6.3, §13 Q1–Q2).
- The 1C PROMO module is the intended source of `PROMO` periods, but the
  mapping from its records to the daily `Date × SKU × Store` grain has not yet
  been established.

### Source status

The 1C PROMO module is confirmed by the project owner to contain historical
promotion records (start/end dates, SKUs, stores). Its schema, completeness,
extraction mechanism, and PostgreSQL integration have **not been audited**.

## Architecture / Usage

Each daily sales observation in the vertical dataset (One Day × One SKU × One
Store × Context) should carry this promotion-status classification.

Research alternatives for handling promotional observations during baseline
estimation (candidate directions, **not approved decisions**):

1. **Mask and exclude** — train on `REGULAR` only, forecasting across promotion
   gaps.
2. **Explicit promotion indicator** — provide promotion status as an input
   feature and train on all observations.
3. **Statistical decomposition** — separate baseline level/trend/seasonality
   from promotional spikes.
4. **Robust weighting** — down-weight or winsorize promotional observations
   during fitting.
5. **Hybrid masking** — exclude known `PROMO` periods while retaining `UNKNOWN`
   with explicit uncertainty treatment.

Each alternative must be evaluated on the same temporally held-out data, with
final PromoSales accuracy as the primary criterion (ADR-0005 §9).

## Related Concepts

- [[concepts/baseline-sales-ml]]
- [[concepts/regular-sales-1c]]
- [[concepts/chronological-validation]]
- [[concepts/missing-vs-zero-sales]]
- [[concepts/lstm-temporal-forecasting]]
- [[concepts/prediction-level-composition]]

## Sources

- [[resume/2026-11-10-development-roadmap]]
- [[resume/2026-11-10-implementation-status]]
- [[resume/2026-11-10-temporal-baseline-architecture]]
- ADR-0005 — Hybrid LSTM and CatBoost Forecast Composition