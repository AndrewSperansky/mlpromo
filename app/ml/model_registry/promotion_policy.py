# app/ml/model_registry/promotion_policy.py
# — PROMOTION POLICY v3 (Drift → Tradeoff → Shadow)

from typing import TypedDict, Literal, Optional

from app.ml.model_registry.tradeoff_policy import decide_tradeoff
from app.ml.monitoring.shadow_latency import evaluate_shadow_latency


class PromotionResult(TypedDict):
    decision: Literal["approve", "reject", "manual_review"]
    reason: str
    promote: bool


def _normalize_result(
    decision: Literal["approve", "reject", "manual_review"],
    reason: str,
) -> PromotionResult:
    return {
        "decision": decision,
        "reason": reason,
        "promote": decision == "approve",
    }


def decide_promotion(
    candidate_metrics: Optional[dict] = None,
    current_metrics: Optional[dict] = None,
    inference_metrics: Optional[dict] = None,
    drift_report: Optional[dict] = None,
    slo_config: Optional[dict] = None,
    **kwargs,
) -> PromotionResult:
    """
    Unified promotion decision.

    Pipeline:

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

    # =========================
    # 1️⃣ BACKWARD COMPATIBILITY (V1)
    # =========================
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

    # =========================
    # 2️⃣ Drift gate
    # =========================
    shap_drift = (
        drift_report.get("summary", {}).get("shap_drift", False)
    )

    if shap_drift:
        return _normalize_result(
            "reject",
            "SHAP drift detected",
        )

    # =========================
    # 3️⃣ Merge latency metrics
    # =========================
    merged_candidate = dict(candidate_metrics)
    merged_current = dict(current_metrics)

    if inference_metrics:
        merged_candidate["latency_p95_ms"] = inference_metrics.get(
            "candidate_latency_p95_ms"
        )
        merged_current["latency_p95_ms"] = inference_metrics.get(
            "current_latency_p95_ms"
        )

    # =========================
    # 4️⃣ Tradeoff policy
    # =========================
    tradeoff_result = decide_tradeoff(
        current_metrics=merged_current,
        candidate_metrics=merged_candidate,
        slo_config=slo_config,
    )

    decision = tradeoff_result["decision"]
    reason = tradeoff_result["reason"]

    # если tradeoff reject → сразу reject
    if decision == "reject":
        return _normalize_result(decision, reason)

    # =========================
    # 5️⃣ Shadow latency gate
    # =========================
    if inference_metrics:
        shadow_result = evaluate_shadow_latency(
            current_latency_p95_ms=inference_metrics.get(
                "current_latency_p95_ms", 0
            ),
            candidate_latency_p95_ms=inference_metrics.get(
                "candidate_latency_p95_ms", 0
            ),
            max_allowed_growth=slo_config.get(
                "max_latency_growth", 0.15
            ),
        )

        shadow_decision = shadow_result["decision"]
        shadow_reason = shadow_result["reason"]

        if shadow_decision != "approve":
            return _normalize_result(
                shadow_decision,
                f"Shadow gate: {shadow_reason}",
            )

    # =========================
    # ✅ FINAL APPROVE
    # =========================
    return _normalize_result(
        "approve",
        "All gates passed (Drift, Tradeoff, Shadow)",
    )
