import { Search } from "lucide-react";
import { useState } from "react";
import { api } from "../api";
import type { Evidence } from "../types";
import { EvidenceCard } from "./EvidenceCard";

const examples = [
  "YouthMax 10GB price",
  "Business Pro rename",
  "Student Social discontinued",
  "activation code Night Owl",
];

export function SourceSearch({ onOpenSource }: { onOpenSource?: (sourceId: string) => void }) {
  const [query, setQuery] = useState("YouthMax 10GB price");
  const [results, setResults] = useState<Evidence[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | undefined>();

  async function search(nextQuery = query) {
    if (!nextQuery.trim()) return;
    setQuery(nextQuery);
    setLoading(true);
    setError(undefined);
    try {
      setResults(await api.searchSources(nextQuery));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-lg border border-line bg-white p-4 shadow-soft">
      <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-lg font-semibold">Mock source search</h2>
          <p className="text-sm text-slate-500">Search local Confluence, wiki, and inbox JSON sources.</p>
        </div>
        <div className="flex min-w-0 flex-1 gap-2 md:max-w-xl">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") void search();
            }}
            className="min-w-0 flex-1 rounded-md border border-line px-3 py-2 text-sm outline-none focus:border-blue-400"
            placeholder="Search mock sources"
          />
          <button
            disabled={loading}
            onClick={() => void search()}
            className="inline-flex items-center gap-2 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
          >
            <Search className="h-4 w-4" /> Search
          </button>
        </div>
      </div>
      <div className="mb-4 flex flex-wrap gap-2">
        {examples.map((example) => (
          <button
            key={example}
            onClick={() => void search(example)}
            className="rounded-md border border-line bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100"
          >
            {example}
          </button>
        ))}
      </div>
      {error && <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>}
      {results.length === 0 && !loading ? (
        <div className="rounded-md bg-slate-50 p-5 text-sm text-slate-500">Run a source search to inspect mock evidence.</div>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {results.map((result) => (
            <EvidenceCard key={result.source_id} evidence={result} onOpenSource={onOpenSource} />
          ))}
        </div>
      )}
    </section>
  );
}
