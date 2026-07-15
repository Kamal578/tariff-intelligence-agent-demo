import { Mail, NotebookText, PanelTop, Search } from "lucide-react";
import { useMemo, useState } from "react";
import type { SourceDocument, SourceType } from "../types";
import { SourceDocumentDetail } from "./SourceDocumentDetail";

const sourceTypeOptions = ["all", "confluence", "wiki", "email"] as const;
const statusOptions = ["all", "approved", "deprecated", "draft", "n/a"] as const;
const chips = [
  "YouthMax 10GB",
  "Business Pro Plus",
  "Student Social 3GB",
  "Night Owl activation code",
  "Family Share 20GB",
  "Revenue assurance policy",
];

const sourceClass: Record<SourceType, string> = {
  confluence: "bg-blue-50 text-blue-700",
  wiki: "bg-violet-50 text-violet-700",
  email: "bg-emerald-50 text-emerald-700",
};

const sourceIcon = {
  confluence: PanelTop,
  wiki: NotebookText,
  email: Mail,
};

export function SourcesOfTruth({
  sources,
  selectedSourceId,
  onSelectSource,
}: {
  sources: SourceDocument[];
  selectedSourceId?: string;
  onSelectSource: (sourceId: string) => void;
}) {
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<(typeof sourceTypeOptions)[number]>("all");
  const [statusFilter, setStatusFilter] = useState<(typeof statusOptions)[number]>("all");

  const selected = sources.find((source) => source.source_id === selectedSourceId) ?? sources[0];
  const filtered = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return sources.filter((source) => {
      const matchesType = typeFilter === "all" || source.source_type === typeFilter;
      const matchesStatus = statusFilter === "all" || source.document_status === statusFilter;
      const haystack = `${source.title_or_subject} ${source.author_or_owner ?? ""} ${source.body} ${source.related_pack_names.join(" ")}`.toLowerCase();
      const matchesQuery = !normalizedQuery || haystack.includes(normalizedQuery);
      return matchesType && matchesStatus && matchesQuery;
    });
  }, [sources, query, typeFilter, statusFilter]);

  const counts = useMemo(() => sourceCounts(sources), [sources]);

  return (
    <div className="space-y-5">
      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <OverviewCard label="Confluence docs" value={counts.confluence} tone="blue" />
        <OverviewCard label="Wiki pages" value={counts.wiki} tone="violet" />
        <OverviewCard label="Email announcements" value={counts.email} tone="emerald" />
        <OverviewCard label="Approved sources" value={counts.approved} tone="slate" />
        <OverviewCard label="Deprecated / draft" value={counts.conflicting} tone="amber" />
      </section>

      <section className="rounded-lg border border-line bg-white p-4 shadow-soft">
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_180px_180px]">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="w-full rounded-md border border-line py-2 pl-9 pr-3 text-sm outline-none focus:border-blue-400"
              placeholder="Search source documents..."
            />
          </div>
          <select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value as typeof typeFilter)} className="rounded-md border border-line px-3 py-2 text-sm">
            {sourceTypeOptions.map((option) => <option key={option} value={option}>{option === "all" ? "All source types" : option}</option>)}
          </select>
          <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as typeof statusFilter)} className="rounded-md border border-line px-3 py-2 text-sm">
            {statusOptions.map((option) => <option key={option} value={option}>{option === "all" ? "All statuses" : option}</option>)}
          </select>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {chips.map((chip) => (
            <button
              key={chip}
              onClick={() => setQuery(chip)}
              className="rounded-md border border-line bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100"
            >
              {chip}
            </button>
          ))}
        </div>
      </section>

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_520px]">
        <section className="rounded-lg border border-line bg-white p-4 shadow-soft">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Source documents</h2>
            <span className="text-sm text-slate-500">{filtered.length} shown</span>
          </div>
          <div className="max-h-[44rem] space-y-3 overflow-auto">
            {filtered.map((source) => (
              <SourceRow
                key={source.source_id}
                source={source}
                selected={selected?.source_id === source.source_id}
                onClick={() => onSelectSource(source.source_id)}
              />
            ))}
            {filtered.length === 0 && (
              <div className="rounded-md bg-slate-50 p-6 text-sm text-slate-500">No mock source documents match the current filters.</div>
            )}
          </div>
        </section>
        <SourceDocumentDetail document={selected} />
      </div>
    </div>
  );
}

function SourceRow({ source, selected, onClick }: { source: SourceDocument; selected: boolean; onClick: () => void }) {
  const Icon = sourceIcon[source.source_type];
  return (
    <button
      onClick={onClick}
      className={`w-full rounded-lg border p-4 text-left hover:bg-blue-50 ${selected ? "border-blue-300 bg-blue-50" : "border-slate-200 bg-white"}`}
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-semibold ${sourceClass[source.source_type]}`}>
          <Icon className="h-3.5 w-3.5" /> {source.source_type}
        </span>
        <span className="rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-600">{source.document_status}</span>
        <span className="rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-600">{source.source_priority}</span>
      </div>
      <h3 className="mt-2 font-semibold">{source.title_or_subject}</h3>
      <p className="mt-1 text-xs text-slate-500">{source.author_or_owner ?? "unknown"} · {new Date(source.timestamp).toLocaleDateString()}</p>
      <p className="mt-2 line-clamp-2 text-sm text-slate-600">{source.excerpt}</p>
      {source.related_pack_names.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {source.related_pack_names.slice(0, 5).map((pack) => (
            <span key={pack} className="rounded bg-slate-100 px-2 py-1 text-xs text-slate-600">{pack}</span>
          ))}
        </div>
      )}
    </button>
  );
}

function OverviewCard({ label, value, tone }: { label: string; value: number; tone: "blue" | "violet" | "emerald" | "slate" | "amber" }) {
  const classes = {
    blue: "bg-blue-50 text-blue-700",
    violet: "bg-violet-50 text-violet-700",
    emerald: "bg-emerald-50 text-emerald-700",
    slate: "bg-slate-100 text-slate-700",
    amber: "bg-amber-50 text-amber-700",
  };
  return (
    <div className="rounded-lg border border-line bg-white p-4 shadow-soft">
      <div className="text-xs font-medium uppercase text-slate-500">{label}</div>
      <div className={`mt-3 inline-flex min-w-12 justify-center rounded-md px-3 py-1 text-2xl font-semibold ${classes[tone]}`}>{value}</div>
    </div>
  );
}

function sourceCounts(sources: SourceDocument[]) {
  return {
    confluence: sources.filter((source) => source.source_type === "confluence").length,
    wiki: sources.filter((source) => source.source_type === "wiki").length,
    email: sources.filter((source) => source.source_type === "email").length,
    approved: sources.filter((source) => source.document_status === "approved").length,
    conflicting: sources.filter((source) => ["deprecated", "draft"].includes(source.document_status)).length,
  };
}
