import { getSession } from "@auth0/nextjs-auth0";
import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_URL ?? "http://localhost:8000";

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });

  const res = await fetch(`${API_URL}/api/projects/`, {
    headers: { Authorization: `Bearer ${session.accessToken}` },
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

export async function POST(req: NextRequest) {
  const session = await getSession();
  if (!session) return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });

  const body = await req.json();
  const res = await fetch(`${API_URL}/api/projects/`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${session.accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
