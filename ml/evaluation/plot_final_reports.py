"""Plot aggregate frozen-test reports, never patient images or new test predictions."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from ml.datasets.registry import PROJECT_ROOT


def main():
    destination = PROJECT_ROOT / "docs/ml-figures"
    destination.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "svg.fonttype": "none", "axes.spines.top": False, "axes.spines.right": False})
    for report_file in sorted((PROJECT_ROOT / "ml/saved_models/final_v1").glob("*/evaluation_report.json")):
        report = json.loads(report_file.read_text())
        task = report["task"]
        curves = report.get("curves")
        figure, axes = plt.subplots(1, 3 if curves else 1, figsize=(13, 3.8) if curves else (5, 4.3), squeeze=False)
        axis = axes[0, 0]
        matrix = np.asarray(report["test_metrics"]["confusion_matrix"])
        labels = ["Hand", "Leg", "Hip", "Shoulder"] if task == "body_part" else ["Non-X-ray", "X-ray"] if task == "validator" else ["No fracture label", "Fracture label"]
        axis.imshow(matrix, cmap="Greens")
        axis.set(xticks=range(len(labels)), yticks=range(len(labels)), xticklabels=labels, yticklabels=labels,
                 xlabel="Model label", ylabel="Dataset label", title="Frozen test confusion matrix")
        axis.tick_params(axis="x", rotation=30)
        for (row, column), count in np.ndenumerate(matrix):
            axis.text(column, row, str(count), ha="center", va="center", color="white" if count > matrix.max() / 2 else "#17352a")
        if curves:
            fpr = np.array([1-point["specificity"] for point in curves])[::-1]
            recall = np.array([point["recall_sensitivity"] for point in curves])[::-1]
            precision = np.array([point["precision"] for point in curves])[::-1]
            axes[0, 1].plot(fpr, recall, color="#245d45")
            axes[0, 1].plot([0,1],[0,1],"--",color="#aaaaaa",linewidth=1)
            axes[0, 1].set(xlim=(0,1),ylim=(0,1),xlabel="False positive rate",ylabel="Sensitivity",title=f"ROC-AUC {report['test_metrics']['roc_auc']:.3f}")
            axes[0, 2].plot(recall, precision, color="#b6653e")
            axes[0, 2].set(xlim=(0,1),ylim=(0,1.02),xlabel="Recall",ylabel="Precision",title=f"PR-AUC (101-threshold grid) {report['test_metrics']['pr_auc']:.3f}")
        figure.suptitle(f"{task.replace('_',' ').title()} · final_v1 · research evaluation, not clinical validation",fontsize=11)
        figure.tight_layout()
        figure.savefig(destination / f"{task}.svg", bbox_inches="tight")
        preview = PROJECT_ROOT / ".venv" / f"{task}-evaluation.png"
        figure.savefig(preview, dpi=130, bbox_inches="tight")
        plt.close(figure)
        print(destination / f"{task}.svg")


if __name__ == "__main__":
    main()
