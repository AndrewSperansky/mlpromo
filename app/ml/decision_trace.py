
# app/ml/decision_trace.py

from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any


# =========================
# --- DATA STRUCTURES ---
# =========================

@dataclass
class DriftInfo:
    data_drift: bool = False
    shap_drift: bool = False
    severity: str = "none"  # none | low | medium | severe


@dataclass
class LatencyInfo:
    p95: Optional[float] = None
    breach: bool = False


@dataclass
class PerformanceInfo:
    current_metric: Optional[float] = None
    baseline_metric: Optional[float] = None
    delta: Optional[float] = None


@dataclass
class DecisionTrace:
    timestamp: str
    active_model: Optional[str] = None
    shadow_model: Optional[str] = None
    drift: DriftInfo = field(default_factory=DriftInfo)
    latency: LatencyInfo = field(default_factory=LatencyInfo)
    performance: PerformanceInfo = field(default_factory=PerformanceInfo)
    tradeoff_decision: Optional[str] = None
    freeze_flag: bool = False
    final_decision: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert trace to serializable dict.
        """
        return asdict(self)

    def to_json(self) -> str:
        """
        Convert trace to formatted JSON string.
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


# =========================
# --- TRACE BUILDER ---
# =========================

class DecisionTraceBuilder:
    """
    Builder for structured decision trace.
    Used during runtime evaluation.
    """

    def __init__(self):
        self._trace = DecisionTrace(
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    # ---- Model Context ----

    def set_models(self, active_model: Optional[str], shadow_model: Optional[str]):
        self._trace.active_model = active_model
        self._trace.shadow_model = shadow_model
        return self

    # ---- Drift ----

    def set_drift(self, data_drift: bool, shap_drift: bool, severity: str):
        self._trace.drift = DriftInfo(
            data_drift=data_drift,
            shap_drift=shap_drift,
            severity=severity,
        )
        return self

    # ---- Latency ----

    def set_latency(self, p95: Optional[float], breach: bool):
        self._trace.latency = LatencyInfo(
            p95=p95,
            breach=breach,
        )
        return self

    # ---- Performance ----

    def set_performance(
        self,
        current_metric: Optional[float],
        baseline_metric: Optional[float],
    ):
        delta = None
        if current_metric is not None and baseline_metric is not None:
            delta = current_metric - baseline_metric

        self._trace.performance = PerformanceInfo(
            current_metric=current_metric,
            baseline_metric=baseline_metric,
            delta=delta,
        )
        return self

    # ---- Decisions ----

    def set_tradeoff_decision(self, decision: Optional[str]):
        self._trace.tradeoff_decision = decision
        return self

    def set_freeze_flag(self, freeze: bool):
        self._trace.freeze_flag = freeze
        return self

    def set_final_decision(self, decision: Optional[str]):
        self._trace.final_decision = decision
        return self

    # ---- Build ----

    def build(self) -> DecisionTrace:
        return self._trace


# =========================
# --- FILE PERSISTENCE ---
# =========================

def save_decision_trace(
    trace: DecisionTrace,
    output_dir: Path,
    filename: Optional[str] = None,
) -> Path:
    """
    Persist decision trace to file.

    If filename not provided — generates timestamp-based name.
    """

    output_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        filename = f"decision_trace_{trace.timestamp.replace(':', '-')}.json"

    path = output_dir / filename

    with path.open("w", encoding="utf-8") as f:
        f.write(trace.to_json())

    return path
