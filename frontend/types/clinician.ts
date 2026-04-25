import type { DivergenceMoment, RiskLevel } from "@/types/brief";

export interface TranscriptItem {
  timestamp: string;
  speaker: "P" | "C";
  text: string;
  affect: string;
}

export interface TrendItem {
  label: string;
  direction: "up" | "stable" | "down";
}

export interface PatientBrief {
  patient_id: string;
  patient_name: string;
  assigned_clinician: string;
  next_appointment: string;
  last_checkin_label: string;
  risk_level: RiskLevel;
  trend_label: string;
  summary: string;
  clinical_summary: string;
  what_changed: string;
  key_themes: string[];
  opening_questions: string[];
  divergence_moments: DivergenceMoment[];
  transcript: TranscriptItem[];
  trends: TrendItem[];
}
