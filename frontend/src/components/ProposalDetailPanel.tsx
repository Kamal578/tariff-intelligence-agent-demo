import { useState } from "react";
import { Check, FileDiff, ShieldCheck, X } from "lucide-react";
import type { ProposedUpdate } from "../types";
import { EvidenceCard } from "./EvidenceCard";

export function ProposalDetailPanel({
  proposal,
  onApprove,
  onReject,
  onOpenSource,
  busy,
}: {
  proposal?: ProposedUpdate;
  onApprove: (proposal: ProposedUpdate, reasoning?: string) => void;
  onReject: (proposal: ProposedUpdate, reasoning?: string) => void;
  onOpenSource?: (sourceId: string) => void;
  busy: boolean;
}) {
  const [reviewNote, setReviewNote] = useState("");

  if (!proposal) {
    return (
      <aside className="rounded-lg border border-line bg-white p-5 shadow-soft">
        <h2 className="text-lg font-semibold">Proposal detail</h2>
        <p className="mt-3 text-sm text-slate-500">Select a proposal to inspect reasoning and approve or reject it.</p>
      </aside>
    );
  }

  const approvedSources = proposal.evidence_sources.filter((item) => item.document_status === "approved").length;
  const deprecatedSources = proposal.evidence_sources.filter((item) => item.document_status === "deprecated" || item.document_status === "draft").length;
  const newestEvidence = proposal.evidence_sources
    .map((item) => new Date(item.timestamp))
    .sort((left, right) => right.getTime() - left.getTime())[0];
  const locked = proposal.status === "applied" || proposal.status === "superseded";

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
      <div className="mt-5 rounded-lg border border-line bg-slate-50 p-3">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-700">
          <FileDiff className="h-4 w-4" />
          Proposed field diff
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-md bg-white p-3">
            <div className="text-xs uppercase text-slate-500">Field</div>
            <div className="mt-1 font-semibold">{proposal.field_name}</div>
          </div>
          <div className="rounded-md bg-red-50 p-3">
            <div className="text-xs uppercase text-red-600">Current Excel</div>
            <div className="mt-1 break-words font-semibold text-red-800">{String(proposal.old_value ?? "-")}</div>
          </div>
          <div className="rounded-md bg-emerald-50 p-3">
            <div className="text-xs uppercase text-emerald-700">Proposed</div>
            <div className="mt-1 break-words font-semibold text-emerald-800">{String(proposal.proposed_value ?? "-")}</div>
          </div>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-3 gap-3 text-sm">
        <TraceMetric label="Confidence" value={`${Math.round(proposal.confidence_score * 100)}%`} />
        <TraceMetric label="Approved sources" value={String(approvedSources)} />
        <TraceMetric label="Newest evidence" value={newestEvidence ? newestEvidence.toLocaleDateString() : "-"} />
      </div>
      <div className="mt-4 rounded-md border border-line bg-white p-3">
        <div className="flex items-center gap-2 text-sm font-semibold">
          <ShieldCheck className="h-4 w-4 text-blue-600" />
          Evidence traceability
        </div>
        <div className="mt-2 grid gap-2 text-sm text-slate-600">
          <div>Authority: {approvedSources} approved source(s), {deprecatedSources} deprecated/draft source(s).</div>
          <div>Conflict policy: {proposal.source_conflict_detected ? "manual review required before approval" : "no conflicting source status detected"}.</div>
          <div>Freshness: {proposal.source_freshness_summary}</div>
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
      <div className="mt-5">
        <h3 className="mb-2 text-sm font-semibold">Evidence</h3>
        <div className="space-y-3">
          {proposal.evidence_sources.length === 0 ? (
            <div className="rounded-md bg-slate-50 p-3 text-sm text-slate-500">No evidence attached.</div>
          ) : (
            proposal.evidence_sources.map((evidence) => (
              <EvidenceCard key={evidence.source_id} evidence={evidence} onOpenSource={onOpenSource} />
            ))
          )}
        </div>
      </div>
      <div className="mt-5">
        <label className="text-sm font-semibold" htmlFor="review-note">Review comment</label>
        <textarea
          id="review-note"
          value={reviewNote}
          onChange={(event) => setReviewNote(event.target.value)}
          rows={3}
          className="mt-2 w-full rounded-md border border-line px-3 py-2 text-sm"
          placeholder="Add rationale for approval or rejection"
        />
      </div>
      <div className="mt-5 flex gap-3">
        <button
          disabled={busy || locked}
          onClick={() => onApprove(proposal, reviewNote)}
          className="inline-flex flex-1 items-center justify-center gap-2 rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700"
        >
          <Check className="h-4 w-4" /> Approve
        </button>
        <button
          disabled={busy || locked}
          onClick={() => onReject(proposal, reviewNote)}
          className="inline-flex flex-1 items-center justify-center gap-2 rounded-md bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700"
        >
          <X className="h-4 w-4" /> Reject
        </button>
      </div>
    </aside>
  );
}

function TraceMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-white p-3">
      <div className="text-xs uppercase text-slate-500">{label}</div>
      <div className="mt-1 font-semibold text-slate-800">{value}</div>
    </div>
  );
}
