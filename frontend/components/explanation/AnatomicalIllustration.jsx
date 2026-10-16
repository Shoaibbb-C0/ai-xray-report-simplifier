"use client";

import React from "react";

/**
 * AnatomicalIllustration: Renders curated vector SVG anatomical guides with accessible labels
 * and explicit non-diagnostic educational badges.
 */
export default function AnatomicalIllustration({
  illustrationUrl,
  title = "Anatomical Guide",
  altText = "Educational anatomy illustration",
  labelNotice = "Example illustration — Not patient's X-ray",
  maxWidth = "max-w-md",
}) {
  return (
    <div className={`flex flex-col items-center bg-slate-50 border border-slate-200 rounded-xl p-4 shadow-sm ${maxWidth} w-full`}>
      {/* Educational Notice Banner */}
      <div className="w-full flex items-center justify-between mb-3 px-3 py-1.5 bg-amber-50 border border-amber-200 rounded-md">
        <span className="text-xs font-semibold text-amber-800 flex items-center gap-1.5">
          <svg className="w-4 h-4 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {labelNotice}
        </span>
        <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 bg-amber-200 text-amber-900 rounded">
          Educational
        </span>
      </div>

      {/* SVG Container */}
      <div className="relative w-full aspect-square flex items-center justify-center bg-white rounded-lg border border-slate-100 overflow-hidden shadow-inner">
        {illustrationUrl ? (
          <img
            src={illustrationUrl}
            alt={altText}
            className="w-full h-full object-contain p-2"
            loading="lazy"
          />
        ) : (
          <div className="text-slate-400 text-sm italic">Illustration not available</div>
        )}
      </div>

      {/* Title & Caption */}
      <div className="mt-3 text-center w-full">
        <h4 className="text-sm font-semibold text-slate-800">{title}</h4>
        <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{altText}</p>
      </div>
    </div>
  );
}
