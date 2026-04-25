import type { UserRole } from "../types/auth";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

interface AuthApiResponse {
  access_token: string;
  token_type: "bearer";
  user: {
    id: string;
    email: string;
    role: UserRole;
  };
}

interface AuthPayload {
  email: string;
  password: string;
}

interface ValidationErrorResponse {
  detail?: Array<{
    loc?: Array<string | number>;
    msg?: string;
  }> | string;
}

const ONE_DAY_SECONDS = 60 * 60 * 24;

function setSessionCookies(response: AuthApiResponse): void {
  document.cookie = `session_authenticated=1; Path=/; Max-Age=${ONE_DAY_SECONDS}; SameSite=Lax`;
  document.cookie = `session_role=${response.user.role}; Path=/; Max-Age=${ONE_DAY_SECONDS}; SameSite=Lax`;
  document.cookie = `session_user=${encodeURIComponent(response.user.email)}; Path=/; Max-Age=${ONE_DAY_SECONDS}; SameSite=Lax`;
  document.cookie = `auth_token=${encodeURIComponent(response.access_token)}; Path=/; Max-Age=${ONE_DAY_SECONDS}; SameSite=Lax`;
}

function clearCookie(name: string): void {
  document.cookie = `${name}=; Path=/; Max-Age=0; SameSite=Lax`;
}

export function clearSessionCookies(): void {
  clearCookie("session_authenticated");
  clearCookie("session_role");
  clearCookie("session_user");
  clearCookie("auth_token");
}

async function parseResponse(response: Response): Promise<AuthApiResponse> {
  const data = (await response.json()) as AuthApiResponse | ValidationErrorResponse;
  if (!response.ok) {
    const detail = "detail" in data ? data.detail : undefined;
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0];
      throw new Error(first.msg ?? `Request failed with status ${response.status}`);
    }
    if (typeof detail === "string" && detail.length > 0) {
      throw new Error(detail);
    }
    throw new Error(`Request failed with status ${response.status}`);
  }
  return data as AuthApiResponse;
}

export async function signUp(
  payload: AuthPayload & { role: UserRole },
): Promise<AuthApiResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/signup`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  const parsed = await parseResponse(response);
  setSessionCookies(parsed);
  return parsed;
}

export async function login(payload: AuthPayload): Promise<AuthApiResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  const parsed = await parseResponse(response);
  setSessionCookies(parsed);
  return parsed;
}

export function getAuthTokenFromCookie(): string | null {
  const tokenPair = document.cookie
    .split("; ")
    .find((cookie) => cookie.startsWith("auth_token="));
  if (!tokenPair) return null;
  return decodeURIComponent(tokenPair.slice("auth_token=".length));
}
