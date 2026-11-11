# Promo-ML — Stage 6 Roadmap

**Stage:** 6  
**Status:** CONSERVED / DEVELOPMENT PAUSED  
**Last updated:** 2026-11-11

## 1. Objective

Preserve the current Promo-ML architecture, implementation knowledge, and research findings so that development can resume without reconstructing previous decisions.

Stage 6 is the transition from the existing CatBoost platform toward the ADR-0005 hybrid forecasting architecture.

## 2. Current Baseline

**Implemented:**

- CatBoost promotional uplift prediction.
- Dataset and model lifecycle capabilities.
- Model Registry, metrics, lineage, and promotion policy.
- Experimental LSTM functionality.

**Accepted architecture, not yet implemented as a validated forecasting system:**

- Independent ML baseline forecasting.
- Prediction-level LSTM and CatBoost composition.
- Leakage-safe historical baseline generation.
- Temporally valid evaluation of final promotional sales forecasts.

## 3. Conservation Checklist

- [x] ADR-0005 established.
- [x] Temporal baseline architecture documented.
- [x] Canonical development roadmap and implementation status documented.
- [x] Wiki INGEST completed.
- [x] LINT evidence reconciled.
- [x] Architecture Center reviewed reconciliation.
- [x] `wiki/queries/` manually created.
- [ ] Stage 6 Logbook and Roadmap created in the repository.
- [ ] Stage 6 documentation synchronized to Google Drive.
- [ ] Conservation snapshot verified.

## 4. Development Resumption Plan

### Phase 1 — Context Recovery

- Review Stage 6 Logbook and Roadmap.
- Read ADR-0005 and the current Wiki index.
- Verify actual repository and infrastructure state.
- Identify changes made since conservation.
- Confirm the scope of the next research iteration.

### Phase 2 — Data Readiness

- Audit 1C PROMO records and their integration.
- Establish reliable promotion-period classification.
- Measure historical sales coverage and quality.
- Define missing-versus-zero handling.
- Confirm target semantics, units, and forecast horizon.

### Phase 3 — Temporal Baseline Research

- Establish chronological train/validation/test boundaries.
- Implement and evaluate simple statistical baselines.
- Evaluate Global LSTM against the same reference periods.
- Validate train/serve feature parity.
- Select a baseline approach based on predictive evidence.

### Phase 4 — Hybrid Forecast Evaluation

- Design leakage-safe historical baseline generation.
- Evaluate CatBoost target alignment.
- Define the composition contract and fallback policy.
- Compare final PromoSales forecasts on a common test period.
- Document uncertainty and calibration requirements.

### Phase 5 — Implementation Authorization

Implementation proceeds only after the Architecture Center approves the research evidence, scope, architecture, and acceptance criteria.

## 5. Governance

- Architecture decisions require approval by Андрей + Умник.
- OpenCode executes explicitly authorized tasks and provides diff, tests, and evidence.
- Canonical `raw/`, `schema/`, and ADR documents remain under Architecture Center control.
- Derived Wiki content is maintained through governed INGEST and LINT.
- Each completed step requires review before subsequent implementation.

## 6. Resume Point

**Next action when development resumes:** perform a repository and data-readiness audit against ADR-0005, starting with the 1C PROMO integration and historical sales coverage.

Do not begin LSTM retraining or CatBoost target changes before this audit.

**Conservation status:** Awaiting Stage 6 file creation, synchronization, and final verification.