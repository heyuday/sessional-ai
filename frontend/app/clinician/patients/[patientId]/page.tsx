import Link from "next/link";
import { notFound } from "next/navigation";

import { ClinicalSummaryCard } from "@/components/clinician/clinical-summary-card";
import { DivergenceTimeline } from "@/components/clinician/divergence-timeline";
import { NotesActionsPanel } from "@/components/clinician/notes-actions-panel";
import { TranscriptAffectPanel } from "@/components/clinician/transcript-affect-panel";
import { getPatientBrief } from "@/lib/mock-data";

interface PatientBriefPageProps {
  params: Promise<{ patientId: string }>;
}

export default async function PatientBriefPage({ params }: PatientBriefPageProps) {
  const { patientId } = await params;
  const brief = getPatientBrief(patientId);

  if (!brief) {
    notFound();
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
            <h1 className="text-3xl font-semibold text-slate-900">{brief.patient_name}</h1>
            <span className="rounded-full bg-rose-100 px-3 py-1 text-xs font-semibold text-rose-700">
              Current risk {brief.risk_level}
            </span>
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
            <TranscriptAffectPanel transcript={brief.transcript} />
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
            <NotesActionsPanel />
          </div>
        </div>
      </main>
    </div>
  );
}
