import { redirect, notFound } from "next/navigation";
import { auth0 } from "@/lib/auth0";
import { getProject } from "@/lib/api";
import { Workspace } from "./workspace";

interface Props {
  params: Promise<{ id: string }>;
}

export default async function ProjectPage({ params }: Props) {
  const session = await auth0.getSession();
  if (!session) redirect("/auth/login");

  const { id } = await params;
  const project = await getProject(session.tokenSet.accessToken, id).catch(() => null);
  if (!project) notFound();

  return <Workspace project={project} userEmail={session.user.email} />;
}
