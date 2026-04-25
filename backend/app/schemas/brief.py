from pydantic import BaseModel, Field


class DivergenceMoment(BaseModel):
    timestamp: str = Field(..., examples=["14:32"])
    transcript_snippet: str
    mismatch_label: str
    severity: str = Field(..., pattern="^(low|medium|high)$")
    confidence: float = Field(..., ge=0, le=1)


class CheckinBrief(BaseModel):
    risk_level: str = Field(..., pattern="^(Green|Yellow|Red)$")
    key_themes: list[str]
    divergence_moments: list[DivergenceMoment]
    summary: str
