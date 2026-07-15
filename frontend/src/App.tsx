import { useEffect, useMemo, useState } from "react";
import { Play, RefreshCw, RotateCcw } from "lucide-react";
import { api } from "./api";
import { Header } from "./components/Header";
import { MetricsCards } from "./components/MetricsCards";
import { ProposalDetailPanel } from "./components/ProposalDetailPanel";
import { ProposalsBoard } from "./components/ProposalsBoard";
import { RecordsTable } from "./components/RecordsTable";
import { WorkflowStepper } from "./components/WorkflowStepper";
import type { Metrics, ProcessSummary, ProposedUpdate, TariffRecord } from "./types";

const emptyMetrics: Metrics = {
  records: 0,
  issues: 0,
  proposals: 0,
  high_risk_proposals: 0,
  approved_updates: 0,
  rejected_updates: 0,
  source_conflicts: 0,
};

export default function App() {
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");
  const [summary, setSummary] = useState<ProcessSummary | undefined>();
  const [metrics, setMetrics] = useState<Metrics>(emptyMetrics);
  const [records, setRecords] = useState<TariffRecord[]>([]);
  const [proposals, setProposals] = useState<ProposedUpdate[]>([]);
  const [selectedId, setSelectedId] = useState<string | undefined>();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | undefined>();

  const selectedProposal = useMemo(
    () => proposals.find((proposal) => proposal.proposal_id === selectedId) ?? proposals[0],
    [proposals, selectedId],
  );

  async function refresh() {
    const [recordsData, proposalsData, metricsData] = await Promise.all([
      api.getRecords(),
      api.getProposals(),
      api.getMetrics(),
    ]);
    setRecords(recordsData);
    setProposals(proposalsData);
    setMetrics(metricsData);
  }

  useEffect(() => {
    api
      .health()
      .then(() => setBackendStatus("online"))
      .then(refresh)
      .catch(() => setBackendStatus("offline"));
  }, []);

  async function runAnalysis() {
    setBusy(true);
    setMessage(undefined);
    try {
      const result = await api.runAnalysis();
      setSummary(result);
      setMessage(`Generated ${result.proposals} proposals from ${result.issues} issues.`);
      await refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Run analysis failed.");
    } finally {
      setBusy(false);
    }
  }

  async function resetDemo() {
    setBusy(true);
    try {
      await api.resetDemo();
      setSummary(undefined);
      setSelectedId(undefined);
      setRecords([]);
      setProposals([]);
      setMetrics(emptyMetrics);
      setMessage("Demo state reset.");
    } finally {
      setBusy(false);
    }
  }

  async function review(proposal: ProposedUpdate, decision: "approved" | "rejected") {
    setBusy(true);
    try {
      await api.reviewProposal(proposal, decision);
      await refresh();
      setMessage(`${proposal.proposal_id} ${decision}.`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <Header backendStatus={backendStatus} mode={summary?.mode} apiBaseUrl={api.baseUrl} />
      <main className="mx-auto max-w-7xl space-y-5 px-6 py-6">
        <div className="flex flex-wrap gap-3">
          <button
            disabled={busy || backendStatus !== "online"}
            onClick={runAnalysis}
            className="inline-flex items-center gap-2 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
          >
            <Play className="h-4 w-4" /> Run Analysis
          </button>
          <button
            disabled={busy || backendStatus !== "online"}
            onClick={refresh}
            className="inline-flex items-center gap-2 rounded-md border border-line bg-white px-4 py-2 text-sm font-semibold hover:bg-slate-50"
          >
            <RefreshCw className="h-4 w-4" /> Refresh
          </button>
          <button
            disabled={busy || backendStatus !== "online"}
            onClick={resetDemo}
            className="inline-flex items-center gap-2 rounded-md border border-line bg-white px-4 py-2 text-sm font-semibold hover:bg-slate-50"
          >
            <RotateCcw className="h-4 w-4" /> Reset Demo
          </button>
          {message && <span className="rounded-md bg-blue-50 px-3 py-2 text-sm text-blue-700">{message}</span>}
        </div>
        <WorkflowStepper activeIndex={proposals.length ? 4 : records.length ? 2 : 0} />
        <MetricsCards metrics={metrics} />
        <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_380px]">
          <div className="space-y-5">
            <RecordsTable records={records} proposals={proposals} />
            <ProposalsBoard proposals={proposals} selectedId={selectedProposal?.proposal_id} onSelect={(proposal) => setSelectedId(proposal.proposal_id)} />
          </div>
          <ProposalDetailPanel
            proposal={selectedProposal}
            busy={busy}
            onApprove={(proposal) => review(proposal, "approved")}
            onReject={(proposal) => review(proposal, "rejected")}
          />
        </div>
      </main>
    </div>
  );
}
