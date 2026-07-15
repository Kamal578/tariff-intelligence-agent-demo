import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Bot, Play, RefreshCw, RotateCcw, Zap } from "lucide-react";
import { api } from "./api";
import { Header } from "./components/Header";
import { ActiveRunPanel } from "./components/ActiveRunPanel";
import { AnalysisOverlay } from "./components/AnalysisOverlay";
import { AppSidebar } from "./components/AppSidebar";
import type { AppView } from "./components/AppSidebar";
import { AuditLog } from "./components/AuditLog";
import { DownloadsPanel } from "./components/DownloadsPanel";
import { MetricsCards } from "./components/MetricsCards";
import { ProposalDetailPanel } from "./components/ProposalDetailPanel";
import { ProposalsBoard } from "./components/ProposalsBoard";
import { RecordsTable } from "./components/RecordsTable";
import { RunHistory } from "./components/RunHistory";
import { SettingsPanel } from "./components/SettingsPanel";
import { SourceSearch } from "./components/SourceSearch";
import { SourcesOfTruth } from "./components/SourcesOfTruth";
import { WorkflowStepper } from "./components/WorkflowStepper";
import type { AnalysisJob, AnalysisMode, AuditEntry, ConfigStatus, Metrics, ProcessSummary, ProposedUpdate, SourceDocument, TariffRecord } from "./types";

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
  const [activeView, setActiveView] = useState<AppView>("dashboard");
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");
  const [summary, setSummary] = useState<ProcessSummary | undefined>();
  const [config, setConfig] = useState<ConfigStatus | undefined>();
  const [metrics, setMetrics] = useState<Metrics>(emptyMetrics);
  const [records, setRecords] = useState<TariffRecord[]>([]);
  const [proposals, setProposals] = useState<ProposedUpdate[]>([]);
  const [auditEntries, setAuditEntries] = useState<AuditEntry[]>([]);
  const [sources, setSources] = useState<SourceDocument[]>([]);
  const [jobs, setJobs] = useState<AnalysisJob[]>([]);
  const [activeJobId, setActiveJobId] = useState<string | undefined>();
  const [selectedSourceId, setSelectedSourceId] = useState<string | undefined>();
  const [selectedId, setSelectedId] = useState<string | undefined>();
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>("preview");
  const [busy, setBusy] = useState(false);
  const [analysisRunning, setAnalysisRunning] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [message, setMessage] = useState<string | undefined>();

  const selectedProposal = useMemo(
    () => proposals.find((proposal) => proposal.proposal_id === selectedId) ?? proposals[0],
    [proposals, selectedId],
  );
  const activeJob = useMemo(
    () => jobs.find((job) => job.job_id === activeJobId),
    [activeJobId, jobs],
  );

  async function refresh() {
    const [recordsData, proposalsData, metricsData, auditData, sourcesData, jobsData, configData] = await Promise.all([
      api.getRecords(),
      api.getProposals(),
      api.getMetrics(),
      api.getAuditLog(),
      api.getSources(),
      api.getAnalysisJobs(),
      api.getConfigStatus(),
    ]);
    setRecords(recordsData);
    setProposals(proposalsData);
    setMetrics(metricsData);
    setAuditEntries(auditData);
    setSources(sourcesData);
    setJobs(jobsData);
    setConfig(configData);
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
    if (!activeJobId || !analysisRunning) return undefined;

    const poll = async () => {
      const job = await api.getAnalysisJob(activeJobId);
      setJobs((current) => [job, ...current.filter((item) => item.job_id !== job.job_id)]);
      setAnalysisProgress(job.progress);
      if (job.status === "completed") {
        setSummary(job.summary ?? undefined);
        setMessage(`Run ${job.job_id} completed in ${job.actual_mode ?? job.requested_mode} mode.`);
        setBusy(false);
        setAnalysisRunning(false);
        await refresh();
      }
      if (job.status === "failed") {
        setMessage(job.error ?? "Analysis job failed.");
        setBusy(false);
        setAnalysisRunning(false);
        await refresh();
      }
      if (job.status === "cancelled") {
        setMessage(`Run ${job.job_id} cancelled before additional proposal steps.`);
        setBusy(false);
        setAnalysisRunning(false);
        await refresh();
      }
    };

    void poll();
    const timer = window.setInterval(() => void poll(), 300);
    return () => window.clearInterval(timer);
  }, [activeJobId, analysisRunning]);

  async function runAnalysis() {
    setBusy(true);
    setAnalysisRunning(true);
    setAnalysisProgress(4);
    setMessage(undefined);
    try {
      const job = await api.startAnalysisJob(analysisMode);
      setActiveJobId(job.job_id);
      setJobs((current) => [job, ...current.filter((item) => item.job_id !== job.job_id)]);
      setActiveView("runs");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Run analysis failed.");
      setBusy(false);
      setAnalysisRunning(false);
    }
  }

  async function resetDemo() {
    setBusy(true);
    try {
      await api.resetDemo();
      setSummary(undefined);
      setActiveJobId(undefined);
      setSelectedId(undefined);
      setRecords([]);
      setProposals([]);
      setAuditEntries([]);
      setJobs([]);
      setMetrics(emptyMetrics);
      setMessage("Demo state reset.");
    } finally {
      setBusy(false);
    }
  }

  async function cancelRun(job: AnalysisJob) {
    try {
      const cancelled = await api.cancelAnalysisJob(job.job_id);
      setJobs((current) => [cancelled, ...current.filter((item) => item.job_id !== cancelled.job_id)]);
      setMessage(`Cancellation requested for ${job.job_id}.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Cancel request failed.");
    }
  }

  function openSource(sourceId: string) {
    setSelectedSourceId(sourceId);
    setActiveView("sources");
  }

  async function review(proposal: ProposedUpdate, decision: "approved" | "rejected", reasoning?: string) {
    setBusy(true);
    try {
      await api.reviewProposal(proposal, decision, reasoning);
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
      <AnalysisOverlay visible={analysisRunning} progress={analysisProgress} stage={activeJob?.stage} />
      <div className="lg:flex">
        <AppSidebar activeView={activeView} onChange={setActiveView} />
        <main className="mx-auto w-full max-w-7xl space-y-5 px-6 py-6">
          <div className="flex flex-wrap gap-3">
          <div className="inline-flex rounded-md border border-line bg-white p-1 shadow-soft">
            <ModeButton
              active={analysisMode === "preview"}
              disabled={busy}
              icon={<Zap className="h-4 w-4" />}
              label="Quick Preview"
              onClick={() => setAnalysisMode("preview")}
            />
            <ModeButton
              active={analysisMode === "gemini"}
              disabled={busy}
              icon={<Bot className="h-4 w-4" />}
              label="Gemini"
              onClick={() => setAnalysisMode("gemini")}
            />
          </div>
          <button
            disabled={busy || backendStatus !== "online"}
            onClick={runAnalysis}
            className={`inline-flex items-center gap-2 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 ${analysisRunning ? "analysis-button-glow" : ""}`}
          >
            <Play className={`h-4 w-4 ${analysisRunning ? "animate-pulse" : ""}`} />{" "}
            {analysisRunning ? `Analyzing with ${analysisMode === "preview" ? "Preview" : "Gemini"}...` : "Run Analysis"}
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
          {message && <span className="status-toast rounded-md bg-blue-50 px-3 py-2 text-sm text-blue-700">{message}</span>}
        </div>
        <ActiveRunPanel job={activeJob} onCancel={cancelRun} />
        {analysisRunning && (
          <div className="rounded-lg border border-blue-100 bg-white p-3 shadow-soft">
            <div className="mb-2 flex items-center justify-between text-sm">
              <span className="font-semibold text-slate-700">{jobs.find((job) => job.job_id === activeJobId)?.stage ?? "Analysis progress"}</span>
              <span className="tabular-nums font-semibold text-blue-700">{Math.round(analysisProgress)}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-blue-50">
              <div className="analysis-determinate h-full rounded-full bg-blue-600" style={{ width: `${analysisProgress}%` }} />
            </div>
          </div>
        )}
        <WorkflowStepper activeIndex={analysisRunning ? 4 : proposals.length ? 4 : records.length ? 2 : 0} running={analysisRunning} />

        <section key={activeView} className="page-transition">
          {activeView === "dashboard" && (
            <div className="space-y-5">
              <MetricsCards metrics={metrics} />
              <RunHistory jobs={jobs.slice(0, 5)} activeJobId={activeJobId} />
            </div>
          )}

          {activeView === "runs" && <RunHistory jobs={jobs} activeJobId={activeJobId} />}

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
                onApprove={(proposal, reasoning) => review(proposal, "approved", reasoning)}
                onReject={(proposal, reasoning) => review(proposal, "rejected", reasoning)}
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

          {activeView === "settings" && (
            <SettingsPanel config={config} analysisMode={analysisMode} onModeChange={setAnalysisMode} />
          )}
        </section>
        </main>
      </div>
    </div>
  );
}

function ModeButton({
  active,
  disabled,
  icon,
  label,
  onClick,
}: {
  active: boolean;
  disabled: boolean;
  icon: ReactNode;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={`inline-flex items-center gap-2 rounded px-3 py-1.5 text-sm font-semibold transition ${
        active ? "bg-ink text-white shadow-sm" : "text-slate-600 hover:bg-slate-100"
      }`}
    >
      {icon}
      {label}
    </button>
  );
}
