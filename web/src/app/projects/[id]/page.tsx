import { getSession } from "@auth0/nextjs-auth0";
import { redirect, notFound } from "next/navigation";
import { getProject } from "@/lib/api";
import { Workspace } from "./workspace";

interface Props {
  params: Promise<{ id: string }>;
}

export default async function ProjectPage({ params }: Props) {
  const session = await getSession();
  if (!session) redirect("/api/auth/login");

  const { id } = await params;
  const project = await getProject(session.accessToken!, id).catch(() => null);
  if (!project) notFound();

  return <Workspace project={project} />;
}
