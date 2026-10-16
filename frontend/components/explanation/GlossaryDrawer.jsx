"use client";

import React, { useState } from "react";

/**
 * GlossaryDrawer: Expandable patient glossary providing plain-language
 * definitions for medical and AI terms used in the explanation.
 */
export default function GlossaryDrawer({
  glossary = {},
  className = "",
}) {
  const [isOpen, setIsOpen] = useState(false);

  const termKeys = Object.keys(glossary);
  if (termKeys.length === 0) return null;

  return (
    <div className={`w-full bg-slate-50 border border-slate-200 rounded-xl overflow-hidden ${className}`}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-slate-100/70 transition-colors"
      >
        <span className="text-sm font-bold text-slate-800 flex items-center gap-2">
          <svg className="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          Medical & AI Glossary ({termKeys.length} terms)
        </span>
        <span className="text-xs font-medium text-slate-500 flex items-center gap-1">
          {isOpen ? "Hide" : "Show terms"}
          <svg
            className={`w-4 h-4 transform transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </span>
      </button>

      {isOpen && (
        <div className="p-4 pt-1 border-t border-slate-200/60 divide-y divide-slate-100">
          {termKeys.map((term) => (
            <div key={term} className="py-2.5">
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-700">
                {term.replace(/_/g, " ")}
              </span>
              <p className="text-xs text-slate-600 mt-0.5 leading-relaxed">
                {glossary[term]}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
