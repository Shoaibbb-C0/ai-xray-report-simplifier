"use client";

import React from "react";
import AnatomicalIllustration from "./AnatomicalIllustration";

/**
 * EducationalComparison: Displays side-by-side comparison of normal intact anatomy
 * versus a generic educational fracture concept.
 */
export default function EducationalComparison({
  neutralUrl,
  fractureUrl,
  regionLabel = "Anatomical Region",
}) {
  return (
    <div className="w-full bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
      <div className="mb-4">
        <h3 className="text-base font-bold text-slate-900">
          Educational Concept: Understanding Normal Continuity vs Fracture
        </h3>
        <p className="text-xs text-slate-600 mt-1">
          Compare intact skeletal continuity with a generic simulated break.
          <strong className="text-rose-700 ml-1">
            Note: These are reference models, not your individual X-ray.
          </strong>
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <AnatomicalIllustration
          illustrationUrl={neutralUrl}
          title={`Normal ${regionLabel} Continuity`}
          altText={`Standard reference illustration of normal unbroken ${regionLabel} anatomy.`}
          labelNotice="Normal Reference Continuity"
          maxWidth="max-w-none"
        />

        <AnatomicalIllustration
          illustrationUrl={fractureUrl}
          title={`Simulated ${regionLabel} Fracture Example`}
          altText={`Generic educational example showing a break discontinuity in ${regionLabel} bones.`}
          labelNotice="Example illustration — Not patient's X-ray"
          maxWidth="max-w-none"
        />
      </div>
    </div>
  );
}
