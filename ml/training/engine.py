"""Reusable training and evaluation engine for PyTorch models."""

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from ml.training.metrics import calculate_binary_metrics, calculate_multiclass_metrics


class TrainingEngine:
    """Orchestrates model training, evaluation, early stopping, and checkpoint saving."""

    def __init__(
        self,
        model: nn.Module,
        optimizer: torch.optim.Optimizer,
        criterion: nn.Module,
        device: torch.device,
        scheduler: Optional[Any] = None,
    ) -> None:
        self.model = model
        self.optimizer = optimizer
        self.criterion = criterion
        self.device = device
        self.scheduler = scheduler

    def train_epoch(
        self,
        loader: DataLoader,
        task_type: str = "binary",
    ) -> Dict[str, float]:
        """Execute one complete training epoch."""
        self.model.train()
        total_loss = 0.0
        n_samples = 0

        for batch_imgs, batch_labels, _ in loader:
            batch_imgs = batch_imgs.to(self.device)
            batch_labels = batch_labels.to(self.device)

            self.optimizer.zero_grad()
            logits = self.model(batch_imgs)

            if task_type == "binary":
                # Ensure batch_labels is [B, 1] float
                loss = self.criterion(logits, batch_labels.float())
            else:
                # multiclass CrossEntropyLoss expects target as [B] int64
                target = batch_labels.squeeze(-1).long() if batch_labels.dim() > 1 else batch_labels.long()
                loss = self.criterion(logits, target)

            loss.backward()
            self.optimizer.step()

            bs = batch_imgs.size(0)
            total_loss += loss.item() * bs
            n_samples += bs

        if self.scheduler:
            self.scheduler.step()

        avg_loss = total_loss / n_samples if n_samples > 0 else 0.0
        current_lr = self.optimizer.param_groups[0]["lr"]

        return {"train_loss": round(avg_loss, 4), "lr": current_lr}

    @torch.no_grad()
    def evaluate(
        self,
        loader: DataLoader,
        task_type: str = "binary",
        class_names: Optional[List[str]] = None,
        threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """Run validation or test evaluation and compute full metrics."""
        self.model.eval()
        total_loss = 0.0
        n_samples = 0

        all_probs: List[np.ndarray] = []
        all_targets: List[np.ndarray] = []

        for batch_imgs, batch_labels, _ in loader:
            batch_imgs = batch_imgs.to(self.device)
            batch_labels = batch_labels.to(self.device)

            logits = self.model(batch_imgs)

            if task_type == "binary":
                target = batch_labels.float()
                loss = self.criterion(logits, target)
                probs = torch.sigmoid(logits).cpu().numpy().flatten()
                targets = target.cpu().numpy().flatten()
            else:
                target = batch_labels.squeeze(-1).long() if batch_labels.dim() > 1 else batch_labels.long()
                loss = self.criterion(logits, target)
                probs = torch.softmax(logits, dim=1).cpu().numpy()
                targets = target.cpu().numpy()

            bs = batch_imgs.size(0)
            total_loss += loss.item() * bs
            n_samples += bs

            all_probs.append(probs)
            all_targets.append(targets)

        avg_loss = total_loss / n_samples if n_samples > 0 else 0.0

        if task_type == "binary":
            y_true = np.concatenate(all_targets) if all_targets else np.array([])
            y_prob = np.concatenate(all_probs) if all_probs else np.array([])
            metrics = calculate_binary_metrics(y_true, y_prob, threshold=threshold)
        else:
            y_true = np.concatenate(all_targets) if all_targets else np.array([])
            y_prob = np.vstack(all_probs) if all_probs else np.array([[]])
            c_names = class_names or [f"class_{i}" for i in range(y_prob.shape[1])]
            metrics = calculate_multiclass_metrics(y_true, y_prob, class_names=c_names)

        metrics["loss"] = round(avg_loss, 4)
        return metrics

    def fit(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        epochs: int,
        checkpoint_path: Path,
        task_type: str = "binary",
        primary_metric: str = "balanced_accuracy",
        class_names: Optional[List[str]] = None,
        patience: int = 3,
        extra_meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Full training loop with validation-based checkpoint saving and early stopping."""
        checkpoint_path = Path(checkpoint_path)
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

        history: List[Dict[str, Any]] = []
        best_score = -float("inf")
        best_epoch = 0
        patience_counter = 0

        for epoch in range(1, epochs + 1):
            train_res = self.train_epoch(train_loader, task_type=task_type)
            val_res = self.evaluate(val_loader, task_type=task_type, class_names=class_names)

            current_score = float(val_res.get(primary_metric, 0.0))

            epoch_record = {
                "epoch": epoch,
                "train_loss": train_res["train_loss"],
                "val_loss": val_res["loss"],
                "lr": train_res["lr"],
                primary_metric: current_score,
                "val_accuracy": val_res.get("accuracy"),
            }
            if task_type == "binary":
                epoch_record["val_f1"] = val_res.get("f1")
                epoch_record["val_sensitivity"] = val_res.get("recall_sensitivity")
                epoch_record["val_specificity"] = val_res.get("specificity")
            else:
                epoch_record["val_macro_f1"] = val_res.get("macro_f1")
                epoch_record["val_weighted_f1"] = val_res.get("weighted_f1")

            history.append(epoch_record)
            print(
                f"Epoch {epoch:02d}/{epochs:02d} | Train Loss: {train_res['train_loss']:.4f} | "
                f"Val Loss: {val_res['loss']:.4f} | Val {primary_metric}: {current_score:.4f}"
            )

            # Check improvement
            if current_score > best_score:
                best_score = current_score
                best_epoch = epoch
                patience_counter = 0

                # Save best checkpoint
                checkpoint_payload = {
                    "epoch": epoch,
                    "model_state_dict": self.model.state_dict(),
                    "optimizer_state_dict": self.optimizer.state_dict(),
                    "best_score": best_score,
                    "primary_metric": primary_metric,
                    "task_type": task_type,
                    "class_names": class_names,
                    "extra_meta": extra_meta or {},
                }
                torch.save(checkpoint_payload, checkpoint_path)
                print(f"  --> Saved new best checkpoint ({primary_metric}: {best_score:.4f})")
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    print(f"Early stopping triggered at epoch {epoch} (patience={patience})")
                    break

        return {
            "best_epoch": best_epoch,
            "best_score": best_score,
            "primary_metric": primary_metric,
            "history": history,
            "checkpoint_path": str(checkpoint_path),
        }
