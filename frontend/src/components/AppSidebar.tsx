import type { ReactNode } from "react";
import { Archive, BarChart3, BookOpen, ClipboardList, History, Settings } from "lucide-react";

export type AppView = "dashboard" | "runs" | "review" | "sources" | "audit" | "settings";

const items: Array<{ view: AppView; label: string; icon: ReactNode }> = [
  { view: "dashboard", label: "Dashboard", icon: <BarChart3 className="h-4 w-4" /> },
  { view: "runs", label: "Analysis Runs", icon: <History className="h-4 w-4" /> },
  { view: "review", label: "Review Queue", icon: <ClipboardList className="h-4 w-4" /> },
  { view: "sources", label: "Sources", icon: <BookOpen className="h-4 w-4" /> },
  { view: "audit", label: "Audit", icon: <Archive className="h-4 w-4" /> },
  { view: "settings", label: "Settings", icon: <Settings className="h-4 w-4" /> },
];

export function AppSidebar({ activeView, onChange }: { activeView: AppView; onChange: (view: AppView) => void }) {
  return (
    <aside className="border-b border-line bg-white lg:min-h-[calc(100vh-81px)] lg:w-64 lg:border-b-0 lg:border-r">
      <nav className="mx-auto flex max-w-7xl gap-2 overflow-x-auto px-6 py-3 lg:sticky lg:top-0 lg:block lg:space-y-1 lg:px-4">
        {items.map((item) => (
          <button
            key={item.view}
            type="button"
            onClick={() => onChange(item.view)}
            className={`nav-item-motion inline-flex min-w-fit items-center gap-2 rounded-md px-3 py-2 text-sm font-semibold lg:w-full ${
              activeView === item.view ? "nav-item-active bg-ink text-white" : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            {item.icon}
            {item.label}
          </button>
        ))}
      </nav>
    </aside>
  );
}
