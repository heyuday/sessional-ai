import type { TranscriptItem } from "@/types/clinician";

interface TranscriptAffectPanelProps {
  transcript: TranscriptItem[];
}

function affectTone(affect: string): string {
  const value = affect.toLowerCase();
  if (value.includes("stressed") || value.includes("anxious") || value.includes("tense")) {
    return "bg-rose-100 text-rose-700";
  }
  if (value.includes("calm")) {
    return "bg-emerald-100 text-emerald-700";
  }
  return "bg-slate-100 text-slate-700";
}

export function TranscriptAffectPanel({ transcript }: TranscriptAffectPanelProps) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5">
      <h2 className="text-xl font-semibold text-slate-900">Transcript + Affect</h2>
      <div className="mt-4 space-y-3">
        {transcript.map((item) => (
          <div key={`${item.timestamp}-${item.text}`} className="rounded-xl border border-slate-200 px-3 py-2">
            <div className="flex items-start justify-between gap-3">
              <p className="text-sm text-slate-800">
                ({item.timestamp}) {item.speaker}: {item.text}
              </p>
              <span className={`shrink-0 rounded-lg px-2 py-1 text-xs font-medium ${affectTone(item.affect)}`}>
                {item.affect}
              </span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
