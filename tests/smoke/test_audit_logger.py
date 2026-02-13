# app/ml/decision_engine.py

from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, Any

from app.ml.decision_trace import (
    DecisionTrace,
    DecisionTraceBuilder,
    save_decision_trace,
)

from app.ml.runtime_state import ML_RUNTIME_STATE
from app.ml.monitoring.combined_drift_detector import detect_combined_drift
from app.ml.monitoring.latency_guard import latency_guard
from app.ml.model_registry.tradeoff_policy import decide_tradeoff
from app.ml.model_registry.promotion_policy import decide_promotion
from app.ml.audit_logger import AuditLogger


class DecisionEngine:
    """
    Functional-style orchestration layer
    compatible with current project architecture.

    Now includes:
    - Decision Trace
    - Audit Logging
    """

    def __init__(
        self,
        trace_output_dir: Path,
        audit_log_path: Path,
    ):
        self.trace_output_dir = trace_output_dir
        self.audit_logger = AuditLogger(audit_log_path)

    # ==========================================================
    # =================== MAIN ENTRYPOINT ======================
    # ==========================================================

    def evaluate(
        self,
        *,
        shap_drift_report: Dict[str, Any],
        data_drift_report: Dict[str, Any],
        current_metrics: Dict[str, Any],
        candidate_metrics: Dict[str, Any],
        slo_config: Dict[str, Any],
        candidate_version: Optional[str] = None,
    ) -> DecisionTrace:

        builder = DecisionTraceBuilder()

        # ------------------------------------------------------
        # 1. MODEL CONTEXT
        # ------------------------------------------------------

        active_model = ML_RUNTIME_STATE.get("version")
        builder.set_models(active_model, shadow_model=candidate_version)

        # ------------------------------------------------------
        # 2. DRIFT SIGNAL
        # ------------------------------------------------------

        drift_result = detect_combined_drift(
            shap_drift_report=shap_drift_report,
            data_drift_report=data_drift_report,
        )

        severity = "severe" if drift_result.get("combined_drift_detected") else "none"

        builder.set_drift(
            data_drift=drift_result["summary"]["data_drift"],
            shap_drift=drift_result["summary"]["shap_drift"],
            severity=severity,
        )

        # ------------------------------------------------------
        # 3. LATENCY SIGNAL
        # ------------------------------------------------------

        latency_result = latency_guard(
            p95_threshold_ms=slo_config.get("latency_p95_ms", 500),
            p99_threshold_ms=slo_config.get("latency_p99_ms", 800),
        )

        p95 = None
        breach = False

        if "slo" in latency_result:
            p95 = latency_result["slo"].get("p95_ms")
            breach = latency_result["slo"].get("breached", False)

        builder.set_latency(
            p95=p95,
            breach=breach,
        )

        # ------------------------------------------------------
        # 4. PERFORMANCE SIGNAL
        # ------------------------------------------------------

        rmse_current = current_metrics.get("rmse")
        rmse_candidate = candidate_metrics.get("rmse")

        builder.set_performance(
            current_metric=rmse_candidate,
            baseline_metric=rmse_current,
        )

        # ------------------------------------------------------
        # 5. TRADEOFF DECISION
        # ------------------------------------------------------

        tradeoff = decide_tradeoff(
            current_metrics=current_metrics,
            candidate_metrics=candidate_metrics,
            slo_config=slo_config,
        )

        tradeoff_decision = tradeoff.get("decision")
        builder.set_tradeoff_decision(tradeoff_decision)

        # ------------------------------------------------------
        # 6. PROMOTION DECISION
        # ------------------------------------------------------

        promotion = decide_promotion(
            candidate_metrics=candidate_metrics,
            current_metrics=current_metrics,
            drift_report=drift_result,
            slo_config=slo_config,
        )

        final_decision = promotion.get("decision")
        reason = promotion.get("reason")

        builder.set_final_decision(final_decision)

        # ------------------------------------------------------
        # 7. AUDIT LOGGING
        # ------------------------------------------------------

        self.audit_logger.log_promotion(
            decision=final_decision,
            candidate_version=candidate_version,
            reason=reason,
        )

        if severity == "severe":
            self.audit_logger.log_event(
                event_type="drift_detected",
                payload=drift_result,
            )

        if breach:
            self.audit_logger.log_event(
                event_type="latency_breach",
                payload=latency_result,
            )

        # ------------------------------------------------------
        # 8. BUILD + SAVE TRACE
        # ------------------------------------------------------

        trace = builder.build()

        save_decision_trace(
            trace=trace,
            output_dir=self.trace_output_dir,
        )

        return trace
