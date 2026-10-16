"use client";

import React, { useState } from "react";
import ExplanationCard from "@/components/explanation/ExplanationCard";
import AnatomicalIllustration from "@/components/explanation/AnatomicalIllustration";
import EducationalComparison from "@/components/explanation/EducationalComparison";
import ModelAttentionOverlay from "@/components/explanation/ModelAttentionOverlay";
import GlossaryDrawer from "@/components/explanation/GlossaryDrawer";

/**
 * DEVELOPMENT PREVIEW ONLY:
 * Interactive harness for testing and inspecting Stage 5 Visual Explanation Components
 * using static deterministic software fixtures. Contains NO clinical diagnoses.
 */

const TEST_FIXTURES = {
  hand_fracture_suspected: {
    name: "1. Hand + Fracture Suspected",
    explanation: {
      analysis_status: "VALID_XRAY_FRACTURE_SUSPECTED",
      body_part: { id: "hand", label: "Hand & Wrist", is_supported: true, confidence: 0.94 },
      finding: { id: "fracture", label: "Bone Fracture", state: "suspected", probability: 0.84, confidence: 0.84 },
      summary: "The model detected features that may be associated with a fracture.",
      what_this_test_checks: "This X-ray shows the bones and joints of the hand region and is commonly used to look for fractures or bone alignment changes.",
      what_the_result_means: "The model detected features that may be associated with a fracture in the hand & wrist. This indicates potential bone discontinuity or alignment disruption requiring clinician review.",
      next_step_message: "Consult an orthopedic specialist or emergency physician for clinical evaluation and formal radiologist interpretation.",
      limitations: [
        "This model result is not a medical diagnosis and the highlighted model-attention area is not an exact fracture location.",
        "The system routes low-confidence predictions to an uncertain state to reduce overconfident classifications; false positives and false negatives remain possible.",
        "This evaluation is limited strictly to musculoskeletal fracture detection on supported limbs and joints.",
      ],
      visual: {
        illustration_id: "hand_fracture_educational",
        illustration_path: "assets/anatomy/hand/hand_fracture_educational.svg",
        illustration_url: "/assets/anatomy/hand/hand_fracture_educational.svg",
        title: "Educational Hand Fracture Concept",
        alt_text: "Educational anatomical diagram showing normal hand anatomy versus a simulated break concept.",
        label_notice: "Example illustration — Not patient's X-ray",
      },
      attention: {
        available: true,
        type: "gradcam",
        disclaimer: "Grad-CAM highlights areas that influenced the model's prediction. It is NOT a confirmed injury site or clinical localization.",
      },
      medical_glossary: {
        fracture: "A medical term for a break, crack, or discontinuity in a bone.",
        model_attention: "Visual heatmaps (such as Grad-CAM) showing image regions that influenced the AI algorithm.",
      },
    },
    neutralUrl: "/assets/anatomy/hand/hand_neutral.svg",
    fractureUrl: "/assets/anatomy/hand/hand_fracture_educational.svg",
  },

  leg_fracture_suspected: {
    name: "2. Leg + Fracture Suspected",
    explanation: {
      analysis_status: "VALID_XRAY_FRACTURE_SUSPECTED",
      body_part: { id: "leg", label: "Leg & Knee", is_supported: true, confidence: 0.91 },
      finding: { id: "fracture", label: "Bone Fracture", state: "suspected", probability: 0.78, confidence: 0.78 },
      summary: "The model detected features that may be associated with a fracture.",
      what_this_test_checks: "This X-ray shows the bones of the leg region and can help identify fractures or changes in bone alignment.",
      what_the_result_means: "The model detected features that may be associated with a fracture in the leg & knee.",
      next_step_message: "Consult an orthopedic specialist or emergency physician for clinical evaluation.",
      limitations: [
        "This model result is not a medical diagnosis and the highlighted model-attention area is not an exact fracture location.",
        "The system routes low-confidence predictions to an uncertain state to reduce overconfident classifications; false positives and false negatives remain possible.",
      ],
      visual: {
        illustration_id: "leg_fracture_educational",
        illustration_path: "assets/anatomy/leg/leg_fracture_educational.svg",
        illustration_url: "/assets/anatomy/leg/leg_fracture_educational.svg",
        title: "Educational Leg Fracture Concept",
        alt_text: "Educational diagram demonstrating a simulated tibia break concept.",
        label_notice: "Example illustration — Not patient's X-ray",
      },
      attention: { available: true, type: "gradcam", disclaimer: "Grad-CAM highlights areas that influenced the model." },
      medical_glossary: { fracture: "A medical term for a break or crack in a bone." },
    },
    neutralUrl: "/assets/anatomy/leg/leg_neutral.svg",
    fractureUrl: "/assets/anatomy/leg/leg_fracture_educational.svg",
  },

  hip_no_fracture_signal: {
    name: "3. Hip + No Fracture Signal",
    explanation: {
      analysis_status: "VALID_XRAY_NO_FRACTURE_SIGNAL",
      body_part: { id: "hip", label: "Hip & Pelvis", is_supported: true, confidence: 0.88 },
      finding: { id: "fracture", label: "Bone Fracture", state: "no_signal", probability: 0.12, confidence: 0.88 },
      summary: "The model did not detect strong fracture-related features in this image.",
      what_this_test_checks: "This X-ray shows the hip region, including the joint and nearby bone structures.",
      what_the_result_means: "The model did not detect strong fracture-related features in this image. This does not rule out a fracture. A clinician should interpret the X-ray together with symptoms and examination findings.",
      next_step_message: "If pain or swelling persists, consult your doctor. Small or hairline fractures can still be present without being detected.",
      limitations: [
        "No strong fracture-related signal was detected, but fractures can still be missed.",
        "The system routes low-confidence predictions to an uncertain state to reduce overconfident classifications; false positives and false negatives remain possible.",
      ],
      visual: {
        illustration_id: "hip_neutral",
        illustration_path: "assets/anatomy/hip/hip_neutral.svg",
        illustration_url: "/assets/anatomy/hip/hip_neutral.svg",
        title: "Standard Hip Anatomy Guide",
        alt_text: "Educational diagram showing intact hip skeletal structures.",
        label_notice: "Standard Reference Anatomy",
      },
      attention: { available: false, type: "gradcam" },
      medical_glossary: { radiograph: "A medical X-ray photographic image." },
    },
    neutralUrl: "/assets/anatomy/hip/hip_neutral.svg",
    fractureUrl: "/assets/anatomy/hip/hip_fracture_educational.svg",
  },

  shoulder_uncertain: {
    name: "4. Shoulder + Uncertain",
    explanation: {
      analysis_status: "VALID_XRAY_UNCERTAIN",
      body_part: { id: "shoulder", label: "Shoulder & Clavicle", is_supported: true, confidence: 0.85 },
      finding: { id: "fracture", label: "Bone Fracture", state: "uncertain", probability: 0.35, confidence: 0.35 },
      summary: "The model could not make a confident classification from this image.",
      what_this_test_checks: "This X-ray shows the shoulder region and surrounding bone structures.",
      what_the_result_means: "The model could not make a confident classification from this image. The visual features fall within a borderline zone, so automated scoring is withheld to prevent misleading conclusions.",
      next_step_message: "Have a qualified radiologist review the image directly alongside physical examination.",
      limitations: [
        "The model could not classify this image confidently.",
        "The system routes low-confidence predictions to an uncertain state to reduce overconfident classifications; false positives and false negatives remain possible.",
      ],
      visual: {
        illustration_id: "common_uncertain",
        illustration_path: "assets/anatomy/common/uncertain.svg",
        illustration_url: "/assets/anatomy/common/uncertain.svg",
        title: "Inconclusive Classification Guide",
        alt_text: "Graphic indicating inconclusive image confidence requiring clinician review.",
        label_notice: "Low Confidence State • Clinician Review Needed",
      },
      attention: { available: false, type: "gradcam" },
      medical_glossary: { uncertain: "An inconclusive classification requiring human review." },
    },
    neutralUrl: "/assets/anatomy/shoulder/shoulder_neutral.svg",
    fractureUrl: "/assets/anatomy/shoulder/shoulder_fracture_educational.svg",
  },

  body_part_unknown: {
    name: "5. Body Part Unknown / Unsupported",
    explanation: {
      analysis_status: "BODY_PART_UNKNOWN",
      body_part: { id: "unknown", label: "Unrecognized Region", is_supported: false, confidence: 0.32 },
      finding: { id: "fracture", label: "Bone Fracture", state: "unsupported" },
      summary: "The body region in this X-ray is outside the currently supported regions (Hand, Leg, Hip, Shoulder).",
      what_this_test_checks: "The anatomical region in this radiograph could not be matched to a supported category.",
      what_the_result_means: "Automated fracture detection is strictly calibrated for supported body regions (Hand, Leg, Hip, Shoulder). Because this region is unrecognized or unsupported, no fracture analysis was run.",
      next_step_message: "Please upload an X-ray of a supported limb or joint.",
      limitations: ["Automated analysis cannot be performed safely on unrecognized anatomy."],
      visual: {
        illustration_id: "generic_neutral",
        illustration_path: "assets/anatomy/common/generic_neutral.svg",
        illustration_url: "/assets/anatomy/common/generic_neutral.svg",
        title: "Standard Skeletal Anatomy Reference",
        alt_text: "Educational diagram of standard skeletal bone continuity.",
        label_notice: "Standard Reference Anatomy",
      },
      attention: { available: false, type: "gradcam" },
      medical_glossary: {},
    },
    neutralUrl: "/assets/anatomy/common/generic_neutral.svg",
    fractureUrl: "/assets/anatomy/common/generic_fracture_educational.svg",
  },

  non_xray: {
    name: "6. Non-X-Ray Image Gate Rejection",
    explanation: {
      analysis_status: "NON_XRAY",
      body_part: { id: "unknown", label: "Unrecognized Region", is_supported: false },
      finding: { id: "fracture", label: "Bone Fracture", state: "not_analyzed" },
      summary: "The uploaded image does not meet medical radiograph criteria.",
      what_this_test_checks: "Safety Gate: Verifies that the input file meets medical radiograph imaging standards.",
      what_the_result_means: "The input image failed radiographic validation criteria (contrast, structure, or content) and was not recognized as a medical X-ray.",
      next_step_message: "Please upload a clear, high-contrast medical X-ray of a supported body region.",
      limitations: ["Non-radiograph images are rejected to prevent spurious classifications."],
      visual: {
        illustration_id: "common_non_xray",
        illustration_path: "assets/anatomy/common/non_xray.svg",
        illustration_url: "/assets/anatomy/common/non_xray.svg",
        title: "Non-Medical Radiograph Notice",
        alt_text: "Graphic displaying an invalid file icon indicating the image is not a medical X-ray.",
        label_notice: "Safety Check • Non-Radiograph",
      },
      attention: { available: false, type: "gradcam" },
      medical_glossary: {},
    },
    neutralUrl: "/assets/anatomy/common/non_xray.svg",
    fractureUrl: "/assets/anatomy/common/non_xray.svg",
  },

  model_unavailable: {
    name: "7. Model Unavailable",
    explanation: {
      analysis_status: "MODEL_UNAVAILABLE",
      body_part: { id: "hand", label: "Hand & Wrist", is_supported: true },
      finding: { id: "fracture", label: "Bone Fracture", state: "not_analyzed" },
      summary: "The abnormality detection model is temporarily offline or unavailable.",
      what_this_test_checks: "System Diagnostic Check",
      what_the_result_means: "The specialized abnormality model is currently offline or undergoing maintenance.",
      next_step_message: "Please try again later or contact the clinical system administrator.",
      limitations: ["Service unavailable fallback."],
      visual: {
        illustration_id: "generic_neutral",
        illustration_path: "assets/anatomy/common/generic_neutral.svg",
        illustration_url: "/assets/anatomy/common/generic_neutral.svg",
        title: "Standard Skeletal Reference",
        alt_text: "Generic skeletal anatomy guide.",
        label_notice: "System Maintenance",
      },
      attention: { available: false, type: "gradcam" },
      medical_glossary: {},
    },
    neutralUrl: "/assets/anatomy/common/generic_neutral.svg",
    fractureUrl: "/assets/anatomy/common/generic_fracture_educational.svg",
  },
};

export default function DevExplanationsPreviewPage() {
  const [selectedKey, setSelectedKey] = useState("hand_fracture_suspected");
  const current = TEST_FIXTURES[selectedKey];

  return (
    <div className="min-h-screen bg-slate-100 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto space-y-8">
        {/* Development Banner */}
        <div className="bg-indigo-900 text-indigo-100 rounded-2xl p-6 shadow-md">
          <div className="flex items-center gap-2 mb-2">
            <span className="bg-amber-400 text-amber-950 font-bold px-2 py-0.5 rounded text-xs uppercase">
              Dev Only
            </span>
            <span className="text-xs text-indigo-200">Stage 5 Component Verification Harness</span>
          </div>
          <h1 className="text-2xl font-black text-white">Visual Explanation Engine Test Bench</h1>
          <p className="text-sm text-indigo-200 mt-1">
            Deterministic software test fixtures for validating SVG rendering, educational comparison,
            accessibility, and clinical disclaimer structures.
          </p>

          {/* Fixture Selector Buttons */}
          <div className="mt-4 flex flex-wrap gap-2">
            {Object.keys(TEST_FIXTURES).map((k) => (
              <button
                key={k}
                type="button"
                onClick={() => setSelectedKey(k)}
                className={`text-xs font-semibold px-3 py-1.5 rounded-lg border transition-all ${
                  selectedKey === k
                    ? "bg-white text-indigo-900 border-white shadow-sm"
                    : "bg-indigo-800/80 text-indigo-200 border-indigo-700 hover:bg-indigo-700 hover:text-white"
                }`}
              >
                {TEST_FIXTURES[k].name}
              </button>
            ))}
          </div>
        </div>

        {/* Selected Component Render Preview */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Patient Explanation Card */}
          <div className="lg:col-span-2 space-y-6">
            <ExplanationCard explanation={current.explanation} />
            <EducationalComparison
              neutralUrl={current.neutralUrl}
              fractureUrl={current.fractureUrl}
              regionLabel={current.explanation.body_part?.label || "Anatomy"}
            />
          </div>

          {/* Right Column: Visual Artwork & Attention */}
          <div className="space-y-6">
            <AnatomicalIllustration
              illustrationUrl={current.explanation.visual?.illustration_url}
              title={current.explanation.visual?.title}
              altText={current.explanation.visual?.alt_text}
              labelNotice={current.explanation.visual?.label_notice}
            />

            <ModelAttentionOverlay
              baseImageSrc={null}
              attentionOverlaySrc={null}
              available={current.explanation.attention?.available}
              disclaimer={current.explanation.attention?.disclaimer}
            />

            <GlossaryDrawer glossary={current.explanation.medical_glossary} />
          </div>
        </div>
      </div>
    </div>
  );
}
