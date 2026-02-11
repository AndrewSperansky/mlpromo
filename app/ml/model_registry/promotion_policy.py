# app/ml/model_registry/promotion_policy.py
# — PROMOTION POLICY v2 (metrics-gated + tradeoff + backward compatible)

from typing import TypedDict, Literal, Optional

from app.ml.model_registry.tradeoff_policy import decide_tradeoff


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

    Поддерживает:
    - Старый API (2 аргумента)
    - Новый API (v2)
    """

    # 🔁 Support v2 naming (tests may use current_meta / candidate_meta)
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
    # 1️⃣ BACKWARD COMPATIBILITY (old tests)
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

    return _normalize_result(decision, reason)
