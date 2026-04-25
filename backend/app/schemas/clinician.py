from pydantic import BaseModel

from .brief import DivergenceMoment


class TranscriptItem(BaseModel):
    timestamp: str
    speaker: str
    text: str
    affect: str


class TrendItem(BaseModel):
    label: str
    direction: str


class PatientBrief(BaseModel):
    patient_id: str
    patient_name: str
    assigned_clinician: str
    next_appointment: str
    last_checkin_label: str
    risk_level: str
    trend_label: str
    summary: str
    clinical_summary: str
    what_changed: str
    key_themes: list[str]
    opening_questions: list[str]
    divergence_moments: list[DivergenceMoment]
    transcript: list[TranscriptItem]
    trends: list[TrendItem]
