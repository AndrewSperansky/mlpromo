# ADR-0005 — Hybrid LSTM and CatBoost Forecast Composition

**Date:** 2026-11-10  
**Status:** Accepted — Target Architecture; Implementation Pending 
**Decision authority:** Architecture Center (Andrey + ChatGPT)  
**Project:** Promo-ML

---

## 1. Context

Promo-ML is a machine learning system designed to forecast product sales during promotional campaigns.

The existing implementation uses CatBoost regression to estimate the promotional uplift coefficient:

\[
K_{uplift} = \frac{PromoSales}{RegularSales}
\]

CatBoost operates on contextual features describing products, stores, pricing, promotional mechanics, and calendar conditions.

The project also contains a separate PyTorch/LSTM implementation for time-series forecasting.

The original architectural proposal was to inject LSTM-generated forecasts directly into the CatBoost feature vector.

However, this approach introduced additional training dependencies, feature-generation complexity, and computational costs.

The Architecture Center subsequently decided to preserve the separation between temporal and contextual modeling.

The 2026-11-10 architecture audit confirmed that the active CatBoost model uses 14 features and does not consume LSTM-derived features.

This is consistent with the intended architectural separation.

The primary source of historical sales is the 1C Sales accumulation
register, providing observed sales quantities at the product, store,
and day level.

The 1C PROMO module supplies an existing RegularSales estimate.
Its calculation methodology is not adopted as the ground truth
for the new forecasting architecture.

Promo-ML will independently estimate regular sales from observed
sales history and evaluate the resulting estimates against the
accuracy of final promotional sales forecasts.



## 2. Business Objective and Scope

The primary objective of Promo-ML is to improve the accuracy and usefulness of sales forecasts during promotional campaigns.

The system should provide:

- A forecast of baseline sales derived from historical sales dynamics.
- A forecast of promotional uplift derived from promotional and contextual factors.
- A composed forecast of absolute sales during the promotional period.

The resulting forecasts may support downstream business decisions, but downstream operational processes are outside the scope of this ADR.

**Out of scope:**

- Automated purchasing and replenishment.
- Inventory management.
- Logistics planning.
- Order generation.
- Development of a universal demand-planning platform.

## 3. Architectural Decision

**The preferred target architecture is independent model training with prediction-level composition.**

The architecture consists of three logical components.

### 3.1 Temporal Forecasting — LSTM

LSTM is responsible for independently forecasting regular sales
from observed historical sales data.

The target quantity is the expected sales volume in the absence
of the evaluated promotional intervention.

The forecasting methodology must not be constrained by the
existing RegularSales calculation provided by the 1C PROMO module.

Alternative baseline estimation methods may be evaluated before
selecting the final temporal model configuration.

External conditions and economic indicators may be introduced
when their predictive value and temporal availability have been
validated.

### 3.2 Promotional Uplift — CatBoost

CatBoost is responsible for estimating promotional uplift from
product, store, pricing, and promotional context.

The existing 14-feature CatBoost model and its current target
definition remain unchanged during the initial research phase.

The current target is calculated using the RegularSales value
supplied by the 1C PROMO module.

Once an independently validated regular-sales estimation method
has been selected, the uplift target must be reviewed and, where
necessary, redefined against the new baseline.

Historical baseline estimates used to construct the revised
uplift target must be generated without future-data leakage.

LSTM output is not required as an input feature for CatBoost.

### 3.3 Forecast Composition

A logical composition layer combines the independent forecasts:

\[
\widehat{PromoSales}_{t,s,p}
=
\widehat{BaselineSales}_{t,s,p}
\times
\widehat{K}_{uplift,t,s,p}
\]

Where:

- \(t\) — forecast date.
- \(s\) — store.
- \(p\) — product.
- \(\widehat{BaselineSales}\) — predicted baseline sales.
- \(\widehat{K}_{uplift}\) — predicted promotional uplift.
- \(\widehat{PromoSales}\) — predicted absolute sales during promotion.

This composition is valid only if the baseline and uplift definitions are semantically consistent.

## 4. Target Architecture

```text
                  PROMO-ML

     Historical Sales       Promo Context
            |                    |
            v                    v
     Temporal Dataset      Context Dataset
            |                    |
            v                    v
       PyTorch / LSTM         CatBoost
            |                    |
            v                    v
      Baseline Forecast     K-uplift Forecast
            |                    |
            +---------+----------+
                      |
                      v
             Forecast Composition
                      |
                      v
            Absolute Promo Sales
                      |
                      v
                Forecast API
```

The two model families remain independent at the training and model-artifact levels.

The composition layer operates on their predictions rather than their internal representations.

## 5. Model Responsibilities

| Component | Responsibility | Primary Output |
|---|---|---|
| LSTM | Model temporal sales dynamics | Baseline sales forecast |
| CatBoost | Model promotional response | K-uplift forecast |
| Forecast Composition | Combine compatible predictions | Absolute promotional sales forecast |

The architecture must preserve these responsibilities without introducing unnecessary coupling.

## 6. Data Architecture

The preferred dataset representation remains vertical:

**One Day × One Product × One Store × Context**

This structure avoids the requirement to maintain a wide feature table containing numerous manually populated historical columns.

### 6.1 LSTM Input

The temporal model consumes ordered historical observations associated with products and stores.

Potential input information includes:

- Historical sales quantities.
- Historical price dynamics.
- Calendar characteristics.
- Seasonality and trends.
- External economic indicators.
- Other temporally available explanatory variables.

External indicators are optional extensions, not mandatory requirements of the initial implementation.

Future information must not leak into historical training examples.

### 6.2 CatBoost Input

The contextual model consumes the established feature schema.

The current implementation contains 14 features:

**Numerical:**

- `month`
- `week`
- `regular_price`
- `promo_price`

**Categorical:**

- `sku`
- `store_id`
- `category`
- `region`
- `store_location_type`
- `format_assortment`
- `promo_mechanics`
- `adv_carrier`
- `adv_material`
- `marketing_type`

The feature schema must not be modified merely to connect the LSTM and CatBoost components.

### 6.3 Baseline Semantics

Regular sales represent the expected sales quantity for a product,
store, and period in the absence of the evaluated promotion.

Two estimation sources must be distinguished:

- RegularSales_1C: the existing estimate supplied by the 1C
  PROMO module.
- BaselineSales_ML: the independent estimate produced by Promo-ML
  from historical sales observations.

Both represent the same business concept but may differ
numerically because their estimation methodologies differ.

RegularSales_1C is retained for historical compatibility,
traceability, and comparative evaluation. It is not considered
an authoritative training target for the new baseline model.

The primary historical data source is the 1C Sales accumulation
register.

Observed sales may include promotional effects. The training
methodology must therefore account for promotional periods
without assuming that all observed quantities represent
regular demand.

The preferred baseline estimation method will be selected
through temporally valid experiments, with priority given to
the accuracy of final promotional sales forecasts.

A revised CatBoost uplift target must use a denominator
consistent with the selected ML baseline methodology.

The existing CatBoost target must not be silently combined
with an incompatible ML baseline estimate.


## 7. Independent Model Lifecycle

LSTM and CatBoost must have independent training and activation lifecycles.

The following principles apply:

1. CatBoost retraining must not automatically trigger LSTM retraining.
2. LSTM retraining must not automatically trigger CatBoost retraining.
3. Each model must retain its own version, metrics, and training metadata.
4. The composition layer must identify the exact model versions used.
5. Model failures must be observable and must not be silently hidden by fabricated predictions.
6. The existing CatBoost Model Registry must not be restructured without a separate approved design.

The implementation should reuse existing services and abstractions wherever possible.

## 8. Forecast Composition Contract

The composition contract must define:

- Product identifier.
- Store identifier.
- Forecast date or period.
- Unit of measurement.
- Baseline forecast value.
- Uplift forecast value.
- Composed promotional sales forecast.
- LSTM model version.
- CatBoost model version.
- Forecast generation timestamp.
- Availability and error status of each component.

All forecasts must refer to compatible product, store, time horizon, and units.

The composition layer must not multiply values that represent different periods or incompatible sales measures.

### 8.1 Fallback Policy

A missing LSTM prediction must not silently be replaced with a constant such as `1.0`.

Fallback behavior requires a separately defined policy.

If a validated alternative baseline is unavailable, the system must report that the composed forecast cannot be produced.

The CatBoost uplift forecast may remain available independently.

## 9. Model Evaluation

The architecture requires separate evaluation of each forecasting component.

### 9.1 CatBoost Evaluation

Evaluate the promotional uplift forecast using appropriate regression metrics, including RMSE and MAE.

### 9.2 LSTM Evaluation

Evaluate the baseline sales forecast against a temporally valid reference.

Validation must account for time ordering and avoid future-data leakage.

### 9.3 Composition Evaluation

Evaluate the final absolute promotional sales forecast against observed promotional sales.

The primary system-level objective is the predictive accuracy
of absolute promotional sales.

Accuracy against the 1C PROMO module's RegularSales estimates
is not the optimization objective.

Baseline estimation methods must be compared using both
component-level diagnostics and their contribution to final
promotional sales forecast accuracy.

Candidate approaches must be evaluated on consistent,
temporally separated datasets.


Component-level accuracy alone is insufficient to establish the accuracy of the composed forecast.

The final evaluation must use a common, temporally valid test period and compare results against a defined baseline forecasting approach.

Prediction intervals and confidence intervals must be treated as distinct statistical concepts.

Uncertainty propagation through forecast composition requires a separate statistical design.

## 10. Implementation Strategy

The target architecture must be implemented incrementally.

### Infrastructure Prerequisites

The current development workstation has 16 GB RAM,
an Intel Core i5-3470 CPU, and an NVIDIA GeForce GT 710 GPU.

This configuration is insufficient for reliable full-scale
Promo-ML model training.

The Architecture Center establishes the following
infrastructure requirements:

- Minimum system RAM: 32 GB.
- Preferred system RAM: 64 GB.
- Preferred GPU: NVIDIA GPU with at least 16 GB VRAM.
- SSD storage for datasets, checkpoints, and model artifacts.
- Resource-isolated training execution.

Full-scale training and performance evaluation must not
resume on the current workstation until the infrastructure
requirements have been addressed.

Limited read-only diagnostics, architecture audits, and
small controlled experiments may continue without an upgrade.

Actual resource requirements must be validated through
profiling before production deployment.


### Stage 1 — Stabilize Existing CatBoost

Resolve the full-dataset training blocker.

Correct the statistical evaluation methodology.

Preserve the existing CatBoost feature schema and lifecycle
until changes are separately approved.

### Stage 2 — Baseline Estimation Research

Audit the existing PostgreSQL sales history and PyTorch/LSTM
data preparation and training pipelines.

Verify the availability of promotion-period identifiers
for historical sales observations.

Establish temporally valid baseline estimation experiments.

Compare simple statistical baselines with the existing
LSTM approach.

Do not use RegularSales_1C as an unquestioned ground-truth
target.

Select the baseline methodology based on demonstrated
predictive performance.

### Stage 3 — Define Composition Contract

Approve the semantic, technical, and versioning contracts
between the independent predictions.

Determine whether existing prediction services can support
composition without introducing a new service.

Define the relationship between the selected ML baseline
and the CatBoost uplift target.

If target redefinition is required, design a leakage-safe
historical baseline generation procedure and a separate
CatBoost retraining experiment.

Preserve the existing CatBoost model as a comparison baseline.

### Stage 4 — Implement and Evaluate Composition

Implement the smallest approved integration.

Evaluate absolute promotional sales forecasts using
independent test data.

Do not introduce mandatory cross-model retraining.

## 11. Consequences

### Positive

- Preserves the existing CatBoost implementation.
- Separates temporal and contextual modeling.
- Avoids a wide manually maintained feature table.
- Allows independent model training and versioning.
- Enables forecasting of absolute promotional sales.
- Supports future research into external economic and environmental influences.

### Trade-offs

- Two model families must be maintained and evaluated.
- Forecast composition requires strict semantic consistency.
- Errors from both models affect the final forecast.
- Baseline demand may not be directly observable during promotional periods.
- End-to-end forecasting accuracy remains to be demonstrated.

## 12. Rejected Alternative

### Feature-Level LSTM → CatBoost Integration

The original proposal required LSTM forecasts to become additional CatBoost features.

This approach is not selected for the current target architecture.

Reasons:

- Additional feature-generation dependencies.
- Increased training and inference coupling.
- Higher computational and operational complexity.
- Need for leakage-safe historical LSTM predictions during CatBoost training.
- No demonstrated improvement over the independent composition approach.

This rejection applies to the feature-level integration strategy, not to the use of LSTM within Promo-ML.

A future change would require a separate architectural decision and comparative evidence.

## 13. Open Architectural Questions

Before implementation, the Architecture Center must resolve:

1. How are promotional periods identified in historical sales?
2. How should promotional observations be handled when
   estimating regular sales?
3. Which baseline estimation methodology provides the best
   out-of-sample performance?
4. How should the CatBoost uplift target be reconstructed
   using the selected ML baseline?
5. What forecast horizon and aggregation level are required?
6. How should unavailable baseline forecasts be handled?
7. How should uncertainty in the composed forecast be estimated?
8. Which existing service should own forecast composition?

These questions do not block continued independent operation of the current CatBoost model.

## 14. Audit Finding Disposition

**Finding:** F-6.1 — LSTM → CatBoost feature integration absent.

**Original audit severity:** P0.

**Architecture Center disposition:** Not a defect in the current CatBoost implementation.

**Reason:** Feature-level integration is not the selected target architecture.

The absence of LSTM-derived features in the 14-feature CatBoost schema is expected.

The implementation of prediction-level composition is a planned architectural evolution, not a corrective action for F-6.1.

## 15. References

- `.adr/0001-training-baseline.md`
- `.adr/0002-infrastructure-blocker.md`
- `.adr/0003-diagnostic-sampling.md`
- `.adr/0004-training-isolation.md`
- `app/ml/train/train_pipeline.py`
- `app/services/ml_prediction_service.py`
- `app/ml_torch/`
- `models/current/29.meta.json`
- `docs/promo-ml-architecture-codebase-audit-2026-11-10.md`
- `llm_wiki/raw/implementation-status.md`
- `llm_wiki/raw/development-roadmap.md`

---

**Decision summary:** Promo-ML will independently estimate regular
sales from observed historical sales data and combine the resulting
forecast with a semantically aligned CatBoost promotional uplift
forecast. The existing 1C PROMO RegularSales estimate is retained
for comparison but does not define the new baseline methodology.
The primary optimization objective is the accuracy of absolute
sales forecasts during promotional campaigns.