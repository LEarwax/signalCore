import type { NextRequest } from "next/server";
import { auth0 } from "@/lib/auth0";

export async function middleware(request: NextRequest) {
  return await auth0.middleware(request);
}

export const config = {
  matcher: [
    // Auth0 v4: middleware handles /auth/* routes — do NOT exclude them
    // Exclude static assets and the public share page only
    "/((?!share|_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt).*)",
  ],
};
