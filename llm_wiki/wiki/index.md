# Promo-ML LLM Wiki — Index

## Architecture and forecasting

### Concepts

- [[concepts/prediction-level-composition]]
- [[concepts/baseline-sales-ml]]
- [[concepts/regular-sales-1c]]
- [[concepts/catboost-uplift-model]]
- [[concepts/lstm-temporal-forecasting]]
- [[concepts/chronological-validation]]
- [[concepts/promotion-period-classification]]
- [[concepts/missing-vs-zero-sales]]

## Training and infrastructure

### Concepts

- [[concepts/training-scalability]]
- [[concepts/model-lifecycle-registry]]

## Quality and evaluation

### Concepts

- [[concepts/statistical-evaluation-and-conformal-calibration]]

## Source-specific resumes

- [[resume/2026-11-10-training-diagnostic]]
- [[resume/2026-11-10-development-roadmap]]
- [[resume/2026-11-10-implementation-status]]
- [[resume/2026-11-10-temporal-baseline-architecture]]

## Related architectural decisions

- ADR-0001 — Existing CatBoost uplift training baseline
- ADR-0002 — Infrastructure blocker and feature development freeze
- ADR-0003 — Diagnostic sampling
- ADR-0004 — Training isolation proposal
- ADR-0005 — Hybrid LSTM and CatBoost forecast composition

## Knowledge governance

The `raw/` layer is immutable source material.

The `resume/` layer contains source-specific summaries.

The `concepts/` layer contains accumulated conceptual knowledge.

The `index.md` file provides navigation.

The `log.md` file records Wiki updates.

## Source status

At inspection on 2026-11-10, the accessible `raw/Promo-ML.md` file was empty.

No missing source content has been reconstructed as if it were present.

Three canonical sources were ingested on 2026-11-11:
- `raw/development-roadmap.md`
- `raw/implementation-status.md`
- `raw/promo-ml-temporal-baseline-architecture.md`