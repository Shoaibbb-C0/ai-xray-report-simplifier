export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col justify-between px-6 py-12 md:px-16 lg:px-24 max-w-6xl mx-auto">
      {/* Header bar */}
      <header className="flex items-center justify-between border-b border-slate-800/80 pb-6">
        <div className="flex items-center space-x-3">
          <div className="w-2.5 h-2.5 rounded-full bg-teal-400"></div>
          <span className="text-sm font-medium tracking-wider text-slate-300 uppercase">
            AI X-Ray Project
          </span>
        </div>
        <div className="text-xs font-mono text-slate-400 px-3 py-1 rounded-full border border-slate-800 bg-slate-900/50">
          Stage 1 Foundation Active
        </div>
      </header>

      {/* Hero section */}
      <section className="py-20 md:py-28 max-w-3xl">
        <p className="text-sm font-mono uppercase tracking-widest text-teal-400 mb-4">
          In-House Clinical Intelligence
        </p>
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-light tracking-tight text-white leading-tight mb-8">
          Patient-support X-ray analysis, simplified.
        </h1>
        <p className="text-lg md:text-xl text-slate-400 leading-relaxed font-normal mb-12">
          A dedicated platform assisting patients in understanding diagnostic imaging.
          Built strictly on in-house trained PyTorch deep learning models—not third-party
          generative AI APIs.
        </p>

        {/* Feature roadmap cards (Minimal architectural overview) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
          <div className="p-6 rounded-xl border border-slate-800/80 bg-slate-900/30">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider block mb-2">
              Feature 1
            </span>
            <h2 className="text-lg font-medium text-slate-200 mb-2">
              Smart X-Ray Analysis
            </h2>
            <p className="text-sm text-slate-400 leading-relaxed">
              Automated validation, anatomical routing, and patient-friendly visual explanations
              derived from custom models.
            </p>
          </div>

          <div className="p-6 rounded-xl border border-slate-800/80 bg-slate-900/30">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider block mb-2">
              Feature 2
            </span>
            <h2 className="text-lg font-medium text-slate-200 mb-2">
              My X-Ray Map
            </h2>
            <p className="text-sm text-slate-400 leading-relaxed">
              Interactive anatomical exploration mapping historical imaging, findings, and longitudinal
              scan comparisons.
            </p>
          </div>
        </div>
      </section>

      {/* Safety boundary & footer */}
      <footer className="pt-8 border-t border-slate-800/80 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-xs text-slate-400">
        <p>
          Medical Boundary: Educational &amp; patient-support tool. Not a medical diagnosis.
        </p>
        <div className="flex items-center space-x-4">
          <span>FastAPI Backend: :8000</span>
          <span>Next.js Frontend: :3000</span>
        </div>
      </footer>
    </main>
  );
}
