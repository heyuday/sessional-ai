interface RecordButtonProps {
  isRecording: boolean;
  disabled?: boolean;
  onStart: () => void;
  onStop: () => void;
}

export function RecordButton({
  isRecording,
  disabled = false,
  onStart,
  onStop,
}: RecordButtonProps) {
  return (
    <button
      type="button"
      disabled={disabled}
      onPointerDown={(event) => {
        event.preventDefault();
        onStart();
      }}
      onPointerUp={onStop}
      onPointerLeave={() => {
        if (isRecording) onStop();
      }}
      className={`relative h-64 w-64 rounded-full border border-blue-200 bg-blue-500 text-white shadow-sm transition active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60 ${
        isRecording ? "animate-pulse" : ""
      }`}
      aria-label="Hold to record your voice check-in"
      aria-pressed={isRecording}
    >
      <span className="pointer-events-none absolute inset-3 rounded-full border border-blue-200/70" />
      <span className="pointer-events-none absolute inset-6 rounded-full border border-blue-200/50" />
      <span className="pointer-events-none flex h-full flex-col items-center justify-center gap-1">
        <span className="text-2xl font-semibold leading-none">MIC</span>
        <span className="text-xl font-medium">Hold to Record</span>
      </span>
    </button>
  );
}
