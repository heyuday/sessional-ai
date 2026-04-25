import re
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, desc, select
from sqlalchemy.orm import Session

from ....db import get_db
from ....dependencies.auth import require_role
from ....models.audio_recording import AudioRecording
from ....models.user_account import UserAccount
from ....schemas.brief import DivergenceMoment
from ....schemas.clinician import PatientBrief, TranscriptItem, TrendItem

router = APIRouter(prefix="/briefs", tags=["briefs"])


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


def _risk_rank(risk_level: str) -> int:
    if risk_level == "Red":
        return 3
    if risk_level == "Yellow":
        return 2
    return 1


def _risk_trend_label(risk_level: str, risk_direction: str) -> str:
    if risk_direction == "up":
        return "Escalating"
    if risk_direction == "down":
        return "Improving"
    if risk_level == "Red":
        return "High-priority review"
    if risk_level == "Yellow":
        return "Monitor closely"
    return "Stable"


def _snapshot_summary(summary: str, key_themes: list[str]) -> str:
    trimmed = re.sub(r"\s+", " ", summary).strip()
    if not trimmed:
        if key_themes:
            return (
                "Recent check-in themes include "
                f"{', '.join(theme.lower() for theme in key_themes[:3])}."
            )
        return "No generated summary available yet."

    raw_sentences = [part.strip() for part in re.split(r"[.!?]", trimmed) if part.strip()]
    non_divergence_sentences = [
        sentence
        for sentence in raw_sentences
        if not re.search(r"\b(divergence|mismatch|prosody)\b", sentence, re.IGNORECASE)
    ]
    selected = non_divergence_sentences[:2] or raw_sentences[:2]

    if len(" ".join(selected)) < 140:
        source = non_divergence_sentences if non_divergence_sentences else raw_sentences
        for sentence in source[2:]:
            selected.append(sentence)
            if len(" ".join(selected)) >= 160:
                break

    snapshot = ". ".join(selected).strip()
    if snapshot and not snapshot.endswith("."):
        snapshot = f"{snapshot}."

    if key_themes:
        themes_line = ", ".join(theme.lower() for theme in key_themes[:3])
        snapshot = f"{snapshot} Key themes this week include {themes_line}."

    if len(snapshot) > 420:
        snapshot = snapshot[:417].rstrip()
        if not snapshot.endswith("."):
            snapshot = f"{snapshot}..."
    return snapshot


def _clinical_summary(
    summary: str,
    divergence_moments: list[DivergenceMoment],
) -> str:
    divergence_count = len(divergence_moments)
    if divergence_count == 0:
        return (
            f"{summary.strip()} No high-confidence semantic-versus-prosody divergence "
            "was detected in this recording."
        )
    return (
        f"{summary.strip()} "
        f"Observed {divergence_count} divergence moment(s) in this check-in."
    )


def _what_changed(
    divergence_moments: list[DivergenceMoment],
    key_themes: list[str],
) -> str:
    if not divergence_moments:
        return "No high-confidence semantic-versus-prosody divergence moments were extracted."
    strongest = sorted(
        divergence_moments,
        key=lambda moment: moment.confidence,
        reverse=True,
    )[0]
    theme_fragment = key_themes[0] if key_themes else "affective strain"
    return (
        f"Most salient mismatch at {strongest.timestamp} ({strongest.mismatch_label}). "
        f"Primary concern in this check-in: {theme_fragment}."
    )


def _opening_questions(
    key_themes: list[str],
    divergence_moments: list[DivergenceMoment],
) -> list[str]:
    questions: list[str] = []
    for theme in key_themes[:2]:
        questions.append(
            f"Ask patient to describe a recent situation where {theme.lower()} felt most intense."
        )
    for moment in divergence_moments[:1]:
        questions.append(
            f"Explore context around the {moment.timestamp} divergence marker and associated emotional load."
        )
    if not questions:
        questions = [
            "Ask patient to summarize mood shifts since the prior check-in.",
            "Identify one concrete stressor and one protective factor from this week.",
        ]
    return questions[:3]


def _divergence_count(recording: AudioRecording | None) -> int:
    if recording is None:
        return 0
    raw = recording.brief_divergence_moments or []
    return len([moment for moment in raw if isinstance(moment, dict)])


def _divergence_intensity(recording: AudioRecording | None) -> float:
    if recording is None:
        return 0.0
    weights = {"low": 1.0, "medium": 2.0, "high": 3.0}
    raw = recording.brief_divergence_moments or []
    weighted_scores: list[float] = []
    for moment in raw:
        if not isinstance(moment, dict):
            continue
        severity = str(moment.get("severity", "low")).lower()
        confidence = moment.get("confidence", 0.0)
        if not isinstance(confidence, int | float):
            confidence = 0.0
        weighted_scores.append(weights.get(severity, 1.0) * float(confidence))
    if not weighted_scores:
        return 0.0
    return round(sum(weighted_scores) / len(weighted_scores), 3)


def _trend_items(
    risk_level: str,
    current_recording: AudioRecording,
    previous_recording: AudioRecording | None,
) -> list[TrendItem]:
    prev_risk_level = previous_recording.brief_risk_level if previous_recording else None
    current_risk_rank = _risk_rank(risk_level)
    previous_risk_rank = _risk_rank(prev_risk_level) if prev_risk_level else current_risk_rank
    if current_risk_rank > previous_risk_rank:
        risk_direction = "up"
    elif current_risk_rank < previous_risk_rank:
        risk_direction = "down"
    else:
        risk_direction = "stable"

    current_count = _divergence_count(current_recording)
    previous_count = _divergence_count(previous_recording)
    if current_count > previous_count:
        frequency_direction = "up"
    elif current_count < previous_count:
        frequency_direction = "down"
    else:
        frequency_direction = "stable"

    current_intensity = _divergence_intensity(current_recording)
    previous_intensity = _divergence_intensity(previous_recording)
    if current_intensity > previous_intensity:
        intensity_direction = "up"
    elif current_intensity < previous_intensity:
        intensity_direction = "down"
    else:
        intensity_direction = "stable"

    return [
        TrendItem(label="Risk direction", direction=risk_direction),
        TrendItem(label="Divergence intensity trend", direction=intensity_direction),
        TrendItem(label="Divergence frequency trend", direction=frequency_direction),
    ]


def _build_patient_brief(
    recording: AudioRecording,
    patient: UserAccount,
    previous_recording: AudioRecording | None = None,
) -> PatientBrief:
    key_themes = recording.brief_key_themes or []
    raw_moments = recording.brief_divergence_moments or []
    divergence_moments = [
        DivergenceMoment.model_validate(moment) for moment in raw_moments if isinstance(moment, dict)
    ]
    base_summary = recording.brief_summary or "No generated summary available yet."
    summary = _snapshot_summary(base_summary, key_themes)
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
    trends = _trend_items(risk_level, recording, previous_recording)
    risk_direction = next(
        (trend.direction for trend in trends if trend.label == "Risk direction"),
        "stable",
    )
    trend = _risk_trend_label(risk_level, risk_direction)
    return PatientBrief(
        patient_id=patient.id,
        patient_name=patient.full_name or "Unknown Patient",
        assigned_clinician="Sessional Care Team",
        next_appointment="Not scheduled",
        last_checkin_label=_relative_label(created_at),
        risk_level=risk_level,
        trend_label=trend,
        summary=summary,
        clinical_summary=_clinical_summary(
            summary=base_summary,
            divergence_moments=divergence_moments,
        ),
        what_changed=_what_changed(divergence_moments, key_themes),
        key_themes=key_themes,
        opening_questions=_opening_questions(key_themes, divergence_moments),
        divergence_moments=divergence_moments,
        transcript=transcript,
        trends=trends,
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

    latest_by_patient: dict[str, list[AudioRecording]] = {}
    for recording in recordings:
        if not recording.patient_id:
            continue
        bucket = latest_by_patient.setdefault(recording.patient_id, [])
        if len(bucket) < 2:
            bucket.append(recording)

    if not latest_by_patient:
        return []

    patients = db.execute(
        select(UserAccount).where(UserAccount.id.in_(list(latest_by_patient.keys())))
    ).scalars().all()
    patient_map = {patient.id: patient for patient in patients}

    briefs: list[PatientBrief] = []
    for patient_id, patient_recordings in latest_by_patient.items():
        patient = patient_map.get(patient_id)
        if not patient:
            continue
        current = patient_recordings[0]
        previous = patient_recordings[1] if len(patient_recordings) > 1 else None
        briefs.append(_build_patient_brief(current, patient, previous))
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
    previous_recording = db.execute(
        select(AudioRecording)
        .where(AudioRecording.patient_id == patient_id)
        .where(AudioRecording.brief_summary.is_not(None))
        .where(AudioRecording.id != recording.id)
        .order_by(desc(AudioRecording.created_at))
        .limit(1)
    ).scalar_one_or_none()

    return _build_patient_brief(recording, patient, previous_recording)


@router.delete("/patients/{patient_id}/reports")
async def delete_patient_reports(
    patient_id: str,
    db: Session = Depends(get_db),
    _current_user: UserAccount = Depends(require_role("clinician")),
) -> dict[str, int]:
    patient = db.get(UserAccount, patient_id)
    if patient is None or patient.role != "patient":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found.")

    deleted = db.execute(
        delete(AudioRecording).where(AudioRecording.patient_id == patient_id)
    ).rowcount or 0
    db.commit()
    return {"deleted_reports": deleted}
