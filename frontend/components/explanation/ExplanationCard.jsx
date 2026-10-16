"use client";

import React from "react";
import LimitationNotice from "./LimitationNotice";

/**
 * ExplanationCard: Renders the structured 4-part patient-facing explanation:
 * 1. WHAT THIS X-RAY IS ABOUT
 * 2. MODEL FINDING
 * 3. WHAT IT MAY MEAN
 * 4. NEXT STEPS
 */
export default function ExplanationCard({
  explanation,
  className = "",
}) {
  if (!explanation) return null;

  const {
    analysis_status,
    body_part,
    finding,
    summary,
    what_this_test_checks,
    what_the_result_means,
    next_step_message,
    limitations = [],
  } = explanation;

  // Status badge styling
  let badgeStyle = "bg-slate-100 text-slate-800 border-slate-300";
  let statusText = "Evaluation Complete";

  if (analysis_status === "VALID_XRAY_FRACTURE_SUSPECTED") {
    badgeStyle = "bg-rose-100 text-rose-900 border-rose-300";
    statusText = "Fracture Features Suspected";
  } else if (analysis_status === "VALID_XRAY_NO_FRACTURE_SIGNAL") {
    badgeStyle = "bg-emerald-100 text-emerald-900 border-emerald-300";
    statusText = "No Strong Fracture Signal";
  } else if (analysis_status === "VALID_XRAY_UNCERTAIN") {
    badgeStyle = "bg-amber-100 text-amber-900 border-amber-300";
    statusText = "Inconclusive / Low Confidence";
  } else if (analysis_status === "NON_XRAY") {
    badgeStyle = "bg-red-100 text-red-900 border-red-300";
    statusText = "Non-Medical Radiograph";
  } else if (analysis_status === "BODY_PART_UNKNOWN") {
    badgeStyle = "bg-purple-100 text-purple-900 border-purple-300";
    statusText = "Unsupported Body Region";
  }

  return (
    <div className={`w-full bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6 ${className}`}>
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Musculoskeletal Radiograph Interpretation
          </span>
          <h2 className="text-xl font-bold text-slate-900 mt-0.5">
            {body_part?.label || "Radiograph Assessment"}
          </h2>
        </div>
        <div className={`px-3 py-1 rounded-full text-xs font-bold border ${badgeStyle} self-start sm:self-auto`}>
          {statusText}
        </div>
      </div>

      {/* 1. WHAT THIS X-RAY IS ABOUT */}
      <div className="space-y-1.5">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-blue-500"></span>
          1. What This X-Ray Is About
        </h3>
        <p className="text-sm text-slate-700 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-100">
          {what_this_test_checks}
        </p>
      </div>

      {/* 2. MODEL FINDING */}
      <div className="space-y-1.5">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
          2. Model Finding
        </h3>
        <div className="p-4 rounded-xl border border-slate-200 bg-white shadow-sm flex items-start gap-3">
          <div className="w-2.5 h-2.5 rounded-full mt-1.5 bg-indigo-600 shrink-0"></div>
          <div>
            <h4 className="text-sm font-semibold text-slate-900">{summary}</h4>
            {finding?.probability !== undefined && finding.probability !== null && (
              <p className="text-xs text-slate-500 mt-1">
                Estimated Fracture Signal: <strong>{(finding.probability * 100).toFixed(1)}%</strong>
              </p>
            )}
          </div>
        </div>
      </div>

      {/* 3. WHAT IT MAY MEAN */}
      <div className="space-y-1.5">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-purple-500"></span>
          3. What It May Mean
        </h3>
        <p className="text-sm text-slate-700 leading-relaxed bg-purple-50/50 p-3 rounded-lg border border-purple-100">
          {what_the_result_means}
        </p>
      </div>

      {/* 4. RECOMMENDED NEXT STEPS */}
      <div className="space-y-1.5">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          4. Recommended Next Steps
        </h3>
        <p className="text-sm font-medium text-emerald-950 leading-relaxed bg-emerald-50/70 p-3 rounded-lg border border-emerald-200">
          {next_step_message}
        </p>
      </div>

      {/* 5. LIMITATIONS & CLINICAL DISCLAIMERS */}
      <LimitationNotice limitations={limitations} />
    </div>
  );
}
