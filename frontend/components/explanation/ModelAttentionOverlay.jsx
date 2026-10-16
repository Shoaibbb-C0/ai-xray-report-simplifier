"use client";

import React, { useState } from "react";

/**
 * ModelAttentionOverlay: Renders Grad-CAM attention heatmap over the radiograph
 * with opacity controls and explicit non-diagnostic medical disclaimers.
 */
export default function ModelAttentionOverlay({
  baseImageSrc,
  attentionOverlaySrc,
  available = false,
  disclaimer = "Grad-CAM highlights areas that influenced the model's prediction. It is NOT a confirmed injury site or clinical localization.",
}) {
  const [opacity, setOpacity] = useState(70);

  if (!available || !attentionOverlaySrc) {
    return (
      <div className="w-full bg-slate-50 border border-slate-200 rounded-xl p-5 text-center">
        <div className="w-10 h-10 mx-auto mb-2 text-slate-400">
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
        </div>
        <h4 className="text-sm font-semibold text-slate-700">Model Attention Heatmap Not Available</h4>
        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
          Attention heatmaps are suppressed for non-fracture, uncertain, or unsupported cases to prevent misleading interpretations.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
      {/* Header with Safety Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <span>Model Visual Attention</span>
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 bg-indigo-100 text-indigo-800 rounded">
              Grad-CAM
            </span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Highlights pixel features that most influenced the network's calculation.
          </p>
        </div>

        {/* Opacity Control */}
        <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 self-start sm:self-auto">
          <label htmlFor="heatmap-opacity" className="text-xs font-medium text-slate-600 whitespace-nowrap">
            Heatmap: {opacity}%
          </label>
          <input
            id="heatmap-opacity"
            type="range"
            min="0"
            max="100"
            value={opacity}
            onChange={(e) => setOpacity(Number(e.target.value))}
            className="w-24 h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
          />
        </div>
      </div>

      {/* Layered Image Display */}
      <div className="relative w-full aspect-square max-w-md mx-auto rounded-lg overflow-hidden bg-black border border-slate-300 shadow-inner flex items-center justify-center">
        {/* Base Radiograph */}
        {baseImageSrc ? (
          <img
            src={baseImageSrc}
            alt="Original radiograph"
            className="absolute inset-0 w-full h-full object-contain"
          />
        ) : (
          <div className="text-slate-500 text-xs italic">Radiograph loaded</div>
        )}

        {/* Grad-CAM Heatmap Layer */}
        <img
          src={attentionOverlaySrc}
          alt="Grad-CAM model attention heatmap overlay"
          style={{ opacity: opacity / 100 }}
          className="absolute inset-0 w-full h-full object-contain pointer-events-none transition-opacity duration-150"
        />

        {/* Overlay Safety Badge */}
        <div className="absolute bottom-2 left-2 right-2 bg-slate-900/80 backdrop-blur-sm text-slate-100 px-2.5 py-1.5 rounded text-[11px] font-medium text-center">
          Areas that influenced the model • Not an exact injury location
        </div>
      </div>

      {/* Explicit Disclaimer Notice */}
      <div className="mt-4 p-3 bg-indigo-50/60 border border-indigo-100 rounded-lg flex items-start gap-2.5">
        <svg className="w-4 h-4 text-indigo-600 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p className="text-xs text-indigo-950 leading-relaxed">
          {disclaimer}
        </p>
      </div>
    </div>
  );
}
