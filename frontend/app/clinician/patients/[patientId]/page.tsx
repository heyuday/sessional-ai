"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { ClinicalSummaryCard } from "@/components/clinician/clinical-summary-card";
import { DivergenceTimeline } from "@/components/clinician/divergence-timeline";
import { deleteClinicianPatientReports, getClinicianBrief } from "@/lib/api";
import type { PatientBrief } from "@/types/clinician";

export default function PatientBriefPage() {
  const router = useRouter();
  const params = useParams<{ patientId: string }>();
  const patientId = params.patientId;
  const [brief, setBrief] = useState<PatientBrief | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    let active = true;
    async function loadPatientBrief() {
      if (!patientId) return;
      try {
        setLoading(true);
        setError("");
        const response = await getClinicianBrief(patientId);
        if (active) setBrief(response);
      } catch {
        if (active) setError("Unable to load this patient brief.");
      } finally {
        if (active) setLoading(false);
      }
    }
    void loadPatientBrief();
    return () => {
      active = false;
    };
  }, [patientId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 px-6 py-8">
        <main className="mx-auto max-w-3xl rounded-2xl border border-slate-200 bg-white p-5">
          <p className="text-sm text-slate-600">Loading patient brief...</p>
        </main>
      </div>
    );
  }

  if (error || !brief) {
    return (
      <div className="min-h-screen bg-slate-50 px-6 py-8">
        <main className="mx-auto max-w-3xl rounded-2xl border border-rose-200 bg-rose-50 p-5">
          <p className="text-sm text-rose-700">{error || "Patient brief not found."}</p>
          <Link href="/clinician" className="mt-3 inline-block text-sm font-medium text-blue-700 hover:underline">
            Back to dashboard
          </Link>
        </main>
      </div>
    );
  }

  async function handleDeleteReports(): Promise<void> {
    const confirmed = window.confirm(
      "Delete all stored reports for this patient? This cannot be undone.",
    );
    if (!confirmed) return;
    try {
      setIsDeleting(true);
      await deleteClinicianPatientReports(patientId);
      router.push("/clinician");
    } catch {
      setError("Unable to delete reports right now.");
    } finally {
      setIsDeleting(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 px-6 py-8">
      <main className="mx-auto max-w-7xl">
        <div className="mb-4">
          <Link href="/clinician" className="text-sm font-medium text-blue-700 hover:underline">
            Back to dashboard
          </Link>
        </div>

        <header className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-semibold text-slate-900">{brief.patient_name}</h1>
              <span className="rounded-full bg-rose-100 px-3 py-1 text-xs font-semibold text-rose-700">
                Current risk {brief.risk_level}
              </span>
            </div>
            <button
              type="button"
              onClick={() => void handleDeleteReports()}
              disabled={isDeleting}
              className="rounded-xl border border-rose-300 bg-rose-50 px-3 py-2 text-xs font-semibold text-rose-700 hover:bg-rose-100 disabled:opacity-60"
            >
              {isDeleting ? "Deleting..." : "Delete Reports"}
            </button>
          </div>
          <div className="mt-3 grid gap-3 text-sm text-slate-700 md:grid-cols-3">
            <p>
              <span className="font-semibold">Patient ID:</span> {brief.patient_id}
            </p>
            <p>
              <span className="font-semibold">Next appointment:</span> {brief.next_appointment}
            </p>
            <p>
              <span className="font-semibold">Assigned clinician:</span> {brief.assigned_clinician}
            </p>
          </div>
        </header>

        <div className="mt-6 grid gap-4 lg:grid-cols-[2fr_1fr]">
          <div className="space-y-4">
            <ClinicalSummaryCard brief={brief} />
            <DivergenceTimeline moments={brief.divergence_moments} />
          </div>

          <div className="space-y-4">
            <section className="rounded-2xl border border-slate-200 bg-white p-5">
              <h2 className="text-xl font-semibold text-slate-900">Trends</h2>
              <div className="mt-3 space-y-3">
                {brief.trends.map((trend) => (
                  <div key={trend.label} className="rounded-xl border border-slate-200 px-3 py-2">
                    <p className="text-sm font-medium text-slate-800">{trend.label}</p>
                    <p className="text-xs text-slate-600">Direction: {trend.direction}</p>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}
