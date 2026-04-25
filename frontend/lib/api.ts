import type { CheckinBrief } from "@/types/brief";
import type { PatientBrief } from "@/types/clinician";
import { getAuthTokenFromCookie } from "@/lib/auth";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function inferExtension(mimeType: string): string {
  if (mimeType.includes("mp4")) return "m4a";
  if (mimeType.includes("wav")) return "wav";
  return "webm";
}

export async function uploadCheckin(audioBlob: Blob): Promise<CheckinBrief> {
  const extension = inferExtension(audioBlob.type);
  const fileName = `checkin-${Date.now()}.${extension}`;
  const formData = new FormData();
  formData.append("file", audioBlob, fileName);

  const token = getAuthTokenFromCookie();
  const response = await fetch(`${API_BASE_URL}/api/v1/checkins/upload`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Upload failed with status ${response.status}`);
  }

  return (await response.json()) as CheckinBrief;
}

function authHeaders(): HeadersInit | undefined {
  const token = getAuthTokenFromCookie();
  if (!token) return undefined;
  return { Authorization: `Bearer ${token}` };
}

export async function getClinicianBriefs(): Promise<PatientBrief[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/briefs/patients`, {
    method: "GET",
    headers: authHeaders(),
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch clinician briefs: ${response.status}`);
  }
  return (await response.json()) as PatientBrief[];
}

export async function getClinicianBrief(patientId: string): Promise<PatientBrief> {
  const response = await fetch(`${API_BASE_URL}/api/v1/briefs/patients/${patientId}`, {
    method: "GET",
    headers: authHeaders(),
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch patient brief: ${response.status}`);
  }
  return (await response.json()) as PatientBrief;
}

export async function deleteClinicianPatientReports(
  patientId: string,
): Promise<{ deleted_reports: number }> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/briefs/patients/${patientId}/reports`,
    {
      method: "DELETE",
      headers: authHeaders(),
    },
  );
  if (!response.ok) {
    throw new Error(`Failed to delete patient reports: ${response.status}`);
  }
  return (await response.json()) as { deleted_reports: number };
}
