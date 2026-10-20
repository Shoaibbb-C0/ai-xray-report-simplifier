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
        "validation.purpose": "The first step checks whether the local model can accept an image as an X-ray before fracture analysis.",
        "validation.non_xray": "The model did not accept this image as an X-ray. The model can make mistakes.",
        "validation.uncertain": "The system could not verify with high confidence whether this image is an X-ray.",
        "validation.unknown_body_part": (
            "The model could not confidently match this image to a supported region "
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
        "validation.purpose": "पहले स्थानीय मॉडल जाँचता है कि छवि एक्स-रे के रूप में स्वीकार हो सकती है या नहीं। इसके बाद ही फ्रैक्चर विश्लेषण होता है।",
        "finding.fracture.suspected": "मॉडल ने ऐसे लक्षणों का पता लगाया है जो फ्रैक्चर (हड्डी टूटने) से जुड़े हो सकते हैं।",
        "finding.fracture.no_signal": "मॉडल को इस छवि में कोई मजबूत फ्रैक्चर से जुड़ा संकेत नहीं मिला।",
        "finding.fracture.uncertain": "मॉडल इस छवि से कोई स्पष्ट और आश्वस्त निष्कर्ष नहीं निकाल सका।",
        "finding.negative_clarification": (
            "यह फ्रैक्चर की संभावना को पूरी तरह खारिज नहीं करता। डॉक्टर को लक्षणों और जांच के आधार पर एक्स-रे देखना चाहिए।"
        ),
        "validation.non_xray": "मॉडल ने इस छवि को एक्स-रे के रूप में स्वीकार नहीं किया। मॉडल से गलती हो सकती है।",
        "validation.unknown_body_part": "मॉडल इस छवि के अंग को हाथ, पैर, कूल्हा या कंधा के रूप में विश्वासपूर्वक नहीं पहचान सका।",

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
        "validation.purpose": "प्रथम स्थानिक मॉडेल प्रतिमा एक्स-रे म्हणून स्वीकारता येते का हे तपासते. त्यानंतरच फ्रॅक्चर विश्लेषण होते.",
        "validation.non_xray": "मॉडेलने ही प्रतिमा एक्स-रे म्हणून स्वीकारली नाही. मॉडेलकडून चूक होऊ शकते.",
        "validation.unknown_body_part": "मॉडेलला या प्रतिमेतील भाग हात, पाय, खुबा किंवा खांदा म्हणून खात्रीपूर्वक ओळखता आला नाही.",

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


TRANSLATION_REGISTRY["en"].update({
    "validation.error": "The image could not be processed completely. No reliable result was produced.",
    "next_step.unavailable": "Check the local model installation, then try again. Consult a clinician about your X-ray.",
    "next_step.unsupported": "Use an X-ray of a supported region, or ask a clinician to interpret this image.",
    "next_step.error": "Check the image and try again. Ask a clinician if you need help interpreting your X-ray.",
})
TRANSLATION_REGISTRY["hi"].update({
    "finding.fracture.unsupported": "इस अपुष्ट अंग के लिए फ्रैक्चर विश्लेषण उपलब्ध नहीं है।",
    "finding.fracture.not_analyzed": "छवि की जाँच पूरी न होने के कारण फ्रैक्चर विश्लेषण नहीं किया गया।",
    "validation.uncertain": "यह छवि एक्स-रे है या नहीं, इसकी पर्याप्त पुष्टि नहीं हो सकी।",
    "validation.model_unavailable": "प्रशिक्षित मॉडल अभी उपलब्ध नहीं है। कोई चिकित्सा निष्कर्ष नहीं निकाला गया।",
    "validation.error": "छवि पूरी तरह संसाधित नहीं हो सकी। कोई विश्वसनीय परिणाम नहीं मिला।",
    "anatomy.purpose.mixed": "यह छवि एक से अधिक शारीरिक क्षेत्रों को दिखाती है।",
    "anatomy.purpose.unknown": "इस छवि का अंग किसी समर्थित क्षेत्र से नहीं मिल सका।",
    "next_step.suspected": "जाँच और एक्स-रे की औपचारिक व्याख्या के लिए योग्य डॉक्टर से परामर्श लें।",
    "next_step.no_signal": "दर्द या सूजन बनी रहे तो डॉक्टर से मिलें। छोटे फ्रैक्चर मॉडल से छूट सकते हैं।",
    "next_step.uncertain": "रेडियोलॉजिस्ट से छवि और लक्षणों की साथ में समीक्षा कराएँ।",
    "next_step.invalid": "हाथ, पैर, कूल्हे या कंधे का स्पष्ट मेडिकल एक्स-रे चुनें।",
    "next_step.unavailable": "स्थानीय मॉडल की स्थापना जाँचकर फिर प्रयास करें। एक्स-रे के बारे में डॉक्टर से सलाह लें।",
    "next_step.unsupported": "समर्थित अंग का एक्स-रे चुनें या डॉक्टर से इस छवि की व्याख्या कराएँ।",
    "next_step.error": "छवि जाँचकर फिर प्रयास करें। जरूरत होने पर डॉक्टर से मदद लें।",
    "limitation.false_negative": "मजबूत संकेत नहीं मिला, फिर भी फ्रैक्चर छूट सकता है।",
    "limitation.anatomy_scope": "यह मॉडल केवल हाथ, पैर, कूल्हे और कंधे के फ्रैक्चर संबंधी संकेतों का अध्ययन करता है।",
    "meaning.VALID_XRAY_FRACTURE_SUSPECTED": "कुछ विशेषताएँ फ्रैक्चर से जुड़ी हो सकती हैं। यह निदान नहीं है; डॉक्टर की समीक्षा आवश्यक है।",
    "meaning.VALID_XRAY_NO_FRACTURE_SIGNAL": "मजबूत संकेत नहीं मिला। इससे फ्रैक्चर की संभावना खारिज नहीं होती; डॉक्टर को लक्षणों के साथ एक्स-रे देखना चाहिए।",
    "meaning.VALID_XRAY_UNCERTAIN": "छवि से स्पष्ट वर्गीकरण नहीं हो सका। अनिश्चित परिणाम पर चिकित्सा निर्णय न लें।",
    "meaning.BODY_PART_UNKNOWN": "अंग की विश्वासपूर्वक पहचान नहीं हुई। फ्रैक्चर विश्लेषण नहीं किया गया।",
    "meaning.NON_XRAY": "छवि को मेडिकल एक्स-रे के रूप में स्वीकार नहीं किया गया। फ्रैक्चर विश्लेषण नहीं हुआ।",
    "meaning.XRAY_VALIDATION_UNCERTAIN": "एक्स-रे की पर्याप्त पुष्टि नहीं हो सकी, इसलिए आगे का विश्लेषण रोका गया।",
    "meaning.MODEL_UNAVAILABLE": "प्रशिक्षित मॉडल उपलब्ध नहीं है। कोई भविष्यवाणी नहीं की गई।",
    "meaning.ERROR": "प्रक्रिया में समस्या आई। कोई विश्वसनीय चिकित्सा परिणाम नहीं मिला।",
    "visual.notice": "उदाहरण चित्र — आपका व्यक्तिगत एक्स-रे नहीं",
    "visual.title": "शैक्षिक शारीरिक चित्र",
    "attention.disclaimer": "यह मॉडल को प्रभावित करने वाला क्षेत्र है, पुष्टि की गई चोट या फ्रैक्चर का स्थान नहीं।",
})
TRANSLATION_REGISTRY["mr"].update({
    "finding.fracture.unsupported": "या अपुष्ट शारीरिक भागासाठी फ्रॅक्चर विश्लेषण उपलब्ध नाही.",
    "finding.fracture.not_analyzed": "प्रतिमेची पडताळणी न झाल्यामुळे फ्रॅक्चर विश्लेषण झाले नाही.",
    "validation.uncertain": "ही प्रतिमा एक्स-रे आहे याची पुरेशी खात्री झाली नाही.",
    "validation.model_unavailable": "प्रशिक्षित मॉडेल सध्या उपलब्ध नाही. वैद्यकीय निष्कर्ष काढलेला नाही.",
    "validation.error": "प्रतिमेवर पूर्ण प्रक्रिया झाली नाही. विश्वासार्ह निकाल मिळाला नाही.",
    "anatomy.purpose.mixed": "ही प्रतिमा एकापेक्षा जास्त शारीरिक भाग दाखवते.",
    "anatomy.purpose.unknown": "या प्रतिमेतील भाग समर्थित श्रेणीशी जुळला नाही.",
    "next_step.suspected": "प्रत्यक्ष तपासणी आणि एक्स-रेच्या औपचारिक अर्थासाठी पात्र डॉक्टरांचा सल्ला घ्या.",
    "next_step.no_signal": "वेदना किंवा सूज कायम राहिल्यास डॉक्टरांना भेटा. लहान फ्रॅक्चर मॉडेलकडून सुटू शकतात.",
    "next_step.uncertain": "रेडिओलॉजिस्टकडून प्रतिमा आणि लक्षणांची एकत्र समीक्षा करून घ्या.",
    "next_step.invalid": "हात, पाय, खुबा किंवा खांद्याचा स्पष्ट वैद्यकीय एक्स-रे निवडा.",
    "next_step.unavailable": "स्थानिक मॉडेलची स्थापना तपासा आणि पुन्हा प्रयत्न करा. डॉक्टरांचा सल्ला घ्या.",
    "next_step.unsupported": "समर्थित भागाचा एक्स-रे निवडा किंवा डॉक्टरांकडून या प्रतिमेचा अर्थ समजून घ्या.",
    "next_step.error": "प्रतिमा तपासून पुन्हा प्रयत्न करा. गरज असल्यास डॉक्टरांची मदत घ्या.",
    "limitation.false_negative": "ठळक संकेत आढळला नाही तरी फ्रॅक्चर चुकू शकते.",
    "limitation.anatomy_scope": "हे मॉडेल फक्त हात, पाय, खुबा आणि खांद्याच्या फ्रॅक्चरशी संबंधित संकेतांचा अभ्यास करते.",
    "meaning.VALID_XRAY_FRACTURE_SUSPECTED": "काही वैशिष्ट्ये फ्रॅक्चरशी संबंधित असू शकतात. हा निदानाचा निकाल नाही; डॉक्टरांची समीक्षा आवश्यक आहे.",
    "meaning.VALID_XRAY_NO_FRACTURE_SIGNAL": "ठळक संकेत मिळाला नाही. यामुळे फ्रॅक्चर नाकारता येत नाही; डॉक्टरांनी लक्षणांसह एक्स-रे तपासावा.",
    "meaning.VALID_XRAY_UNCERTAIN": "प्रतिमेचे खात्रीपूर्वक वर्गीकरण झाले नाही. अनिश्चित निकालावर वैद्यकीय निर्णय घेऊ नका.",
    "meaning.BODY_PART_UNKNOWN": "शारीरिक भाग खात्रीपूर्वक ओळखला गेला नाही. फ्रॅक्चर विश्लेषण केलेले नाही.",
    "meaning.NON_XRAY": "प्रतिमा वैद्यकीय एक्स-रे म्हणून स्वीकारली नाही. फ्रॅक्चर विश्लेषण झाले नाही.",
    "meaning.XRAY_VALIDATION_UNCERTAIN": "एक्स-रेची खात्री झाली नाही, म्हणून पुढील विश्लेषण थांबवले.",
    "meaning.MODEL_UNAVAILABLE": "प्रशिक्षित मॉडेल उपलब्ध नाही. कोणतीही भविष्यवाणी केलेली नाही.",
    "meaning.ERROR": "प्रक्रियेत अडचण आली. विश्वासार्ह वैद्यकीय निकाल मिळाला नाही.",
    "visual.notice": "उदाहरण चित्र — तुमचा वैयक्तिक एक्स-रे नाही",
    "visual.title": "शैक्षणिक शरीररचना चित्र",
    "attention.disclaimer": "हे मॉडेलवर परिणाम करणारे क्षेत्र आहे; निश्चित जखमेचे किंवा फ्रॅक्चरचे ठिकाण नाही.",
})


def t(key: str, lang: str = "en", default: str = "") -> str:
    """Look up a translated text key with fallback to English then default."""
    if lang in TRANSLATION_REGISTRY and key in TRANSLATION_REGISTRY[lang]:
        return TRANSLATION_REGISTRY[lang][key]
    if key in TRANSLATION_REGISTRY.get("en", {}):
        return TRANSLATION_REGISTRY["en"][key]
    return default or key
