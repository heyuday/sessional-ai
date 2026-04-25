import { NextResponse, type NextRequest } from "next/server";

type UserRole = "patient" | "clinician";

function getSession(request: NextRequest): {
  isAuthenticated: boolean;
  role: UserRole | null;
} {
  const token = request.cookies.get("auth_token")?.value;
  const isAuthenticated =
    request.cookies.get("session_authenticated")?.value === "1" && Boolean(token);
  const roleCookie = request.cookies.get("session_role")?.value;
  const role = roleCookie === "patient" || roleCookie === "clinician" ? roleCookie : null;

  return { isAuthenticated, role };
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const { isAuthenticated, role } = getSession(request);

  if (pathname.startsWith("/patient") && (!isAuthenticated || role !== "patient")) {
    return NextResponse.redirect(new URL("/auth/patient", request.url));
  }

  if (pathname.startsWith("/clinician") && (!isAuthenticated || role !== "clinician")) {
    return NextResponse.redirect(new URL("/auth/clinician", request.url));
  }

  if (pathname.startsWith("/auth/patient") && isAuthenticated && role === "patient") {
    return NextResponse.redirect(new URL("/patient", request.url));
  }

  if (pathname.startsWith("/auth/clinician") && isAuthenticated && role === "clinician") {
    return NextResponse.redirect(new URL("/clinician", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/patient/:path*", "/clinician/:path*", "/auth/patient", "/auth/clinician"],
};
