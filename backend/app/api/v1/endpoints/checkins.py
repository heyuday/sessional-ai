import logging
from datetime import timezone
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ....db import get_db
from ....dependencies.auth import require_role
from ....models.audio_recording import AudioRecording
from ....models.user_account import UserAccount
from ....schemas.checkin import StoredAudioMetadata, UploadCheckinResponse
from ....services.hume_service import extract_utterances
from ....services.synthesis_service import generate_brief

router = APIRouter(prefix="/checkins", tags=["checkins"])


def _fallback_brief() -> UploadCheckinResponse:
    return UploadCheckinResponse(
        risk_level="Yellow",
        summary=(
            "Your recording was saved, but real-time analysis is temporarily unavailable. "
            "Please retry later for a fully generated brief."
        ),
        key_themes=["Analysis pending retry"],
        divergence_moments=[],
    )


@router.post("/upload", response_model=UploadCheckinResponse)
async def upload_checkin(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserAccount = Depends(require_role("patient")),
) -> UploadCheckinResponse:
    logger = logging.getLogger(__name__)
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name is required.",
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    logger.info(
        "Upload received: file_name=%s mime_type=%s size_bytes=%s",
        file.filename,
        file.content_type or "application/octet-stream",
        len(contents),
    )
    try:
        recording = AudioRecording(
            file_name=file.filename,
            mime_type=file.content_type or "application/octet-stream",
            size_bytes=len(contents),
            audio_data=contents,
            patient_id=current_user.id,
            processing_status="pending",
        )
        db.add(recording)
        db.commit()
        db.refresh(recording)
        logger.info("Recording persisted: recording_id=%s status=%s", recording.id, recording.processing_status)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to persist audio in local PostgreSQL.",
        ) from exc

    try:
        recording.processing_status = "processing"
        db.commit()
        logger.info("Recording processing started: recording_id=%s", recording.id)

        utterances = await extract_utterances(
            audio_bytes=contents,
            mime_type=file.content_type or "application/octet-stream",
        )
        logger.info("Hume utterances extracted: recording_id=%s utterances=%s", recording.id, len(utterances))
        brief = await generate_brief(utterances)
        logger.info(
            "Brief generated: recording_id=%s risk_level=%s divergence_moments=%s",
            recording.id,
            brief.risk_level,
            len(brief.divergence_moments),
        )
        recording.brief_risk_level = brief.risk_level
        recording.brief_summary = brief.summary
        recording.brief_key_themes = brief.key_themes
        recording.brief_divergence_moments = [
            moment.model_dump() for moment in brief.divergence_moments
        ]

        recording.processing_status = "processed"
        recording.processed_at = datetime.now(UTC)
        db.commit()
        logger.info("Recording processing completed: recording_id=%s status=%s", recording.id, recording.processing_status)
    except RuntimeError as exc:
        db.rollback()
        logging.warning("Check-in processing fallback triggered: %s", exc)
        try:
            fallback = _fallback_brief()
            recording.processing_status = "processed_fallback"
            recording.processed_at = datetime.now(UTC)
            recording.brief_risk_level = fallback.risk_level
            recording.brief_summary = fallback.summary
            recording.brief_key_themes = fallback.key_themes
            recording.brief_divergence_moments = [
                moment.model_dump() for moment in fallback.divergence_moments
            ]
            db.commit()
            logger.info("Recording fallback saved: recording_id=%s status=%s", recording.id, recording.processing_status)
        except SQLAlchemyError:
            db.rollback()
        return fallback
    except SQLAlchemyError as exc:
        db.rollback()
        try:
            recording.processing_status = "failed"
            db.commit()
        except SQLAlchemyError:
            db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to process upload: {exc}",
        ) from exc

    return UploadCheckinResponse.model_validate(brief.model_dump())


@router.get("/storage/latest", response_model=StoredAudioMetadata)
async def get_latest_stored_audio(
    db: Session = Depends(get_db),
    _current_user: UserAccount = Depends(require_role("clinician")),
) -> StoredAudioMetadata:
    try:
        latest = db.execute(
            select(AudioRecording).order_by(desc(AudioRecording.created_at)).limit(1)
        ).scalar_one_or_none()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to query local PostgreSQL.",
        ) from exc

    if latest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No stored audio found.",
        )

    created_at = latest.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    return StoredAudioMetadata(
        id=latest.id,
        file_name=latest.file_name,
        mime_type=latest.mime_type,
        size_bytes=latest.size_bytes,
        processing_status=latest.processing_status,
        created_at=created_at.isoformat(),
    )


@router.get("/storage/{recording_id}/download")
async def download_stored_audio(
    recording_id: str,
    db: Session = Depends(get_db),
    _current_user: UserAccount = Depends(require_role("clinician")),
) -> StreamingResponse:
    try:
        recording = db.get(AudioRecording, recording_id)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to query local PostgreSQL.",
        ) from exc

    if recording is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found.",
        )

    return StreamingResponse(
        content=iter([recording.audio_data]),
        media_type=recording.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{recording.file_name}"',
        },
    )
