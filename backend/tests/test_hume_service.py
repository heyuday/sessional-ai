from app.services.hume_service import _normalize_utterances


def test_normalize_utterances_includes_language_sentiment_and_duration() -> None:
    payload = [
        {
            "results": {
                "predictions": [
                    {
                        "models": {
                            "prosody": {
                                "grouped_predictions": [
                                    {
                                        "predictions": [
                                            {
                                                "text": "I am doing fine.",
                                                "time": {"begin": 1.0, "end": 3.5},
                                                "emotions": [
                                                    {"name": "Distress", "score": 0.81},
                                                    {"name": "Anxiety", "score": 0.74},
                                                    {"name": "Sadness", "score": 0.44},
                                                    {"name": "Fear", "score": 0.33},
                                                    {"name": "Calmness", "score": 0.22},
                                                    {"name": "Joy", "score": 0.2},
                                                    {"name": "Awe", "score": 0.19},
                                                ],
                                            }
                                        ]
                                    }
                                ]
                            },
                            "language": {
                                "grouped_predictions": [
                                    {
                                        "predictions": [
                                            {
                                                "text": "I am doing fine.",
                                                "time": {"begin": 1.0, "end": 3.5},
                                                "sentiment": [
                                                    {"name": "1", "score": 0.0},
                                                    {"name": "5", "score": 0.3},
                                                    {"name": "7", "score": 0.7},
                                                ],
                                            }
                                        ]
                                    }
                                ]
                            },
                        }
                    }
                ]
            }
        }
    ]

    utterances = _normalize_utterances(payload)
    assert len(utterances) == 1
    utterance = utterances[0]
    assert utterance.timestamp == "00:01"
    assert utterance.begin_seconds == 1.0
    assert utterance.end_seconds == 3.5
    assert utterance.duration_seconds == 2.5
    assert len(utterance.top_emotions) == 6
    assert utterance.top_emotions[0].name == "Distress"
    assert utterance.text_sentiment_score is not None
    assert utterance.text_sentiment_score > 6
    assert utterance.text_sentiment_label == "positive"
