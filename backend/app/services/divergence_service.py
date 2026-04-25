from .models import UtteranceExtraction

NEGATIVE_VALENCE_EMOTIONS = {
    "anxiety",
    "distress",
    "fear",
    "sadness",
    "shame",
    "guilt",
    "disappointment",
    "pain",
    "awkwardness",
    "horror",
    "despair",
}


def _prosody_distress_score(utterance: UtteranceExtraction) -> float:
    negative_scores = [
        emotion.score
        for emotion in utterance.top_emotions
        if emotion.name.lower() in NEGATIVE_VALENCE_EMOTIONS
    ]
    if not negative_scores:
        return 0.0
    return round(max(negative_scores), 3)


def _semantic_bucket(sentiment_score: float | None) -> str:
    if sentiment_score is None:
        return "unknown"
    if sentiment_score >= 6.0:
        return "positive"
    if sentiment_score <= 4.0:
        return "negative"
    return "neutral"


def build_divergence_context(utterances: list[UtteranceExtraction]) -> dict:
    """Build grounded semantic-vs-prosody evidence summary."""
    candidate_divergence = 0
    prosody_negative = 0
    sentiment_available = 0
    evidence_rows: list[dict] = []

    for utterance in utterances:
        distress_score = _prosody_distress_score(utterance)
        semantic_bucket = _semantic_bucket(utterance.text_sentiment_score)
        if utterance.text_sentiment_score is not None:
            sentiment_available += 1
        if distress_score >= 0.65:
            prosody_negative += 1

        is_candidate = semantic_bucket in {"neutral", "positive"} and distress_score >= 0.65
        if is_candidate:
            candidate_divergence += 1

        evidence_rows.append(
            {
                "timestamp": utterance.timestamp,
                "transcript": utterance.transcript,
                "semantic_sentiment_score": utterance.text_sentiment_score,
                "semantic_sentiment_bucket": semantic_bucket,
                "prosody_distress_score": distress_score,
                "duration_seconds": round(utterance.duration_seconds, 2),
                "candidate_divergence": is_candidate,
                "top_emotions": [
                    {"name": emotion.name, "score": round(emotion.score, 3)}
                    for emotion in utterance.top_emotions
                ],
            }
        )

    return {
        "utterance_count": len(utterances),
        "utterances_with_semantic_sentiment": sentiment_available,
        "negative_prosody_utterance_count": prosody_negative,
        "negative_prosody_ratio": round(prosody_negative / max(1, len(utterances)), 3),
        "candidate_divergence_count": candidate_divergence,
        "candidate_divergence_ratio": round(candidate_divergence / max(1, len(utterances)), 3),
        "evidence_rows": evidence_rows,
    }
