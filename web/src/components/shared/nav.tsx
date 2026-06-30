"use client";

import Link from "next/link";
import { useUser } from "@auth0/nextjs-auth0/client";

export function Nav() {
  const { user } = useUser();

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
              href="/api/auth/logout"
              className="text-sm text-gray-400 hover:text-gray-100"
            >
              Sign out
            </a>
          </>
        ) : (
          <a
            href="/api/auth/login"
            className="text-sm font-medium text-orange-600 hover:text-orange-700"
          >
            Sign in
          </a>
        )}
      </div>
    </nav>
  );
}
