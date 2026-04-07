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
    Расширенная политика promotion со статистическими критериями

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

        # ========== НОВЫЕ СТАТИСТИЧЕСКИЕ ПРОВЕРКИ ==========

        # 1. Проверка Confidence Interval (не должны пересекаться)
        if current_metrics and candidate_metrics:
            curr_ci = current_metrics.get("rmse_ci")
            cand_ci = candidate_metrics.get("rmse_ci")

            if curr_ci and cand_ci:
                # Проверяем перекрытие интервалов
                overlap = not (cand_ci["upper"] < curr_ci["lower"])
                if overlap:
                    return _normalize_result(
                        "reject",
                        f"Confidence intervals overlap: current [{curr_ci['lower']:.4f}, {curr_ci['upper']:.4f}], "
                        f"candidate [{cand_ci['lower']:.4f}, {cand_ci['upper']:.4f}]"
                    )

        # 2. Проверка Uplift (бизнес-метрика)
        if current_metrics and candidate_metrics:
            curr_uplift = current_metrics.get("uplift")
            cand_uplift = candidate_metrics.get("uplift")

            if curr_uplift is not None and cand_uplift is not None:
                if cand_uplift < curr_uplift:
                    return _normalize_result(
                        "reject",
                        f"Uplift decreased: {curr_uplift:.4f} → {cand_uplift:.4f}"
                    )

        # 3. Проверка Calibration (coverage должен быть близок к target)
        cand_conformal = candidate_metrics.get("conformal", {})
        if cand_conformal:
            coverage = candidate_metrics.get("coverage", 0)
            target = 1 - cand_conformal.get("alpha", 0.05)

            if abs(coverage - target) > 0.03:
                return _normalize_result(
                    "manual_review",
                    f"Model not calibrated: coverage={coverage:.3f}, target={target:.3f}"
                )

        # 4. Проверка Accuracy@ε
        if current_metrics and candidate_metrics:
            curr_acc = current_metrics.get("accuracy_eps")
            cand_acc = candidate_metrics.get("accuracy_eps")

            if curr_acc is not None and cand_acc is not None:
                if cand_acc < curr_acc - 0.01:
                    return _normalize_result(
                        "reject",
                        f"Accuracy@ε decreased: {curr_acc:.3f} → {cand_acc:.3f}"
                    )

        # ========== НОВАЯ ПРОВЕРКА: p-value ==========
        # 5. Статистическая значимость (p-value < 0.05)
        stat_comparison = candidate_metrics.get("statistical_comparison")
        if stat_comparison and stat_comparison.get("is_significant") is not None:
            if not stat_comparison["is_significant"]:
                return _normalize_result(
                    "reject",
                    f"Not statistically significant (p={stat_comparison.get('p_value', 0):.4f})"
                )


    # =====================================================
    # FINAL DECISION
    # =====================================================
    return _normalize_result(decision, reason)
