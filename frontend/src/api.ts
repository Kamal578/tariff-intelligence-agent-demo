import type { AuditEntry, Evidence, Metrics, ProcessSummary, ProposedUpdate, TariffRecord } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(options?.headers ?? {}) },
    ...options,
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  baseUrl: API_BASE_URL,
  health: () => request<{ status: string }>("/health"),
  resetDemo: () => request<{ reset: boolean; removed: string[] }>("/reset-demo", { method: "POST" }),
  runAnalysis: () => request<ProcessSummary>("/process", { method: "POST" }),
  getRecords: () => request<TariffRecord[]>("/records"),
  getProposals: () => request<ProposedUpdate[]>("/proposals"),
  getMetrics: () => request<Metrics>("/metrics"),
  reviewProposal: (proposal: ProposedUpdate, decision: "approved" | "rejected") =>
    request("/review", {
      method: "POST",
      body: JSON.stringify({
        proposal_id: proposal.proposal_id,
        pack_id: proposal.pack_id,
        field_name: proposal.field_name,
        decision,
        reviewer: "react_demo",
        reasoning: `${decision} in React dashboard`,
      }),
    }),
  applyApproved: () => request<{ applied_updates: number; output_excel: string }>("/apply-approved", { method: "POST" }),
  getAuditLog: () => request<AuditEntry[]>("/audit-log"),
  searchSources: (query: string) =>
    request<Evidence[]>(`/sources/search?q=${encodeURIComponent(query)}`),
};

export const downloadUrl = (path: string) => `${API_BASE_URL}${path}`;
