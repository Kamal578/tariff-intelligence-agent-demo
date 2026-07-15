import { AlertTriangle, Check, Database, FileSpreadsheet, ShieldAlert, X } from "lucide-react";
import type { Metrics } from "../types";

const metricConfig = [
  ["records", "Total records", FileSpreadsheet],
  ["issues", "Detected issues", AlertTriangle],
  ["proposals", "Generated proposals", Database],
  ["high_risk_proposals", "High risk", ShieldAlert],
  ["approved_updates", "Approved", Check],
  ["rejected_updates", "Rejected", X],
  ["source_conflicts", "Source conflicts", AlertTriangle],
] as const;

export function MetricsCards({ metrics }: { metrics: Metrics }) {
  return (
    <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-7">
      {metricConfig.map(([key, label, Icon], index) => (
        <div
          key={key}
          className="motion-card rounded-lg border border-line bg-white p-4 shadow-soft"
          style={{ animationDelay: `${index * 45}ms` }}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase text-slate-500">{label}</span>
            <Icon className="h-4 w-4 text-slate-400" />
          </div>
          <div className="mt-3 text-2xl font-semibold">{metrics[key]}</div>
        </div>
      ))}
    </section>
  );
}
