"use client";

import { useState, useCallback } from "react";
import Link from "next/link";
import { useUser } from "@auth0/nextjs-auth0/client";
import type { Project, Sheet } from "@/types";
import { WorkspaceSidebar } from "@/components/workspace/sidebar";
import { UploadZone } from "@/components/workspace/upload-zone";
import { SheetGrid } from "@/components/workspace/sheet-grid";
import { FloorPlanView } from "@/components/workspace/floor-plan-view";

type WorkspaceStep = "upload" | "select" | "running" | "results";

interface Props {
  project: Project;
}

export function Workspace({ project }: Props) {
  const { user } = useUser();
  const [step, setStep] = useState<WorkspaceStep>("upload");
  const [fileName, setFileName] = useState<string | null>(null);
  const [sheets, setSheets] = useState<Sheet[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const handleSheetsExtracted = useCallback((name: string, extracted: Sheet[]) => {
    setFileName(name);
    setSheets(extracted);
    // Auto-select floor plans
    const floorIds = extracted.filter((s) => s.type === "floor_plan").map((s) => s.id);
    setSelectedIds(floorIds);
    setStep("select");
  }, []);

  const toggleSheet = useCallback((id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  }, []);

  const selectAll = useCallback((ids: string[]) => {
    setSelectedIds(ids);
  }, []);

  const handleRunEngine = useCallback(async () => {
    setStep("running");
    // Simulate engine run — replace with real API call when SIG-3 is implemented
    await new Promise((r) => setTimeout(r, 2500));
    setStep("results");
  }, []);

  const handleBack = useCallback(() => {
    setStep("select");
  }, []);

  return (
    <div className="h-screen flex flex-col bg-gray-950">
      {/* Top bar */}
      <header className="flex-shrink-0 h-12 bg-gray-900 border-b border-gray-800 flex items-center px-4 gap-3">
        <Link href="/dashboard" className="font-bold text-sm tracking-tight flex-shrink-0">
          signal<span className="text-orange-500">Core</span>
        </Link>
        <span className="text-gray-700">/</span>
        <span className="text-sm text-gray-300 font-medium truncate">{project.name}</span>

        {/* Step chips */}
        <div className="flex items-center gap-2 ml-2">
          {step !== "upload" && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 border border-green-500/20">
              Uploaded
            </span>
          )}
          {(step === "running" || step === "results") && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-orange-500/10 text-orange-400 border border-orange-500/20">
              {selectedIds.length} sheets selected
            </span>
          )}
          {step === "running" && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
              Running engine…
            </span>
          )}
          {step === "results" && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 border border-green-500/20">
              Results ready
            </span>
          )}
        </div>

        <div className="flex-1" />

        {user && (
          <span className="text-xs text-gray-500 hidden md:block">{user.email}</span>
        )}
        <a
          href="/api/auth/logout"
          className="text-xs text-gray-500 hover:text-gray-200 transition"
        >
          Sign out
        </a>
      </header>

      {/* Body */}
      <div className="flex flex-1 overflow-hidden">
        <WorkspaceSidebar
          project={project}
          step={step}
          sheets={sheets}
          selectedIds={selectedIds}
          onRunEngine={handleRunEngine}
        />

        {/* Main canvas */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {step === "upload" && (
            <UploadZone projectId={project.id} onSheetsExtracted={handleSheetsExtracted} />
          )}
          {(step === "select" || step === "running") && fileName && (
            <SheetGrid
              fileName={fileName}
              sheets={sheets}
              selectedIds={selectedIds}
              onToggle={toggleSheet}
              onSelectAll={selectAll}
            />
          )}
          {step === "results" && (
            <FloorPlanView
              sheets={sheets}
              selectedIds={selectedIds}
              onBack={handleBack}
            />
          )}
        </main>
      </div>
    </div>
  );
}
