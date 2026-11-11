# Training Scalability — Promo-ML

## Definition

Training scalability describes the ability of Promo-ML to train models on
target-volume datasets while preserving the operational availability of the
platform.

## Knowledge

The CatBoost training pipeline loads qualifying database rows into a pandas
DataFrame. Training, statistical calculations, and SHAP processing are executed
as part of the backend training workflow.

Training succeeds on 10,000 rows but has not completed successfully on the
observed full dataset of 1,038,784 rows. The backend becomes unhealthy during
full-volume execution. The root cause remains unknown — investigation is
required. Memory exhaustion is one hypothesis, not an established diagnosis.

## Architecture / Usage

- Separate functional correctness from operational scalability.
- Preserve the complete source dataset.
- Measure resource consumption before redesigning infrastructure.
- Reuse existing services where possible.
- Keep diagnostic sampling explicit.
- Preserve model provenance and dataset versioning.
- Require full-volume acceptance evidence.

### Approved hardware policy (2026-11-10)

Per `llm_wiki/raw/promo-ml-hardware-requirements.md` and ADR-0005 §10:

| Resource | Minimum | Preferred |
|---|---|---|
| System RAM | 32 GB | 64 GB |
| GPU | CPU-only permitted | NVIDIA GPU, ≥16 GB VRAM |
| Storage | SSD | NVMe SSD |
| Training execution | Isolated process | Isolated with resource limits |

Operational constraints:
- Full-dataset training must not run inside the primary API worker.
- Model training must not compromise backend availability.
- Dataset preparation must avoid unnecessary full-memory materialization.
- Training must support resource monitoring and failure diagnostics.
- GPU acceleration is optional at the architecture level.
- CPU-only operation remains supported for diagnostics and bounded experiments.

Until suitable infrastructure is available, work is restricted to architecture,
code audits, data analysis, and bounded experiments.

## Related Concepts

- [[concepts/model-lifecycle-registry]]
- [[concepts/statistical-evaluation-and-conformal-calibration]]
- [[concepts/prediction-level-composition]]

## Sources

- [[resume/2026-11-10-training-diagnostic]]
- [[resume/2026-11-10-development-roadmap]]
- [[resume/2026-11-10-implementation-status]]
- [[resume/2026-11-10-temporal-baseline-architecture]]
- ADR-0001
- ADR-0002
- ADR-0003
- ADR-0004
- ADR-0005

## Open Questions

1. Which training stage causes backend health failure?
2. What is the peak memory consumption?
3. Are Docker resource limits the primary constraint?
4. Can existing worker infrastructure isolate training?
5. What is the minimum architectural correction?
6. How should independent validation and conformal calibration be organized?