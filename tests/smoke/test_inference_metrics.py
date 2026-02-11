# tests/smoke/test_inference_metrics.py
# — SMOKE TEST FOR INFERENCE METRICS COLLECTOR


import json
import numpy as np
from pathlib import Path


from app.ml.monitoring.inference_metrics import collect_inference_metrics


def test_inference_metrics_smoke(monkeypatch, tmp_path):
    """
    Smoke test:
    - метрики инференса сохраняются
    - файл inference_metrics.jsonl создаётся
    - структура записи корректна
    """

    # 🔹 изолируем METRICS_DIR
    monkeypatch.setenv("METRICS_DIR", str(tmp_path))  # меняем на лету переменную окружения

    inputs = np.array([[1.0, 2.0], [3.0, 4.0]])
    outputs = np.array([10.0, 20.0])

    record = collect_inference_metrics(
        ml_model_id="test_model_v1",
        inputs=inputs,
        outputs=outputs,
        latency_ms=12.5,
    )

    metrics_file = tmp_path / "inference_metrics.jsonl"

    # ✅ файл создан
    assert metrics_file.exists()

    # ✅ запись возвращена
    assert record["ml_model_id"] == "test_model_v1"
    assert record["latency_ms"] == 12.5

    # ✅ проверяем содержимое файла
    lines = metrics_file.read_text().strip().splitlines()
    assert len(lines) == 1

    stored = json.loads(lines[0])

    assert stored["input_shape"] == [2, 2]
    assert stored["output_shape"] == [2]

    assert "output_stats" in stored
    assert stored["output_stats"]["mean"] == 15.0
