import { Activity, Clock3, Loader2, Square } from "lucide-react";
import type { AnalysisJob } from "../types";

export function ActiveRunPanel({ job, onCancel }: { job?: AnalysisJob; onCancel: (job: AnalysisJob) => void }) {
  if (!job || !["queued", "running", "cancelling"].includes(job.status)) return null;
  const cancelling = job.status === "cancelling";

  return (
    <section className="live-run-panel rounded-lg border border-blue-100 bg-white p-4 shadow-soft">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-2 rounded-md bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700">
              {job.status === "running" ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Clock3 className="h-3.5 w-3.5" />}
              {job.status}
            </span>
            <span className="font-mono text-xs text-slate-500">{job.job_id}</span>
          </div>
          <h2 className="mt-2 truncate text-lg font-semibold tracking-normal">{job.stage}</h2>
          <p className="mt-1 text-sm text-slate-500">
            Requested {job.requested_mode} mode. Last backend update {formatTime(job.updated_at)}.
          </p>
        </div>
        <div className="w-full shrink-0 space-y-3 md:w-80">
          <div className="mb-2 flex items-center justify-between text-sm">
            <span className="inline-flex items-center gap-2 font-semibold text-slate-700">
              <Activity className="h-4 w-4 text-blue-600" />
              Live progress
            </span>
            <span className="tabular-nums font-semibold text-blue-700">{job.progress}%</span>
          </div>
          <div className="h-3 overflow-hidden rounded-full bg-blue-50">
            <div className="analysis-determinate h-full rounded-full bg-blue-600" style={{ width: `${job.progress}%` }} />
          </div>
          <button
            type="button"
            disabled={cancelling}
            onClick={() => onCancel(job)}
            className="inline-flex w-full items-center justify-center gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm font-semibold text-red-700 hover:bg-red-100 disabled:bg-slate-100 disabled:text-slate-500"
          >
            {cancelling ? <Loader2 className="h-4 w-4 animate-spin" /> : <Square className="h-4 w-4" />}
            {cancelling ? "Cancelling..." : "Cancel Run"}
          </button>
        </div>
      </div>
    </section>
  );
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(value));
}
