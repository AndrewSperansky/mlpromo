# app/ml/self_healing/self_healing_worker.py

from __future__ import annotations

import threading
import time
from typing import Optional

from app.ml.self_healing.retrain_orchestrator import RetrainOrchestrator


class SelfHealingWorker:
    """
    Stage 5.2.5 — Background Self-Healing Worker

    - Runs RetrainOrchestrator periodically
    - Non-blocking (daemon thread)
    - Safe exception handling
    """

    def __init__(self, interval_seconds: int = 30):
        self.interval_seconds = interval_seconds
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._orchestrator = RetrainOrchestrator()

    # --------------------------------------------------
    # Worker Loop
    # --------------------------------------------------

    def _run_loop(self):

        while not self._stop_event.is_set():
            try:
                self._orchestrator.process()
            except Exception as e:
                # Никогда не падаем — self-healing не должен ломать backend
                print(f"[SelfHealingWorker] error: {e}")

            time.sleep(self.interval_seconds)

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def start(self):

        if self._thread and self._thread.is_alive():
            return

        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
        )
        self._thread.start()

    def stop(self):

        self._stop_event.set()

        if self._thread:
            self._thread.join(timeout=5)
