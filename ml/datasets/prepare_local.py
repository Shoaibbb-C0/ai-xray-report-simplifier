"""Prepare a new reproducible run without overwriting historical manifests.

Run after downloading the official ignored FracAtlas, CIFAR10 and MedMNIST files.
All generated image files remain under raw/. No patient uploads are used.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import random

import numpy as np
from PIL import Image
from torchvision.datasets import CIFAR10
from ml.datasets.adapters.fracatlas import FracAtlasAdapter
from ml.datasets.adapters.base import NormalizedSample
from ml.datasets.duplicate_audit import compute_dhash
from ml.datasets.registry import PROJECT_ROOT, RAW_DATASETS_DIR
from ml.datasets.splitting import DatasetSplitter, check_data_leakage

OUT = PROJECT_ROOT / "ml/datasets/splits/final_v1"


def prepare(anatomy_only=False):
    samples = FracAtlasAdapter(RAW_DATASETS_DIR / "fracatlas").load_manifest()
    if len(samples) != 4083:
        raise RuntimeError("The complete official FracAtlas dataset is required")
    # Cluster exact and near dHash matches before any split. Patient IDs are not
    # provided by FracAtlas: duplicate groups are a proxy, not proven patient isolation.
    hashes = []
    for sample in samples:
        with Image.open(sample.image_path) as image:
            hashes.append(compute_dhash(image))
    hashes = np.stack(hashes)
    parent = list(range(len(samples)))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    near_pairs = 0
    for i in range(len(samples)):
        distances = np.count_nonzero(hashes[i + 1:] != hashes[i], axis=1)
        for j in np.flatnonzero(distances <= 2) + i + 1:
            parent[root(int(j))] = root(i)
            near_pairs += 1
    for i, sample in enumerate(samples):
        sample.patient_id = f"duplicate_group_{root(i):05d}"
        sample.image_path = Path(sample.image_path).relative_to(PROJECT_ROOT).as_posix()
    splits = DatasetSplitter(seed=42).split_samples(samples, preserve_existing_splits=False)
    OUT.mkdir(parents=True, exist_ok=True)
    if anatomy_only:
        for task in ("body_part", "fracture"):
            folder = OUT / task
            folder.mkdir(exist_ok=True)
            for split, rows in splits.items():
                selected = rows if task == "fracture" else [row for row in rows if row.body_part in {"hand", "leg", "hip", "shoulder"}]
                (folder / f"{split}.json").write_text(json.dumps([row.to_dict() for row in selected], indent=2), encoding="utf-8")
        print(f"Prepared anatomy/fracture manifests: {near_pairs} near-duplicate pairs grouped before splitting")
        return
    negatives = {split: [] for split in splits}
    negative_root = RAW_DATASETS_DIR / "negative_samples"
    def save_negative(array, name, source, split):
        destination = negative_root / source / f"{name}.png"
        destination.parent.mkdir(parents=True, exist_ok=True)
        # All negative sources fill the same image canvas. Tiny source images
        # must not become a class-specific black-border shortcut after letterboxing.
        Image.fromarray(array).resize((224, 224), Image.Resampling.BICUBIC).save(destination)
        return NormalizedSample(sample_id=f"{source}_{name}", dataset=source,
            image_path=destination.relative_to(PROJECT_ROOT).as_posix(), is_abnormal=False,
            finding_labels=["non_xray"], split=split, metadata={"source_category": source})
    natural_train = CIFAR10(str(negative_root / "cifar10"), train=True, download=False)
    natural_test = CIFAR10(str(negative_root / "cifar10"), train=False, download=False)
    indices = list(range(len(natural_train)))
    random.Random(42).shuffle(indices)
    for split, selected, data in [("train", indices[:1400], natural_train.data),
                                  ("validation", indices[1400:1700], natural_train.data),
                                  ("test", list(range(400)), natural_test.data)]:
        for index in selected:
            name = f"{'official_test' if split == 'test' else 'official_train'}_{index}"
            negatives[split].append(save_negative(data[index], name, "cifar10", split))
    retina_path = negative_root / "retinamnist.npz"
    if hashlib.md5(retina_path.read_bytes()).hexdigest() != "bd4c0672f1bba3e3a89f0e4e876791e4":
        raise RuntimeError("RetinaMNIST checksum mismatch")
    retina = np.load(retina_path, allow_pickle=False)
    for split, official in [("train", "train"), ("validation", "val"), ("test", "test")]:
        for i, array in enumerate(retina[f"{official}_images"]):
            negatives[split].append(save_negative(array, f"{official}_{i}", "retinamnist", split))
    # Remove exact cross-split negative duplicates before training; retain first split.
    seen = set()
    seen_perceptual = []
    removed = 0
    for split in ("train", "validation", "test"):
        keep = []
        for sample in negatives[split]:
            digest = hashlib.sha256((PROJECT_ROOT / sample.image_path).read_bytes()).hexdigest()
            with Image.open(PROJECT_ROOT / sample.image_path) as image:
                perceptual = compute_dhash(image)
            near_seen = any(np.count_nonzero(perceptual != previous) <= 2 for previous in seen_perceptual)
            if digest in seen or near_seen:
                removed += 1
            else:
                seen.add(digest)
                seen_perceptual.append(perceptual)
                keep.append(sample)
        negatives[split] = keep
    OUT.mkdir(parents=True, exist_ok=True)
    summaries = {}
    for task in ("validator", "body_part", "fracture"):
        task_splits = {}
        for split, rows in splits.items():
            if task == "validator":
                records = [NormalizedSample(**{**row.to_dict(), "is_abnormal": True}) for row in rows] + negatives[split]
            elif task == "body_part":
                records = [row for row in rows if row.body_part in {"hand", "leg", "hip", "shoulder"}]
            else:
                records = rows
            task_splits[split] = records
            folder = OUT / task
            folder.mkdir(exist_ok=True)
            (folder / f"{split}.json").write_text(json.dumps([row.to_dict() for row in records], indent=2), encoding="utf-8")
        check_data_leakage(task_splits)
        summaries[task] = {split: {"count": len(rows), "positive": sum(bool(row.is_abnormal) for row in rows),
                "body_parts": dict(Counter(row.body_part for row in rows))} for split, rows in task_splits.items()}
    derma_path = negative_root / "dermamnist.npz"
    if hashlib.md5(derma_path.read_bytes()).hexdigest() != "0744692d530f8e62ec473284d019b0c7":
        raise RuntimeError("DermaMNIST checksum mismatch")
    derma = np.load(derma_path, allow_pickle=False)
    ood = [save_negative(array, f"test_{i}", "dermamnist", "ood_test").to_dict()
           for i, array in enumerate(derma["test_images"][:500])]
    (OUT / "validator/ood_test.json").write_text(json.dumps(ood, indent=2), encoding="utf-8")
    summary = {"version": "final_v1", "seed": 42, "near_duplicate_distance": 2,
        "near_duplicate_pairs": near_pairs, "duplicate_groups": len({root(i) for i in range(len(samples))}),
        "removed_negative_duplicates": removed, "patient_isolation": "unknown; duplicate-group proxy only",
        "sources": {"fracatlas": "CC BY 4.0; official Figshare article 22363012",
                    "retinamnist": "CC BY 4.0; official MedMNIST Zenodo record 10519652",
                    "dermamnist": "CC BY-NC 4.0; OOD only; official MedMNIST",
                    "cifar10": "Official Toronto distribution; cite Krizhevsky 2009"},
        "limitations": ["Natural negatives are CIFAR10 32px; RetinaMNIST and DermaMNIST are 28px, uniformly upsampled before preprocessing.",
            "Resolution/source shortcuts and domain shift remain possible; not clinical validation."],
        "tasks": summaries}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--anatomy-only", action="store_true")
    prepare(parser.parse_args().anatomy_only)
