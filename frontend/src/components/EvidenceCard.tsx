import { ExternalLink, Mail, NotebookText, PanelTop } from "lucide-react";
import type { Evidence } from "../types";

const sourceIcons = {
  confluence: PanelTop,
  wiki: NotebookText,
  email: Mail,
};

const sourceClasses = {
  confluence: "bg-blue-50 text-blue-700",
  wiki: "bg-violet-50 text-violet-700",
  email: "bg-emerald-50 text-emerald-700",
};

export function EvidenceCard({ evidence }: { evidence: Evidence }) {
  const Icon = sourceIcons[evidence.source_type];
  return (
    <article className="rounded-md border border-slate-200 bg-white p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-semibold ${sourceClasses[evidence.source_type]}`}>
              <Icon className="h-3.5 w-3.5" /> {evidence.source_type}
            </span>
            <span className="rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-600">
              {Math.round(evidence.relevance_score * 100)}% match
            </span>
            <span className="rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-600">
              {evidence.document_status}
            </span>
          </div>
          <h3 className="mt-2 font-semibold">{evidence.title_or_subject}</h3>
          <p className="text-xs text-slate-500">
            {evidence.author_or_owner ?? "unknown"} · {new Date(evidence.timestamp).toLocaleDateString()}
          </p>
        </div>
        <a href={evidence.fake_url} className="text-slate-400 hover:text-slate-700" title={evidence.fake_url}>
          <ExternalLink className="h-4 w-4" />
        </a>
      </div>
      <p className="mt-3 text-sm text-slate-600">{evidence.excerpt}</p>
      {evidence.matched_terms.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {evidence.matched_terms.slice(0, 8).map((term) => (
            <span key={term} className="rounded bg-slate-100 px-2 py-1 text-xs text-slate-600">
              {term}
            </span>
          ))}
        </div>
      )}
    </article>
  );
}
