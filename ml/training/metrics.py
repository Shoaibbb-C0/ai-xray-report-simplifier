"""Comprehensive performance metrics calculation for binary and multi-class models."""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np


def calculate_binary_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float = 0.5,
) -> Dict[str, Any]:
    """Calculate clinical and classification metrics for binary tasks.
    
    y_true: binary array {0, 1}
    y_prob: continuous probability array [0.0, 1.0]
    """
    y_true = np.asarray(y_true, dtype=int)
    y_prob = np.asarray(y_prob, dtype=float)
    y_pred = (y_prob >= threshold).astype(int)

    # Confusion matrix elements
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))

    total = len(y_true)
    accuracy = (tp + tn) / total if total > 0 else 0.0

    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0  # Recall
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    balanced_acc = (sensitivity + specificity) / 2.0

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    f1 = (2 * precision * sensitivity) / (precision + sensitivity) if (precision + sensitivity) > 0 else 0.0

    # ROC-AUC calculation (trapezoidal integration across sorting order)
    roc_auc = _compute_roc_auc(y_true, y_prob)
    pr_auc = _compute_pr_auc(y_true, y_prob)

    return {
        "accuracy": round(float(accuracy), 4),
        "balanced_accuracy": round(float(balanced_acc), 4),
        "precision": round(float(precision), 4),
        "recall_sensitivity": round(float(sensitivity), 4),
        "specificity": round(float(specificity), 4),
        "f1": round(float(f1), 4),
        "roc_auc": round(float(roc_auc), 4) if roc_auc is not None else None,
        "pr_auc": round(float(pr_auc), 4) if pr_auc is not None else None,
        "true_positives": tp,
        "true_negatives": tn,
        "false_positives": fp,
        "false_negatives": fn,
        "confusion_matrix": [[tn, fp], [fn, tp]],
        "threshold": float(threshold),
        "total_samples": total,
    }


def calculate_multiclass_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    class_names: List[str],
) -> Dict[str, Any]:
    """Calculate multi-class metrics including macro-F1, balanced accuracy, and per-class stats.
    
    y_true: array of class indices [0 .. C-1]
    y_prob: array of shape [N, C] containing class probabilities
    """
    y_true = np.asarray(y_true, dtype=int)
    y_prob = np.asarray(y_prob, dtype=float)
    y_pred = np.argmax(y_prob, axis=1)

    n_classes = len(class_names)
    cm = np.zeros((n_classes, n_classes), dtype=int)
    for t, p in zip(y_true, y_pred):
        if 0 <= t < n_classes and 0 <= p < n_classes:
            cm[t, p] += 1

    total = len(y_true)
    accuracy = float(np.trace(cm) / total) if total > 0 else 0.0

    per_class = {}
    f1_list = []
    recall_list = []
    support_list = []

    for i, name in enumerate(class_names):
        tp = int(cm[i, i])
        fp = int(np.sum(cm[:, i]) - tp)
        fn = int(np.sum(cm[i, :]) - tp)
        support = int(np.sum(cm[i, :]))

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        per_class[name.upper()] = {
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1": round(float(f1), 4),
            "support": support,
        }
        f1_list.append(f1)
        recall_list.append(rec)
        support_list.append(support)

    macro_f1 = float(np.mean(f1_list))
    balanced_acc = float(np.mean(recall_list))
    weighted_f1 = float(np.sum(np.array(f1_list) * np.array(support_list)) / total) if total > 0 else 0.0

    return {
        "accuracy": round(accuracy, 4),
        "balanced_accuracy": round(balanced_acc, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "per_class": per_class,
        "confusion_matrix": cm.tolist(),
        "total_samples": total,
    }


def _compute_roc_auc(y_true: np.ndarray, y_score: np.ndarray) -> Optional[float]:
    """Compute Area Under Receiver Operating Characteristic Curve."""
    n_pos = np.sum(y_true == 1)
    n_neg = np.sum(y_true == 0)
    if n_pos == 0 or n_neg == 0:
        return None

    # Rank score
    order = np.argsort(y_score)
    ranks = np.empty_like(order)
    ranks[order] = np.arange(len(y_score))
    sum_ranks_pos = np.sum(ranks[y_true == 1])
    u_stat = sum_ranks_pos - (n_pos * (n_pos - 1)) / 2.0
    return float(u_stat / (n_pos * n_neg))


def _compute_pr_auc(y_true: np.ndarray, y_score: np.ndarray) -> Optional[float]:
    """Compute Area Under Precision-Recall Curve via trapezoidal rule."""
    n_pos = np.sum(y_true == 1)
    if n_pos == 0:
        return None

    thresholds = np.linspace(0.0, 1.0, 101)
    recalls = []
    precisions = []

    for t in sorted(thresholds, reverse=True):
        y_pred = (y_score >= t).astype(int)
        tp = np.sum((y_true == 1) & (y_pred == 1))
        fp = np.sum((y_true == 0) & (y_pred == 1))
        rec = tp / n_pos
        prec = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        recalls.append(rec)
        precisions.append(prec)

    # Trapezoid integration
    auc = 0.0
    for i in range(1, len(recalls)):
        auc += (recalls[i] - recalls[i - 1]) * (precisions[i] + precisions[i - 1]) / 2.0
    return float(auc)
