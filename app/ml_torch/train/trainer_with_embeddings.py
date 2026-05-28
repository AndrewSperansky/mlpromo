# app/ml_torch/train/trainer_with_embeddings.py

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from typing import Dict, Any
import logging

logger = logging.getLogger("promo_ml")


class TorchTrainerWithEmbeddings:
    """Обучатель для моделей с эмбеддингами (3 входа: numeric, categorical, target)"""

    def __init__(self, model: nn.Module, learning_rate: float = 0.001, device: str = "cpu"):
        self.model = model.to(device)
        self.device = device
        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()
        self.history = {"train_loss": [], "val_loss": []}

    def train_epoch(self, dataloader: DataLoader) -> float:
        self.model.train()
        total_loss = 0.0

        for X_numeric, X_categorical, y in dataloader:
            X_numeric = X_numeric.to(self.device)
            X_categorical = X_categorical.to(self.device)
            y = y.to(self.device)

            self.optimizer.zero_grad()
            predictions = self.model(X_numeric, X_categorical)
            loss = self.criterion(predictions, y)
            loss.backward()
            self.optimizer.step()
            total_loss += loss.item()

        return total_loss / len(dataloader)

    def validate_epoch(self, dataloader: DataLoader) -> float:
        self.model.eval()
        total_loss = 0.0

        with torch.no_grad():
            for X_numeric, X_categorical, y in dataloader:
                X_numeric = X_numeric.to(self.device)
                X_categorical = X_categorical.to(self.device)
                y = y.to(self.device)

                predictions = self.model(X_numeric, X_categorical)
                loss = self.criterion(predictions, y)
                total_loss += loss.item()

        return total_loss / len(dataloader)

    def train(
        self,
        train_dataloader: DataLoader,
        val_dataloader: DataLoader,
        epochs: int = 50,
        early_stopping_patience: int = 10
    ) -> Dict[str, Any]:
        best_val_loss = float('inf')
        patience_counter = 0

        for epoch in range(epochs):
            train_loss = self.train_epoch(train_dataloader)

            if val_dataloader:
                val_loss = self.validate_epoch(val_dataloader)
                logger.info(f"Epoch {epoch + 1}/{epochs} | Train Loss: {train_loss:.6f} | Val Loss: {val_loss:.6f}")
                self.history["train_loss"].append(train_loss)
                self.history["val_loss"].append(val_loss)

                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                    self.save_checkpoint("best_model.pt")
                else:
                    patience_counter += 1

                if patience_counter >= early_stopping_patience:
                    logger.info(f"Early stopping на эпохе {epoch + 1}")
                    break
            else:
                logger.info(f"Epoch {epoch + 1}/{epochs} | Train Loss: {train_loss:.6f}")
                self.history["train_loss"].append(train_loss)

        return {
            "history": self.history,
            "best_val_loss": best_val_loss if val_dataloader else None,
            "epochs_completed": epoch + 1
        }

    def save_checkpoint(self, path: str):
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'history': self.history
        }, path)

    def load_checkpoint(self, path: str):
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.history = checkpoint['history']