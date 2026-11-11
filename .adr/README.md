# Architecture Decision Records — Promo-ML

This directory is a reconstructed ADR register created on 2026-11-10.

Historical decisions not supported by repository or source evidence must not be represented as previously approved ADRs.

## Decision register

| ADR | Subject | Status |
|---|---|---|
| ADR-0001 | Existing CatBoost uplift training baseline | Accepted — as-built documentation |
| ADR-0002 | Infrastructure blocker and feature development freeze | Accepted |
| ADR-0003 | Diagnostic sampling is not production training | Accepted |
| ADR-0004 | Evaluate isolated training execution | Proposed |

## Governance

- Preserve the distinction between observed implementation, accepted decisions and proposed changes.
- Do not retroactively claim that reconstructed ADRs were approved when the original implementation was created.
- Record new architectural decisions before implementation.
- Prefer extending existing infrastructure over creating duplicate services.
- Preserve historical decisions; supersede them through new ADRs when necessary.
- Keep ADRs synchronized with project documentation and Google Drive.

## Current project status

**Development Paused — Infrastructure Blocker P0**

Full-dataset training has not passed operational acceptance.

See `../docs/blocker-evidence.md` and `../docs/restart-checklist.md`.