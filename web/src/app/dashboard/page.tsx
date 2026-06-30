import { getSession } from "@auth0/nextjs-auth0";
import { redirect } from "next/navigation";
import { Nav } from "@/components/shared/nav";
import { ProjectList } from "@/components/projects/project-list";
import { getProjects } from "@/lib/api";

export default async function DashboardPage() {
  const session = await getSession();
  if (!session) redirect("/api/auth/login");

  const projects = await getProjects(session.accessToken!).catch(() => []);

  return (
    <div className="min-h-screen">
      <Nav />
      <main className="max-w-5xl mx-auto px-6 py-10">
        <ProjectList projects={projects} />
      </main>
    </div>
  );
}
