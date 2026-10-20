"""Opt-in real HTTP acceptance, using public validation examples, not accuracy estimation.

Start the local backend, then: .venv/Scripts/python scripts/check_local_api.py
Writes detailed local-only evidence under ignored .venv/. Never contacts a database.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import time

import httpx

ROOT = Path(__file__).resolve().parents[1]
SPLITS = ROOT / "ml/datasets/splits/final_v1"


def main(base_url):
    with httpx.Client(base_url=base_url, timeout=90) as client:
        assert client.get("/health").status_code == 200
        readiness = client.get("/ready")
        assert readiness.status_code == 200, readiness.text
        assert readiness.json()["loaded_models_count"] == 3
        for content, mime, expected in [(b"broken PNG", "image/png", 422), (b"<svg/>", "image/svg+xml", 415)]:
            response = client.post("/api/v1/analyze", files={"file": ("untrusted", content, mime)})
            assert response.status_code == expected, response.text
        rows = json.loads((SPLITS / "fracture/validation.json").read_text())
        examples = []
        for region in ("hand", "leg", "hip", "shoulder"):
            for fractured in (True, False):
                examples.extend([row for row in rows if row["body_part"] == region and row["is_abnormal"] == fractured][:2])
        examples.extend([row for row in rows if row["body_part"] not in {"hand", "leg", "hip", "shoulder"}][:2])
        validator = json.loads((SPLITS / "validator/validation.json").read_text())
        for dataset in ("cifar10", "retinamnist"):
            examples.extend([row for row in validator if row["dataset"] == dataset][:2])
        examples.extend(json.loads((SPLITS / "validator/ood_test.json").read_text())[:2])
        results = []
        for index, row in enumerate(examples):
            path = ROOT / row["image_path"]
            started = time.perf_counter()
            language = ("en", "hi", "mr")[index % 3]
            with path.open("rb") as image:
                response = client.post("/api/v1/analyze", files={"file": ("upload" + path.suffix, image, "image/png" if path.suffix.lower() == ".png" else "image/jpeg")}, data={"language": language, "attention": "true"})
            assert response.status_code == 200, response.text
            assert response.headers["cache-control"] == "private, no-store"
            result = response.json()
            assert result["persistence"]["saved"] is False
            assert result["explanation"]["language"] == language
            assert all(value.startswith("sha256:") for value in result["model_versions"].values())
            assert ":\\" not in response.text and "model_state_dict" not in response.text
            json.dumps(result, allow_nan=False)
            results.append({"source": row["dataset"], "dataset_region": row["body_part"],
                "dataset_fracture_label": row["is_abnormal"] if row["dataset"] == "fracatlas" else None,
                "image_path": row["image_path"], "http_ms": round((time.perf_counter()-started)*1000,1), "result": result})
            print(f"{index+1}/{len(examples)} {row['dataset']}/{row['body_part']}: {result['explanation']['analysis_status']}", flush=True)
        report = {"purpose": "Validation/OOD examples for HTTP acceptance, NOT an accuracy estimate or model selection", "counts": dict(Counter(row["result"]["explanation"]["analysis_status"] for row in results)), "results": results}
        (ROOT / ".venv/local-api-check.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report["counts"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8001")
    main(parser.parse_args().url)
