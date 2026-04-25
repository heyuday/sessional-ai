import type { DivergenceMoment } from "@/types/brief";

interface DivergenceTimelineProps {
  moments: DivergenceMoment[];
}

function severityClass(severity: DivergenceMoment["severity"]): string {
  if (severity === "high") return "bg-rose-100 text-rose-700";
  if (severity === "medium") return "bg-amber-100 text-amber-700";
  return "bg-slate-100 text-slate-700";
}

export function DivergenceTimeline({ moments }: DivergenceTimelineProps) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5">
      <h2 className="text-xl font-semibold text-slate-900">Divergence Timeline</h2>
      <div className="mt-4 space-y-4">
        {moments.map((moment) => (
          <article key={`${moment.timestamp}-${moment.transcript_snippet}`} className="rounded-xl border border-slate-200 p-4">
            <p className="text-xs font-semibold tracking-wide text-slate-500">{moment.timestamp}</p>
            <p className="mt-1 text-sm font-semibold text-slate-900">
              Transcript snippet: {moment.transcript_snippet}
            </p>
            <p className="mt-2 text-sm text-slate-800">
              Mismatch: {moment.mismatch_label}
            </p>
            <p className="mt-1 text-xs text-slate-600">
              Interpretation: this segment shows mismatch between what is said and how it is expressed in voice.
            </p>
            <div className="mt-3 flex items-center gap-3">
              <span className={`rounded-full px-2 py-1 text-xs font-medium ${severityClass(moment.severity)}`}>
                {moment.severity}
              </span>
              <span className="text-xs text-slate-600">
                Confidence: {Math.round(moment.confidence * 100)}%
              </span>
            </div>
            <p className="mt-2 text-xs text-slate-500">
              Clinical context: probe this timestamp for stressor details, perceived coping, and emotional intensity.
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}
