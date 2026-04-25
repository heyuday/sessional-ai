from dataclasses import dataclass


@dataclass
class EmotionScore:
    name: str
    score: float


@dataclass
class UtteranceExtraction:
    timestamp: str
    transcript: str
    top_emotions: list[EmotionScore]
