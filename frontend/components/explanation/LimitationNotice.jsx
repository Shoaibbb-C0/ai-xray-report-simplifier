"use client";

import React from "react";

/**
 * LimitationNotice: Displays prominent medical limitation notices and clinical safety warnings.
 */
export default function LimitationNotice({
  limitations = [],
  className = "",
}) {
  if (!limitations || limitations.length === 0) {
    return null;
  }

  return (
    <div className={`w-full bg-amber-50/80 border border-amber-200 rounded-xl p-4 text-amber-950 ${className}`}>
      <div className="flex items-center gap-2 mb-2 text-amber-900 font-bold text-sm">
        <svg className="w-5 h-5 text-amber-700 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <span>Important Limitations & Clinical Disclaimers</span>
      </div>

      <ul className="space-y-1.5 pl-6 list-disc text-xs text-amber-900/90 leading-relaxed">
        {limitations.map((item, index) => (
          <li key={index}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
