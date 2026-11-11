# ADR-0002 — Infrastructure Blocker and Feature Development Freeze

**Date:** 2026-11-10  
**Status:** Accepted  
**Severity:** P0 — Blocker

## Context

The PostgreSQL table `industrial_dataset_raw` contains 1,038,784 records.

Training against the full dataset caused the backend container to become unhealthy while remaining in the running state.

The last available training log reached the full-dataset loading stage.

A diagnostic training run limited to 10,000 records completed successfully.

The exact root cause remains unconfirmed.

## Decision

Pause new functional development of Promo-ML until training on the full target dataset can be completed reliably without making the API unavailable.

Prioritize:

1. Reproducible diagnostics.
2. Resource and execution profiling.
3. Root-cause identification.
4. Minimal corrective changes.
5. Full-volume acceptance testing.

## Acceptance criteria

- The failure is reproduced and supported by diagnostic evidence.
- Per-stage execution time and memory consumption are measured.
- Full-volume training completes successfully.
- Backend HTTP health remains operational.
- Model Registry, metrics, SHAP and Lineage are verified.
- The correction passes relevant unit, integration and E2E tests.
- A diff, test evidence and rollback procedure are documented.
- Final acceptance is explicitly approved.

## Non-goals

- No destructive dataset modifications.
- No unverified assumption that OOM is the root cause.
- No blind resource increases.
- No architecture rewrite without evidence.
- No additional ML features before blocker resolution.

## Consequences

Project status: **Development Paused / Infrastructure Blocked**.

The existing functional implementation is preserved for future recovery.