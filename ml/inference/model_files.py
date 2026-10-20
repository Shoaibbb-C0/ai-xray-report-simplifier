"""Select complete local artifacts and verify tracked checksums before loading."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def select_checkpoint(task, legacy):
    final = ROOT / "ml/saved_models/final_v1" / task / f"best_{task}.pt"
    return final if final.is_file() and (final.parent / "model_metadata.json").is_file() else legacy


def model_metadata(checkpoint):
    checkpoint = Path(checkpoint)
    sidecar = checkpoint.parent / "model_metadata.json"
    if not checkpoint.is_file():
        raise FileNotFoundError("A trained model checkpoint is unavailable")
    if not sidecar.is_file():
        return {}
    metadata = json.loads(sidecar.read_text(encoding="utf-8"))
    if metadata.get("sha256") and hashlib.sha256(checkpoint.read_bytes()).hexdigest() != metadata["sha256"]:
        raise ValueError("Model checksum verification failed")
    return metadata
