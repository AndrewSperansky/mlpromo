# app/ml_torch/models/base.py

import torch
import torch.nn as nn
from abc import ABC, abstractmethod


class BaseTorchModel(nn.Module, ABC):
    """Базовый класс для всех PyTorch моделей"""

    @abstractmethod
    def forward(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_config(self) -> dict:
        """Возвращает конфигурацию модели для сохранения в meta"""
        pass

    def save(self, path: str):
        torch.save({
            'model_state_dict': self.state_dict(),
            'config': self.get_config()
        }, path)

    @classmethod
    def load(cls, path: str, config: dict):
        model = cls(**config)
        checkpoint = torch.load(path, map_location='cpu')
        model.load_state_dict(checkpoint['model_state_dict'])
        return model