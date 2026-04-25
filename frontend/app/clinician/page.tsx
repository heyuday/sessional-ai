"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { SignOutButton } from "@/components/auth/sign-out-button";
import { MOCK_PATIENT_BRIEFS } from "@/lib/mock-data";

export default function ClinicianDashboardPage() {
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);

  const selected = useMemo(
    () => MOCK_PATIENT_BRIEFS.find((p) => p.patient_id === selectedPatientId) ?? null,
    [selectedPatientId],
  );

  return (
    <div className="min-h-screen bg-slate-50 px-6 py-8">
      <main className="mx-auto max-w-6xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold text-slate-900">Clinician Dashboard</h1>
            <p className="mt-1 text-sm text-slate-600">
              Pre-session briefing with divergence-focused triage.
            </p>
          </div>
          <SignOutButton />
        </div>

        <section className="mt-6 grid gap-4">
          {MOCK_PATIENT_BRIEFS.map((brief) => (
            <button
              key={brief.patient_id}
              type="button"
              className="rounded-2xl border border-slate-200 bg-white p-4 text-left shadow-sm hover:border-blue-200"
              onClick={() => setSelectedPatientId(brief.patient_id)}
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-slate-900">{brief.patient_name}</h2>
                  <p className="text-sm text-slate-600">Last check-in: {brief.last_checkin_label}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                    {brief.trend_label}
                  </span>
                  <span className="rounded-full bg-rose-100 px-3 py-1 text-xs font-semibold text-rose-700">
                    {brief.risk_level}
                  </span>
                </div>
              </div>
              <p className="mt-3 text-sm text-slate-700">{brief.summary}</p>
            </button>
          ))}
        </section>
      </main>

      {selected ? (
        <div className="fixed inset-0 z-20 flex items-center justify-center bg-slate-900/45 px-4">
          <div className="w-full max-w-2xl rounded-2xl border border-slate-200 bg-white p-5 shadow-xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold text-slate-900">{selected.patient_name}</h2>
                <p className="text-sm text-slate-600">
                  Last check-in: {selected.last_checkin_label} · Trend: {selected.trend_label}
                </p>
              </div>
              <span className="rounded-full bg-rose-100 px-3 py-1 text-xs font-semibold text-rose-700">
                {selected.risk_level}
              </span>
            </div>

            <section className="mt-4">
              <h3 className="text-sm font-semibold text-slate-900">60-second snapshot</h3>
              <p className="mt-1 text-sm text-slate-700">{selected.summary}</p>
              <p className="mt-1 text-xs text-slate-600">{selected.what_changed}</p>
            </section>

            <section className="mt-4">
              <h3 className="text-sm font-semibold text-slate-900">Top divergence moments</h3>
              <ul className="mt-2 space-y-2">
                {selected.divergence_moments.slice(0, 3).map((moment) => (
                  <li
                    key={`${moment.timestamp}-${moment.transcript_snippet}`}
                    className="rounded-xl border border-slate-200 p-3"
                  >
                    <p className="text-xs font-semibold text-slate-500">{moment.timestamp}</p>
                    <p className="text-sm text-slate-800">{moment.transcript_snippet}</p>
                    <p className="text-xs text-slate-600">{moment.mismatch_label}</p>
                  </li>
                ))}
              </ul>
            </section>

            <div className="mt-5 flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => setSelectedPatientId(null)}
                className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700"
              >
                Close
              </button>
              <Link
                href={`/clinician/patients/${selected.patient_id}`}
                className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
              >
                Open Full Brief
              </Link>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
