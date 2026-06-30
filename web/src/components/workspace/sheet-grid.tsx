"use client";

import { useState } from "react";
import type { Sheet, SheetType } from "@/types";

const FILTERS: { label: string; value: SheetType | "all" }[] = [
  { label: "All", value: "all" },
  { label: "Floor Plans", value: "floor_plan" },
  { label: "Elevations", value: "elevation" },
  { label: "Sections", value: "section" },
  { label: "Details", value: "detail" },
];

const TYPE_LABELS: Record<SheetType, string> = {
  floor_plan: "Floor Plan",
  elevation: "Elevation",
  section: "Section",
  detail: "Detail",
  other: "Other",
};

const TYPE_COLORS: Record<SheetType, string> = {
  floor_plan: "bg-orange-500/20 text-orange-400",
  elevation: "bg-blue-500/20 text-blue-400",
  section:   "bg-purple-500/20 text-purple-400",
  detail:    "bg-green-500/20 text-green-400",
  other:     "bg-gray-700 text-gray-400",
};

interface Props {
  fileName: string;
  sheets: Sheet[];
  selectedIds: string[];
  onToggle: (id: string) => void;
  onSelectAll: (ids: string[]) => void;
}

export function SheetGrid({ fileName, sheets, selectedIds, onToggle, onSelectAll }: Props) {
  const [activeFilter, setActiveFilter] = useState<SheetType | "all">("all");

  const filtered =
    activeFilter === "all" ? sheets : sheets.filter((s) => s.type === activeFilter);

  const countByType = (type: SheetType | "all") =>
    type === "all" ? sheets.length : sheets.filter((s) => s.type === type).length;

  function handleAutoSelectFloors() {
    const floorIds = sheets.filter((s) => s.type === "floor_plan").map((s) => s.id);
    onSelectAll(floorIds);
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Top bar */}
      <div className="px-6 pt-5 pb-0 flex-shrink-0">
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-widest mb-0.5">Plan Set</p>
            <h3 className="text-sm font-semibold text-gray-200 truncate max-w-sm">{fileName}</h3>
          </div>
          <button
            onClick={handleAutoSelectFloors}
            className="text-xs px-3 py-1.5 rounded bg-orange-500/10 text-orange-400 hover:bg-orange-500/20 border border-orange-500/30 transition font-medium"
          >
            Auto-select floor plans
          </button>
        </div>

        {/* Filter tabs */}
        <div className="flex gap-1 border-b border-gray-800">
          {FILTERS.map((f) => {
            const count = countByType(f.value);
            const isActive = activeFilter === f.value;
            return (
              <button
                key={f.value}
                onClick={() => setActiveFilter(f.value)}
                className={[
                  "px-3 py-2 text-xs font-medium rounded-t transition flex items-center gap-1.5",
                  isActive
                    ? "bg-gray-800 text-gray-100 border border-b-0 border-gray-700"
                    : "text-gray-500 hover:text-gray-300",
                ].join(" ")}
              >
                {f.label}
                <span className={["text-[10px] rounded px-1 py-0.5", isActive ? "bg-gray-700 text-gray-300" : "text-gray-600"].join(" ")}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Grid */}
      <div className="flex-1 overflow-y-auto p-6">
        {filtered.length === 0 ? (
          <p className="text-sm text-gray-600 italic">No sheets in this category.</p>
        ) : (
          <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
            {filtered.map((sheet) => {
              const selIdx = selectedIds.indexOf(sheet.id);
              const isSelected = selIdx !== -1;
              return (
                <button
                  key={sheet.id}
                  onClick={() => onToggle(sheet.id)}
                  className={[
                    "relative flex flex-col rounded-lg overflow-hidden border-2 transition text-left",
                    isSelected
                      ? "border-orange-500 shadow-[0_0_0_1px_rgba(249,115,22,0.4)]"
                      : "border-gray-800 hover:border-gray-600",
                  ].join(" ")}
                >
                  {/* Thumbnail */}
                  <div className="aspect-[3/4] bg-gray-800 flex items-center justify-center relative">
                    {sheet.thumbnail_url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={sheet.thumbnail_url} alt={sheet.label} className="w-full h-full object-cover" />
                    ) : (
                      <div className="flex flex-col items-center gap-1 px-2">
                        <svg className="w-7 h-7 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                          <rect x="4" y="2" width="16" height="20" rx="1.5" strokeLinejoin="round" />
                          <path d="M4 7h16M8 11h8M8 15h5" strokeLinecap="round" />
                        </svg>
                        <span className="text-[10px] text-gray-600 text-center leading-tight">
                          p.{sheet.page_number}
                        </span>
                      </div>
                    )}
                    {/* Selection badge */}
                    {isSelected && (
                      <span className="absolute top-1.5 right-1.5 w-5 h-5 rounded-full bg-orange-500 text-white text-[10px] font-bold flex items-center justify-center shadow">
                        {selIdx + 1}
                      </span>
                    )}
                  </div>
                  {/* Label + type badge */}
                  <div className="p-2 bg-gray-900 flex-1">
                    <p className="text-[11px] text-gray-300 leading-tight line-clamp-2 mb-1.5" title={sheet.label}>
                      {sheet.label}
                    </p>
                    <span className={["text-[9px] px-1.5 py-0.5 rounded font-medium uppercase tracking-wide", TYPE_COLORS[sheet.type]].join(" ")}>
                      {TYPE_LABELS[sheet.type]}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
