import { CheckCircle2 } from "lucide-react";

const steps = [
  "Data Input",
  "Issue Detection",
  "Evidence Retrieval",
  "AI Proposal",
  "Human Review",
  "Excel Update",
];

export function WorkflowStepper({ activeIndex }: { activeIndex: number }) {
  return (
    <section className="rounded-lg border border-line bg-white p-4 shadow-soft">
      <div className="grid gap-3 md:grid-cols-6">
        {steps.map((step, index) => {
          const active = index <= activeIndex;
          return (
            <div
              key={step}
              className={`flex min-h-16 items-center gap-3 rounded-md border px-3 py-2 ${
                active ? "border-blue-200 bg-blue-50 text-blue-800" : "border-slate-200 bg-slate-50 text-slate-500"
              }`}
            >
              <CheckCircle2 className={`h-5 w-5 ${active ? "text-blue-600" : "text-slate-300"}`} />
              <span className="text-sm font-medium">{step}</span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
