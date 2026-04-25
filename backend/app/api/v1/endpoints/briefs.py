from fastapi import APIRouter
from fastapi import Depends

from ....dependencies.auth import require_role
from ....models.user_account import UserAccount
from ....schemas.brief import CheckinBrief

router = APIRouter(prefix="/briefs", tags=["briefs"])


@router.get("/{patient_id}", response_model=CheckinBrief)
async def get_patient_brief(
    patient_id: str,
    _current_user: UserAccount = Depends(require_role("clinician")),
) -> CheckinBrief:
    return CheckinBrief(
        risk_level="Red" if patient_id == "SC12345" else "Yellow",
        summary="Patient continues to exhibit semantic-prosodic divergence in key moments.",
        key_themes=["Cognitive mismatch", "Treatment anxiety", "Social withdrawal"],
        divergence_moments=[
            {
                "timestamp": "14:32",
                "transcript_snippet": "I'm doing fine.",
                "mismatch_label": "Positive wording with high vocal tension",
                "severity": "high",
                "confidence": 0.91,
            }
        ],
    )
