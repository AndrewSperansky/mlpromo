# ADR-0003 — Diagnostic Sampling Is Not Production Training

**Date:** 2026-11-10  
**Status:** Accepted

## Context

The full-dataset training attempt caused backend health failures.

A temporary SQL restriction was used:

```sql
ORDER BY id
LIMIT 10000
```

Training completed successfully.

Observed results:

- Model ID: 29
- Sample size: 10,000
- Training size: 8,000
- Validation size: 2,000
- Validation RMSE: 1.5733502125528713
- Best iteration: 209
- Coverage: 0.95325

The UI reported the model as activated.

The API response contained inconsistent dataset counts and candidate/activation status fields.

## Decision

Preserve the original complete dataset.

Remove the active sampling restriction from normal training while optionally retaining the SQL lines as comments documenting the diagnostic experiment.

Do not initiate full-dataset training until the infrastructure blocker is resolved.

If diagnostic sampling is required again, implement an explicitly configured diagnostic mode rather than an undocumented hardcoded SQL limit.

Diagnostic models must not be automatically promoted as production models.

## Limitations

The first 10,000 ordered records are not proven representative of the full dataset.

The resulting RMSE cannot be compared directly with server-side model quality without verifying dataset and validation comparability.

## Follow-up

- Correct dataset row-count reporting.
- Reconcile API candidate status with UI activation status.
- Verify dataset distribution and sampling strategy.
- Record training dataset version and sample configuration in model metadata.