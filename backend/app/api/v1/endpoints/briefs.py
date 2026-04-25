from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ....db import get_db
from ....dependencies.auth import require_role
from ....models.audio_recording import AudioRecording
from ....models.user_account import UserAccount
from ....schemas.brief import DivergenceMoment
from ....schemas.clinician import PatientBrief, TranscriptItem, TrendItem

router = APIRouter(prefix="/briefs", tags=["briefs"])


def _patient_name(email: str) -> str:
    left = email.split("@", maxsplit=1)[0]
    return " ".join(part.capitalize() for part in left.replace("_", " ").replace(".", " ").split())


def _relative_label(created_at: datetime) -> str:
    now = datetime.now(UTC)
    age = now - created_at.astimezone(UTC)
    minutes = int(age.total_seconds() // 60)
    if minutes < 60:
        return f"{max(1, minutes)}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    return f"{hours // 24}d ago"


def _risk_trend_label(risk_level: str) -> str:
    if risk_level == "Red":
        return "High-priority review"
    if risk_level == "Yellow":
        return "Monitor closely"
    return "Stable"


def _build_patient_brief(recording: AudioRecording, patient: UserAccount) -> PatientBrief:
    key_themes = recording.brief_key_themes or []
    raw_moments = recording.brief_divergence_moments or []
    divergence_moments = [
        DivergenceMoment.model_validate(moment) for moment in raw_moments if isinstance(moment, dict)
    ]
    summary = recording.brief_summary or "No generated summary available yet."
    risk_level = recording.brief_risk_level or "Yellow"
    created_at = recording.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)

    transcript: list[TranscriptItem] = [
        TranscriptItem(
            timestamp=moment.timestamp,
            speaker="P",
            text=moment.transcript_snippet,
            affect=moment.mismatch_label,
        )
        for moment in divergence_moments
    ]
    if not transcript:
        transcript = [
            TranscriptItem(
                timestamp="00:00",
                speaker="P",
                text=summary,
                affect="Neutral",
            )
        ]

    trend = _risk_trend_label(risk_level)
    return PatientBrief(
        patient_id=patient.id,
        patient_name=_patient_name(patient.email),
        assigned_clinician="Sessional Care Team",
        next_appointment="Not scheduled",
        last_checkin_label=_relative_label(created_at),
        risk_level=risk_level,
        trend_label=trend,
        summary=summary,
        what_changed="Most recent AI brief from latest voice check-in.",
        key_themes=key_themes,
        opening_questions=[
            "How have you been since this check-in?",
            "What felt most difficult this week?",
        ],
        divergence_moments=divergence_moments,
        transcript=transcript,
        trends=[
            TrendItem(label="Risk direction", direction="stable"),
            TrendItem(label="Divergence intensity trend", direction="stable"),
            TrendItem(label="Divergence frequency trend", direction="stable"),
        ],
    )


@router.get("/patients", response_model=list[PatientBrief])
async def list_patient_briefs(
    db: Session = Depends(get_db),
    _current_user: UserAccount = Depends(require_role("clinician")),
) -> list[PatientBrief]:
    recordings = db.execute(
        select(AudioRecording)
        .where(AudioRecording.patient_id.is_not(None))
        .where(AudioRecording.brief_summary.is_not(None))
        .order_by(desc(AudioRecording.created_at))
    ).scalars().all()

    latest_by_patient: dict[str, AudioRecording] = {}
    for recording in recordings:
        if not recording.patient_id:
            continue
        if recording.patient_id not in latest_by_patient:
            latest_by_patient[recording.patient_id] = recording

    if not latest_by_patient:
        return []

    patients = db.execute(
        select(UserAccount).where(UserAccount.id.in_(list(latest_by_patient.keys())))
    ).scalars().all()
    patient_map = {patient.id: patient for patient in patients}

    briefs: list[PatientBrief] = []
    for patient_id, recording in latest_by_patient.items():
        patient = patient_map.get(patient_id)
        if not patient:
            continue
        briefs.append(_build_patient_brief(recording, patient))
    return briefs


@router.get("/patients/{patient_id}", response_model=PatientBrief)
async def get_patient_brief(
    patient_id: str,
    db: Session = Depends(get_db),
    _current_user: UserAccount = Depends(require_role("clinician")),
) -> PatientBrief:
    patient = db.get(UserAccount, patient_id)
    if patient is None or patient.role != "patient":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found.")

    recording = db.execute(
        select(AudioRecording)
        .where(AudioRecording.patient_id == patient_id)
        .where(AudioRecording.brief_summary.is_not(None))
        .order_by(desc(AudioRecording.created_at))
        .limit(1)
    ).scalar_one_or_none()
    if recording is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No brief found for patient.")

    return _build_patient_brief(recording, patient)
