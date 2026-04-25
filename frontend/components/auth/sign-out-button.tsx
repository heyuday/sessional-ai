"use client";

import { useRouter } from "next/navigation";

import { clearSessionCookies } from "@/lib/auth";

export function SignOutButton() {
  const router = useRouter();

  return (
    <button
      type="button"
      onClick={() => {
        clearSessionCookies();
        router.push("/");
      }}
      className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
    >
      Sign out
    </button>
  );
}
