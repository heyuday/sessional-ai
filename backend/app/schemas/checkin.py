from pydantic import BaseModel

from .brief import CheckinBrief


class UploadCheckinResponse(CheckinBrief):
    pass


class StoredAudioMetadata(BaseModel):
    id: str
    file_name: str
    mime_type: str
    size_bytes: int
    processing_status: str
    created_at: str
