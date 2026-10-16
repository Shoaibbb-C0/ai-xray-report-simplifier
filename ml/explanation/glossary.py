"""Curated plain-language medical glossary for patient education."""

GLOSSARY_EN = {
    "fracture": (
        "A medical term for a break, crack, or discontinuity in a bone, "
        "ranging from a tiny hairline fissure to a complete separation."
    ),
    "radiograph": (
        "A medical X-ray photographic image created by sending low-dose radiation "
        "through the body to visualize internal bone structures and joint spaces."
    ),
    "bone": (
        "A rigid organ forming the human skeletal framework, protecting internal organs "
        "and anchoring muscles to enable movement."
    ),
    "joint": (
        "The anatomical connection where two or more bones meet to allow mobility, "
        "such as the wrist, knee, hip, or shoulder."
    ),
    "uncertain": (
        "An inconclusive classification where image features fall within a borderline "
        "range, meaning the model cannot make a confident assessment."
    ),
    "model_attention": (
        "A computational visualization (such as Grad-CAM) showing which pixel regions "
        "most influenced the AI algorithm. It highlights algorithm focus, not an exact injury site."
    ),
}


def get_glossary(lang: str = "en") -> dict:
    """Return plain-language definitions for key medical and AI concepts."""
    # Currently English is the primary source; localized mappings can extend this.
    return dict(GLOSSARY_EN)
