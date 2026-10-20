"""Bounded CPU reproduction: validation selects checkpoints/policies, test runs once.

python -m ml.training.final_run --task body_part
python -m ml.training.final_run --task fracture
python -m ml.training.final_run --task validator
Historical Stage 3/4 reports are retained; new artifacts live under final_v1.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import gc
import hashlib
import json
import platform
from pathlib import Path
import random
import subprocess
import time

import numpy as np
import torch
from torch import nn
from torchvision import transforms
from ml.datasets.adapters.base import NormalizedSample
from ml.datasets.registry import PROJECT_ROOT
from ml.datasets.torch_dataset import NormalizedXRayDataset, create_xray_dataloader
from ml.models.body_part_classifier import BodyPartClassifierCNN
from ml.models.fracture_classifier import FractureClassifierCNN
from ml.models.xray_validator import XRayValidatorCNN
from ml.training.engine import TrainingEngine
from ml.training.metrics import calculate_binary_metrics, calculate_multiclass_metrics
from ml.preprocessing.pipeline import XRayPreprocessor

SPLITS = PROJECT_ROOT / "ml/datasets/splits/final_v1"
OUTPUT = PROJECT_ROOT / "ml/saved_models/final_v1"
CLASSES = ["hand", "leg", "hip", "shoulder"]
INPUT_SIZE = 128


def load(task, split):
    return [NormalizedSample.from_dict(row) for row in json.loads((SPLITS / task / f"{split}.json").read_text())]


def predict(model, loader, multiclass=False):
    model.eval()
    probabilities, labels = [], []
    with torch.inference_mode():
        for images, target, _ in loader:
            output = model(images)
            probabilities.extend((torch.softmax(output, 1) if multiclass else torch.sigmoid(output).flatten()).numpy().tolist())
            labels.extend(target.numpy().reshape(-1).tolist())
    return np.asarray(labels), np.asarray(probabilities)


def binary_policy(labels, probabilities, task):
    candidates = [(threshold, calculate_binary_metrics(labels, probabilities, threshold)) for threshold in np.linspace(.05, .95, 91)]
    if task == "fracture":
        eligible = [(threshold, metrics) for threshold, metrics in candidates if metrics["recall_sensitivity"] >= .75 and metrics["specificity"] >= .35]
        threshold, metrics = max(eligible or candidates, key=lambda pair: (pair[1]["f1"], pair[1]["balanced_accuracy"]))
    else:
        threshold, metrics = max(candidates, key=lambda pair: pair[1]["balanced_accuracy"])
    # Validation-only margin; uncertain outcomes never become diagnosis claims.
    margin = .10
    return {"decision_threshold": round(float(threshold), 4),
            "lower_bound": round(max(.02, float(threshold) - margin), 4),
            "upper_bound": round(min(.98, float(threshold) + margin), 4),
            "selection_split": "validation", "validation_metrics": metrics,
            "uncertainty_method": "prespecified +/-0.10 probability rejection margin"}


def run(task):
    torch.set_num_threads(2)
    torch.manual_seed(42); np.random.seed(42); random.seed(42)
    train, validation = load(task, "train"), load(task, "validation")
    output = OUTPUT / task
    output.mkdir(parents=True, exist_ok=True)
    multiclass = task == "body_part"
    dataset_task = "body_part" if multiclass else "binary"
    preprocessor = XRayPreprocessor(target_size=(INPUT_SIZE, INPUT_SIZE))
    validation_dataset = NormalizedXRayDataset(validation, task=dataset_task, cache_tensors=True, preprocessor=preprocessor)
    val_loader = create_xray_dataloader(validation_dataset, batch_size=16)
    model_class = {"validator": XRayValidatorCNN, "body_part": BodyPartClassifierCNN, "fracture": FractureClassifierCNN}[task]
    experiments = [("baseline", 6 if multiclass else 5, False)]
    if task == "fracture":
        experiments = [("baseline", 4, False), ("conservative_augmentation", 6, True)]
    comparisons = []
    started = time.perf_counter()
    for name, epochs, augment in experiments:
        torch.manual_seed(42)
        model = model_class()
        augmentation = transforms.Compose([transforms.RandomHorizontalFlip(), transforms.RandomAffine(6, translate=(.03,.03), scale=(.97,1.03))]) if augment else None
        if task == "validator":
            # Apply the same resolution perturbation to both labels, reducing
            # reliance on low-resolution negative-source texture differences.
            augmentation = transforms.RandomApply([transforms.Resize((32,32)), transforms.Resize((INPUT_SIZE,INPUT_SIZE))], p=.5)
        augmentation_description = (
            "Both labels: resize 32px then 128px, probability 0.5" if task == "validator"
            else "Horizontal flip; affine rotation +/-6deg, translation +/-3%, scale 0.97-1.03" if augment
            else "None"
        )
        train_dataset = NormalizedXRayDataset(train, task=dataset_task, cache_tensors=True, transform=augmentation, preprocessor=preprocessor)
        train_loader = create_xray_dataloader(train_dataset, batch_size=16, shuffle=True)
        if multiclass:
            counts = Counter(row.body_part for row in train)
            criterion = nn.CrossEntropyLoss(weight=torch.tensor([len(train)/(4*counts[part]) for part in CLASSES]))
        else:
            positives = sum(bool(row.is_abnormal) for row in train)
            criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([(len(train)-positives)/positives]))
        optimizer = torch.optim.AdamW(model.parameters(), lr=.001, weight_decay=.0001)
        engine = TrainingEngine(model, optimizer, criterion, torch.device("cpu"),
            scheduler=torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=.5, patience=1))
        checkpoint = output / f"{name}.pt"
        print(f"TRAIN {task}/{name}: {len(train)} train, {len(validation)} validation", flush=True)
        history = engine.fit(train_loader, val_loader, epochs, checkpoint,
            task_type="multiclass" if multiclass else "binary",
            primary_metric="macro_f1" if multiclass else "balanced_accuracy" if task == "validator" else "f1",
            class_names=CLASSES if multiclass else None, patience=3,
            extra_meta={"task":task,"split_version":"final_v1","seed":42,"augmentation":augmentation_description})
        model.load_state_dict(torch.load(checkpoint, map_location="cpu", weights_only=True)["model_state_dict"])
        labels, probabilities = predict(model, val_loader, multiclass)
        policy = {"unknown_threshold": .60, "selection_split":"validation"} if multiclass else binary_policy(labels, probabilities, task)
        metrics = calculate_multiclass_metrics(labels, probabilities, CLASSES) if multiclass else policy["validation_metrics"]
        selection = metrics["macro_f1"] if multiclass else metrics["balanced_accuracy"] if task == "validator" else metrics["f1"]
        comparisons.append({"name":name,"augmentation":augmentation_description,"selection_score":selection,"validation_metrics":metrics,"policy":policy,"history":history})
        del train_loader, train_dataset, model, optimizer, engine
        gc.collect()
    chosen = max(comparisons, key=lambda row: row["selection_score"])
    model = model_class()
    checkpoint_data = torch.load(output / f"{chosen['name']}.pt", map_location="cpu", weights_only=True)
    model.load_state_dict(checkpoint_data["model_state_dict"])
    # All choices above are frozen before loading the final test manifest.
    test = load(task, "test")
    test_loader = create_xray_dataloader(NormalizedXRayDataset(test, task=dataset_task, preprocessor=preprocessor), batch_size=16)
    test_started = time.perf_counter()
    labels, probabilities = predict(model, test_loader, multiclass)
    metrics = calculate_multiclass_metrics(labels, probabilities, CLASSES) if multiclass else calculate_binary_metrics(labels, probabilities, chosen["policy"]["decision_threshold"])
    report = {"task":task,"selected":chosen["name"],"test_metrics":metrics,"policy":chosen["policy"],
              "experiments":comparisons,"test_evaluated_once":True,"per_region":{},
              "inference_ms_per_image":round((time.perf_counter()-test_started)*1000/len(test),2)}
    if multiclass:
        accepted = probabilities.max(axis=1) >= chosen["policy"]["unknown_threshold"]
        report["unknown_rejection"] = {"accepted":int(accepted.sum()),"rejected":int((~accepted).sum()),
            "coverage":float(accepted.mean()),"accepted_accuracy":float((probabilities.argmax(axis=1)[accepted]==labels[accepted]).mean()) if accepted.any() else None}
    if task == "validator":
        ood_samples = load(task,"ood_test")
        ood_loader = create_xray_dataloader(NormalizedXRayDataset(ood_samples,task="binary",preprocessor=preprocessor),batch_size=16)
        _, ood_probabilities = predict(model,ood_loader)
        report["ood"] = {"source":"DermaMNIST official test only, 500 samples",
            "accepted_as_xray":int((ood_probabilities>chosen["policy"]["upper_bound"]).sum()),
            "rejected_non_xray":int((ood_probabilities<chosen["policy"]["lower_bound"]).sum()),
            "uncertain":int(((ood_probabilities>=chosen["policy"]["lower_bound"])&(ood_probabilities<=chosen["policy"]["upper_bound"])).sum())}
    if not multiclass:
        for part in sorted({row.body_part or row.dataset for row in test}):
            mask = np.array([(row.body_part or row.dataset)==part for row in test])
            report["per_region"][part] = calculate_binary_metrics(labels[mask], probabilities[mask], chosen["policy"]["decision_threshold"])
        # Plot-ready exact curve points; no image data or patient identifiers.
        thresholds = np.unique(np.r_[0, probabilities, 1])
        report["curves"] = [{"threshold":float(t), **{key:value for key,value in calculate_binary_metrics(labels, probabilities,float(t)).items() if key in {"recall_sensitivity","specificity","precision"}}} for t in thresholds]
    final_checkpoint = output / f"best_{task}.pt"
    torch.save(checkpoint_data, final_checkpoint)
    sha = hashlib.sha256(final_checkpoint.read_bytes()).hexdigest()
    metadata = {"model_name":model_class.__name__,"version":"final_v1","architecture":str(model),
        "parameter_count":sum(p.numel() for p in model.parameters()),"split_version":"final_v1",
        "datasets":["FracAtlas", "CIFAR-10", "RetinaMNIST"] if task == "validator" else ["FracAtlas"],
        "manifest_sha256":{split:hashlib.sha256((SPLITS/task/f"{split}.json").read_bytes()).hexdigest() for split in ("train","validation","test")},
        "cpu_threads":2,"python_version":platform.python_version(),"torch_version":str(torch.__version__),
        "git_worktree_dirty":bool(subprocess.check_output(["git","status","--porcelain"],text=True).strip()),
        "best_validation_metric":chosen["validation_metrics"],
        "input_shape":[1,INPUT_SIZE,INPUT_SIZE],"normalization":{"mean":.5,"std":.5},
        "augmentation":chosen["augmentation"],"seed":42,
        "training_date":datetime.now(timezone.utc).isoformat(),"hardware":platform.processor(),
        "device":"cpu","optimizer":"AdamW(lr=.001,weight_decay=.0001)",
        "loss":"weighted CrossEntropyLoss" if multiclass else "train-weighted BCEWithLogitsLoss",
        "policy":chosen["policy"],"checkpoint_file":final_checkpoint.name,"sha256":sha,
        "git_commit":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
        "training_seconds":round(time.perf_counter()-started,1),"test_metrics":metrics,
        "limitations":["Research/educational model, not clinically validated.","FracAtlas has no verified patient identifiers; duplicate clusters are only a proxy."]}
    (output / "model_metadata.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
    (output / "evaluation_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({"task":task,"selected":chosen["name"],"test_metrics":metrics,"sha256":sha}),flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--task",choices=["validator","body_part","fracture"],required=True)
    run(parser.parse_args().task)
