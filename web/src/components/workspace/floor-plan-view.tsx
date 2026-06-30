"use client";

import { useState, useRef } from "react";
import type { Sheet } from "@/types";

type ViewMode = "layout" | "heatmap" | "both";

interface Props {
  sheets: Sheet[];
  selectedIds: string[];
  onBack: () => void;
}

export function FloorPlanView({ sheets, selectedIds, onBack }: Props) {
  const selectedSheets = selectedIds
    .map((id) => sheets.find((s) => s.id === id))
    .filter((s): s is Sheet => s !== undefined);

  const [activeIndex, setActiveIndex] = useState(0);
  const [viewMode, setViewMode] = useState<ViewMode>("layout");
  const [zoom, setZoom] = useState(1);
  const canvasRef = useRef<HTMLDivElement>(null);

  const activeSheet = selectedSheets[activeIndex] ?? null;

  function handleZoomIn() { setZoom((z) => Math.min(z + 0.25, 3)); }
  function handleZoomOut() { setZoom((z) => Math.max(z - 0.25, 0.25)); }
  function handleFit() { setZoom(1); }

  const VIEW_MODES: { key: ViewMode; label: string }[] = [
    { key: "layout", label: "Layout" },
    { key: "heatmap", label: "Heatmap" },
    { key: "both", label: "Both" },
  ];

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Toolbar */}
      <div className="flex-shrink-0 px-5 py-3 border-b border-gray-800 flex items-center gap-4">
        {/* Back button */}
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-100 transition"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 16 16" stroke="currentColor" strokeWidth={2}>
            <path d="M10 12L6 8l4-4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          Plan Set
        </button>

        <span className="text-gray-700">|</span>

        {/* Breadcrumb */}
        {activeSheet && (
          <span className="text-xs text-gray-300 font-medium truncate max-w-xs">
            {activeSheet.label}
          </span>
        )}

        <div className="flex-1" />

        {/* View mode toggle */}
        <div className="flex rounded-md overflow-hidden border border-gray-700">
          {VIEW_MODES.map((m) => (
            <button
              key={m.key}
              onClick={() => setViewMode(m.key)}
              className={[
                "px-3 py-1.5 text-xs font-medium transition",
                viewMode === m.key
                  ? "bg-orange-500 text-white"
                  : "text-gray-400 hover:text-gray-200 bg-gray-900",
              ].join(" ")}
            >
              {m.label}
            </button>
          ))}
        </div>

        {/* Zoom controls */}
        <div className="flex items-center gap-1 rounded-md border border-gray-700 overflow-hidden">
          <button
            onClick={handleZoomOut}
            className="px-2.5 py-1.5 text-sm text-gray-400 hover:text-gray-100 hover:bg-gray-800 transition"
            title="Zoom out"
          >
            −
          </button>
          <span className="px-2 py-1.5 text-xs text-gray-400 border-x border-gray-700 min-w-[3rem] text-center">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={handleZoomIn}
            className="px-2.5 py-1.5 text-sm text-gray-400 hover:text-gray-100 hover:bg-gray-800 transition"
            title="Zoom in"
          >
            +
          </button>
          <button
            onClick={handleFit}
            className="px-2.5 py-1.5 text-xs text-gray-400 hover:text-gray-100 hover:bg-gray-800 transition border-l border-gray-700"
            title="Fit to view"
          >
            Fit
          </button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Sheet list */}
        <div className="w-44 flex-shrink-0 border-r border-gray-800 overflow-y-auto bg-gray-900/50">
          <p className="text-[10px] text-gray-600 uppercase tracking-widest px-3 pt-3 pb-2">Floors</p>
          {selectedSheets.map((sheet, i) => (
            <button
              key={sheet.id}
              onClick={() => setActiveIndex(i)}
              className={[
                "w-full text-left px-3 py-2.5 flex items-center gap-2 transition",
                activeIndex === i
                  ? "bg-gray-800 border-l-2 border-orange-500"
                  : "hover:bg-gray-800/50 border-l-2 border-transparent",
              ].join(" ")}
            >
              <span className="flex-shrink-0 w-4 h-4 rounded bg-orange-500 text-white text-[9px] font-bold flex items-center justify-center">
                {i + 1}
              </span>
              <span className="text-[11px] text-gray-300 leading-tight line-clamp-2">
                {sheet.label}
              </span>
            </button>
          ))}
        </div>

        {/* Canvas */}
        <div className="flex-1 overflow-auto flex items-center justify-center bg-gray-950 p-8">
          <div
            ref={canvasRef}
            className="relative"
            style={{ transform: `scale(${zoom})`, transformOrigin: "center center", transition: "transform 0.15s ease" }}
          >
            {activeSheet ? (
              <div className="relative rounded-lg overflow-hidden border border-gray-800 shadow-2xl">
                {/* Placeholder floor plan */}
                <div className="w-[600px] h-[800px] bg-gray-900 flex flex-col">
                  {/* Mock floor plan outline */}
                  <div className="flex-1 relative p-8">
                    {/* Outer walls */}
                    <div className="absolute inset-8 border-2 border-gray-500 rounded">
                      {/* Room dividers */}
                      <div className="absolute top-1/3 left-0 right-0 border-t border-gray-600" />
                      <div className="absolute top-2/3 left-0 right-0 border-t border-gray-600" />
                      <div className="absolute top-0 bottom-0 left-1/2 border-l border-gray-600" />
                      {/* Sheet label */}
                      <div className="absolute bottom-2 left-2 right-2 flex items-end justify-between">
                        <span className="text-[10px] text-gray-500 font-mono">{activeSheet.label}</span>
                      </div>
                    </div>

                    {/* Antenna overlay (Layout / Both) */}
                    {(viewMode === "layout" || viewMode === "both") && (
                      <>
                        {[
                          { x: 30, y: 25 },
                          { x: 65, y: 25 },
                          { x: 30, y: 60 },
                          { x: 65, y: 60 },
                          { x: 48, y: 42 },
                        ].map((pos, i) => (
                          <div
                            key={i}
                            className="absolute"
                            style={{ left: `${pos.x}%`, top: `${pos.y}%`, transform: "translate(-50%, -50%)" }}
                          >
                            {/* Coverage ring */}
                            <div className="w-20 h-20 rounded-full border border-orange-500/30 bg-orange-500/5 absolute"
                              style={{ transform: "translate(-50%, -50%)", left: "50%", top: "50%" }} />
                            {/* Antenna dot */}
                            <div className="w-3 h-3 rounded-full bg-orange-500 border-2 border-white shadow relative z-10" />
                          </div>
                        ))}
                      </>
                    )}

                    {/* Heatmap overlay (Heatmap / Both) */}
                    {(viewMode === "heatmap" || viewMode === "both") && (
                      <div className="absolute inset-8 pointer-events-none">
                        <div
                          className="w-full h-full rounded"
                          style={{
                            background:
                              "radial-gradient(ellipse at 30% 30%, rgba(34,197,94,0.25) 0%, transparent 50%), " +
                              "radial-gradient(ellipse at 70% 30%, rgba(34,197,94,0.25) 0%, transparent 50%), " +
                              "radial-gradient(ellipse at 30% 65%, rgba(34,197,94,0.25) 0%, transparent 50%), " +
                              "radial-gradient(ellipse at 70% 65%, rgba(34,197,94,0.25) 0%, transparent 50%), " +
                              "radial-gradient(ellipse at 50% 47%, rgba(34,197,94,0.2) 0%, transparent 45%)",
                          }}
                        />
                      </div>
                    )}
                  </div>

                  {/* Title block */}
                  <div className="border-t border-gray-700 px-4 py-2 flex items-center justify-between bg-gray-900">
                    <span className="text-[10px] text-gray-500 font-mono">signalCore / ERRCS</span>
                    <span className="text-[10px] text-gray-500 font-mono">
                      {new Date().toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-600">No sheet selected.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
