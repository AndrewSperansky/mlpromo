# Resume — Promo-ML Training Diagnostic

**Date:** 2026-11-10

## Source

Project discussion, observed Docker and PostgreSQL outputs, training pipeline source code and model ID 29 training results.

## Initial problem

Full-dataset training caused the backend to become unhealthy.

The PostgreSQL dataset contained 1,038,784 records.

The backend remained running but HTTP health checks did not complete normally.

## Diagnostic experiment

A temporary SQL limit reduced the training dataset to 10,000 records.

The training pipeline completed successfully.

### Results

| Metric | Value |
|---|---:|
| Model ID | 29 |
| Sample size | 10,000 |
| Training size | 8,000 |
| Validation size | 2,000 |
| Validation RMSE | 1.573350 |
| Best iteration | 209 |
| Coverage | 0.95325 |

The frontend reported the first model as activated.

## Observed inconsistencies

The API response reported the full database row count while training metrics reflected the 10,000-row sample.

The response also reported candidate/not-promoted status while the UI displayed the model as active.

## Conclusion

The training pipeline is functional on the diagnostic sample.

Full-dataset operational stability remains unverified.

The root cause of backend health failure remains unknown.

## Related documents

- `docs/blocker-evidence.md`
- `docs/restart-checklist.md`
- `.adr/0002-infrastructure-blocker.md`
- `.adr/0003-diagnostic-sampling.md`