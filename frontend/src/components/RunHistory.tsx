import { AlertTriangle, CheckCircle2, Clock3, Loader2 } from "lucide-react";
import type { AnalysisJob } from "../types";

function statusIcon(status: AnalysisJob["status"]) {
  if (status === "completed") return <CheckCircle2 className="h-4 w-4 text-emerald-600" />;
  if (status === "failed") return <AlertTriangle className="h-4 w-4 text-red-600" />;
  if (status === "running") return <Loader2 className="h-4 w-4 animate-spin text-blue-600" />;
  return <Clock3 className="h-4 w-4 text-slate-500" />;
}

export function RunHistory({ jobs, activeJobId }: { jobs: AnalysisJob[]; activeJobId?: string }) {
  return (
    <section className="rounded-lg border border-line bg-white shadow-soft">
      <div className="border-b border-line px-4 py-3">
        <h2 className="text-lg font-semibold tracking-normal">Analysis Runs</h2>
        <p className="text-sm text-slate-500">Operational history for preview and Gemini tariff analysis jobs.</p>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-line text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              {["Run", "Status", "Stage", "Mode", "Progress", "Counts", "Started", "Finished"].map((header) => (
                <th key={header} className="px-4 py-3 font-semibold">{header}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {jobs.map((job, index) => (
              <tr
                key={job.job_id}
                className={`motion-row ${job.job_id === activeJobId ? "bg-blue-50/60" : "hover:bg-slate-50"}`}
                style={{ animationDelay: `${index * 35}ms` }}
              >
                <td className="px-4 py-3 font-mono text-xs text-slate-700">{job.job_id}</td>
                <td className="px-4 py-3">
                  <span className="inline-flex items-center gap-2 rounded-md bg-slate-100 px-2 py-1 font-semibold capitalize text-slate-700">
                    {statusIcon(job.status)}
                    {job.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-700">{job.error ?? job.stage}</td>
                <td className="px-4 py-3">
                  <div className="text-slate-700">Requested {job.requested_mode}</div>
                  <div className="text-xs text-slate-500">Actual {job.actual_mode ?? "-"}</div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex min-w-32 items-center gap-2">
                    <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                      <div className="h-full rounded-full bg-blue-600" style={{ width: `${job.progress}%` }} />
                    </div>
                    <span className="w-9 text-right tabular-nums text-xs font-semibold">{job.progress}%</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-slate-600">
                  {job.summary ? `${job.summary.records} records / ${job.summary.proposals} proposals` : "-"}
                </td>
                <td className="px-4 py-3 text-slate-500">{formatDate(job.started_at ?? job.created_at)}</td>
                <td className="px-4 py-3 text-slate-500">{job.finished_at ? formatDate(job.finished_at) : "-"}</td>
              </tr>
            ))}
            {!jobs.length && (
              <tr>
                <td className="px-4 py-8 text-center text-slate-500" colSpan={8}>No analysis runs yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}
