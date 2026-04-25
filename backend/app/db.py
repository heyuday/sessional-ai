from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from .core.config import settings
from .models import Base

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                ALTER TABLE audio_recordings
                ADD COLUMN IF NOT EXISTS patient_id VARCHAR(36)
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE audio_recordings
                ADD COLUMN IF NOT EXISTS brief_risk_level VARCHAR(16)
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE audio_recordings
                ADD COLUMN IF NOT EXISTS brief_summary VARCHAR(2000)
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE audio_recordings
                ADD COLUMN IF NOT EXISTS brief_key_themes JSON
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE audio_recordings
                ADD COLUMN IF NOT EXISTS brief_divergence_moments JSON
                """
            )
        )
