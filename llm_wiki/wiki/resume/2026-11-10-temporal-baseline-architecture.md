# Resume — Promo-ML Temporal Baseline Architecture

**Date:** 2026-11-10
**Authority:** ADR-0005 — Hybrid LSTM and CatBoost Forecast Composition
**Status:** Proposed architecture — research pending

## Summary

This document describes the temporal baseline component of Promo-ML: how regular
(non-promotional) sales are to be estimated independently and then composed with
the CatBoost uplift forecast into an absolute promotional sales forecast. It
does not itself sanction implementation; ADR-0005 remains the decision
authority, and unresolved items are listed in its section 11.

## Key Points

- The architecture defines **prediction-level composition**:
  `BaselineSales_ML (temporal) × K_uplift (CatBoost) → PromoSales forecast`.
- Feature-level LSTM→CatBoost integration is explicitly rejected (ADR-0005 §12).
- The existing 14-feature CatBoost schema is unchanged and out of scope for this
  document.
- Source systems: 1C Sales register (primary historical sales, extraction
  observed), 1C PROMO module (promotion records, existence confirmed by project
  owner, schema/completeness/extraction/PostgreSQL integration **not audited**),
  PostgreSQL `sales_fact` (schema confirmed, volume/coverage **not measured**),
  and auxiliary tables (`retail_price_history`, `average_cheque`, `calendar`,
  `exchange_rates`).
- Preferred granularity: vertical — One Day × One SKU × One Store × Context.
- Promotion-period classification: each daily observation carries
  `PROMO` / `REGULAR` / `UNKNOWN`. Do not assume observations outside available
  promotion data are regular. `UNKNOWN` must not be silently treated as
  `REGULAR`. 1C PROMO is the intended source for `PROMO` periods but the daily
  mapping is not established.
- Existing LSTM: per-SKU and unified entry points, `LSTMUpliftModel` with
  categorical embeddings, target `shift(-1)` (next-observation `quantity`, **not**
  regular sales), `random_split` (not chronological), no scaling, broken
  train/serve feature parity (8 or 6 features in training vs 6 fixed at
  inference), synthetic inference sequence. It is a next-day quantity forecaster,
  **not** a regular-sales baseline estimator.
- `RegularSales_1C` (1C PROMO estimate) and `BaselineSales_ML` (independent
  Promo-ML estimate from observed history) are distinct concepts. Both describe
  the same business concept but may differ numerically. `RegularSales_1C` is
  retained for compatibility and traceability; it is **not** an authoritative
  training target for the new baseline.
- The `k_uplift` zero fallback is internally inconsistent: one audit section
  states fallback is **0**, another states **1**, and the 1C extraction script
  contains `THEN 1`. This conflict is unresolved and requires source-code
  reconciliation against the authoritative 1C PROMO module.
- Chronological validation principles: chronological splits only; backward-
  looking lags/rolling statistics; historical context from earlier periods may
  be used if available at prediction time; no future data leakage; refit
  encoders/scalers per split; promotion-aware evaluation; leakage-safe
  historical baseline generation (rolling-origin); common test period for
  baseline, CatBoost, and composed forecasts.
- Missing-versus-zero sales: revenue threshold and SKU exclusions mean a
  missing daily observation can mean genuine zero, below threshold, excluded, or
  absent. Missing rows **must not** be automatically imputed as zero. Any
  baseline model must define an explicit reindexing and zero/missing policy on a
  continuous calendar per `(SKU, store)`.
- Approved hardware constraints: minimum 32 GB RAM, preferred 64 GB RAM,
  preferred NVIDIA GPU 16 GB VRAM, training isolated from API worker, no
  backend availability compromise, GPU optional at architecture level.
- Research alternatives for handling promotional observations (candidate
  directions, **not approved decisions**): mask and exclude, explicit promotion
  indicator, statistical decomposition, robust weighting, hybrid masking. Each
  must be evaluated on the same temporally held-out data with final PromoSales
  accuracy as the primary criterion.
- Open architectural decisions (must be resolved before implementation):
  1. Promotion-period identification and PostgreSQL integration.
  2. Regular-sales target definition (`BaselineSales_ML` semantics).
  3. Baseline method selection (statistical baseline vs Global LSTM).
  4. Leakage-safe historical baseline generation procedure.
  5. CatBoost uplift-target alignment and any retraining experiment.
  6. Forecast horizon, aggregation level, unit-of-measure normalization.
  7. Fallback policy when a baseline forecast is unavailable (no silent `1.0`).
  8. Uncertainty propagation through composition.
  9. Composition-layer ownership.
- Acceptance criteria for the research phase: historical sales coverage and
  quality measured and documented; promotion periods classified for the evaluated
  dataset; chronological validation protocol with a common test period exists;
  statistical baselines and Global LSTM compared on that protocol; selected
  baseline justified by final PromoSales accuracy (not component fit alone);
  composition contract and fallback policy documented and approved; no unresolved
  leakage path remains.

## Related Concepts

- [[concepts/prediction-level-composition]]
- [[concepts/baseline-sales-ml]]
- [[concepts/regular-sales-1c]]
- [[concepts/lstm-temporal-forecasting]]
- [[concepts/chronological-validation]]
- [[concepts/promotion-period-classification]]
- [[concepts/missing-vs-zero-sales]]

## Source

- [[raw/promo-ml-temporal-baseline-architecture]]