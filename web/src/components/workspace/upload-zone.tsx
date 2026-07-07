"use client";

import { useRef, useState, useCallback } from "react";
import type { Sheet } from "@/types";

interface Props {
  projectId: string;
  onSheetsExtracted: (fileName: string, sheets: Sheet[], uploadId: string) => void;
}

export function UploadZone({ projectId, onSheetsExtracted }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [statusText, setStatusText] = useState("Uploading…");
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        setError("Please upload a PDF file.");
        return;
      }

      setError(null);
      setUploading(true);
      setStatusText("Uploading…");

      try {
        // Get access token client-side so we can upload directly to the API,
        // bypassing Vercel's 4.5 MB serverless body limit.
        const tokenRes = await fetch("/auth/access-token");
        if (!tokenRes.ok) throw new Error("Could not retrieve auth token");
        const { token } = await tokenRes.json();

        const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "";
        const form = new FormData();
        form.append("file", file);

        setStatusText("Extracting sheets…");

        const res = await fetch(`${apiUrl}/api/projects/${projectId}/upload`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
          body: form,
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: "Upload failed" }));
          throw new Error(err.detail ?? "Upload failed");
        }

        const data = await res.json();

        // Map API response to Sheet type.
        // Prefix relative thumbnail URLs (local-storage fallback) with the API origin.
        const sheets: Sheet[] = data.sheets.map((s: {
          id: string;
          page_number: number;
          label: string;
          type: string;
          thumbnail_url: string | null;
        }) => ({
          id: s.id,
          page_number: s.page_number,
          label: s.label,
          type: s.type as Sheet["type"],
          thumbnail_url: s.thumbnail_url?.startsWith("/")
            ? `${apiUrl}${s.thumbnail_url}`
            : s.thumbnail_url ?? null,
        }));

        onSheetsExtracted(file.name, sheets, data.upload_id);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Upload failed. Please try again.");
      } finally {
        setUploading(false);
        setStatusText("Uploading…");
      }
    },
    [projectId, onSheetsExtracted]
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
          "w-full max-w-xl border-2 border-dashed rounded-xl p-16 flex flex-col items-center gap-4 transition",
          uploading
            ? "border-orange-500/50 bg-gray-900/50 cursor-not-allowed"
            : dragging
            ? "border-orange-500 bg-orange-500/5 cursor-pointer"
            : "border-gray-700 hover:border-gray-500 bg-gray-900/50 cursor-pointer",
        ].join(" ")}
        onDragOver={(e) => { e.preventDefault(); if (!uploading) setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => !uploading && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={onInputChange}
        />

        {uploading ? (
          <>
            <div className="w-12 h-12 rounded-full border-2 border-orange-500 border-t-transparent animate-spin" />
            <p className="text-sm text-gray-300 font-medium">{statusText}</p>
            <p className="text-xs text-gray-500">This may take a moment for large plan sets</p>
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
            {error ? (
              <p className="text-sm text-red-400 text-center">{error}</p>
            ) : (
              <p className="text-xs text-gray-600">
                Supports architectural plan sets — all sheet types detected automatically
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
