"use client";

import type { Project, Sheet } from "@/types";

type WorkspaceStep = "upload" | "select" | "running" | "results";

const STEPS: { key: WorkspaceStep; label: string; num: number }[] = [
  { key: "upload", label: "Upload Plan Set", num: 1 },
  { key: "select", label: "Select Sheets", num: 2 },
  { key: "results", label: "Floor Plan View", num: 3 },
];

interface Props {
  project: Project;
  step: WorkspaceStep;
  sheets: Sheet[];
  selectedIds: string[];
  onRunEngine: () => void;
}

export function WorkspaceSidebar({ project, step, sheets, selectedIds, onRunEngine }: Props) {
  const selectedSheets = selectedIds
    .map((id) => sheets.find((s) => s.id === id))
    .filter((s): s is Sheet => s !== undefined);

  const stepIndex = STEPS.findIndex((s) => s.key === step);

  return (
    <aside className="w-64 flex-shrink-0 bg-gray-900 border-r border-gray-800 flex flex-col overflow-y-auto">
      {/* Project info */}
      <div className="p-4 border-b border-gray-800">
        <p className="text-xs text-gray-500 uppercase tracking-widest mb-1">Project</p>
        <h2 className="text-sm font-semibold text-gray-100 leading-snug">{project.name}</h2>
        {project.address && (
          <p className="text-xs text-gray-500 mt-0.5 leading-snug">{project.address}</p>
        )}
      </div>

      {/* Steps */}
      <div className="p-4 border-b border-gray-800">
        <p className="text-xs text-gray-500 uppercase tracking-widest mb-3">Workflow</p>
        <ol className="flex flex-col gap-2">
          {STEPS.map((s, i) => {
            const isActive = s.key === step || (step === "running" && s.key === "results" && i === 2);
            const isDone = i < stepIndex || (step === "running" && i < 2);
            return (
              <li key={s.key} className="flex items-center gap-2.5">
                <span
                  className={[
                    "flex-shrink-0 w-5 h-5 rounded-full text-xs flex items-center justify-center font-medium",
                    isDone
                      ? "bg-orange-500 text-white"
                      : isActive
                      ? "bg-orange-500/20 text-orange-400 ring-1 ring-orange-500"
                      : "bg-gray-800 text-gray-500",
                  ].join(" ")}
                >
                  {isDone ? "✓" : s.num}
                </span>
                <span
                  className={[
                    "text-sm",
                    isActive ? "text-gray-100 font-medium" : isDone ? "text-gray-400" : "text-gray-500",
                  ].join(" ")}
                >
                  {s.label}
                </span>
              </li>
            );
          })}
        </ol>
      </div>

      {/* Selected floors */}
      <div className="flex-1 p-4">
        <p className="text-xs text-gray-500 uppercase tracking-widest mb-3">
          Selected floors{" "}
          {selectedSheets.length > 0 && (
            <span className="text-orange-500 ml-1">{selectedSheets.length}</span>
          )}
        </p>
        {selectedSheets.length === 0 ? (
          <p className="text-xs text-gray-600 italic">No sheets selected yet.</p>
        ) : (
          <ol className="flex flex-col gap-1.5">
            {selectedSheets.map((sheet, i) => (
              <li key={sheet.id} className="flex items-start gap-2">
                <span className="flex-shrink-0 mt-0.5 w-4 h-4 rounded bg-orange-500 text-white text-[10px] flex items-center justify-center font-bold">
                  {i + 1}
                </span>
                <span className="text-xs text-gray-300 leading-snug truncate" title={sheet.label}>
                  {sheet.label}
                </span>
              </li>
            ))}
          </ol>
        )}
      </div>

      {/* Run Engine */}
      <div className="p-4 border-t border-gray-800">
        <button
          onClick={onRunEngine}
          disabled={selectedSheets.length === 0 || step === "running" || step === "results"}
          className="w-full py-2 rounded-md text-sm font-semibold bg-orange-500 text-white hover:bg-orange-600 disabled:opacity-40 disabled:cursor-not-allowed transition"
        >
          {step === "running" ? "Running…" : "Run Engine"}
        </button>
        {selectedSheets.length === 0 && step === "select" && (
          <p className="text-xs text-gray-600 text-center mt-2">Select floor plans to continue</p>
        )}
      </div>
    </aside>
  );
}
