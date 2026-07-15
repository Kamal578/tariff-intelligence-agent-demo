export type RiskLevel = "low" | "medium" | "high";
export type ProposalStatus = "proposed" | "approved" | "rejected" | "needs_review";
export type SourceType = "confluence" | "wiki" | "email";

export interface TariffRecord {
  pack_id: string;
  pack_name: string;
  tariff_name?: string | null;
  price_azn?: number | null;
  validity_days?: number | null;
  data_gb?: number | null;
  minutes?: number | null;
  sms?: number | null;
  activation_code?: string | null;
  effective_date?: string | null;
  status?: string | null;
  last_updated?: string | null;
  source_note?: string | null;
}

export interface Evidence {
  source_id: string;
  source_type: SourceType;
  title_or_subject: string;
  author_or_owner?: string | null;
  timestamp: string;
  fake_url: string;
  excerpt: string;
  relevance_score: number;
  source_priority: "high" | "medium" | "low";
  document_status: "approved" | "deprecated" | "draft" | "n/a";
  matched_terms: string[];
}

export interface ProposedUpdate {
  proposal_id: string;
  pack_id: string;
  pack_name: string;
  field_name: string;
  old_value: unknown;
  proposed_value: unknown;
  issue_type: string;
  confidence_score: number;
  risk_level: RiskLevel;
  status: ProposalStatus;
  evidence_sources: Evidence[];
  reasoning_summary: string;
  source_conflict_detected: boolean;
  source_freshness_summary: string;
  decision_basis: string;
  created_at: string;
  requires_human_review: boolean;
}

export interface Metrics {
  records: number;
  issues: number;
  proposals: number;
  high_risk_proposals: number;
  approved_updates: number;
  rejected_updates: number;
  source_conflicts: number;
}

export interface ProcessSummary {
  records: number;
  issues: number;
  proposals: number;
  high_risk_proposals: number;
  source_conflicts: number;
  mode: string;
  generated_at: string;
}
