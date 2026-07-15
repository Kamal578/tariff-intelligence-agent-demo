import type { ProposalStatus, ProposedUpdate, RiskLevel } from "../types";

const riskClasses: Record<RiskLevel, string> = {
  low: "bg-emerald-50 text-emerald-700",
  medium: "bg-amber-50 text-amber-700",
  high: "bg-red-50 text-red-700",
};

const statusClasses: Record<ProposalStatus, string> = {
  proposed: "bg-blue-50 text-blue-700",
  needs_review: "bg-orange-50 text-orange-700",
  approved: "bg-emerald-50 text-emerald-700",
  rejected: "bg-red-50 text-red-700",
};

export function ProposalsBoard({
  proposals,
  selectedId,
  onSelect,
}: {
  proposals: ProposedUpdate[];
  selectedId?: string;
  onSelect: (proposal: ProposedUpdate) => void;
}) {
  return (
    <section className="rounded-lg border border-line bg-white p-4 shadow-soft">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Proposal review board</h2>
        <span className="text-sm text-slate-500">{proposals.length} proposals</span>
      </div>
      {proposals.length === 0 ? (
        <div className="rounded-md bg-slate-50 p-6 text-sm text-slate-500">Run analysis to generate proposals.</div>
      ) : (
        <div className="max-h-[34rem] overflow-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="sticky top-0 bg-slate-100 text-xs uppercase text-slate-500">
              <tr>
                {["Pack", "Field", "Old", "Proposed", "Confidence", "Risk", "Status", "Conflict"].map((header) => (
                  <th key={header} className="px-3 py-2 font-semibold">{header}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {proposals.map((proposal) => (
                <tr
                  key={proposal.proposal_id}
                  onClick={() => onSelect(proposal)}
                  className={`cursor-pointer border-t border-slate-100 hover:bg-blue-50 ${
                    selectedId === proposal.proposal_id ? "bg-blue-50" : ""
                  }`}
                >
                  <td className="px-3 py-2 font-medium">{proposal.pack_name}</td>
                  <td className="px-3 py-2">{proposal.field_name}</td>
                  <td className="px-3 py-2">{String(proposal.old_value ?? "-")}</td>
                  <td className="px-3 py-2">{String(proposal.proposed_value ?? "-")}</td>
                  <td className="px-3 py-2">{Math.round(proposal.confidence_score * 100)}%</td>
                  <td className="px-3 py-2">
                    <span className={`rounded-md px-2 py-1 text-xs font-medium ${riskClasses[proposal.risk_level]}`}>
                      {proposal.risk_level}
                    </span>
                  </td>
                  <td className="px-3 py-2">
                    <span className={`rounded-md px-2 py-1 text-xs font-medium ${statusClasses[proposal.status]}`}>
                      {proposal.status}
                    </span>
                  </td>
                  <td className="px-3 py-2">{proposal.source_conflict_detected ? "Yes" : "No"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
