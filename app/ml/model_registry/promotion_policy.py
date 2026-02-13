# app/ml/model_registry/promotion_policy.py
# — PROMOTION POLICY v3 (Drift → Tradeoff → Shadow)
# app/ml/model_registry/promotion_policy.py

from typing import Optional, Dict, Any, TypedDict

from app.ml.monitoring.shadow_latency import evaluate_shadow_latency
from app.ml.model_registry.tradeoff_policy import decide_tradeoff


class PromotionResult(TypedDict):
    decision: str
    reason: str
    promote: bool


def _normalize_result(decision: str, reason: str) -> PromotionResult:
    """
    Normalizes decision into unified PromotionResult structure.
    """

    promote = decision == "approve"

    return {
        "decision": decision,
        "reason": reason,
        "promote": promote,
    }


def decide_promotion(
    candidate_metrics: Optional[dict] = None,
    current_metrics: Optional[dict] = None,
    inference_metrics: Optional[dict] = None,
    drift_report: Optional[dict] = None,
    slo_config: Optional[dict] = None,
    alert_state: Optional[dict] = None,
    **kwargs,
) -> PromotionResult:
    """
    Unified promotion decision pipeline.

    Execution order:

    0️⃣ Freeze gate
    1️⃣ Drift gate
    2️⃣ Tradeoff gate
    3️⃣ Shadow latency gate
    """

    # 🔁 Support v2 naming
    if "current_meta" in kwargs:
        current_metrics = kwargs["current_meta"]

    if "candidate_meta" in kwargs:
        candidate_metrics = kwargs["candidate_meta"]

    candidate_metrics = candidate_metrics or {}
    current_metrics = current_metrics or {}
    inference_metrics = inference_metrics or {}
    drift_report = drift_report or {}
    slo_config = slo_config or {}
    alert_state = alert_state or {}

    # =====================================================
    # 0️⃣ FREEZE GATE
    # =====================================================
    if alert_state.get("active"):
        alert_type = alert_state.get("type", "unknown")

        return _normalize_result(
            "frozen",
            f"promotion frozen due to active alert: {alert_type}",
        )

    # =====================================================
    # 1️⃣ BACKWARD COMPATIBILITY (V1)
    # =====================================================
    if not inference_metrics and not drift_report and not slo_config:
        if not current_metrics:
            return _normalize_result(
                "approve",
                "No current model — auto approve",
            )

        rmse_current = current_metrics.get("rmse")
        rmse_candidate = candidate_metrics.get("rmse")

        if rmse_candidate is not None and rmse_current is not None:
            if rmse_candidate < rmse_current:
                return _normalize_result(
                    "approve",
                    "RMSE improved",
                )

        return _normalize_result(
            "reject",
            "RMSE not improved",
        )

    # =====================================================
    # 2️⃣ DRIFT GATE
    # =====================================================
    shap_drift = drift_report.get("summary", {}).get("shap_drift", False)

    if shap_drift:
        return _normalize_result(
            "reject",
            "SHAP drift detected",
        )

    # =====================================================
    # 3️⃣ MERGE LATENCY METRICS
    # =====================================================
    merged_candidate = dict(candidate_metrics)
    merged_current = dict(current_metrics)

    if inference_metrics:
        merged_candidate["latency_p95_ms"] = inference_metrics.get(
            "candidate_latency_p95_ms"
        )
        merged_current["latency_p95_ms"] = inference_metrics.get(
            "current_latency_p95_ms"
        )

    # =====================================================
    # 4️⃣ TRADEOFF POLICY
    # =====================================================
    tradeoff_result = decide_tradeoff(
        current_metrics=merged_current,
        candidate_metrics=merged_candidate,
        slo_config=slo_config,
    )

    decision = str(tradeoff_result["decision"])
    reason = str(tradeoff_result["reason"])

    # Если tradeoff уже reject → сразу reject
    if decision == "reject":
        return _normalize_result(decision, reason)

    # =====================================================
    # 5️⃣ SHADOW LATENCY GATE
    # =====================================================
    if inference_metrics:
        shadow_result = evaluate_shadow_latency(
            inference_metrics=inference_metrics,
            slo_config=slo_config,
        )

        shadow_decision = str(shadow_result["decision"])
        shadow_reason = str(shadow_result["reason"])

        # Shadow может эскалировать до reject
        if shadow_decision == "reject":
            return _normalize_result(shadow_decision, shadow_reason)

        # Если tradeoff manual_review, но shadow approve → оставляем manual_review
        if decision == "manual_review":
            return _normalize_result(decision, reason)

        # Если tradeoff approve, но shadow manual_review → эскалация
        if decision == "approve" and shadow_decision == "manual_review":
            return _normalize_result(shadow_decision, shadow_reason)

    # =====================================================
    # FINAL DECISION
    # =====================================================
    return _normalize_result(decision, reason)
