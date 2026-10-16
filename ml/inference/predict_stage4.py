"""CLI Entrypoint for Stage 4 Model Inference.

Usage:
  python ml/inference/predict_stage4.py --image path/to/image.jpg
  python ml/inference/predict_stage4.py --image path/to/image.jpg --json
"""

import argparse
import json
from pathlib import Path
import sys

# Ensure repository root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.inference.stage4_pipeline import Stage4InferencePipeline


def main():
    parser = argparse.ArgumentParser(description="Stage 4 Inference CLI: Abnormality (Fracture) Detection Pipeline")
    parser.add_argument("--image", type=str, required=True, help="Path to input image")
    parser.add_argument("--json", action="store_true", help="Output pure JSON format")
    parser.add_argument("--device", type=str, default="cpu", help="Device (cpu or cuda)")
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"Error: image '{image_path}' not found.", file=sys.stderr)
        sys.exit(1)

    pipeline = Stage4InferencePipeline(device=args.device)
    result = pipeline.predict(image_path)
    result["image_path"] = str(image_path)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("========================================")
        print("   AI X-RAY PROJECT - STAGE 4 INFERENCE")
        print("========================================")
        print(f"Input Image:   {image_path}")
        val = result["xray_validation"]
        print(f"Validator:     {val['result'].upper()} (conf={val['confidence']:.4f})")

        if result["body_part"]:
            bp = result["body_part"]
            print(f"Body Part:     {bp['result'].upper()} (conf={bp['confidence']:.4f})")
        else:
            print("Body Part:     SKIPPED")

        if result["abnormality"]:
            ab = result["abnormality"]
            print(f"Abnormality:   {ab['result'].upper()} (prob={ab['fracture_probability']:.4f})")
            print(f"Explanation:   {ab['status_description']}")
        else:
            print("Abnormality:   SKIPPED")

        print(f"Pipeline:      {result['pipeline_status']}")
        if "timings_ms" in result:
            print(f"Latency:       {result['timings_ms']}")
        print("========================================")


if __name__ == "__main__":
    main()
