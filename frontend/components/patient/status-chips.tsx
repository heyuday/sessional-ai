import type { RecordingStatus } from "@/types/brief";

const STATUS_CONFIG: Array<{
  key: RecordingStatus;
  label: string;
  className: string;
}> = [
  {
    key: "idle",
    label: "Idle",
    className: "bg-slate-100 text-slate-700 border-slate-200",
  },
  {
    key: "recording",
    label: "Recording",
    className: "bg-blue-600 text-white border-blue-600",
  },
  {
    key: "uploading",
    label: "Uploading",
    className: "bg-blue-100 text-blue-800 border-blue-200",
  },
  {
    key: "saved",
    label: "Saved",
    className: "bg-emerald-100 text-emerald-800 border-emerald-200",
  },
  {
    key: "error",
    label: "Error",
    className: "bg-rose-100 text-rose-700 border-rose-200",
  },
];

interface StatusChipsProps {
  status: RecordingStatus;
  recordingDurationLabel: string;
}

export function StatusChips({
  status,
  recordingDurationLabel,
}: StatusChipsProps) {
  return (
    <div className="flex flex-wrap items-center justify-center gap-2">
      {STATUS_CONFIG.map((item) => {
        const isActive = item.key === status;
        return (
          <span
            key={item.key}
            className={`rounded-xl border px-3 py-1 text-sm transition-colors ${item.className} ${
              isActive ? "ring-1 ring-black/10" : "opacity-80"
            }`}
          >
            {item.key === "recording"
              ? `${item.label} ${recordingDurationLabel}`
              : item.label}
          </span>
        );
      })}
    </div>
  );
}
