import type { PatientBrief } from "@/types/clinician";

interface ClinicalSummaryCardProps {
  brief: PatientBrief;
}

export function ClinicalSummaryCard({ brief }: ClinicalSummaryCardProps) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5">
      <h2 className="text-xl font-semibold text-slate-900">Clinical Summary</h2>
      <p className="mt-2 text-sm text-slate-800">
        <span className="font-semibold">Risk rationale:</span> {brief.summary}
      </p>
      <div className="mt-4 grid gap-6 md:grid-cols-2">
        <div>
          <h3 className="text-sm font-semibold text-slate-900">Prioritized key themes:</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-800">
            {brief.key_themes.map((theme) => (
              <li key={theme}>{theme}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-slate-900">Suggested opening questions:</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-800">
            {brief.opening_questions.map((question) => (
              <li key={question}>{question}</li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
