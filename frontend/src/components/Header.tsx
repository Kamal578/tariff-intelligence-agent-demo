import { Activity, Bot, Server } from "lucide-react";

interface HeaderProps {
  backendStatus: "checking" | "online" | "offline";
  mode?: string;
  apiBaseUrl: string;
}

export function Header({ backendStatus, mode, apiBaseUrl }: HeaderProps) {
  const statusClass =
    backendStatus === "online"
      ? "bg-emerald-100 text-emerald-700"
      : backendStatus === "offline"
        ? "bg-red-100 text-red-700"
        : "bg-slate-100 text-slate-600";

  return (
    <header className="border-b border-line bg-white">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-5 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-ink text-white">
              <Bot className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold tracking-normal">Tariff Intelligence Agent</h1>
              <p className="text-sm text-slate-600">
                Synthetic enterprise workflow demo: Excel {"->"} Evidence {"->"} AI Proposal {"->"} Human Approval {"->"} Updated Report
              </p>
            </div>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className={`inline-flex items-center gap-2 rounded-md px-3 py-2 ${statusClass}`}>
            <Server className="h-4 w-4" />
            Backend {backendStatus}
          </span>
          <span className="inline-flex items-center gap-2 rounded-md bg-blue-50 px-3 py-2 text-blue-700">
            <Activity className="h-4 w-4" />
            Mode {mode ?? "not run"}
          </span>
          <span className="rounded-md bg-slate-100 px-3 py-2 text-slate-600">{apiBaseUrl}</span>
        </div>
      </div>
    </header>
  );
}
