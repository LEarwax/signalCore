import { getSession } from "@auth0/nextjs-auth0";
import { redirect } from "next/navigation";

export default async function Home() {
  const session = await getSession();
  if (session) redirect("/dashboard");

  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-6 p-8 bg-gray-50">
      <div className="text-center">
        <h1 className="text-5xl font-bold tracking-tight mb-2">
          signal<span className="text-orange-600">Core</span>
        </h1>
        <p className="text-gray-500 max-w-md mt-3">
          Upload a floor plan PDF and get a ready-to-submit ERRCS packet in seconds.
        </p>
      </div>
      <a
        href="/api/auth/login"
        className="px-6 py-3 bg-orange-600 text-white font-medium rounded-md hover:bg-orange-700 transition"
      >
        Sign in to get started
      </a>
    </main>
  );
}
