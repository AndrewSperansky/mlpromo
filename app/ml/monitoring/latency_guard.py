# app/ml/monitoring/latency_guard.py
# — LATENCY SLO GUARD WITH AUTOMATIC ROLLBACK


from typing import Dict, Any

from app.ml.monitoring.latency_slo import evaluate_latency_slo
from app.ml.monitoring.latency_actions import rollback_current_to_previous


def latency_guard(
    *,
    p95_threshold_ms: float,
    p99_threshold_ms: float,
    auto_rollback: bool = True,
) -> Dict[str, Any]:
    """
    Проверяет latency SLO и выполняет rollback при breach
    """

    slo_result = evaluate_latency_slo(
        p95_threshold_ms=p95_threshold_ms,
        p99_threshold_ms=p99_threshold_ms,
    )

    if slo_result["status"] != "ok":
        return {
            "status": "skipped",
            "reason": slo_result["status"],
        }

    if slo_result["breached"] and auto_rollback:
        rollback_result = rollback_current_to_previous()

        return {
            "status": "rollback_triggered",
            "slo": slo_result,
            "rollback": rollback_result,
        }

    return {
        "status": "healthy",
        "slo": slo_result,
    }


"""
🎯 Роль latency_guard
Это policy-level компонент:
читает SLO
принимает решение
вызывает infra-action
👉 точка, где бизнес-правило превращается в действие
"""