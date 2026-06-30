"use client";

import { useRef, useState, useCallback } from "react";
import type { Sheet } from "@/types";

interface Props {
  projectId: string;
  onSheetsExtracted: (fileName: string, sheets: Sheet[]) => void;
}

// Simulated extraction — replace with real API call when SIG-1 is implemented
function simulateExtraction(fileName: string): Sheet[] {
  return [
    { id: "s1", page_number: 1,  label: "G-001 COVER SHEET",               type: "other",      thumbnail_url: null },
    { id: "s2", page_number: 2,  label: "A-001 SITE PLAN",                  type: "other",      thumbnail_url: null },
    { id: "s3", page_number: 3,  label: "A-101 FLOOR PLAN — LEVEL 1",       type: "floor_plan", thumbnail_url: null },
    { id: "s4", page_number: 4,  label: "A-102 FLOOR PLAN — LEVEL 2",       type: "floor_plan", thumbnail_url: null },
    { id: "s5", page_number: 5,  label: "A-103 FLOOR PLAN — LEVEL 3",       type: "floor_plan", thumbnail_url: null },
    { id: "s6", page_number: 6,  label: "A-104 FLOOR PLAN — ROOF",          type: "floor_plan", thumbnail_url: null },
    { id: "s7", page_number: 7,  label: "A-201 EAST ELEVATION",             type: "elevation",  thumbnail_url: null },
    { id: "s8", page_number: 8,  label: "A-202 WEST ELEVATION",             type: "elevation",  thumbnail_url: null },
    { id: "s9", page_number: 9,  label: "A-301 BUILDING SECTION A",         type: "section",    thumbnail_url: null },
    { id: "s10", page_number: 10, label: "A-401 STAIR DETAIL",              type: "detail",     thumbnail_url: null },
  ];
}

export function UploadZone({ projectId, onSheetsExtracted }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleFile = useCallback(
    async (file: File) => {
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        alert("Please upload a PDF file.");
        return;
      }
      setExtracting(true);
      setProgress(0);
      // Simulate extraction progress
      const interval = setInterval(() => {
        setProgress((p) => {
          if (p >= 90) { clearInterval(interval); return 90; }
          return p + 10;
        });
      }, 150);
      await new Promise((r) => setTimeout(r, 2000));
      clearInterval(interval);
      setProgress(100);
      await new Promise((r) => setTimeout(r, 300));
      const sheets = simulateExtraction(file.name);
      setExtracting(false);
      setProgress(0);
      onSheetsExtracted(file.name, sheets);
    },
    [onSheetsExtracted]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const onInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div className="flex-1 flex items-center justify-center p-10">
      <div
        className={[
          "w-full max-w-xl border-2 border-dashed rounded-xl p-16 flex flex-col items-center gap-4 transition cursor-pointer",
          dragging
            ? "border-orange-500 bg-orange-500/5"
            : "border-gray-700 hover:border-gray-500 bg-gray-900/50",
        ].join(" ")}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => !extracting && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={onInputChange}
        />

        {extracting ? (
          <>
            <div className="w-12 h-12 rounded-full border-2 border-orange-500 border-t-transparent animate-spin" />
            <p className="text-sm text-gray-300 font-medium">Extracting sheets…</p>
            <div className="w-48 h-1.5 bg-gray-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-orange-500 rounded-full transition-all duration-150"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-xs text-gray-500">{progress}%</p>
          </>
        ) : (
          <>
            {/* PDF icon */}
            <svg className="w-12 h-12 text-gray-600" fill="none" viewBox="0 0 48 48" stroke="currentColor" strokeWidth={1.5}>
              <rect x="8" y="4" width="32" height="40" rx="3" strokeLinejoin="round" />
              <path d="M8 14h32M8 24h20M8 32h14" strokeLinecap="round" />
              <path d="M28 4v10h12" strokeLinejoin="round" />
            </svg>
            <div className="text-center">
              <p className="text-base font-semibold text-gray-200">Drop plan set PDF here</p>
              <p className="text-sm text-gray-500 mt-1">or click to browse</p>
            </div>
            <p className="text-xs text-gray-600">
              Supports architectural plan sets — all sheet types detected automatically
            </p>
          </>
        )}
      </div>
    </div>
  );
}
