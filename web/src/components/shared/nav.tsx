import Link from "next/link";
import { auth0 } from "@/lib/auth0";

export async function Nav() {
  const session = await auth0.getSession();
  const user = session?.user;

  return (
    <nav className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center justify-between">
      <Link href="/dashboard" className="font-bold text-lg tracking-tight">
        signal<span className="text-orange-600">Core</span>
      </Link>
      <div className="flex items-center gap-4">
        {user ? (
          <>
            <span className="text-sm text-gray-400">{user.email}</span>
            <a
              href="/auth/logout"
              className="text-sm text-gray-400 hover:text-gray-100"
            >
              Sign out
            </a>
          </>
        ) : (
          <a
            href="/auth/login"
            className="text-sm font-medium text-orange-600 hover:text-orange-700"
          >
            Sign in
          </a>
        )}
      </div>
    </nav>
  );
}
