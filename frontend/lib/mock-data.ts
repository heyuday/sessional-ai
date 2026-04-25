import type { PatientBrief } from "@/types/clinician";

export const MOCK_PATIENT_BRIEFS: PatientBrief[] = [
  {
    patient_id: "SC12345",
    patient_name: "Sarah Chen",
    assigned_clinician: "Dr. Elias Vance",
    next_appointment: "Oct 26, 2024, 10:00 AM",
    last_checkin_label: "2h ago",
    risk_level: "Red",
    trend_label: "Rising tension",
    summary:
      "Increased acute anxiety and cognitive dissonance related to treatment plan changes.",
    what_changed:
      "Anxiety markers and mismatch events increased compared with the prior check-in.",
    key_themes: [
      "Treatment Plan Anxiety",
      "Cognitive Mismatch",
      "Past Trauma Re-triggering",
    ],
    opening_questions: [
      "How have the new recommendations been for you?",
      "Notice anything unexpected?",
      "Revisit recent discussions?",
    ],
    divergence_moments: [
      {
        timestamp: "14:32",
        transcript_snippet: "I've been feeling okay overall.",
        mismatch_label: "Neutral words, elevated vocal stress",
        severity: "high",
        confidence: 0.92,
      },
      {
        timestamp: "16:17",
        transcript_snippet: "The medication is not helping.",
        mismatch_label: "Flat text, anxious tense prosody",
        severity: "high",
        confidence: 0.92,
      },
      {
        timestamp: "16:15",
        transcript_snippet: "That happens sometimes.",
        mismatch_label: "Minimizing language, distress markers",
        severity: "medium",
        confidence: 0.86,
      },
    ],
    transcript: [
      { timestamp: "0:02", speaker: "P", text: "I've been feeling...", affect: "Stressed" },
      { timestamp: "0:06", speaker: "C", text: "Tell me more.", affect: "Calm" },
      {
        timestamp: "0:10",
        speaker: "P",
        text: "The medication is not helping...",
        affect: "Anxious, Tense Prosody",
      },
      {
        timestamp: "0:15",
        speaker: "P",
        text: "I've no way near anxiety.",
        affect: "Tense Prosody",
      },
    ],
    trends: [
      { label: "Risk direction", direction: "up" },
      { label: "Divergence intensity trend", direction: "up" },
      { label: "Divergence frequency trend", direction: "up" },
    ],
  },
  {
    patient_id: "MN38920",
    patient_name: "Mia Navarro",
    assigned_clinician: "Dr. Elias Vance",
    next_appointment: "Oct 27, 2024, 2:30 PM",
    last_checkin_label: "1d ago",
    risk_level: "Yellow",
    trend_label: "Stable",
    summary: "Moderate stress around sleep and work pressure; no escalation markers.",
    what_changed: "Sleep disruption is recurring but less severe than last week.",
    key_themes: ["Sleep disruption", "Work stress", "Social fatigue"],
    opening_questions: [
      "How has your sleep been in the last two nights?",
      "What helped you cope this week?",
    ],
    divergence_moments: [
      {
        timestamp: "08:10",
        transcript_snippet: "I'm handling things okay.",
        mismatch_label: "Positive statement, strained vocal profile",
        severity: "medium",
        confidence: 0.74,
      },
    ],
    transcript: [
      { timestamp: "0:04", speaker: "P", text: "I'm handling things...", affect: "Tired" },
    ],
    trends: [
      { label: "Risk direction", direction: "stable" },
      { label: "Divergence intensity trend", direction: "down" },
      { label: "Divergence frequency trend", direction: "stable" },
    ],
  },
];

export function getPatientBrief(patientId: string): PatientBrief | undefined {
  return MOCK_PATIENT_BRIEFS.find((brief) => brief.patient_id === patientId);
}
