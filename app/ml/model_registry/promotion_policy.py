# app/ml/model_registry/promotion_policy.py
# — METRICS-GATED PROMOTION POLICY (PROD-LIKE)

from typing import Dict, Any


def decide_promotion(
    candidate_metrics: Dict[str, float],
    current_metrics: Dict[str, float] | None,
    policy: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Решение о promotion модели на основе метрик.

    Логика максимально приближена к MLflow / SageMaker:
    - явные метрики
    - явные пороги
    - детерминированное решение
    - audit-friendly output
    """

    policy = policy or {
        "metric": "rmse",
        "mode": "lower_is_better",
        "min_improvement": 0.0,
    }

    metric = policy["metric"]
    min_improvement = policy["min_improvement"]

    candidate_value = candidate_metrics.get(metric)

    if candidate_value is None:
        return {
            "promote": False,
            "reason": f"Candidate metric '{metric}' missing",
        }

    # 🟨 если current отсутствует — разрешаем promotion
    if current_metrics is None:
        return {
            "promote": True,
            "reason": "No current model — bootstrap promotion",
        }

    current_value = current_metrics.get(metric)

    if current_value is None:
        return {
            "promote": False,
            "reason": f"Current metric '{metric}' missing",
        }

    improvement = current_value - candidate_value

    if improvement >= min_improvement:
        return {
            "promote": True,
            "reason": (
                f"{metric} improved "
                f"from {current_value:.4f} to {candidate_value:.4f}"
            ),
            "improvement": improvement,
        }

    return {
        "promote": False,
        "reason": (
            f"{metric} not improved enough "
            f"(current={current_value:.4f}, candidate={candidate_value:.4f})"
        ),
        "improvement": improvement,
    }

