import { Download, FileArchive, FileSpreadsheet, FileText } from "lucide-react";
import { api, downloadUrl } from "../api";

const downloads = [
  ["Updated Excel", "/download/updated-excel", FileSpreadsheet],
  ["Audit JSON", "/download/audit-json", FileArchive],
  ["Markdown report", "/download/report-md", FileText],
] as const;

export function DownloadsPanel({
  busy,
  onApply,
}: {
  busy: boolean;
  onApply: () => Promise<void>;
}) {
  return (
    <section className="rounded-lg border border-line bg-white p-4 shadow-soft">
      <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-lg font-semibold">Excel update and downloads</h2>
          <p className="text-sm text-slate-500">Apply approved changes, then export the workbook and audit artifacts.</p>
        </div>
        <button
          disabled={busy}
          onClick={() => void onApply()}
          className="inline-flex items-center justify-center gap-2 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
        >
          <Download className="h-4 w-4" /> Apply Approved Updates
        </button>
      </div>
      <div className="grid gap-3 md:grid-cols-3">
        {downloads.map(([label, path, Icon]) => (
          <a
            key={path}
            href={downloadUrl(path)}
            className="flex items-center justify-between rounded-md border border-line bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-100"
          >
            <span className="inline-flex items-center gap-2">
              <Icon className="h-4 w-4" /> {label}
            </span>
            <Download className="h-4 w-4 text-slate-400" />
          </a>
        ))}
      </div>
      <p className="mt-3 text-xs text-slate-500">Backend: {api.baseUrl}</p>
    </section>
  );
}
