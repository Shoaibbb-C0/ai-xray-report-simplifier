"""CLI Entrypoint for Stage 3 Model Inference.

Usage:
  python ml/inference/predict_stage3.py --image path/to/image.jpg
  python ml/inference/predict_stage3.py --image path/to/image.jpg --json
"""

import argparse
import json
from pathlib import Path
import sys

# Ensure repository root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.inference.stage3_pipeline import Stage3InferencePipeline


def main():
    parser = argparse.ArgumentParser(description="Stage 3 Inference CLI: Validator & Body-Part Classifier")
    parser.add_argument("--image", type=str, required=True, help="Path to input image")
    parser.add_argument("--json", action="store_true", help="Output pure JSON format")
    parser.add_argument("--device", type=str, default="cpu", help="Device (cpu or cuda)")
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"Error: image '{image_path}' not found.", file=sys.stderr)
        sys.exit(1)

    pipeline = Stage3InferencePipeline(device=args.device)
    result = pipeline.predict(image_path)
    result["image_path"] = str(image_path)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("========================================")
        print("   AI X-RAY PROJECT - STAGE 3 INFERENCE")
        print("========================================")
        print(f"Input Image: {image_path}")
        val = result["validator"]
        print(f"Validator:   {val['decision']} (prob={val['probability']:.4f}, status={val['status']})")
        if result["body_part"]:
            bp = result["body_part"]
            print(f"Body Part:   {bp['predicted_anatomy'].upper()} (conf={bp['confidence']:.4f})")
            print(f"Candidates:  {bp['class_probabilities']}")
        else:
            print("Body Part:   SKIPPED (Image rejected by X-Ray Validator)")
        print(f"Pipeline:    {result['pipeline_status']}")
        print("========================================")


if __name__ == "__main__":
    main()
