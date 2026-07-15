import { Bot, Database, FileSearch, FileSpreadsheet, ShieldCheck, Sparkles } from "lucide-react";

const stages = [
  ["Reading Excel", FileSpreadsheet],
  ["Detecting issues", FileSearch],
  ["Searching sources", Database],
  ["Structuring proposals", Bot],
  ["Preparing review", ShieldCheck],
] as const;

export function AnalysisOverlay({ visible }: { visible: boolean }) {
  if (!visible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 px-4 backdrop-blur-sm">
      <div className="analysis-card w-full max-w-3xl rounded-xl border border-white/50 bg-white p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 rounded-md bg-blue-50 px-3 py-1.5 text-sm font-semibold text-blue-700">
              <Sparkles className="h-4 w-4 animate-pulse" />
              Analysis running
            </div>
            <h2 className="mt-4 text-2xl font-semibold tracking-normal">Building evidence-backed tariff proposals</h2>
            <p className="mt-2 text-sm text-slate-600">
              The agent is reading the workbook, checking deterministic controls, searching mock enterprise sources, and preparing human-review proposals.
            </p>
          </div>
          <div className="analysis-orbit hidden h-20 w-20 shrink-0 rounded-full border border-blue-100 bg-blue-50 md:block" />
        </div>

        <div className="mt-6 overflow-hidden rounded-lg border border-line bg-slate-50">
          <div className="analysis-progress h-2 bg-blue-600" />
          <div className="grid gap-3 p-4 md:grid-cols-5">
            {stages.map(([label, Icon], index) => (
              <div key={label} className="analysis-step rounded-md border border-slate-200 bg-white p-3" style={{ animationDelay: `${index * 160}ms` }}>
                <Icon className="h-5 w-5 text-blue-600" />
                <div className="mt-3 text-sm font-semibold">{label}</div>
                <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100">
                  <div className="analysis-mini-bar h-full rounded-full bg-blue-500" style={{ animationDelay: `${index * 180}ms` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-5 grid grid-cols-3 gap-2">
          {Array.from({ length: 18 }).map((_, index) => (
            <div key={index} className="analysis-skeleton h-2 rounded-full bg-slate-100" style={{ animationDelay: `${index * 45}ms` }} />
          ))}
        </div>
      </div>
    </div>
  );
}
