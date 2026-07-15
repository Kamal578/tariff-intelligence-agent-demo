import { Check, X } from "lucide-react";
import type { ProposedUpdate } from "../types";

export function ProposalDetailPanel({
  proposal,
  onApprove,
  onReject,
  busy,
}: {
  proposal?: ProposedUpdate;
  onApprove: (proposal: ProposedUpdate) => void;
  onReject: (proposal: ProposedUpdate) => void;
  busy: boolean;
}) {
  if (!proposal) {
    return (
      <aside className="rounded-lg border border-line bg-white p-5 shadow-soft">
        <h2 className="text-lg font-semibold">Proposal detail</h2>
        <p className="mt-3 text-sm text-slate-500">Select a proposal to inspect reasoning and approve or reject it.</p>
      </aside>
    );
  }

  return (
    <aside className="rounded-lg border border-line bg-white p-5 shadow-soft">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold">{proposal.pack_name}</h2>
          <p className="text-sm text-slate-500">{proposal.issue_type}</p>
        </div>
        {proposal.source_conflict_detected && (
          <span className="rounded-md bg-red-50 px-2 py-1 text-xs font-medium text-red-700">conflict</span>
        )}
      </div>
      <div className="mt-5 grid grid-cols-2 gap-3">
        <div className="rounded-md bg-slate-50 p-3">
          <div className="text-xs uppercase text-slate-500">Old value</div>
          <div className="mt-1 font-semibold">{String(proposal.old_value ?? "-")}</div>
        </div>
        <div className="rounded-md bg-blue-50 p-3">
          <div className="text-xs uppercase text-blue-600">Proposed value</div>
          <div className="mt-1 font-semibold text-blue-800">{String(proposal.proposed_value ?? "-")}</div>
        </div>
      </div>
      <div className="mt-5 space-y-4 text-sm">
        <div>
          <h3 className="font-semibold">Reasoning</h3>
          <p className="mt-1 text-slate-600">{proposal.reasoning_summary}</p>
        </div>
        <div>
          <h3 className="font-semibold">Decision basis</h3>
          <p className="mt-1 text-slate-600">{proposal.decision_basis}</p>
        </div>
        <div>
          <h3 className="font-semibold">Freshness</h3>
          <p className="mt-1 text-slate-600">{proposal.source_freshness_summary}</p>
        </div>
      </div>
      <div className="mt-5 flex gap-3">
        <button
          disabled={busy}
          onClick={() => onApprove(proposal)}
          className="inline-flex flex-1 items-center justify-center gap-2 rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700"
        >
          <Check className="h-4 w-4" /> Approve
        </button>
        <button
          disabled={busy}
          onClick={() => onReject(proposal)}
          className="inline-flex flex-1 items-center justify-center gap-2 rounded-md bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700"
        >
          <X className="h-4 w-4" /> Reject
        </button>
      </div>
    </aside>
  );
}
