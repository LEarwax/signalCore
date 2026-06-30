import { withMiddlewareAuthRequired } from "@auth0/nextjs-auth0/edge";

export default withMiddlewareAuthRequired();

export const config = {
  // Protect everything except the share page and auth routes
  matcher: ["/((?!share|api/auth|_next/static|_next/image|favicon.ico).*)"],
};
