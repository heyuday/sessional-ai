from app.services.divergence_service import build_divergence_context
from app.services.models import EmotionScore, UtteranceExtraction


def _utterance(
    *,
    transcript: str,
    timestamp: str,
    sentiment: float | None,
    emotions: list[tuple[str, float]],
) -> UtteranceExtraction:
    return UtteranceExtraction(
        timestamp=timestamp,
        transcript=transcript,
        begin_seconds=0.0,
        end_seconds=2.0,
        duration_seconds=2.0,
        top_emotions=[EmotionScore(name=name, score=score) for name, score in emotions],
        text_sentiment_score=sentiment,
        text_sentiment_label=None,
    )


def test_build_divergence_context_uses_semantic_and_prosody_evidence() -> None:
    utterances = [
        _utterance(
            transcript="I'm fine.",
            timestamp="00:01",
            sentiment=6.4,
            emotions=[("Distress", 0.8), ("Calmness", 0.2)],
        ),
        _utterance(
            transcript="I feel low today.",
            timestamp="00:05",
            sentiment=2.2,
            emotions=[("Sadness", 0.79), ("Calmness", 0.1)],
        ),
        _utterance(
            transcript="Work was manageable.",
            timestamp="00:09",
            sentiment=5.7,
            emotions=[("Calmness", 0.7), ("Joy", 0.6)],
        ),
    ]

    context = build_divergence_context(utterances)
    assert context["utterance_count"] == 3
    assert context["utterances_with_semantic_sentiment"] == 3
    assert context["negative_prosody_utterance_count"] == 2
    assert context["candidate_divergence_count"] == 1
    assert context["candidate_divergence_ratio"] == round(1 / 3, 3)
