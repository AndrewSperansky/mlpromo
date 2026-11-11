# ADR-0001 — Existing CatBoost Uplift Training Baseline

**Date:** 2026-11-10  
**Status:** Accepted — as-built documentation

## Context

Promo-ML implements a CatBoost regression pipeline for predicting promotional sales uplift.

The existing implementation is located primarily in:

`app/ml/train/train_pipeline.py`

The pipeline:

1. Reads records from `industrial_dataset_raw`.
2. Uses `k_uplift` as the target variable.
3. Prepares four numeric and ten categorical features.
4. Splits the dataset into training and validation subsets.
5. Trains a CatBoostRegressor.
6. Calculates regression and statistical metrics.
7. Performs conformal calculations.
8. Registers the model and saves artifacts.
9. Calculates SHAP explanations.
10. Optionally promotes the candidate model.

## Existing model configuration

- Algorithm: CatBoostRegressor
- Iterations: 300
- Depth: 4
- Learning rate: 0.05
- Loss function: RMSE
- Random seed: 42
- Early stopping rounds: 50
- Validation split: 20%

## Decision

Preserve the existing architecture as the recovery baseline.

Do not introduce new services, modify the feature schema or redesign the training pipeline without first inspecting existing implementations.

## Known limitations

- Dataset loading currently uses `pd.read_sql(...)` without chunking.
- Training and validation use a random row split.
- Independent conformal calibration and evaluation have not been established.
- Full-dataset training causes backend health failures in the observed local environment.
- Existing ML worker-related Docker assets require inspection before proposing additional infrastructure.

## Consequences

The baseline is suitable for controlled diagnostic experiments but has not passed full-volume operational acceptance.

This ADR documents the existing implementation; it does not claim historical approval of every implementation choice.