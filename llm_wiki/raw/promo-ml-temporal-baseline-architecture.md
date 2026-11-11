# Promo-ML — Temporal Baseline Architecture

**Status:** Proposed architecture — research pending
**Date:** 2026-11-10
**Authority:** ADR-0005 — Hybrid LSTM and CatBoost Forecast Composition
**Related:** `docs/promo-ml-lstm-sales-data-audit-2026-11-10.md`, `docs/promo-ml-architecture-codebase-audit-2026-11-10.md`

---

## 1. Purpose and Relationship to ADR-0005

This document describes the temporal baseline component of Promo-ML: how
regular (non-promotional) sales are to be estimated independently and then
composed with the CatBoost uplift forecast into an absolute promotional sales
forecast.

It exists to give the Architecture Center a single, auditable description of
the intended baseline subsystem. It does not itself sanction implementation;
ADR-0005 remains the decision authority, and unresolved items are listed in
§11.

ADR-0005 defines a **prediction-level composition** architecture:

```text
BaselineSales_ML (temporal)  ×  K_uplift (CatBoost)  →  PromoSales forecast
```

Feature-level LSTM→CatBoost integration is explicitly rejected (ADR-0005
§12). Consequentially, the CatBoost feature schema (14 features) is unchanged
and is not part of this document's scope.

---

## 2. Confirmed Source Systems and Data Provenance

| Source | Role | Verification status |
|---|---|---|
| 1C Sales accumulation register (`Продажи`) | Primary historical sales observations | Extraction logic observed in `1c_scripts/data_set_loader.os` |
| 1C PROMO module | Historical promotion records (start/end dates, SKUs, stores) | **Existence confirmed by project owner**; schema, completeness, extraction, and PostgreSQL integration **not audited** |
| PostgreSQL `sales_fact` | Ingested daily sales | Schema confirmed from `backup/schema_v1.5.sql`; data volume/coverage **not measured** |
| PostgreSQL `retail_price_history`, `average_cheque`, `calendar`, `exchange_rates` | Auxiliary temporal context | Schema confirmed; coverage **not measured** |

Observed 1C Sales extraction shape (from `1c_scripts/data_set_loader.os`):
daily aggregation by product, store, and measurement unit; summed
`quantity` and `revenue`; an SKU exclusion list; and a revenue threshold that
filters low-turnover entities. The threshold means **absence of a row is not
equivalent to zero sales** (see §9).

The 1C PROMO module is the origin of the current `k_uplift` target in
`industrial_dataset_raw`. The specific object names, field mappings, and
business rules of the promotion-history source must be established during the
integration audit and are not asserted here.

---

## 3. Logical Granularity

The preferred dataset representation is vertical (ADR-0005 §6):

```text
One Day × One SKU × One Store × Context
```

This avoids a wide, manually maintained feature table. The grain is daily at
the product-store level; any coarser aggregation (e.g., weekly) is an open
decision (§11).

---

## 4. Promotion-Period Classification Concept

Each daily sales observation should carry a promotion-status classification:

| Class | Meaning |
|---|---|
| `PROMO` | The date falls inside a known promotion period for that SKU and store. |
| `REGULAR` | The date is confirmed outside any promotion period. |
| `UNKNOWN` | Promotion status cannot be determined from available data. |

Principles:

- Do **not** assume that observations outside any available promotion dataset
  are regular. If coverage is incomplete, the observation is `UNKNOWN`.
- `UNKNOWN` observations must not be silently treated as `REGULAR`.
- Promotion classification is the critical input for leakage-safe baseline
  research (ADR-0005 §6.3, §13 Q1–Q2).

The 1C PROMO module is the intended source of `PROMO` periods, but the mapping
from its records to the daily `Date × SKU × Store` grain has not yet been
established.

---

## 5. Existing LSTM Architecture and Limitations

The existing PyTorch/LSTM implementation is documented in detail in the
2026-11-10 LSTM audit. Summary of confirmed behavior:

- Training entry points: `train_lstm_pipeline` (per-SKU) and
  `train_lstm_unified` (all SKUs), in `app/ml_torch/train/train_pipeline.py`.
- Model: `LSTMUpliftModel` with categorical embeddings
  (`app/ml_torch/models/lstm.py`).
- Target: next-observation `quantity` (`shift(-1)`), **not** regular sales.
- Split: random `random_split`, **not** chronological.
- No scaling/normalization of numeric inputs.
- Broken train/serve feature parity (8 or 6 numeric features in training vs a
  fixed 6-feature order at inference).
- Synthetic inference sequence: a single feature vector repeated `seq_len`
  times instead of a real rolling window.

Consequences for baseline work:

- The existing LSTM is a next-day quantity forecaster, not a regular-sales
  baseline estimator.
- It must not be treated as already capable of producing `BaselineSales_ML`.
- Its defects must be addressed (or its role reconsidered) before any
  comparative evaluation is trustworthy.

---

## 6. BaselineSales_ML versus RegularSales_1C

| Concept | Definition | Status |
|---|---|---|
| `RegularSales_1C` | Regular-sales estimate produced by the 1C PROMO module | The current CatBoost uplift denominator derives from it |
| `BaselineSales_ML` | Independent regular-sales estimate produced by Promo-ML from observed history | To be established by research |

Both describe the same business concept (expected sales absent the evaluated
promotion) but may differ numerically because their methodologies differ.
ADR-0005 §6.3 states that `RegularSales_1C` is retained for compatibility,
traceability, and comparison, and is **not** an authoritative training target
for the new baseline model.

### 6.1 Known documentation conflict — `k_uplift` zero handling

The audit material is internally inconsistent about the zero-value fallback
used when constructing `k_uplift`:

- `docs/promo-ml-lstm-sales-data-audit-2026-11-10.md` Executive Summary states
  the fallback is **0** ("0 if either is 0").
- The same report's detailed section describes the fallback as **1**, and the
  1C extraction script `1c_scripts/data_set_loader.os` (dividing
  `historical_sales_qty_promo` by `regular_sales_qty`) contains a `THEN 1`
  branch.

**This conflict is not resolved here.** Neither value is adopted as an
approved business rule. It **requires source-code reconciliation** against the
authoritative 1C PROMO module before any CatBoost uplift-target re-derivation.
The audit report is intentionally left unmodified so the inconsistency stays
visible.

---

## 7. Prediction-Level Composition

ADR-0005 §3.3 defines the composition:

```text
PromoSaleŝ(t,s,p) = BaselineSaleŝ(t,s,p) × K̂_uplift(t,s,p)
```

Where:

- `t` — forecast date.
- `s` — store.
- `p` — product.
- `BaselineSaleŝ` — predicted baseline sales.
- `K̂_uplift` — predicted promotional uplift.
- `PromoSaleŝ` — predicted absolute sales during the promotion.

The composition is valid only if both components refer to the **same product,
store, period, and unit of measurement**. The composition layer must not
multiply values representing different periods or incompatible sales measures
(ADR-0005 §8).

---

## 8. Chronological Validation and Leakage Prevention

Principles:

1. **Chronological splits only.** Training, validation, and test periods are
   ordered in time; no random shuffle across the time axis.
2. **No future information in historical features.** Lags and rolling
   statistics must be strictly backward-looking at the target date.
3. **Leakage-safe sequence boundaries.** Validation and test targets must
   remain strictly within their respective chronological periods. Historical
   observations from earlier periods may be used as input context for later
   predictions, provided they would have been available at prediction time.
   No future target values or unavailable future features may enter the
   training or inference pipeline.
4. **Original splitters recomputed per split.** Encoders/scalers must be fit
   on training data only.
5. **Promotion-aware evaluation.** The evaluation must distinguish `PROMO`
   from `REGULAR` observations.
6. **Leakage-safe historical baseline generation.** Any historical baseline
   used to re-derive the CatBoost target must be generated without using
   future data (e.g., rolling-origin generation).
7. **Common test period.** Baseline, CatBoost, and composed forecasts are
   compared on a single temporally valid holdout (ADR-0005 §9.3).

---

## 9. Missing-versus-Zero Sales

Because the source extraction applies a revenue threshold and SKU exclusions,
a missing daily observation can mean one of several things:

- The entity genuinely had zero sales.
- The entity fell below the revenue threshold.
- The entity was excluded by SKU selection.
- The observation is genuinely absent from the source register.

Therefore:

- Missing rows **must not** be automatically imputed as zero.
- Any baseline model must define an explicit reindexing and zero/missing
  policy on a continuous calendar per `(SKU, store)`.
- The policy must be documented and applied consistently across training,
  validation, and inference.

No specific imputation rule is approved here; it is an open decision (§11).

---

## 10. Resource and Infrastructure Constraints

Approved hardware policy (see
`llm_wiki/raw/promo-ml-hardware-requirements.md`):

- Minimum 32 GB RAM.
- Preferred 64 GB RAM.
- Preferred NVIDIA GPU with at least 16 GB VRAM.
- No full-scale training on the existing 16 GB workstation.

Additional constraints consistent with ADR-0002/ADR-0004:

- Training must not run inside the primary API worker.
- Training must not compromise backend availability.
- Dataset preparation must avoid unnecessary full-memory materialization.
- GPU acceleration is optional at the architecture level; CPU-only operation
  remains supported for diagnostics and bounded experiments.

---

## 11. Research Alternatives for Handling Promotional Observations

These are candidate research directions, not approved decisions:

1. **Mask and exclude.** Train the baseline model on `REGULAR` observations
   only, forecasting across promotion gaps.
2. **Explicit promotion indicator.** Provide the promotion status as an input
   feature and train on all observations.
3. **Statistical decomposition.** Separate baseline level/trend/seasonality
   from promotional spikes and estimate the baseline component directly.
4. **Robust weighting.** Down-weight or winsorize promotional observations
   during fitting.
5. **Hybrid masking.** Exclude known `PROMO` periods while retaining `UNKNOWN`
   with an explicit uncertainty treatment.

Each alternative must be evaluated on the same temporally held-out data, with
final PromoSales accuracy as the primary criterion (ADR-0005 §9).

---

## 12. Open Architectural Decisions and Acceptance Criteria

### Open decisions

1. Promotion-period identification and its PostgreSQL integration.
2. Regular-sales target definition (`BaselineSales_ML` semantics).
3. Selection of the baseline method (statistical baseline vs Global LSTM).
4. Leakage-safe historical baseline generation procedure.
5. CatBoost uplift-target alignment and any resulting retraining experiment.
6. Forecast horizon, aggregation level, and unit-of-measure normalization.
7. Fallback policy when a baseline forecast is unavailable (no silent `1.0`).
8. Uncertainty propagation through composition.
9. Composition-layer ownership.

### Acceptance criteria (for the research phase)

- Historical sales coverage and quality are measured and documented.
- Promotion periods are classified for the evaluated dataset.
- A chronological validation protocol with a common test period exists.
- Statistical baselines and the Global LSTM are compared on that protocol.
- The selected baseline is justified by final PromoSales accuracy, not by
  component fit alone.
- The composition contract and fallback policy are documented and approved.
- No unresolved leakage path remains.

---

## 13. References

- `.adr/0005-hybrid-lstm-catboost.md` — architectural authority.
- `.adr/0001-training-baseline.md` — CatBoost as-built baseline.
- `.adr/0002-infrastructure-blocker.md` — full-dataset training blocker.
- `.adr/0004-training-isolation.md` — training isolation directions.
- `docs/promo-ml-lstm-sales-data-audit-2026-11-10.md` — LSTM and sales-data audit.
- `docs/promo-ml-architecture-codebase-audit-2026-11-10.md` — codebase audit.
- `llm_wiki/raw/promo-ml-hardware-requirements.md` — hardware policy.
- `llm_wiki/raw/implementation-status.md` — implementation status.
- `llm_wiki/raw/development-roadmap.md` — phased plan.

---

*Proposed architecture. No implementation is authorized by this document.
Returned to the Architecture Center for review and FINAL ACCEPTANCE.*