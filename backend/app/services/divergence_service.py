from .models import UtteranceExtraction


def build_divergence_context(utterances: list[UtteranceExtraction]) -> dict:
    """Build compact signal summary to pass into LLM prompt."""
    high_distress = 0
    for utterance in utterances:
        if any(emotion.score >= 0.65 for emotion in utterance.top_emotions):
            high_distress += 1

    return {
        "utterance_count": len(utterances),
        "high_distress_utterance_count": high_distress,
        "high_distress_ratio": round(high_distress / max(1, len(utterances)), 3),
    }
