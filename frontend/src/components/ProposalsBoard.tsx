import { useMemo, useState } from "react";
import type { ProposalStatus, ProposedUpdate, RiskLevel } from "../types";

const riskClasses: Record<RiskLevel, string> = {
  low: "bg-emerald-50 text-emerald-700",
  medium: "bg-amber-50 text-amber-700",
  high: "bg-red-50 text-red-700",
};

const statusClasses: Record<ProposalStatus, string> = {
  new: "bg-blue-50 text-blue-700",
  proposed: "bg-blue-50 text-blue-700",
  needs_review: "bg-orange-50 text-orange-700",
  approved: "bg-emerald-50 text-emerald-700",
  rejected: "bg-red-50 text-red-700",
  applied: "bg-teal-50 text-teal-700",
  superseded: "bg-slate-100 text-slate-600",
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
  const [riskFilter, setRiskFilter] = useState<"all" | RiskLevel>("all");
  const [statusFilter, setStatusFilter] = useState<"all" | ProposalStatus>("all");
  const [confidenceFilter, setConfidenceFilter] = useState<"all" | "high" | "low">("all");
  const [conflictsOnly, setConflictsOnly] = useState(false);
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return proposals.filter((proposal) => {
      const matchesRisk = riskFilter === "all" || proposal.risk_level === riskFilter;
      const matchesStatus = statusFilter === "all" || proposal.status === statusFilter;
      const matchesConfidence =
        confidenceFilter === "all" ||
        (confidenceFilter === "high" && proposal.confidence_score >= 0.8) ||
        (confidenceFilter === "low" && proposal.confidence_score < 0.7);
      const matchesConflict = !conflictsOnly || proposal.source_conflict_detected;
      const matchesQuery =
        !needle ||
        [proposal.pack_id, proposal.pack_name, proposal.field_name, proposal.issue_type]
          .join(" ")
          .toLowerCase()
          .includes(needle);
      return matchesRisk && matchesStatus && matchesConfidence && matchesConflict && matchesQuery;
    });
  }, [confidenceFilter, conflictsOnly, proposals, query, riskFilter, statusFilter]);

  return (
    <section className="rounded-lg border border-line bg-white p-4 shadow-soft">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold">Proposal review board</h2>
        <span className="text-sm text-slate-500">{filtered.length} of {proposals.length} proposals</span>
      </div>
      <div className="mb-3 grid gap-2 md:grid-cols-[minmax(180px,1fr)_repeat(4,max-content)]">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search pack, field, issue"
          className="rounded-md border border-line px-3 py-2 text-sm"
        />
        <Select value={riskFilter} onChange={(value) => setRiskFilter(value as "all" | RiskLevel)} options={["all", "low", "medium", "high"]} />
        <Select value={statusFilter} onChange={(value) => setStatusFilter(value as "all" | ProposalStatus)} options={["all", "new", "proposed", "needs_review", "approved", "rejected", "applied", "superseded"]} />
        <Select value={confidenceFilter} onChange={(value) => setConfidenceFilter(value as "all" | "high" | "low")} options={["all", "high", "low"]} />
        <label className="inline-flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm font-semibold text-slate-600">
          <input type="checkbox" checked={conflictsOnly} onChange={(event) => setConflictsOnly(event.target.checked)} />
          Conflicts
        </label>
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
              {filtered.map((proposal, index) => (
                <tr
                  key={proposal.proposal_id}
                  onClick={() => onSelect(proposal)}
                  className={`motion-row cursor-pointer border-t border-slate-100 hover:bg-blue-50 ${
                    selectedId === proposal.proposal_id ? "bg-blue-50" : ""
                  }`}
                  style={{ animationDelay: `${Math.min(index, 12) * 28}ms` }}
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
              {!filtered.length && (
                <tr>
                  <td className="px-3 py-8 text-center text-slate-500" colSpan={8}>No proposals match the current filters.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function Select({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  return (
    <select
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className="rounded-md border border-line bg-white px-3 py-2 text-sm font-semibold text-slate-600"
    >
      {options.map((option) => (
        <option key={option} value={option}>{option.replace("_", " ")}</option>
      ))}
    </select>
  );
}
