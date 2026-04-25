"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { SignOutButton } from "@/components/auth/sign-out-button";
import { RecordButton } from "@/components/patient/record-button";
import { StatusChips } from "@/components/patient/status-chips";
import { uploadCheckin } from "@/lib/api";
import type { CheckinBrief, RecordingStatus } from "@/types/brief";

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
  const padded = String(seconds).padStart(2, "0");
  return `00:${padded}`;
}

export function PatientCheckinPage() {
  const [status, setStatus] = useState<RecordingStatus>("idle");
  const [durationSec, setDurationSec] = useState(0);
  const [latestBrief, setLatestBrief] = useState<CheckinBrief | null>(null);
  const [errorMessage, setErrorMessage] = useState<string>("");

  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const timerRef = useRef<number | null>(null);

  const cleanupRecorder = useCallback(() => {
    if (timerRef.current) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    recorderRef.current = null;
  }, []);

  useEffect(() => {
    return () => cleanupRecorder();
  }, [cleanupRecorder]);

  const onStart = useCallback(async () => {
    if (status === "uploading" || status === "recording") return;

    try {
      setErrorMessage("");
      setLatestBrief(null);
      setDurationSec(0);
      setStatus("recording");

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mimeType = chooseMimeType();
      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);

      recorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.start();

      timerRef.current = window.setInterval(() => {
        setDurationSec((current) => current + 1);
      }, 1000);
    } catch {
      cleanupRecorder();
      setStatus("error");
      setErrorMessage(
        "Microphone access was blocked. Please enable microphone permissions and try again.",
      );
    }
  }, [cleanupRecorder, status]);

  const onStop = useCallback(() => {
    if (!recorderRef.current || recorderRef.current.state !== "recording") {
      return;
    }

    setStatus("uploading");

    recorderRef.current.onstop = async () => {
      try {
        const mime = recorderRef.current?.mimeType || "audio/webm";
        const audioBlob = new Blob(chunksRef.current, { type: mime });
        const brief = await uploadCheckin(audioBlob);

        setLatestBrief(brief);
        setStatus("saved");
      } catch {
        setStatus("error");
        setErrorMessage("Upload failed. Please try recording again.");
      } finally {
        cleanupRecorder();
      }
    };

    recorderRef.current.stop();
  }, [cleanupRecorder]);

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
              Share how you are feeling in your own words.
            </p>
          </div>

          <div className="mt-8 flex justify-center">
            <RecordButton
              isRecording={status === "recording"}
              disabled={status === "uploading"}
              onStart={onStart}
              onStop={onStop}
            />
          </div>

          <div className="mt-8">
            <StatusChips
              status={status}
              recordingDurationLabel={formatDuration(durationSec)}
            />
          </div>

          {errorMessage ? (
            <p className="mt-4 rounded-xl bg-rose-50 px-4 py-2 text-center text-sm text-rose-700">
              {errorMessage}
            </p>
          ) : null}

          {latestBrief ? (
            <p className="mt-4 rounded-xl bg-emerald-50 px-4 py-2 text-center text-sm text-emerald-800">
              Check-in saved. Risk level: {latestBrief.risk_level}.
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
