# app/ml_torch/models/mlp.py

import torch
import torch.nn as nn
from ml_torch.models.base import BaseTorchModel

class MLPUpliftModel(BaseTorchModel):
    """MLP + Embeddings для категориальных признаков"""

    def __init__(
            self,
            numeric_features: int,
            categorical_dims: dict,  # {feature_name: cardinality}
            embedding_dim: int = 16,
            hidden_dims: list = [128, 64, 32],     # ignore
            dropout: float = 0.2
    ):
        super().__init__()

        # Embeddings для категориальных признаков
        self.embeddings = nn.ModuleDict({
            name: nn.Embedding(dim, embedding_dim)
            for name, dim in categorical_dims.items()
        })

        embedding_total = len(categorical_dims) * embedding_dim
        input_dim = numeric_features + embedding_total

        # Dense слои
        layers = []
        prev_dim = input_dim
        for h_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, h_dim),
                nn.BatchNorm1d(h_dim),
                nn.ReLU(),
                nn.Dropout(dropout)
            ])
            prev_dim = h_dim

        layers.append(nn.Linear(prev_dim, 1))
        self.network = nn.Sequential(*layers)

    def forward(self, x_numeric, x_categorical):
        # Embeddings
        embedded = [self.embeddings[name](x_categorical[name]) for name in self.embeddings]
        x = torch.cat([x_numeric] + embedded, dim=1)
        return self.network(x).squeeze(-1)

    def get_config(self):
        return {"type": "mlp"}