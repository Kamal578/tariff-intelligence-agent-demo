import type { ProposedUpdate, TariffRecord } from "../types";

export function RecordsTable({ records, proposals }: { records: TariffRecord[]; proposals: ProposedUpdate[] }) {
  const issueIds = new Set(proposals.map((proposal) => proposal.pack_id));

  return (
    <section className="rounded-lg border border-line bg-white p-4 shadow-soft">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Original tariff records</h2>
        <span className="text-sm text-slate-500">{records.length} rows</span>
      </div>
      {records.length === 0 ? (
        <div className="rounded-md bg-slate-50 p-6 text-sm text-slate-500">Run analysis to load Excel records.</div>
      ) : (
        <div className="max-h-96 overflow-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="sticky top-0 bg-slate-100 text-xs uppercase text-slate-500">
              <tr>
                {["Pack", "Tariff", "Price", "Validity", "Data", "Minutes", "Status", "Updated"].map((header) => (
                  <th key={header} className="px-3 py-2 font-semibold">{header}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {records.map((record) => (
                <tr key={record.pack_id} className={issueIds.has(record.pack_id) ? "bg-amber-50/60" : "border-t border-slate-100"}>
                  <td className="px-3 py-2 font-medium">{record.pack_name}</td>
                  <td className="px-3 py-2">{record.tariff_name ?? "-"}</td>
                  <td className="px-3 py-2">{record.price_azn ?? "-"}</td>
                  <td className="px-3 py-2">{record.validity_days ?? "-"}</td>
                  <td className="px-3 py-2">{record.data_gb ?? "-"}</td>
                  <td className="px-3 py-2">{record.minutes ?? "-"}</td>
                  <td className="px-3 py-2">{record.status ?? "-"}</td>
                  <td className="px-3 py-2">{record.last_updated ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
