# Promo-ML — Hardware and Training Infrastructure Requirements

**Status:** Architecture Approved — Hardware Upgrade Pending  
**Date:** 2026-11-10  
**Related ADR:** ADR-0005

## 1. Objective

Establish the minimum hardware conditions for reliable model training and experimental development in Promo-ML.

## 2. Current Workstation

- CPU: Intel Core i5-3470, 3.20 GHz.
- RAM: 16 GB.
- GPU: NVIDIA GeForce GT 710, approximately 1 GB VRAM.
- Storage: SATA SSD and HDD.

The existing workstation is not approved for full-scale model training.

## 3. Hardware Requirements

| Resource | Minimum | Preferred |
|---|---|---|
| System RAM | 32 GB | 64 GB |
| GPU | CPU-only permitted | NVIDIA GPU, 16 GB VRAM or more |
| Storage | SSD | NVMe SSD |
| Training execution | Isolated process | Isolated execution with resource limits |

The minimum RAM requirement is a project infrastructure policy and must be validated against actual workload measurements.

## 4. Operational Constraints

- Full-dataset training must not run inside the primary API worker.
- Model training must not compromise backend availability.
- Dataset preparation must avoid unnecessary full-memory materialization.
- Training must support resource monitoring and failure diagnostics.
- GPU acceleration must be optional at the architecture level.
- CPU-only operation remains supported for diagnostics and limited experiments.

## 5. Upgrade Gate

Before resuming full-scale training:

1. Upgrade or provision a workstation with at least 32 GB RAM.
2. Prefer 64 GB RAM for sustained model development.
3. Evaluate a GPU with at least 16 GB VRAM for PyTorch workloads.
4. Validate memory consumption and training duration.
5. Confirm that backend services remain stable during training.

## 6. Current Project Policy

Until suitable infrastructure is available, work is restricted to architecture, code audits, data analysis, and bounded experiments.

The project must not depend on successful full-scale training using the current 16 GB workstation.