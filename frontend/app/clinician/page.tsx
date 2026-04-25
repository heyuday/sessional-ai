"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { SignOutButton } from "@/components/auth/sign-out-button";
import { deleteClinicianPatientReports, getClinicianBriefs } from "@/lib/api";
import type { PatientBrief } from "@/types/clinician";

function riskBadgeClass(riskLevel: PatientBrief["risk_level"]): string {
  if (riskLevel === "Red") {
    return "bg-rose-100 text-rose-700";
  }
  if (riskLevel === "Yellow") {
    return "bg-amber-100 text-amber-800";
  }
  return "bg-emerald-100 text-emerald-700";
}

function severityChipClass(severity: "low" | "medium" | "high"): string {
  if (severity === "high") return "bg-rose-100 text-rose-700";
  if (severity === "medium") return "bg-amber-100 text-amber-800";
  return "bg-slate-100 text-slate-700";
}

function SnapshotText({ summary }: { summary: string }) {
  const marker = "Key themes this week include ";
  const markerIndex = summary.indexOf(marker);
  if (markerIndex === -1) {
    return <>{summary}</>;
  }
  const intro = summary.slice(0, markerIndex).trimEnd();
  const themed = summary.slice(markerIndex).trim();
  return (
    <>
      {intro}{" "}
      <strong>{themed}</strong>
    </>
  );
}

export default function ClinicianDashboardPage() {
  const [briefs, setBriefs] = useState<PatientBrief[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [deletingPatientId, setDeletingPatientId] = useState<string | null>(null);
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function loadBriefs() {
      try {
        setLoading(true);
        setError("");
        const response = await getClinicianBriefs();
        if (active) setBriefs(response);
      } catch {
        if (active) setError("Unable to load patient briefs right now.");
      } finally {
        if (active) setLoading(false);
      }
    }
    void loadBriefs();
    return () => {
      active = false;
    };
  }, []);

  const selected = useMemo(
    () => briefs.find((p) => p.patient_id === selectedPatientId) ?? null,
    [briefs, selectedPatientId],
  );

  async function handleDeleteReports(patientId: string): Promise<void> {
    const confirmed = window.confirm(
      "Delete all stored reports for this patient? This cannot be undone.",
    );
    if (!confirmed) return;

    try {
      setDeletingPatientId(patientId);
      await deleteClinicianPatientReports(patientId);
      setBriefs((current) => current.filter((brief) => brief.patient_id !== patientId));
      if (selectedPatientId === patientId) {
        setSelectedPatientId(null);
      }
    } catch {
      setError("Unable to delete reports right now.");
    } finally {
      setDeletingPatientId(null);
    }
  }

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
          {loading ? (
            <p className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600">
              Loading patient briefs...
            </p>
          ) : null}
          {error ? (
            <p className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
              {error}
            </p>
          ) : null}
          {!loading && !error && briefs.length === 0 ? (
            <p className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600">
              No patient check-ins yet.
            </p>
          ) : null}
          {briefs.map((brief) => (
            <div
              key={brief.patient_id}
              className="rounded-2xl border border-slate-200 bg-white p-4 text-left shadow-sm"
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
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-semibold ${riskBadgeClass(brief.risk_level)}`}
                  >
                    {brief.risk_level}
                  </span>
                </div>
              </div>
              <p className="mt-3 text-sm text-slate-700">{brief.summary}</p>
              <div className="mt-3 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setSelectedPatientId(brief.patient_id)}
                  className="rounded-xl border border-slate-300 px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50"
                >
                  Quick View
                </button>
                <button
                  type="button"
                  onClick={() => handleDeleteReports(brief.patient_id)}
                  disabled={deletingPatientId === brief.patient_id}
                  className="rounded-xl border border-rose-300 bg-rose-50 px-3 py-2 text-xs font-semibold text-rose-700 hover:bg-rose-100 disabled:opacity-60"
                >
                  {deletingPatientId === brief.patient_id ? "Deleting..." : "Delete Reports"}
                </button>
              </div>
            </div>
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
              <span
                className={`rounded-full px-3 py-1 text-xs font-semibold ${riskBadgeClass(selected.risk_level)}`}
              >
                {selected.risk_level}
              </span>
            </div>

            <section className="mt-4">
              <h3 className="text-sm font-semibold text-slate-900">60-second snapshot</h3>
              <p className="mt-1 text-sm text-slate-700">
                <SnapshotText summary={selected.summary} />
              </p>
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
                    <div className="mt-2 flex items-center gap-2">
                      <span
                        className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${severityChipClass(moment.severity)}`}
                      >
                        {moment.severity}
                      </span>
                      <span className="text-[11px] text-slate-600">
                        {Math.round(moment.confidence * 100)}% confidence
                      </span>
                    </div>
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
