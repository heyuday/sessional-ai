import type { CheckinBrief } from "@/types/brief";
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
