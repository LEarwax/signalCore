import { NextRequest, NextResponse } from "next/server";
import { auth0 } from "@/lib/auth0";

const API_URL = process.env.API_URL ?? "http://localhost:8000";

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await auth0.getSession();
  if (!session) return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
  const { id } = await params;
  const res = await fetch(`${API_URL}/api/projects/${id}`, {
    headers: { Authorization: `Bearer ${session.tokenSet.accessToken}` },
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await auth0.getSession();
  if (!session) return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
  const { id } = await params;
  const body = await req.json();
  const res = await fetch(`${API_URL}/api/projects/${id}`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${session.tokenSet.accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

export async function DELETE(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await auth0.getSession();
  if (!session) return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
  const { id } = await params;
  const res = await fetch(`${API_URL}/api/projects/${id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${session.tokenSet.accessToken}` },
  });
  if (res.status === 204) return new NextResponse(null, { status: 204 });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
