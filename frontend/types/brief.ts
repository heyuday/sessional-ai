export type RiskLevel = "Green" | "Yellow" | "Red";

export type RecordingStatus =
  | "idle"
  | "recording"
  | "uploading"
  | "saved"
  | "error";

export interface DivergenceMoment {
  timestamp: string;
  transcript_snippet: string;
  mismatch_label: string;
  severity: "low" | "medium" | "high";
  confidence: number;
}

export interface CheckinBrief {
  risk_level: RiskLevel;
  key_themes: string[];
  divergence_moments: DivergenceMoment[];
  summary: string;
}
