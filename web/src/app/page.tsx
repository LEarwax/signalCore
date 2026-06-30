import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-4xl font-bold tracking-tight">signalCore</h1>
      <p className="text-gray-500 text-center max-w-md">
        ERRCS engineering platform — upload a floor plan PDF and get a ready-to-submit AHJ packet in seconds.
      </p>
      <div className="flex gap-4">
        <Link
          href="/api/auth/login"
          className="px-6 py-2 bg-black text-white rounded-md hover:bg-gray-800 transition"
        >
          Sign in
        </Link>
        <Link
          href="/dashboard"
          className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition"
        >
          Dashboard
        </Link>
      </div>
    </main>
  );
}
