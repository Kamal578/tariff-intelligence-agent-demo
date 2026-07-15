import type { AuditEntry } from "../types";

export function AuditLog({ entries }: { entries: AuditEntry[] }) {
  return (
    <section className="rounded-lg border border-line bg-white p-4 shadow-soft">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Audit log</h2>
        <span className="text-sm text-slate-500">{entries.length} decisions</span>
      </div>
      {entries.length === 0 ? (
        <div className="rounded-md bg-slate-50 p-5 text-sm text-slate-500">Approve or reject proposals to populate the audit trail.</div>
      ) : (
        <div className="max-h-72 overflow-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="sticky top-0 bg-slate-100 text-xs uppercase text-slate-500">
              <tr>
                {["Time", "Pack", "Field", "Decision", "Reviewer", "Reason"].map((header) => (
                  <th key={header} className="px-3 py-2 font-semibold">{header}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={`${entry.proposal_id}-${entry.timestamp}`} className="border-t border-slate-100">
                  <td className="px-3 py-2">{new Date(entry.timestamp).toLocaleString()}</td>
                  <td className="px-3 py-2 font-medium">{entry.pack_name ?? entry.pack_id}</td>
                  <td className="px-3 py-2">{entry.field_name}</td>
                  <td className="px-3 py-2">
                    <span className={`rounded-md px-2 py-1 text-xs font-semibold ${
                      entry.decision === "approved" ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"
                    }`}>
                      {entry.decision}
                    </span>
                  </td>
                  <td className="px-3 py-2">{entry.reviewer}</td>
                  <td className="px-3 py-2 text-slate-600">{entry.review_reasoning}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
