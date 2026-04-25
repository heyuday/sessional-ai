import json
import logging
import time

import httpx

from ...core.config import settings
from ...schemas.brief import CheckinBrief
from ..divergence_service import build_divergence_context
from ..models import UtteranceExtraction
from .base import BriefLLMProvider

logger = logging.getLogger(__name__)


def _build_prompt(utterances: list[UtteranceExtraction]) -> str:
    rows = []
    for utterance in utterances:
        emotions = ", ".join([f"{emotion.name}:{emotion.score:.2f}" for emotion in utterance.top_emotions])
        rows.append(
            {
                "timestamp": utterance.timestamp,
                "transcript": utterance.transcript,
                "top_emotions": emotions,
            }
        )

    context = build_divergence_context(utterances)
    return (
        "You are a clinical-support AI that summarizes asynchronous patient voice check-ins.\n"
        "Use only the provided utterance transcript and acoustic emotion evidence.\n"
        "Detect divergence moments where text sounds neutral/positive but prosody indicates distress.\n"
        "Do not diagnose. Keep language concise and clinical.\n\n"
        f"Signal summary: {json.dumps(context)}\n"
        f"Utterances: {json.dumps(rows)}"
    )


def _gemini_schema() -> dict:
    return {
        "type": "OBJECT",
        "properties": {
            "risk_level": {"type": "STRING", "enum": ["Green", "Yellow", "Red"]},
            "key_themes": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
            },
            "divergence_moments": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "timestamp": {"type": "STRING"},
                        "transcript_snippet": {"type": "STRING"},
                        "mismatch_label": {"type": "STRING"},
                        "severity": {"type": "STRING", "enum": ["low", "medium", "high"]},
                        "confidence": {"type": "NUMBER"},
                    },
                    "required": [
                        "timestamp",
                        "transcript_snippet",
                        "mismatch_label",
                        "severity",
                        "confidence",
                    ],
                },
            },
            "summary": {"type": "STRING"},
        },
        "required": ["risk_level", "key_themes", "divergence_moments", "summary"],
    }


class GeminiLLMProvider(BriefLLMProvider):
    async def generate_brief(self, utterances: list[UtteranceExtraction]) -> CheckinBrief:
        if not settings.gemini_api_key:
            raise RuntimeError("Gemini API key missing.")

        logger.info(
            "Gemini generation started: model=%s utterances=%s",
            settings.gemini_model,
            len(utterances),
        )
        started = time.monotonic()
        prompt = _build_prompt(utterances)
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": _gemini_schema(),
            },
        }
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
            f"?key={settings.gemini_api_key}"
        )

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, json=payload)
        logger.info("Gemini response received: status=%s", response.status_code)

        if not response.is_success:
            raise RuntimeError(f"Gemini call failed with status {response.status_code}.")

        body = response.json()
        candidates = body.get("candidates", [])
        logger.info("Gemini candidates parsed: count=%s", len(candidates))
        if not candidates:
            raise RuntimeError("Gemini response has no candidates.")

        text = (
            candidates[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        if not text:
            raise RuntimeError("Gemini response did not include text.")

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Gemini response was not valid JSON.") from exc

        validated = CheckinBrief.model_validate(parsed)
        logger.info(
            "Gemini brief validated: risk_level=%s themes=%s divergence_moments=%s elapsed_ms=%s",
            validated.risk_level,
            len(validated.key_themes),
            len(validated.divergence_moments),
            int((time.monotonic() - started) * 1000),
        )
        return validated
