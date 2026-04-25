from dataclasses import dataclass


@dataclass
class EmotionScore:
    name: str
    score: float


@dataclass
class UtteranceExtraction:
    timestamp: str
    transcript: str
    begin_seconds: float
    end_seconds: float
    duration_seconds: float
    top_emotions: list[EmotionScore]
    text_sentiment_score: float | None
    text_sentiment_label: str | None
