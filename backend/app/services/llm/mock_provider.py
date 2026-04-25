from ...schemas.brief import CheckinBrief
from ..models import UtteranceExtraction
from .base import BriefLLMProvider


class MockLLMProvider(BriefLLMProvider):
    async def generate_brief(self, utterances: list[UtteranceExtraction]) -> CheckinBrief:
        _ = utterances
        return CheckinBrief(
            risk_level="Yellow",
            summary="Patient reports being okay, but voice affect suggests elevated baseline anxiety.",
            key_themes=["Sleep disruption", "Work stress", "Emotional suppression"],
            divergence_moments=[
                {
                    "timestamp": "00:14",
                    "transcript_snippet": "I think everything has been okay this week.",
                    "mismatch_label": "Neutral-positive wording with high distress prosody",
                    "severity": "high",
                    "confidence": 0.9,
                }
            ],
        )
