from datetime import timezone

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

router = APIRouter(prefix="/checkins", tags=["checkins"])


@router.post("/upload", response_model=UploadCheckinResponse)
async def upload_checkin(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _current_user: UserAccount = Depends(require_role("patient")),
) -> UploadCheckinResponse:
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

    try:
        recording = AudioRecording(
            file_name=file.filename,
            mime_type=file.content_type or "application/octet-stream",
            size_bytes=len(contents),
            audio_data=contents,
            processing_status="pending",
        )
        db.add(recording)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to persist audio in local PostgreSQL.",
        ) from exc

    return UploadCheckinResponse(
        risk_level="Yellow",
        summary="Moderate stress markers with notable vocal tension in mismatch segments.",
        key_themes=["Sleep disruption", "Work stress", "Treatment uncertainty"],
        divergence_moments=[
            {
                "timestamp": "14:32",
                "transcript_snippet": "I've been okay overall.",
                "mismatch_label": "Neutral semantics with elevated vocal stress",
                "severity": "high",
                "confidence": 0.92,
            },
            {
                "timestamp": "16:17",
                "transcript_snippet": "It has been manageable.",
                "mismatch_label": "Positive framing with anxious prosody",
                "severity": "medium",
                "confidence": 0.85,
            },
        ],
    )


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
