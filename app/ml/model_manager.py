# app/ml/model_manager.py
import asyncio
from pathlib import Path
import time
import pickle
from typing import Optional

class ModelManager:
    def __init__(self, model_path: str, check_interval: int = 10):
        self.model_path = Path(model_path)
        self._model = None
        self._mtime = 0.0
        self.check_interval = check_interval

    def load(self):
        if not self.model_path.exists():
            raise FileNotFoundError(self.model_path)
        with open(self.model_path, "rb") as f:
            self._model = pickle.load(f)
        self._mtime = self.model_path.stat().st_mtime

    def get(self):
        return self._model

    async def watch(self):
        while True:
            try:
                mtime = self.model_path.stat().st_mtime
                if mtime != self._mtime:
                    self.load()
                    # логирование перезагрузки
                    import logging
                    logging.getLogger("uvicorn").info(f"Model reloaded from {self.model_path}")
            except FileNotFoundError:
                pass
            await asyncio.sleep(self.check_interval)
