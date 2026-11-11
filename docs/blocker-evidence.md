# Promo-ML — Infrastructure Blocker Evidence

**Date:** 2026-11-10  
**Status:** Open  
**Severity:** P0

## Observed environment

- Backend container: `promo_ml_backend`
- PostgreSQL container: `promo_postgres`
- Redis container: `promo_redis`
- Dataset table: `public.industrial_dataset_raw`
- Dataset size: 1,038,784 rows

## Confirmed observations

### Full-dataset training

Backend logs reached:

```text
Starting training pipeline
Loading full dataset from industrial_dataset_raw
```

No subsequent completion was observed in the available log excerpt.

The backend container remained running but became unhealthy.

Health-check requests accumulated.

PostgreSQL and Redis remained healthy.

### Resource observation

At one point:

- Backend CPU: approximately 1.80%
- Backend memory: 1.738 GiB / 2.842 GiB

These values are not peak measurements and do not prove an out-of-memory event.

### Diagnostic training

A 10,000-row training run completed successfully.

Model ID 29 was registered and reported as activated by the UI.

Validation RMSE: 1.5733502125528713.

## Unconfirmed hypotheses

- Memory exhaustion
- CPU or thread contention
- Database query bottleneck
- Excessive pandas memory allocation
- Blocking or expensive post-training calculations
- Runtime or health-check configuration problems

## Diagnostic procedure

1. Capture Git revision and effective Docker Compose configuration.
2. Verify actual memory and CPU limits.
3. Verify no previous training operation remains active.
4. Collect Docker OOM, exit-code and health-check evidence.
5. Instrument dataset loading and transformation stages.
6. Measure CatBoost training duration and peak memory.
7. Measure statistical calculations and SHAP separately.
8. Repeat controlled experiments at increasing dataset sizes.
9. Inspect existing ML worker infrastructure.
10. Select the smallest evidence-based correction.

## Exit criteria

Full-dataset training completes successfully without API outage.

Model artifacts, metrics, registry state and lineage are consistent.

Repeatability is demonstrated and evidence is preserved.

Final acceptance remains a joint architectural decision.