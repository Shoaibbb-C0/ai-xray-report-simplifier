"""Deterministic dataset splitting and leakage verification."""

import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from ml.datasets.adapters.base import NormalizedSample


class DataLeakageError(Exception):
    """Raised when data leakage (patient, study, or sample overlap) is detected across splits."""
    pass


class DatasetSplitter:
    """Deterministic splitter ensuring patient-level or study-level isolation across splits."""

    def __init__(
        self,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        seed: int = 42,
    ) -> None:
        total = train_ratio + val_ratio + test_ratio
        if not (0.999 <= total <= 1.001):
            raise ValueError(f"Ratios must sum to 1.0, got {total}")
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.seed = seed

    def split_samples(
        self,
        samples: List[NormalizedSample],
        preserve_existing_splits: bool = True,
    ) -> Dict[str, List[NormalizedSample]]:
        """Split normalized samples into train, validation, and test subsets.
        
        If samples already contain explicit official split metadata (e.g. MURA's train vs valid),
        and `preserve_existing_splits` is True, those splits are respected.
        Otherwise, samples are grouped by patient_id, study_id, or sample_id to prevent leakage.
        """
        # 1. Check if official splits are already provided and complete
        if preserve_existing_splits:
            existing_splits = defaultdict(list)
            has_explicit = True
            for s in samples:
                if s.split in ("train", "validation", "test"):
                    existing_splits[s.split].append(s)
                else:
                    has_explicit = False
                    break
            if has_explicit and existing_splits:
                # Validate leakage before returning
                check_data_leakage(existing_splits)
                return dict(existing_splits)

        # 2. Group samples by entity (patient_id -> study_id -> sample_id)
        # to ensure that all images from the same patient/study remain in one split
        groups: Dict[str, List[NormalizedSample]] = defaultdict(list)
        for s in samples:
            key = s.patient_id or s.study_id or s.sample_id
            groups[key].append(s)

        sorted_group_keys = sorted(groups.keys())
        rng = random.Random(self.seed)
        rng.shuffle(sorted_group_keys)

        n_total = len(sorted_group_keys)
        n_train = int(n_total * self.train_ratio)
        n_val = int(n_total * self.val_ratio)

        train_keys = set(sorted_group_keys[:n_train])
        val_keys = set(sorted_group_keys[n_train : n_train + n_val])
        test_keys = set(sorted_group_keys[n_train + n_val :])

        splits: Dict[str, List[NormalizedSample]] = {
            "train": [],
            "validation": [],
            "test": [],
        }

        for k, sample_list in groups.items():
            assigned_split = "train" if k in train_keys else ("validation" if k in val_keys else "test")
            for s in sample_list:
                s.split = assigned_split
                splits[assigned_split].append(s)

        # Verify no leakage occurred
        check_data_leakage(splits)

        return splits


def check_data_leakage(splits: Dict[str, List[NormalizedSample]]) -> None:
    """Verifies that sample IDs, patient IDs, and study IDs do not cross split boundaries.
    
    Raises:
        DataLeakageError: if any overlap is identified.
    """
    sample_sets: Dict[str, Set[str]] = {}
    patient_sets: Dict[str, Set[str]] = {}
    study_sets: Dict[str, Set[str]] = {}

    for split_name, sample_list in splits.items():
        sample_sets[split_name] = {s.sample_id for s in sample_list if s.sample_id}
        patient_sets[split_name] = {s.patient_id for s in sample_list if s.patient_id}
        study_sets[split_name] = {s.study_id for s in sample_list if s.study_id}

    split_names = list(splits.keys())
    for i in range(len(split_names)):
        for j in range(i + 1, len(split_names)):
            s1, s2 = split_names[i], split_names[j]

            # 1. Sample ID overlap
            sample_overlap = sample_sets[s1].intersection(sample_sets[s2])
            if sample_overlap:
                raise DataLeakageError(
                    f"CRITICAL: Sample ID leakage detected between '{s1}' and '{s2}': "
                    f"{len(sample_overlap)} overlapping samples! Example: {list(sample_overlap)[:3]}"
                )

            # 2. Patient ID overlap
            patient_overlap = patient_sets[s1].intersection(patient_sets[s2])
            if patient_overlap:
                raise DataLeakageError(
                    f"CRITICAL: Patient ID leakage detected between '{s1}' and '{s2}': "
                    f"{len(patient_overlap)} overlapping patients! Example: {list(patient_overlap)[:3]}"
                )

            # 3. Study ID overlap
            study_overlap = study_sets[s1].intersection(study_sets[s2])
            if study_overlap:
                raise DataLeakageError(
                    f"CRITICAL: Study ID leakage detected between '{s1}' and '{s2}': "
                    f"{len(study_overlap)} overlapping studies! Example: {list(study_overlap)[:3]}"
                )


def export_split_manifests(
    splits: Dict[str, List[NormalizedSample]],
    output_dir: Path,
) -> Dict[str, Path]:
    """Save split sample lists to reproducible JSON manifests."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {}

    for split_name, sample_list in splits.items():
        file_path = output_dir / f"{split_name}.json"
        data = [s.to_dict() for s in sample_list]
        with open(file_path, mode="w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        paths[split_name] = file_path

    return paths
