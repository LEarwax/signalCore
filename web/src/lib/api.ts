import type { Project, AHJProfile, SubmittalPacket } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchWithAuth(path: string, token: string, options?: RequestInit) {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "API error");
  }
  return res.json();
}

// ── Projects ──────────────────────────────────────────────────────

export async function getProject(token: string, projectId: string): Promise<Project> {
  return fetchWithAuth(`/api/projects/${projectId}`, token);
}

export async function getProjects(token: string): Promise<Project[]> {
  return fetchWithAuth("/api/projects/", token);
}

export async function createProject(
  token: string,
  data: { name: string; address?: string; notes?: string }
): Promise<Project> {
  return fetchWithAuth("/api/projects/", token, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ── AHJ ──────────────────────────────────────────────────────────

export async function lookupAHJ(token: string, address: string): Promise<AHJProfile> {
  return fetchWithAuth(`/api/ahj/lookup?address=${encodeURIComponent(address)}`, token);
}

// ── Packets ───────────────────────────────────────────────────────

export async function getPacket(token: string, packetId: string): Promise<SubmittalPacket> {
  return fetchWithAuth(`/api/packets/${packetId}`, token);
}

export async function generatePacket(
  token: string,
  projectId: string,
  floorPlans: File[]
): Promise<{ id: string }> {
  const form = new FormData();
  form.append("project_id", projectId);
  for (const file of floorPlans) {
    form.append("floor_plans", file);
  }
  const res = await fetch(`${API_URL}/api/packets/`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
  if (!res.ok) throw new Error("Failed to generate packet");
  return res.json();
}

// ── Share (no auth) ───────────────────────────────────────────────

export async function getSharedPacket(token: string): Promise<Record<string, unknown>> {
  const res = await fetch(`${API_URL}/api/share/${token}`);
  if (!res.ok) throw new Error("Share link not found");
  return res.json();
}
