# RegularSales_1C — Promo-ML

## Definition

`RegularSales_1C` is the existing regular-sales estimate supplied by the 1C
PROMO module. It serves as the current denominator for the CatBoost uplift
target `K_uplift = PromoSales / RegularSales_1C`.

## Knowledge

### Role and status

- The current CatBoost uplift target is calculated using `RegularSales_1C`.
- It is retained for historical compatibility, traceability, and comparative
  evaluation.
- It is **not** considered an authoritative training target for the new baseline
  model (`BaselineSales_ML`) (ADR-0005 §6.3).
- The 1C PROMO module is the origin of the current `k_uplift` target in
  `industrial_dataset_raw`. The specific object names, field mappings, and
  business rules of the promotion-history source must be established during the
  integration audit and are not asserted here.

### Known documentation conflict — k_uplift zero handling

The audit material is internally inconsistent about the zero-value fallback used
when constructing `k_uplift`:

- `docs/promo-ml-lstm-sales-data-audit-2026-11-10.md` Executive Summary states
  the fallback is **0** ("0 if either is 0").
- The same report's detailed section describes the fallback as **1**, and the
  1C extraction script `1c_scripts/data_set_loader.os` (dividing
  `historical_sales_qty_promo` by `regular_sales_qty`) contains a `THEN 1`
  branch.

**This conflict is not resolved.** Neither value is adopted as an approved
business rule. It **requires source-code reconciliation** against the
authoritative 1C PROMO module before any CatBoost uplift-target re-derivation.
The audit report is intentionally left unmodified so the inconsistency stays
visible.

### Source availability

The 1C PROMO module is confirmed by the project owner to contain historical
promotion records (start/end dates, SKUs, stores). Its schema, completeness,
extraction mechanism, and PostgreSQL integration have **not been audited**.

## Architecture / Usage

Once an independently validated regular-sales estimation method has been
selected, the uplift target must be reviewed and, where necessary, redefined
against `BaselineSales_ML`. Historical baseline estimates used to construct the
revised uplift target must be generated without future-data leakage (ADR-0005
§3.2).

## Related Concepts

- [[concepts/baseline-sales-ml]]
- [[concepts/catboost-uplift-model]]
- [[concepts/promotion-period-classification]]
- [[concepts/prediction-level-composition]]

## Sources

- [[resume/2026-11-10-development-roadmap]]
- [[resume/2026-11-10-implementation-status]]
- [[resume/2026-11-10-temporal-baseline-architecture]]
- ADR-0005 — Hybrid LSTM and CatBoost Forecast Composition