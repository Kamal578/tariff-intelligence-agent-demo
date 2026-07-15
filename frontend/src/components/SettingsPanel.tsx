import { CheckCircle2, Database, Server, Sparkles, XCircle } from "lucide-react";
import type { ReactNode } from "react";
import type { AnalysisMode, ConfigStatus } from "../types";

export function SettingsPanel({
  config,
  analysisMode,
  onModeChange,
}: {
  config?: ConfigStatus;
  analysisMode: AnalysisMode;
  onModeChange: (mode: AnalysisMode) => void;
}) {
  return (
    <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
      <section className="rounded-lg border border-line bg-white shadow-soft">
        <div className="border-b border-line px-4 py-3">
          <h2 className="text-lg font-semibold tracking-normal">Runtime Settings</h2>
          <p className="text-sm text-slate-500">Controls that affect how analysis jobs are created.</p>
        </div>
        <div className="space-y-5 p-4">
          <div>
            <div className="text-sm font-semibold text-slate-700">Analysis mode</div>
            <div className="mt-2 inline-flex rounded-md border border-line bg-slate-50 p-1">
              <button
                type="button"
                onClick={() => onModeChange("preview")}
                className={`rounded px-3 py-2 text-sm font-semibold ${analysisMode === "preview" ? "bg-ink text-white" : "text-slate-600 hover:bg-white"}`}
              >
                Quick Preview
              </button>
              <button
                type="button"
                onClick={() => onModeChange("gemini")}
                className={`rounded px-3 py-2 text-sm font-semibold ${analysisMode === "gemini" ? "bg-ink text-white" : "text-slate-600 hover:bg-white"}`}
              >
                Gemini
              </button>
            </div>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <StatusRow label="Environment" value={config?.environment ?? "-"} icon={<Server className="h-4 w-4" />} />
            <StatusRow label="Gemini model" value={config?.gemini_model ?? "-"} icon={<Sparkles className="h-4 w-4" />} />
            <StatusRow label="Input Excel" value={config?.input_excel ?? "-"} icon={<Database className="h-4 w-4" />} />
            <StatusRow label="Output directory" value={config?.output_dir ?? "-"} icon={<Database className="h-4 w-4" />} />
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-line bg-white p-4 shadow-soft">
        <h2 className="text-lg font-semibold tracking-normal">Readiness</h2>
        <div className="mt-4 space-y-3">
          <ReadinessItem ready={Boolean(config?.mock_sources_ready)} label="Mock sources indexed" />
          <ReadinessItem ready={Boolean(config && !config.real_connectors_used)} label="No real connectors enabled" />
          <ReadinessItem ready={Boolean(config?.gemini_configured)} label="Gemini API key configured" optional />
        </div>
        <div className="mt-5 rounded-md bg-slate-50 p-3 text-sm text-slate-600">
          Source counts:{" "}
          {config
            ? Object.entries(config.source_counts).map(([key, value]) => `${key} ${value}`).join(" / ")
            : "-"}
        </div>
      </section>
    </div>
  );
}

function StatusRow({ label, value, icon }: { label: string; value: string; icon: ReactNode }) {
  return (
    <div className="rounded-md border border-line bg-slate-50 p-3">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
        {icon}
        {label}
      </div>
      <div className="mt-2 break-words text-sm font-semibold text-slate-800">{value}</div>
    </div>
  );
}

function ReadinessItem({ ready, label, optional = false }: { ready: boolean; label: string; optional?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-md border border-line px-3 py-2">
      <span className="text-sm font-semibold text-slate-700">{label}</span>
      <span className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-semibold ${ready ? "bg-emerald-50 text-emerald-700" : optional ? "bg-amber-50 text-amber-700" : "bg-red-50 text-red-700"}`}>
        {ready ? <CheckCircle2 className="h-3.5 w-3.5" /> : <XCircle className="h-3.5 w-3.5" />}
        {ready ? "Ready" : optional ? "Optional" : "Blocked"}
      </span>
    </div>
  );
}
