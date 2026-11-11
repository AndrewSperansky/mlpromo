# Promo-ML — Project Restart Checklist

## Before restarting development

- [ ] Read the project handover documentation.
- [ ] Review all ADRs and their statuses.
- [ ] Confirm current Git revision.
- [ ] Verify deployed backend and Docker configuration.
- [ ] Verify PostgreSQL dataset integrity and backup.
- [ ] Confirm the training query has no unintended diagnostic limit.
- [ ] Confirm previous training processes have stopped.

## Infrastructure diagnostics

- [ ] Measure container resource limits.
- [ ] Inspect Docker OOM and health-check evidence.
- [ ] Measure dataset loading time and memory.
- [ ] Profile pandas transformations.
- [ ] Profile CatBoost training.
- [ ] Profile statistical calculations.
- [ ] Profile SHAP processing.
- [ ] Inspect existing worker infrastructure.

## Corrective implementation

- [ ] Approve the architectural approach.
- [ ] Implement the minimum required changes.
- [ ] Preserve existing code conventions and comments.
- [ ] Run relevant unit tests.
- [ ] Run integration tests.
- [ ] Run E2E tests.

## Acceptance

- [ ] Complete training on the full dataset.
- [ ] Confirm API remains available.
- [ ] Verify model registration and artifacts.
- [ ] Verify SHAP and Lineage.
- [ ] Reconcile API and UI activation status.
- [ ] Validate dataset split and statistical metrics.
- [ ] Record logs, diff and rollback instructions.
- [ ] Obtain final acceptance.
- [ ] Synchronize ADRs and Wiki to Google Drive.