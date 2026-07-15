import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Archive, BookOpen, ClipboardList, Play, RefreshCw, RotateCcw } from "lucide-react";
import { api } from "./api";
import { Header } from "./components/Header";
import { AnalysisOverlay } from "./components/AnalysisOverlay";
import { AuditLog } from "./components/AuditLog";
import { DownloadsPanel } from "./components/DownloadsPanel";
import { MetricsCards } from "./components/MetricsCards";
import { ProposalDetailPanel } from "./components/ProposalDetailPanel";
import { ProposalsBoard } from "./components/ProposalsBoard";
import { RecordsTable } from "./components/RecordsTable";
import { SourceSearch } from "./components/SourceSearch";
import { SourcesOfTruth } from "./components/SourcesOfTruth";
import { WorkflowStepper } from "./components/WorkflowStepper";
import type { AuditEntry, Metrics, ProcessSummary, ProposedUpdate, SourceDocument, TariffRecord } from "./types";

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
  const [activeView, setActiveView] = useState<"review" | "sources" | "audit">("review");
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");
  const [summary, setSummary] = useState<ProcessSummary | undefined>();
  const [metrics, setMetrics] = useState<Metrics>(emptyMetrics);
  const [records, setRecords] = useState<TariffRecord[]>([]);
  const [proposals, setProposals] = useState<ProposedUpdate[]>([]);
  const [auditEntries, setAuditEntries] = useState<AuditEntry[]>([]);
  const [sources, setSources] = useState<SourceDocument[]>([]);
  const [selectedSourceId, setSelectedSourceId] = useState<string | undefined>();
  const [selectedId, setSelectedId] = useState<string | undefined>();
  const [busy, setBusy] = useState(false);
  const [analysisRunning, setAnalysisRunning] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [message, setMessage] = useState<string | undefined>();

  const selectedProposal = useMemo(
    () => proposals.find((proposal) => proposal.proposal_id === selectedId) ?? proposals[0],
    [proposals, selectedId],
  );

  async function refresh() {
    const [recordsData, proposalsData, metricsData, auditData, sourcesData] = await Promise.all([
      api.getRecords(),
      api.getProposals(),
      api.getMetrics(),
      api.getAuditLog(),
      api.getSources(),
    ]);
    setRecords(recordsData);
    setProposals(proposalsData);
    setMetrics(metricsData);
    setAuditEntries(auditData);
    setSources(sourcesData);
    setSelectedSourceId((current) => current ?? sourcesData[0]?.source_id);
  }

  useEffect(() => {
    api
      .health()
      .then(() => setBackendStatus("online"))
      .then(refresh)
      .catch(() => setBackendStatus("offline"));
  }, []);

  useEffect(() => {
    if (!analysisRunning) return undefined;

    setAnalysisProgress((current) => Math.max(current, 8));
    const timer = window.setInterval(() => {
      setAnalysisProgress((current) => {
        if (current >= 94) return current;
        const remaining = 94 - current;
        return Math.min(94, current + Math.max(2, Math.round(remaining * 0.18)));
      });
    }, 420);

    return () => window.clearInterval(timer);
  }, [analysisRunning]);

  async function runAnalysis() {
    setBusy(true);
    setAnalysisRunning(true);
    setAnalysisProgress(4);
    setMessage(undefined);
    try {
      const result = await api.runAnalysis();
      setAnalysisProgress(100);
      setSummary(result);
      setMessage(`Generated ${result.proposals} proposals from ${result.issues} issues.`);
      await new Promise((resolve) => window.setTimeout(resolve, 300));
      await refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Run analysis failed.");
    } finally {
      setBusy(false);
      setAnalysisRunning(false);
      window.setTimeout(() => setAnalysisProgress(0), 400);
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
      setAuditEntries([]);
      setMetrics(emptyMetrics);
      setMessage("Demo state reset.");
    } finally {
      setBusy(false);
    }
  }

  function openSource(sourceId: string) {
    setSelectedSourceId(sourceId);
    setActiveView("sources");
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

  async function applyApproved() {
    setBusy(true);
    try {
      const result = await api.applyApproved();
      await refresh();
      setMessage(`Applied ${result.applied_updates} approved updates.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Apply approved updates failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <Header backendStatus={backendStatus} mode={summary?.mode} apiBaseUrl={api.baseUrl} />
      <AnalysisOverlay visible={analysisRunning} progress={analysisProgress} />
      <main className="mx-auto max-w-7xl space-y-5 px-6 py-6">
        <div className="flex flex-wrap gap-3">
          <button
            disabled={busy || backendStatus !== "online"}
            onClick={runAnalysis}
            className={`inline-flex items-center gap-2 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 ${analysisRunning ? "analysis-button-glow" : ""}`}
          >
            <Play className={`h-4 w-4 ${analysisRunning ? "animate-pulse" : ""}`} /> {analysisRunning ? "Analyzing..." : "Run Analysis"}
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
        {analysisRunning && (
          <div className="rounded-lg border border-blue-100 bg-white p-3 shadow-soft">
            <div className="mb-2 flex items-center justify-between text-sm">
              <span className="font-semibold text-slate-700">Analysis progress</span>
              <span className="tabular-nums font-semibold text-blue-700">{Math.round(analysisProgress)}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-blue-50">
              <div className="analysis-determinate h-full rounded-full bg-blue-600" style={{ width: `${analysisProgress}%` }} />
            </div>
          </div>
        )}
        <WorkflowStepper activeIndex={analysisRunning ? 4 : proposals.length ? 4 : records.length ? 2 : 0} running={analysisRunning} />
        <MetricsCards metrics={metrics} />
        <nav className="flex flex-wrap gap-2 rounded-lg border border-line bg-white p-2 shadow-soft">
          <ViewButton active={activeView === "review"} onClick={() => setActiveView("review")} icon={<ClipboardList className="h-4 w-4" />} label="Review Queue" />
          <ViewButton active={activeView === "sources"} onClick={() => setActiveView("sources")} icon={<BookOpen className="h-4 w-4" />} label="Sources of Truth" />
          <ViewButton active={activeView === "audit"} onClick={() => setActiveView("audit")} icon={<Archive className="h-4 w-4" />} label="Audit & Downloads" />
        </nav>

        {activeView === "review" && (
          <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_380px]">
            <div className="space-y-5">
              <RecordsTable records={records} proposals={proposals} />
              <ProposalsBoard proposals={proposals} selectedId={selectedProposal?.proposal_id} onSelect={(proposal) => setSelectedId(proposal.proposal_id)} />
              <SourceSearch onOpenSource={openSource} />
            </div>
            <ProposalDetailPanel
              proposal={selectedProposal}
              busy={busy}
              onApprove={(proposal) => review(proposal, "approved")}
              onReject={(proposal) => review(proposal, "rejected")}
              onOpenSource={openSource}
            />
          </div>
        )}

        {activeView === "sources" && (
          <SourcesOfTruth
            sources={sources}
            selectedSourceId={selectedSourceId}
            onSelectSource={setSelectedSourceId}
          />
        )}

        {activeView === "audit" && (
          <div className="space-y-5">
            <DownloadsPanel busy={busy} onApply={applyApproved} />
            <AuditLog entries={auditEntries} />
          </div>
        )}
      </main>
    </div>
  );
}

function ViewButton({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: ReactNode;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center gap-2 rounded-md px-4 py-2 text-sm font-semibold ${
        active ? "bg-ink text-white" : "text-slate-600 hover:bg-slate-100"
      }`}
    >
      {icon}
      {label}
    </button>
  );
}
