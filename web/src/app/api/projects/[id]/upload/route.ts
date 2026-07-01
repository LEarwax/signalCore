import { getSession } from "@auth0/nextjs-auth0";
import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_URL ?? "http://localhost:8000";

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await getSession();
  if (!session) return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });

  const { id } = await params;
  const formData = await req.formData();

  const res = await fetch(`${API_URL}/api/projects/${id}/upload`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${session.accessToken}`,
      // Do NOT set Content-Type — let fetch set multipart boundary automatically
    },
    body: formData,
  });

  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
