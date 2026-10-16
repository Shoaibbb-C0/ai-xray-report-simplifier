"""Visual asset mapping engine for anatomical illustrations.

Maps body-part identifiers and finding states to educational SVG illustrations,
ensuring every combination resolves to a valid, accessible, and non-diagnostic asset.
"""

from pathlib import Path
from typing import Tuple
from ml.explanation.schema import BodyPartId, FindingState, VisualExplanation


BODY_PART_DISPLAY_NAMES = {
    BodyPartId.HAND: "Hand & Wrist",
    BodyPartId.LEG: "Leg & Knee",
    BodyPartId.HIP: "Hip & Pelvis",
    BodyPartId.SHOULDER: "Shoulder & Clavicle",
    BodyPartId.MIXED: "Mixed Anatomy",
    BodyPartId.UNKNOWN: "Unrecognized Region",
}


def resolve_illustration(
    body_part: BodyPartId,
    finding_state: FindingState,
    is_non_xray: bool = False,
    is_xray_uncertain: bool = False,
) -> VisualExplanation:
    """Resolve the appropriate educational anatomical SVG for a given diagnostic state.

    Guarantees that:
    1. Every returned asset is marked `educational_only=True` and `exact_location=False`.
    2. Fallbacks exist for unknown or mixed anatomies.
    3. Input validation errors map to safety indicators.
    """
    # 1. Non-X-ray input gate rejection
    if is_non_xray:
        return VisualExplanation(
            illustration_id="common_non_xray",
            illustration_path="assets/anatomy/common/non_xray.svg",
            illustration_url="/assets/anatomy/common/non_xray.svg",
            title="Non-Medical Radiograph Notice",
            alt_text="Graphic displaying an invalid file icon indicating the image is not a medical X-ray.",
            educational_only=True,
            exact_location=False,
            label_notice="Safety Check • Non-Radiograph",
        )

    # 2. X-ray validation uncertain
    if is_xray_uncertain or finding_state == FindingState.UNCERTAIN:
        return VisualExplanation(
            illustration_id="common_uncertain",
            illustration_path="assets/anatomy/common/uncertain.svg",
            illustration_url="/assets/anatomy/common/uncertain.svg",
            title="Inconclusive Classification Guide",
            alt_text="Graphic indicating inconclusive image confidence requiring clinician review.",
            educational_only=True,
            exact_location=False,
            label_notice="Low Confidence State • Clinician Review Needed",
        )

    # 3. Known anatomy mapping
    if body_part in (BodyPartId.HAND, BodyPartId.LEG, BodyPartId.HIP, BodyPartId.SHOULDER):
        region_str = body_part.value
        region_label = BODY_PART_DISPLAY_NAMES[body_part]

        if finding_state == FindingState.SUSPECTED:
            return VisualExplanation(
                illustration_id=f"{region_str}_fracture_educational",
                illustration_path=f"assets/anatomy/{region_str}/{region_str}_fracture_educational.svg",
                illustration_url=f"/assets/anatomy/{region_str}/{region_str}_fracture_educational.svg",
                title=f"Educational {region_label} Fracture Concept",
                alt_text=(
                    f"Educational anatomical diagram showing normal {region_label} anatomy "
                    f"versus a simulated break concept. This is a generic diagram and not the patient's X-ray."
                ),
                educational_only=True,
                exact_location=False,
                label_notice="Example illustration — Not patient's X-ray",
            )
        else:
            return VisualExplanation(
                illustration_id=f"{region_str}_neutral",
                illustration_path=f"assets/anatomy/{region_str}/{region_str}_neutral.svg",
                illustration_url=f"/assets/anatomy/{region_str}/{region_str}_neutral.svg",
                title=f"Standard {region_label} Anatomy Guide",
                alt_text=f"Educational anatomical diagram showing intact {region_label} skeletal structures.",
                educational_only=True,
                exact_location=False,
                label_notice="Standard Reference Anatomy",
            )

    # 4. Mixed or Unknown anatomy fallback
    if finding_state == FindingState.SUSPECTED:
        return VisualExplanation(
            illustration_id="generic_fracture_educational",
            illustration_path="assets/anatomy/common/generic_fracture_educational.svg",
            illustration_url="/assets/anatomy/common/generic_fracture_educational.svg",
            title="Generic Skeletal Fracture Concept",
            alt_text=(
                "Educational diagram demonstrating the concept of a bone fracture "
                "on a generic long bone. This is not the patient's X-ray."
            ),
            educational_only=True,
            exact_location=False,
            label_notice="Generic Educational Reference",
        )
    else:
        return VisualExplanation(
            illustration_id="generic_neutral",
            illustration_path="assets/anatomy/common/generic_neutral.svg",
            illustration_url="/assets/anatomy/common/generic_neutral.svg",
            title="Standard Skeletal Anatomy Reference",
            alt_text="Educational diagram of standard skeletal bone continuity.",
            educational_only=True,
            exact_location=False,
            label_notice="Standard Reference Anatomy",
        )
