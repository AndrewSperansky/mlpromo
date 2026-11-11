# Promo-ML — Stage 6 Logbook

**Stage:** 6  
**Status:** CONSERVED / DEVELOPMENT PAUSED  
**Last updated:** 2026-11-11

## Purpose

This Logbook records Stage 6 activities, architectural decisions, implementation progress, audit findings, and acceptance outcomes in chronological order.

Entries are append-only. Previous decisions must not be silently rewritten. Superseded decisions require explicit references to their replacements.

---

## 2026-11-11 — Stage 6 Initialization and Project Conservation

**Participants:** Андрей + Умник  
**Decision:** Establish Stage 6 management documentation and conserve the current Promo-ML state.

### 1. Current project state

- The existing CatBoost platform provides promotional uplift prediction and model lifecycle capabilities.
- ADR-0005 defines the target architecture combining independent temporal baseline and CatBoost uplift predictions.
- The existing LSTM implementation is experimental and has not been validated as a regular-sales baseline.
- Further model development and training are deferred until the research prerequisites are satisfied.

### 2. Architecture baseline

The accepted forecast composition principle is:

$$
\widehat{PromoSales}=\widehat{BaselineSales}_{ML}\times\widehat{K}_{uplift}
$$

LSTM and CatBoost remain independent predictors. LSTM output must not be introduced as an additional CatBoost feature without a separate architectural decision.

`RegularSales_1C` and `BaselineSales_ML` are distinct quantities and must not be silently substituted for one another.

### 3. Knowledge preservation

The following documentation remains the authoritative recovery foundation:

- `.adr/0005-hybrid-lstm-catboost.md`
- `llm_wiki/raw/development-roadmap.md`
- `llm_wiki/raw/implementation-status.md`
- `llm_wiki/raw/promo-ml-temporal-baseline-architecture.md`
- `llm_wiki/raw/Theory/CatBost.md`
- `llm_wiki/wiki/index.md`
- `llm_wiki/wiki/log.md`

The Wiki INGEST and subsequent LINT reconciliation have been reviewed by the Architecture Center.

### 4. Known unresolved issues

- Promotion-period extraction and integration from 1C PROMO remain unaudited.
- Chronological validation and independent conformal calibration require further work.
- The missing-versus-zero sales policy is not approved.
- CatBoost uplift-target alignment with the future ML baseline requires research.
- Composition fallback behavior requires an explicit policy.
- The historical `k_uplift` zero fallback discrepancy requires reconciliation.
- Wiki provenance for the earlier training diagnostic resume remains unresolved.

The `llm_wiki/wiki/queries/` directory has been created manually and may remain empty until active development resumes.

### 5. Conservation decision

No new model implementation, architectural refactoring, or additional research experiments are authorized during the conservation period.

At project resumption, the team must first review current repository state, ADR-0005, the Stage 6 Roadmap, and the latest Wiki audit evidence.

**Outcome:** Stage 6 documentation initialized. Project conservation approved at the architecture level.

**Implementation evidence:** Pending creation and synchronization of Stage 6 files.