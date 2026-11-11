# ADR-0004 — Evaluate Isolated Training Execution

**Date:** 2026-11-10  
**Status:** Proposed — Not Approved

## Context

The current training operation is initiated through the FastAPI backend.

Training on the full dataset causes the backend to become unhealthy.

Possible contributing factors include memory pressure, blocking operations, resource contention and expensive post-training calculations.

None has yet been established as the root cause.

## Options

### Option A — Optimize existing pipeline

Investigate dataset loading, pandas transformations, CatBoost execution, statistical calculations and SHAP.

Retain the existing architecture where feasible.

### Option B — Reuse existing worker infrastructure

Inspect existing Docker, Compose and ML worker-related implementations.

Extend an existing mechanism if it is suitable.

### Option C — Introduce isolated training execution

Consider a separate training worker only if existing infrastructure is insufficient and the need is supported by evidence.

## Decision pending

No implementation option is approved.

Before selecting an approach:

1. Inspect the repository and deployment configuration.
2. Establish the failure mechanism.
3. Evaluate the smallest viable correction.
4. Estimate operational and maintenance consequences.
5. Submit the architectural decision for approval.

## Constraints

Do not create duplicate workers, queues, services or registries without verifying whether equivalent components already exist.