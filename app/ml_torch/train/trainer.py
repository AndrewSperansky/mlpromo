# app/ml_torch/train/trainer.py

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger("promo_ml")


class TorchTrainer:
    """
    Обучатель PyTorch моделей.

    Английские термины:
    - epoch (рус. эпоха) — один проход по всем данным
    - batch (рус. батч) — порция данных, обрабатываемая за раз
    - loss (рус. потеря) — число, показывающее, насколько модель ошибается
    - gradient descent — движение в сторону уменьшения ошибки
    """

    def __init__(
            self,
            model: nn.Module,
            learning_rate: float = 0.001,
            device: str = "cpu"
    ):
        """
        Args:
            model: нейросеть
            learning_rate: скорость обучения (шаг градиентного спуска)
            device: "cuda" если есть GPU, иначе "cpu"
        """
        self.model = model.to(device)
        self.device = device

        # Adam — оптимизатор (метод настройки весов)
        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

        # MSE Loss — среднеквадратичная ошибка (чем меньше, тем лучше)
        self.criterion = nn.MSELoss()

        self.current_epoch = 0
        self.history = {"train_loss": [], "val_loss": []}

    def train_epoch(self, dataloader: DataLoader) -> float:
        """
        Одна эпоха обучения

        Returns:
            средняя ошибка (loss) за эпоху
        """
        self.model.train()
        total_loss = 0.0

        for X, y in tqdm(dataloader, desc=f"Epoch {self.current_epoch + 1}"):
            X, y = X.to(self.device), y.to(self.device)

            # Обнуляем градиенты (чтобы не накапливались)
            self.optimizer.zero_grad()

            # Предсказание
            predictions = self.model(X)

            # Считаем ошибку
            loss = self.criterion(predictions, y)

            # Обратное распространение (backpropagation)
            loss.backward()

            # Обновляем веса
            self.optimizer.step()

            total_loss += loss.item()

        avg_loss = total_loss / len(dataloader)
        self.history["train_loss"].append(avg_loss)
        return avg_loss

    def validate_epoch(self, dataloader: DataLoader) -> float:
        """
        Валидация (проверка на данных, которые модель не видела)
        """
        self.model.eval()
        total_loss = 0.0

        with torch.no_grad():  # отключаем градиенты (экономия памяти)
            for X, y in dataloader:
                X, y = X.to(self.device), y.to(self.device)
                predictions = self.model(X)
                loss = self.criterion(predictions, y)
                total_loss += loss.item()

        avg_loss = total_loss / len(dataloader)
        self.history["val_loss"].append(avg_loss)
        return avg_loss

    def train(
            self,
            train_dataloader: DataLoader,
            val_dataloader: Optional[DataLoader] = None,
            epochs: int = 50,
            early_stopping_patience: int = 10
    ) -> Dict[str, Any]:
        """
        Полный цикл обучения

        Args:
            train_dataloader: батчи для обучения
            val_dataloader: батчи для валидации (опционально)
            epochs: количество эпох
            early_stopping_patience: сколько эпох ждать улучшения
        """
        best_val_loss = float('inf')
        patience_counter = 0

        for epoch in range(epochs):
            self.current_epoch = epoch

            train_loss = self.train_epoch(train_dataloader)

            if val_dataloader:
                val_loss = self.validate_epoch(val_dataloader)
                logger.info(
                    f"Epoch {epoch + 1}/{epochs} | "
                    f"Train Loss: {train_loss:.6f} | "
                    f"Val Loss: {val_loss:.6f}"
                )

                # Early stopping — останавливаем, если ошибка перестала уменьшаться
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                    # Сохраняем лучшую модель
                    self.save_checkpoint("best_model.pt")
                else:
                    patience_counter += 1

                if patience_counter >= early_stopping_patience:
                    logger.info(f"Early stopping на эпохе {epoch + 1}")
                    break
            else:
                logger.info(f"Epoch {epoch + 1}/{epochs} | Train Loss: {train_loss:.6f}")

        return {
            "history": self.history,
            "best_val_loss": best_val_loss if val_dataloader else None,
            "epochs_completed": self.current_epoch + 1
        }

    def save_checkpoint(self, path: str):
        """Сохраняет состояние модели для последующей загрузки"""
        torch.save({
            'epoch': self.current_epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'history': self.history
        }, path)

    def load_checkpoint(self, path: str):
        """Загружает сохранённую модель"""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.current_epoch = checkpoint['epoch']
        self.history = checkpoint['history']
        logger.info(f"Модель загружена из {path}, эпоха {self.current_epoch}")