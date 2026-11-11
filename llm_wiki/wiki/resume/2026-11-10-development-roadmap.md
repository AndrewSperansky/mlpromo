# Resume — Promo-ML Development Roadmap

**Date:** 2026-11-10
**Current state recorded by the source:** Development Paused

## Summary

The roadmap describes five phases for Promo-ML. Only Phase 1 (CatBoost
baseline) is functionally implemented. Phase 2 (infrastructure stabilization)
is the highest-priority blocker. Phase 4 defines the prediction-level
composition direction and is explicitly a proposed research and implementation
sequence, not an as-built capability.

## Key Points

- Phase 1 — CatBoost baseline: functionally implemented. Delivered areas
  include dataset management, CatBoost training, Model Registry, candidate and
  active model lifecycle, comparison and promotion, rollback and lineage,
  regression metrics, statistical calculations, conformal prediction, SHAP,
  frontend visualization, Docker deployment, and monitoring.
- Operational acceptance on the complete dataset is still pending.
- Phase 2 — infrastructure stabilization: blocked and highest priority. The
  exit criterion is successful full-volume training without an API outage.
- Phase 3 — statistical and data-quality review: planned. Covers confidence
  interval validity, negative lower bound, independent conformal calibration,
  random versus temporal/grouped validation, dataset representativeness, API/UI
  status reconciliation, training row-count metadata, and reproducible model
  comparisons.
- Phase 4 — prediction-level baseline plus uplift composition: proposed, not
  started. Authority is ADR-0005.
- Phase 4 supersedes the earlier feature-level direction in which an
  LSTM-derived value was injected into the CatBoost feature vector. ADR-0005
  §12 rejects that integration.
- The target composition is `BaselineSales_ML (temporal) × K_uplift (CatBoost)
  → PromoSales forecast`.
- The existing 14-feature CatBoost model and its lifecycle remain unchanged
  during baseline research.
- Phase 5 — extended forecasting: future directions only (temporal forecasting,
  macroeconomic indicators, context-dependent uplift, drift and coverage
  monitoring, batch and near-real-time inference, further PyTorch work).
- Development gate: no new functional phase starts until the infrastructure
  blocker is resolved and formally accepted.
- Governance for every phase: architecture and scope agreement, repository
  inspection, implementation plan, minimal changes, build and tests, E2E
  verification, diff and evidence review, final acceptance, documentation
  synchronization.

## Important Details

### Phase 4 research sequence (planned)

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

No item in this sequence is completed.

### Phase 4 unresolved decisions

- Promotion-period identification: 1C PROMO is confirmed by the project owner
  to contain historical promotion records (start/end dates, SKUs, stores), but
  its schema, completeness, extraction mechanism, and PostgreSQL integration
  have not been audited.
- Regular-sales target definition: promo-masked observed sales versus a
  statistical decomposition.
- Baseline method selection: statistical baselines versus the Global LSTM,
  judged primarily by final PromoSales accuracy rather than component-level fit.
- CatBoost uplift-target alignment: whether, and how, the uplift target must be
  re-derived against `BaselineSales_ML`.
- Fallback policy when a baseline forecast is unavailable. ADR-0005 §8.1
  forbids a silent constant such as `1.0`.
- Forecast horizon, aggregation level, and unit-of-measure normalization.
- Composition ownership: which existing service, if any, should own the
  composition layer.

### Referenced evidence

The source points to `llm_wiki/raw/promo-ml-temporal-baseline-architecture.md`
for architecture detail and to
`docs/promo-ml-lstm-sales-data-audit-2026-11-10.md` for audit evidence.

## Related Concepts

- [[concepts/prediction-level-composition]]
- [[concepts/baseline-sales-ml]]
- [[concepts/catboost-uplift-model]]
- [[concepts/chronological-validation]]
- [[concepts/promotion-period-classification]]
- [[concepts/model-lifecycle-registry]]
- [[concepts/statistical-evaluation-and-conformal-calibration]]
- [[concepts/training-scalability]]

## Source

- [[raw/development-roadmap]]
