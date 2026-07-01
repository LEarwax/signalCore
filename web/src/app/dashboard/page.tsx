import { redirect } from "next/navigation";
import { auth0 } from "@/lib/auth0";
import { Nav } from "@/components/shared/nav";
import { ProjectList } from "@/components/projects/project-list";
import { getProjects } from "@/lib/api";

export default async function DashboardPage() {
  const session = await auth0.getSession();
  if (!session) redirect("/auth/login");

  const projects = await getProjects(session.tokenSet.accessToken).catch(() => []);

  return (
    <div className="min-h-screen">
      <Nav />
      <main className="max-w-5xl mx-auto px-6 py-10">
        <ProjectList projects={projects} />
      </main>
    </div>
  );
}
