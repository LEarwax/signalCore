import { NextRequest, NextResponse } from "next/server";
import { auth0 } from "@/lib/auth0";

const API_URL = process.env.API_URL ?? "http://localhost:8000";

export async function GET() {
  const session = await auth0.getSession();
  if (!session) return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });

  const res = await fetch(`${API_URL}/api/projects/`, {
    headers: { Authorization: `Bearer ${session.tokenSet.accessToken}` },
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

export async function POST(req: NextRequest) {
  const session = await auth0.getSession();
  if (!session) return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });

  const body = await req.json();
  const res = await fetch(`${API_URL}/api/projects/`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${session.tokenSet.accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
