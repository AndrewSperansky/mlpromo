
# app/ml/audit_logger.py

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional


class AuditLogger:
    """
    JSON Lines audit logger.

    Каждое событие — одна строка JSON.
    Формат совместим с:
    - Loki
    - ELK
    - SIEM
    - forensic analysis
    """

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    # ==========================================================
    # ====================== PUBLIC API ========================
    # ==========================================================

    def log_event(
        self,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Generic audit event.
        """

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "payload": payload or {},
        }

        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # ----------------------------------------------------------
    # Specialized helpers
    # ----------------------------------------------------------

    def log_prediction(
        self,
        model_version: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
    ) -> None:
        self.log_event(
            event_type="prediction",
            payload={
                "model_version": model_version,
                "input": input_data,
                "output": output_data,
            },
        )

    def log_promotion(
        self,
        decision: str,
        candidate_version: Optional[str],
        reason: Optional[str] = None,
    ) -> None:
        self.log_event(
            event_type="promotion_decision",
            payload={
                "decision": decision,
                "candidate_version": candidate_version,
                "reason": reason,
            },
        )

    def log_rollback(
        self,
        from_version: str,
        to_version: str,
    ) -> None:
        self.log_event(
            event_type="rollback",
            payload={
                "from_version": from_version,
                "to_version": to_version,
            },
        )

    def log_freeze(
        self,
        reason: Optional[str] = None,
    ) -> None:
        self.log_event(
            event_type="freeze",
            payload={
                "reason": reason,
            },
        )

    def log_retrain(
        self,
        trigger_reason: str,
        new_model_version: Optional[str] = None,
    ) -> None:
        self.log_event(
            event_type="retrain",
            payload={
                "trigger_reason": trigger_reason,
                "new_model_version": new_model_version,
            },
        )
