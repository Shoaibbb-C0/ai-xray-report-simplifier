"""Translation registry and localization keys for English, Hindi, and Marathi.

All patient-facing strings are mapped to deterministic keys so the engine
remains cleanly decoupled from raw hardcoded strings.
"""

from typing import Dict

TRANSLATION_REGISTRY: Dict[str, Dict[str, str]] = {
    "en": {
        # Core Findings
        "finding.fracture.suspected": "The model detected features that may be associated with a fracture.",
        "finding.fracture.no_signal": "The model did not detect strong fracture-related features in this image.",
        "finding.fracture.uncertain": "The model could not make a confident classification from this image.",
        "finding.fracture.unsupported": "Fracture analysis is not supported for this unverified anatomical region.",
        "finding.fracture.not_analyzed": "Fracture analysis was not performed due to input validation rejection.",

        # Negative Clarification
        "finding.negative_clarification": (
            "This does not rule out a fracture. A clinician should interpret the X-ray "
            "together with symptoms and examination findings."
        ),

        # Input & Validation
        "validation.non_xray": "The uploaded image does not meet medical radiograph criteria.",
        "validation.uncertain": "The system could not verify with high confidence whether this image is an X-ray.",
        "validation.unknown_body_part": (
            "The body region in this X-ray is outside the currently supported regions "
            "(Hand, Leg, Hip, Shoulder)."
        ),
        "validation.model_unavailable": "The abnormality detection model is temporarily offline or unavailable.",

        # Anatomy Purpose Descriptions
        "anatomy.purpose.hand": (
            "This X-ray shows the bones and joints of the hand region and is "
            "commonly used to look for fractures or bone alignment changes."
        ),
        "anatomy.purpose.leg": (
            "This X-ray shows the bones of the leg region and can help "
            "identify fractures or changes in bone alignment."
        ),
        "anatomy.purpose.hip": (
            "This X-ray shows the hip region, including the joint and nearby bone structures."
        ),
        "anatomy.purpose.shoulder": (
            "This X-ray shows the shoulder region and surrounding bone structures."
        ),
        "anatomy.purpose.mixed": (
            "This X-ray appears to cover multiple anatomical regions or transition areas."
        ),
        "anatomy.purpose.unknown": (
            "The anatomical region in this radiograph could not be matched to a supported category."
        ),

        # Next Steps
        "next_step.suspected": (
            "Consult an orthopedic specialist or emergency physician for clinical evaluation "
            "and formal radiologist interpretation."
        ),
        "next_step.no_signal": (
            "If pain or swelling persists, consult your doctor. Small or hairline fractures "
            "can still be present without being detected."
        ),
        "next_step.uncertain": (
            "Have a qualified radiologist review the image directly alongside physical examination."
        ),
        "next_step.invalid": (
            "Please upload a clear, high-contrast medical X-ray of a supported body region."
        ),

        # Limitations
        "limitation.educational": (
            "This model result is not a medical diagnosis and the highlighted model-attention "
            "area is not an exact fracture location."
        ),
        "limitation.false_negative": (
            "No strong fracture-related signal was detected, but fractures can still be missed."
        ),
        "limitation.uncertainty_routing": (
            "The system routes low-confidence predictions to an uncertain state to reduce "
            "overconfident classifications; false positives and false negatives remain possible."
        ),
        "limitation.anatomy_scope": (
            "This evaluation is limited strictly to musculoskeletal fracture detection on "
            "supported limbs and joints."
        ),
    },

    "hi": {
        # Core Findings (Hindi)
        "finding.fracture.suspected": "मॉडल ने ऐसे लक्षणों का पता लगाया है जो फ्रैक्चर (हड्डी टूटने) से जुड़े हो सकते हैं।",
        "finding.fracture.no_signal": "मॉडल को इस छवि में कोई मजबूत फ्रैक्चर से जुड़ा संकेत नहीं मिला।",
        "finding.fracture.uncertain": "मॉडल इस छवि से कोई स्पष्ट और आश्वस्त निष्कर्ष नहीं निकाल सका।",
        "finding.negative_clarification": (
            "यह फ्रैक्चर की संभावना को पूरी तरह खारिज नहीं करता। डॉक्टर को लक्षणों और जांच के आधार पर एक्स-रे देखना चाहिए।"
        ),
        "validation.non_xray": "अपलोड की गई छवि मेडिकल एक्स-रे के मानकों को पूरा नहीं करती है।",
        "validation.unknown_body_part": "यह अंग वर्तमान में समर्थित क्षेत्रों (हाथ, पैर, कूल्हा, कंधा) में शामिल नहीं है।",

        # Anatomy Purpose Descriptions
        "anatomy.purpose.hand": "यह एक्स-रे हाथ और कलाई की हड्डियों को दिखाता है और फ्रैक्चर की जांच के लिए उपयोग किया जाता है।",
        "anatomy.purpose.leg": "यह एक्स-रे पैर की हड्डियों को दिखाता है और फ्रैक्चर या हड्डी के संरेखण की जांच में मदद करता है।",
        "anatomy.purpose.hip": "यह एक्स-रे कूल्हे के जोड़ और आसपास की हड्डियों को दिखाता है।",
        "anatomy.purpose.shoulder": "यह एक्स-रे कंधे के जोड़ और आसपास की हड्डियों को दिखाता है।",

        # Limitations
        "limitation.educational": "यह मॉडल परिणाम कोई अंतिम चिकित्सा निदान नहीं है और यह केवल शैक्षिक सहायता के लिए है।",
        "limitation.uncertainty_routing": (
            "कम विश्वास वाली भविष्यवाणियों को अनिश्चित स्थिति में भेजा जाता है ताकि गलत अनुमान न लगे; त्रुटियां संभव हैं।"
        ),
    },

    "mr": {
        # Core Findings (Marathi)
        "finding.fracture.suspected": "मॉडेलला हाड फ्रॅक्चर (हाड मोडणे) शी संबंधित असू शकणारी लक्षणे आढळली आहेत.",
        "finding.fracture.no_signal": "मॉडेलला या प्रतिमेत फ्रॅक्चरशी संबंधित कोणतेही तीव्र संकेत आढळले नाहीत.",
        "finding.fracture.uncertain": "मॉडेल या प्रतिमेवरून निश्चित निष्कर्ष काढू शकले नाही.",
        "finding.negative_clarification": (
            "यामुळे फ्रॅक्चरची शक्यता पूर्णपणे नाकारता येत नाही. डॉक्टरांनी प्रत्यक्ष तपासणी करून एक्स-रे तपासला पाहिजे."
        ),
        "validation.non_xray": "अपलोड केलेली प्रतिमा वैध वैद्यकीय क्ष-किरण (X-Ray) प्रतिमेच्या निकषांमध्ये बसत नाही.",
        "validation.unknown_body_part": "हा अवयव सध्या समर्थित भागांमध्ये (हात, पाय, कंबर/हिप, खांदा) मोडत नाही.",

        # Anatomy Purpose Descriptions
        "anatomy.purpose.hand": "हा एक्स-रे हाताच्या व मनगटाच्या हाडांची स्थिती दर्शवतो आणि फ्रॅक्चर तपासण्यासाठी वापरला जातो.",
        "anatomy.purpose.leg": "हा एक्स-रे पायाच्या हाडांची रचना दर्शवतो आणि फ्रॅक्चर शोधण्यास मदत करतो.",
        "anatomy.purpose.hip": "हा एक्स-रे खुब्याचा (हिप) सांधा आणि संबंधित हाडांची रचना दर्शवतो.",
        "anatomy.purpose.shoulder": "हा एक्स-रे खांद्याचा सांधा आणि संबंधित हाडांची स्थिती दर्शवतो.",

        # Limitations
        "limitation.educational": "हा मॉडेल निकाल वैद्यकीय निदान नाही आणि हायलाइट केलेला भाग हा जखमेचे अचूक ठिकाण नाही.",
        "limitation.uncertainty_routing": (
            "कमी खात्री असलेली निष्कर्षांची प्रकरणे अनिश्चित श्रेणीत वर्ग केली जातात; चुका होण्याची शक्यता नाकारता येत नाही."
        ),
    },
}


def t(key: str, lang: str = "en", default: str = "") -> str:
    """Look up a translated text key with fallback to English then default."""
    if lang in TRANSLATION_REGISTRY and key in TRANSLATION_REGISTRY[lang]:
        return TRANSLATION_REGISTRY[lang][key]
    if key in TRANSLATION_REGISTRY.get("en", {}):
        return TRANSLATION_REGISTRY["en"][key]
    return default or key
