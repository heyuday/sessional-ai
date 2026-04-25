import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, LargeBinary, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AudioRecording(Base):
    __tablename__ = "audio_recordings"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    file_name: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(128))
    size_bytes: Mapped[int] = mapped_column(Integer)
    audio_data: Mapped[bytes] = mapped_column(LargeBinary)
    patient_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    processing_status: Mapped[str] = mapped_column(String(32), default="pending")
    brief_risk_level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    brief_summary: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    brief_key_themes: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    brief_divergence_moments: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
