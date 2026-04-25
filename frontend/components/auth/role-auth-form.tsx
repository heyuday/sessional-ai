"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login, signUp } from "@/lib/auth";
import type { UserRole } from "@/types/auth";

type AuthMode = "login" | "signup";

interface RoleAuthFormProps {
  role: UserRole;
  title: string;
  subtitle: string;
  destination: string;
}

export function RoleAuthForm({
  role,
  title,
  subtitle,
  destination,
}: RoleAuthFormProps) {
  const router = useRouter();
  const [mode, setMode] = useState<AuthMode>("login");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!email || !password) return;
    if (mode === "signup" && !fullName.trim()) return;
    setError("");
    setIsSubmitting(true);

    try {
      if (mode === "signup") {
        await signUp({ full_name: fullName.trim(), email, password, role });
      } else {
        const response = await login({ email, password });
        if (response.user.role !== role) {
          setError(`This account belongs to ${response.user.role}. Use the correct sign-in page.`);
          setIsSubmitting(false);
          return;
        }
      }
      router.push(destination);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Authentication failed.";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#f5f1e8] px-4 py-10">
      <main className="mx-auto max-w-md rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-3xl font-semibold text-slate-900">{title}</h1>
        <p className="mt-2 text-sm text-slate-600">{subtitle}</p>

        <div className="mt-5 grid grid-cols-2 gap-2 rounded-xl bg-slate-100 p-1">
          <button
            type="button"
            onClick={() => setMode("login")}
            className={`rounded-lg px-3 py-2 text-sm font-medium ${
              mode === "login"
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Login
          </button>
          <button
            type="button"
            onClick={() => setMode("signup")}
            className={`rounded-lg px-3 py-2 text-sm font-medium ${
              mode === "signup"
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Sign up
          </button>
        </div>

        <form
          suppressHydrationWarning
          onSubmit={handleSubmit}
          className="mt-6 space-y-4"
        >
          {mode === "signup" ? (
            <label className="block text-sm font-medium text-slate-700">
              Full name
              <input
                type="text"
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-slate-900 focus:border-blue-500 focus:outline-none"
                required
              />
            </label>
          ) : null}

          <label className="block text-sm font-medium text-slate-700">
            Email
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-slate-900 focus:border-blue-500 focus:outline-none"
              required
            />
          </label>

          <label className="block text-sm font-medium text-slate-700">
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              minLength={8}
              className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-slate-900 focus:border-blue-500 focus:outline-none"
              required
            />
            <span className="mt-1 block text-xs text-slate-500">
              Minimum 8 characters.
            </span>
          </label>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white hover:bg-blue-700"
          >
            {isSubmitting
              ? "Please wait..."
              : mode === "signup"
                ? "Create account"
                : "Sign in"}
          </button>

          {error ? (
            <p className="rounded-xl bg-rose-50 px-4 py-2 text-sm text-rose-700">
              {error}
            </p>
          ) : null}
        </form>
      </main>
    </div>
  );
}
