"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { SignOutButton } from "@/components/auth/sign-out-button";
import { uploadCheckin } from "@/lib/api";
import type { CheckinBrief } from "@/types/brief";

function chooseMimeType(): string | undefined {
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];

  for (const candidate of candidates) {
    if (MediaRecorder.isTypeSupported(candidate)) {
      return candidate;
    }
  }

  return undefined;
}

function formatDuration(seconds: number): string {
  const minutes = String(Math.floor(seconds / 60)).padStart(2, "0");
  const remainder = String(seconds % 60).padStart(2, "0");
  return `${minutes}:${remainder}`;
}

type CapturePhase =
  | "idle"
  | "recording"
  | "paused"
  | "ready"
  | "uploading"
  | "saved"
  | "error";

export function PatientCheckinPage() {
  const [phase, setPhase] = useState<CapturePhase>("idle");
  const [durationSec, setDurationSec] = useState(0);
  const [latestBrief, setLatestBrief] = useState<CheckinBrief | null>(null);
  const [errorMessage, setErrorMessage] = useState<string>("");

  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const segmentsRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);

  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const releaseStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  }, []);

  const cleanupRecorder = useCallback(() => {
    stopTimer();
    releaseStream();

    recorderRef.current = null;
  }, [releaseStream, stopTimer]);

  useEffect(() => {
    return () => cleanupRecorder();
  }, [cleanupRecorder]);

  const startTimer = useCallback(() => {
    stopTimer();
    timerRef.current = window.setInterval(() => {
      setDurationSec((current) => current + 1);
    }, 1000);
  }, [stopTimer]);

  const startSegment = useCallback(async () => {
    if (phase === "uploading" || phase === "recording") return;

    try {
      setErrorMessage("");
      setLatestBrief(null);

      const stream =
        streamRef.current ??
        (await navigator.mediaDevices.getUserMedia({ audio: true }));
      streamRef.current = stream;

      const mimeType = chooseMimeType();
      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);
      const segmentChunks: BlobPart[] = [];

      recorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          segmentChunks.push(event.data);
        }
      };

      recorder.onstop = () => {
        if (segmentChunks.length > 0) {
          const segmentMimeType = recorder.mimeType || mimeType || "audio/webm";
          segmentsRef.current.push(
            new Blob(segmentChunks, {
              type: segmentMimeType,
            }),
          );
        }
        recorderRef.current = null;
      };

      recorder.start();
      startTimer();
      setPhase("recording");
    } catch {
      cleanupRecorder();
      setPhase("error");
      setErrorMessage(
        "Microphone access was blocked. Please enable microphone permissions and try again.",
      );
    }
  }, [cleanupRecorder, phase, startTimer]);

  const stopSegment = useCallback(async () => {
    const recorder = recorderRef.current;
    if (!recorder || recorder.state !== "recording") return;

    stopTimer();
    await new Promise<void>((resolve) => {
      const handleStop = () => {
        recorder.removeEventListener("stop", handleStop);
        resolve();
      };
      recorder.addEventListener("stop", handleStop);
      recorder.stop();
    });
  }, [stopTimer]);

  const startNewRecording = useCallback(async () => {
    segmentsRef.current = [];
    setDurationSec(0);
    setErrorMessage("");
    setLatestBrief(null);
    setPhase("idle");
    await startSegment();
  }, [startSegment]);

  const stopRecording = useCallback(async () => {
    if (phase !== "recording") return;
    await stopSegment();
    setPhase("paused");
  }, [phase, stopSegment]);

  const resumeRecording = useCallback(async () => {
    if (phase !== "paused") return;
    await startSegment();
  }, [phase, startSegment]);

  const endRecording = useCallback(async () => {
    if (phase === "recording") {
      await stopSegment();
    }

    stopTimer();
    releaseStream();

    if (segmentsRef.current.length === 0) {
      setPhase("error");
      setErrorMessage("No audio was captured. Please record before ending.");
      return;
    }

    setPhase("ready");
  }, [phase, releaseStream, stopSegment, stopTimer]);

  const submitRecording = useCallback(async () => {
    if (segmentsRef.current.length === 0) return;

    setPhase("uploading");
    setErrorMessage("");

    try {
      const mimeType = segmentsRef.current[0]?.type || "audio/webm";
      const audioBlob = new Blob(segmentsRef.current, { type: mimeType });
      const brief = await uploadCheckin(audioBlob);
      setLatestBrief(brief);
      setPhase("saved");
    } catch {
      setPhase("error");
      setErrorMessage("Upload failed. Please try submitting again.");
    } finally {
      releaseStream();
    }
  }, [releaseStream]);

  return (
    <div className="min-h-screen bg-[#f5f1e8] px-4 py-8">
      <main className="mx-auto flex w-full max-w-md flex-col items-center gap-6">
        <div className="flex w-full items-center justify-between">
          <h1 className="text-5xl font-semibold tracking-tight text-slate-900">
            Sessional
          </h1>
          <SignOutButton />
        </div>

        <section className="w-full rounded-3xl bg-white px-6 py-8 shadow-sm">
          <div className="space-y-2 text-center">
            <h2 className="text-4xl font-semibold text-slate-900">
              Quick voice check-in
            </h2>
            <p className="text-2xl text-slate-700">
              Record your check-in. You can stop, resume, and submit when ready.
            </p>
          </div>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            {phase === "idle" || phase === "saved" || phase === "error" ? (
              <button
                type="button"
                onClick={startNewRecording}
                className="rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700"
              >
                {phase === "saved" ? "Record Another Check-in" : "Start Recording"}
              </button>
            ) : null}

            {phase === "recording" ? (
              <>
                <button
                  type="button"
                  onClick={stopRecording}
                  className="rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white hover:bg-slate-800"
                >
                  Stop Recording
                </button>
                <button
                  type="button"
                  onClick={endRecording}
                  className="rounded-xl border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-800 hover:bg-slate-50"
                >
                  End Recording
                </button>
              </>
            ) : null}

            {phase === "paused" ? (
              <>
                <button
                  type="button"
                  onClick={resumeRecording}
                  className="rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700"
                >
                  Resume Recording
                </button>
                <button
                  type="button"
                  onClick={endRecording}
                  className="rounded-xl border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-800 hover:bg-slate-50"
                >
                  End Recording
                </button>
              </>
            ) : null}

            {phase === "ready" ? (
              <>
                <button
                  type="button"
                  onClick={submitRecording}
                  className="rounded-xl bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700"
                >
                  Submit Check-in
                </button>
                <button
                  type="button"
                  onClick={startNewRecording}
                  className="rounded-xl border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-800 hover:bg-slate-50"
                >
                  Start Over
                </button>
              </>
            ) : null}
          </div>

          {phase === "recording" || phase === "paused" || phase === "ready" ? (
            <p className="mt-4 text-center text-sm text-slate-600">
              Recorded time: {formatDuration(durationSec)}
            </p>
          ) : null}

          {phase === "uploading" ? (
            <p className="mt-4 rounded-xl bg-blue-50 px-4 py-2 text-center text-sm text-blue-800">
              Uploading your check-in...
            </p>
          ) : null}

          {errorMessage ? (
            <p className="mt-4 rounded-xl bg-rose-50 px-4 py-2 text-center text-sm text-rose-700">
              {errorMessage}
            </p>
          ) : null}

          {latestBrief ? (
            <p className="mt-4 rounded-xl bg-emerald-50 px-4 py-2 text-center text-sm text-emerald-800">
              Check-in submitted successfully.
            </p>
          ) : null}
        </section>

        <p className="w-full rounded-2xl bg-white px-4 py-3 text-center text-xl text-slate-700 shadow-sm">
          Your check-in is shared only with your care team.
        </p>
      </main>
    </div>
  );
}
