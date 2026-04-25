from app.schemas.brief import CheckinBrief
from app.services.llm.gemini_provider import _repair_brief_with_evidence
from app.services.models import EmotionScore, UtteranceExtraction


def test_repair_brief_drops_unsupported_divergence_snippets() -> None:
    utterances = [
        UtteranceExtraction(
            timestamp="00:01",
            transcript="I'm doing fine.",
            begin_seconds=1.0,
            end_seconds=3.0,
            duration_seconds=2.0,
            top_emotions=[EmotionScore(name="Distress", score=0.8)],
            text_sentiment_score=6.5,
            text_sentiment_label="positive",
        )
    ]
    context = {
        "candidate_divergence_ratio": 1.0,
    }
    brief = CheckinBrief.model_validate(
        {
            "risk_level": "Yellow",
            "key_themes": ["Stress", "Stress", "  "],
            "summary": "Likely bipolar episode.",
            "divergence_moments": [
                {
                    "timestamp": "00:01",
                    "transcript_snippet": "I'm doing fine.",
                    "mismatch_label": "positive words with distress prosody",
                    "severity": "high",
                    "confidence": 0.9,
                },
                {
                    "timestamp": "00:04",
                    "transcript_snippet": "Unsupported line",
                    "mismatch_label": "made up",
                    "severity": "medium",
                    "confidence": 0.6,
                },
            ],
        }
    )

    repaired = _repair_brief_with_evidence(brief, utterances, context)
    assert repaired.key_themes == ["Stress"]
    assert len(repaired.divergence_moments) == 1
    assert repaired.divergence_moments[0].transcript_snippet == "I'm doing fine."
    assert "bipolar" not in repaired.summary.lower()


def test_repair_brief_expands_fragmented_divergence_snippet() -> None:
    utterances = [
        UtteranceExtraction(
            timestamp="00:35",
            transcript="I might need to take a short break because the workload feels heavy.",
            begin_seconds=35.0,
            end_seconds=41.0,
            duration_seconds=6.0,
            top_emotions=[EmotionScore(name="Distress", score=0.86)],
            text_sentiment_score=5.2,
            text_sentiment_label="neutral",
        )
    ]
    brief = CheckinBrief.model_validate(
        {
            "risk_level": "Yellow",
            "key_themes": ["Workload stress"],
            "summary": "Patient reports strain related to school workload.",
            "divergence_moments": [
                {
                    "timestamp": "00:35",
                    "transcript_snippet": "I might need",
                    "mismatch_label": "Divergence",
                    "severity": "high",
                    "confidence": 0.82,
                }
            ],
        }
    )

    repaired = _repair_brief_with_evidence(brief, utterances, {"candidate_divergence_ratio": 1.0})
    assert repaired.divergence_moments[0].transcript_snippet == utterances[0].transcript
