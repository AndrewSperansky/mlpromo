# Promo-ML — Development Roadmap

**Date:** 2026-11-10  
**Current state:** Development Paused

## Phase 1 — CatBoost Baseline

**Status: Functionally implemented**

Delivered capabilities include:

- Dataset management
- CatBoost training
- Model Registry
- Candidate and active model lifecycle
- Model comparison and promotion
- Rollback and lineage
- Regression metrics
- Statistical calculations
- Conformal Prediction
- SHAP explanations
- Frontend visualization
- Docker-based deployment
- Monitoring infrastructure

Operational acceptance on the complete dataset is pending.

## Phase 2 — Infrastructure Stabilization

**Status: Blocked / Highest priority**

Objectives:

1. Identify the full-dataset training failure mechanism.
2. Measure memory and execution time by pipeline stage.
3. Inspect existing worker infrastructure.
4. Implement the minimum viable correction.
5. Preserve backend availability during training.
6. Verify complete training and model lifecycle.
7. Establish repeatable operational tests.

**Exit criterion:** Successful full-volume training without API outage.

## Phase 3 — Statistical and Data Quality Review

**Status: Planned**

Objectives:

- Validate confidence interval construction.
- Resolve negative lower-bound handling.
- Establish independent conformal calibration.
- Review random versus temporal/grouped validation.
- Verify dataset representativeness.
- Reconcile API and UI model status.
- Correct training row-count metadata.
- Establish reproducible model comparisons.

## Phase 4 — Prediction-Level Baseline + Uplift Composition

**Status: Proposed research and implementation sequence (not started)**

**Authority:** ADR-0005 — Hybrid LSTM and CatBoost Forecast Composition.

This phase supersedes the earlier feature-level direction, in which an
LSTM-derived value was to be injected into the CatBoost feature vector.
ADR-0005 §12 explicitly rejects feature-level integration. The target
architecture composes two independent predictions at inference time:

```text
BaselineSales_ML (temporal)  ×  K_uplift (CatBoost)  →  PromoSales forecast
```

The existing 14-feature CatBoost model and its lifecycle remain unchanged
during baseline research.

### Research and implementation sequence

1. Validate historical sales data and promotion-history integration.
2. Define the Temporal Dataset Contract.
3. Define regular-sales baseline semantics (`BaselineSales_ML`).
4. Establish chronological validation and leakage controls.
5. Compare statistical baseline methods against a Global LSTM.
6. Design leakage-safe historical baseline generation.
7. Evaluate CatBoost uplift-target alignment.
8. Define the composition contract and fallback policy.
9. Evaluate final absolute PromoSales forecast accuracy.
10. Implement and operationally validate the accepted solution.

### Unresolved decisions (resolve before implementation)

- **Promotion-period identification.** The 1C PROMO module is confirmed by
  the project owner to contain historical promotion records (start/end
  dates, SKUs, stores). Its schema, completeness, extraction mechanism, and
  PostgreSQL integration have not yet been audited.
- **Regular-sales target definition.** Promo-masked observed sales versus a
  statistical decomposition.
- **Baseline method selection.** Statistical baselines versus the Global
  LSTM, judged primarily by final PromoSales accuracy rather than
  component-level fit.
- **CatBoost uplift-target alignment.** Whether, and how, the uplift target
  must be re-derived against `BaselineSales_ML`.
- **Fallback policy.** Behaviour when a baseline forecast is unavailable;
  ADR-0005 §8.1 forbids a silent constant such as `1.0`.
- **Forecast horizon, aggregation level, and unit-of-measure normalization.**
- **Composition ownership.** Which existing service, if any, should own the
  composition layer.

See `llm_wiki/raw/promo-ml-temporal-baseline-architecture.md` for the
architecture detail and `docs/promo-ml-lstm-sales-data-audit-2026-11-10.md`
for the audit evidence.

**No item in this sequence is completed. This is a planned research and
implementation path, not an as-built capability.**

## Phase 5 — Extended Forecasting

**Status: Future**

Potential directions:

- Temporal sales forecasting
- Microeconomic and macroeconomic indicators
- Context-dependent uplift prediction
- Drift and coverage monitoring
- Batch and near-real-time inference
- Further PyTorch experimentation

## Development gate

No new functional phase begins until the infrastructure blocker is resolved and formally accepted.

## Governance

Each phase requires:

1. Architecture and scope agreement.
2. Repository inspection.
3. Implementation plan.
4. Minimal changes.
5. Build and tests.
6. E2E verification.
7. Diff and evidence review.
8. Final acceptance.
9. Documentation synchronization.