import { Mail, NotebookText, PanelTop } from "lucide-react";
import type { SourceDocument, SourceType } from "../types";

const iconByType = {
  confluence: PanelTop,
  wiki: NotebookText,
  email: Mail,
};

const styleByType: Record<SourceType, string> = {
  confluence: "border-blue-200 bg-blue-50 text-blue-800",
  wiki: "border-violet-200 bg-violet-50 text-violet-800",
  email: "border-emerald-200 bg-emerald-50 text-emerald-800",
};

export function SourceDocumentDetail({ document }: { document?: SourceDocument }) {
  if (!document) {
    return (
      <aside className="rounded-lg border border-line bg-white p-5 shadow-soft">
        <h2 className="text-lg font-semibold">Source document</h2>
        <p className="mt-3 text-sm text-slate-500">Select a source to inspect the full local mock document.</p>
      </aside>
    );
  }

  const Icon = iconByType[document.source_type];

  return (
    <aside className="rounded-lg border border-line bg-white p-5 shadow-soft">
      <div className={`mb-4 inline-flex items-center gap-2 rounded-md border px-3 py-1.5 text-sm font-semibold ${styleByType[document.source_type]}`}>
        <Icon className="h-4 w-4" />
        {label(document.source_type)}
      </div>

      {document.source_type === "email" ? (
        <EmailHeader document={document} />
      ) : (
        <PageHeader document={document} />
      )}

      {document.related_pack_names.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {document.related_pack_names.map((pack) => (
            <span key={pack} className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
              {pack}
            </span>
          ))}
        </div>
      )}

      <DocumentBody document={document} />
    </aside>
  );
}

function PageHeader({ document }: { document: SourceDocument }) {
  return (
    <div>
      <h2 className="text-2xl font-semibold tracking-normal">{document.title_or_subject}</h2>
      <div className="mt-3 grid gap-2 text-sm text-slate-600 md:grid-cols-2">
        <div>Owner team: <span className="font-medium text-slate-800">{document.author_or_owner ?? "-"}</span></div>
        <div>Last updated: <span className="font-medium text-slate-800">{formatDate(document.timestamp)}</span></div>
        <div>Status: <Badge value={document.document_status} /></div>
        <div>Priority: <Badge value={document.source_priority} /></div>
      </div>
      {(document.tags?.length ?? 0) > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {document.tags.map((tag) => (
            <span key={tag} className="rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-600">{tag}</span>
          ))}
        </div>
      )}
    </div>
  );
}

function EmailHeader({ document }: { document: SourceDocument }) {
  return (
    <div>
      <h2 className="text-2xl font-semibold tracking-normal">{document.title_or_subject}</h2>
      <div className="mt-4 rounded-md border border-emerald-100 bg-emerald-50 p-4 text-sm">
        <div className="grid gap-2">
          <div><span className="text-slate-500">From:</span> <span className="font-medium">{document.from ?? document.author_or_owner}</span></div>
          <div><span className="text-slate-500">To:</span> <span className="font-medium">{(document.to ?? []).join(", ") || "-"}</span></div>
          {(document.cc?.length ?? 0) > 0 && <div><span className="text-slate-500">CC:</span> <span className="font-medium">{document.cc?.join(", ")}</span></div>}
          <div><span className="text-slate-500">Sent:</span> <span className="font-medium">{formatDate(document.timestamp)}</span></div>
        </div>
      </div>
      {(document.labels?.length ?? 0) > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {document.labels.map((labelValue) => (
            <span key={labelValue} className="rounded-md bg-emerald-100 px-2 py-1 text-xs text-emerald-700">{labelValue}</span>
          ))}
        </div>
      )}
    </div>
  );
}

function DocumentBody({ document }: { document: SourceDocument }) {
  const paragraphs = document.body.split(/\n{2,}/).filter(Boolean);
  return (
    <div className={`mt-6 rounded-lg border p-5 ${document.source_type === "email" ? "border-emerald-100 bg-white" : "border-slate-200 bg-slate-50"}`}>
      {paragraphs.map((paragraph, index) => (
        <p key={`${document.source_id}-${index}`} className="mb-4 last:mb-0 text-sm leading-6 text-slate-700">
          {paragraph}
        </p>
      ))}
    </div>
  );
}

function Badge({ value }: { value: string }) {
  return <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">{value}</span>;
}

function formatDate(value: string) {
  return new Date(value).toLocaleString();
}

function label(type: SourceType) {
  return type === "confluence" ? "Confluence" : type === "wiki" ? "Wiki" : "Email";
}
