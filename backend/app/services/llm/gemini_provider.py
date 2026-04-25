import json
import logging
import re
import time

import httpx

from ...core.config import settings
from ...schemas.brief import CheckinBrief
from ..divergence_service import build_divergence_context
from ..models import UtteranceExtraction
from .base import BriefLLMProvider

logger = logging.getLogger(__name__)


def _system_instruction() -> str:
    return (
        "You are a clinical-support summarizer for asynchronous patient voice check-ins. "
        "Use only supplied evidence. Do not diagnose, label disorders, or invent history. "
        "Divergence means semantic sentiment is neutral/positive while prosody distress is high. "
        "If evidence is weak, be explicit about uncertainty and keep divergence_moments empty."
    )


def _build_data_prompt(utterances: list[UtteranceExtraction]) -> str:
    rows = []
    for utterance in utterances:
        rows.append(
            {
                "timestamp": utterance.timestamp,
                "transcript": utterance.transcript,
                "begin_seconds": round(utterance.begin_seconds, 2),
                "end_seconds": round(utterance.end_seconds, 2),
                "duration_seconds": round(utterance.duration_seconds, 2),
                "semantic_sentiment_score": utterance.text_sentiment_score,
                "semantic_sentiment_label": utterance.text_sentiment_label,
                "top_emotions": [
                    {"name": emotion.name, "score": round(emotion.score, 3)}
                    for emotion in utterance.top_emotions
                ],
            }
        )

    context = build_divergence_context(utterances)
    return (
        "Return JSON only following the provided schema.\n"
        "Create concise, evidence-grounded fields:\n"
        "- risk_level: Green/Yellow/Red based on observed distress pattern.\n"
        "- key_themes: concrete topics in transcript and affect.\n"
        "- divergence_moments: only include rows where semantic sentiment is neutral/positive and prosody distress is high.\n"
        "- summary: 2-4 clinically concise sentences.\n\n"
        f"Signal summary: {json.dumps(context, ensure_ascii=True)}\n"
        f"Utterance evidence: {json.dumps(rows, ensure_ascii=True)}"
    )


def _gemini_schema() -> dict:
    return {
        "type": "OBJECT",
        "properties": {
            "risk_level": {"type": "STRING", "enum": ["Green", "Yellow", "Red"]},
            "key_themes": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "maxItems": 6,
            },
            "divergence_moments": {
                "type": "ARRAY",
                "maxItems": 6,
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "timestamp": {"type": "STRING"},
                        "transcript_snippet": {"type": "STRING"},
                        "mismatch_label": {"type": "STRING"},
                        "severity": {"type": "STRING", "enum": ["low", "medium", "high"]},
                        "confidence": {"type": "NUMBER", "minimum": 0, "maximum": 1},
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
            "summary": {"type": "STRING", "maxLength": 700},
        },
        "required": ["risk_level", "key_themes", "divergence_moments", "summary"],
    }


def _is_supported_snippet(snippet: str, utterances: list[UtteranceExtraction]) -> bool:
    normalized = snippet.strip().lower()
    if not normalized:
        return False
    for utterance in utterances:
        text = utterance.transcript.strip().lower()
        if normalized in text or text in normalized:
            return True
    return False


def _find_utterance_for_snippet(
    snippet: str, utterances: list[UtteranceExtraction]
) -> UtteranceExtraction | None:
    normalized = snippet.strip().lower()
    if not normalized:
        return None
    for utterance in utterances:
        text = utterance.transcript.strip().lower()
        if normalized in text or text in normalized:
            return utterance
    return None


def _enrich_mismatch_label(
    mismatch_label: str,
    snippet: str,
    utterances: list[UtteranceExtraction],
) -> str:
    utterance = _find_utterance_for_snippet(snippet, utterances)
    if utterance is None:
        trimmed = mismatch_label.strip()
        return trimmed or "Divergence: neutral sentiment, high prosody distress"

    sentiment_label = (utterance.text_sentiment_label or "neutral").strip().lower()
    if sentiment_label not in {"positive", "neutral"}:
        sentiment_label = "neutral"
    return f"Divergence: {sentiment_label} sentiment, high prosody distress"


def _normalize_transcript_snippet(
    snippet: str, utterance: UtteranceExtraction | None
) -> str:
    cleaned = re.sub(r"\s+", " ", snippet).strip()
    if utterance is None:
        return cleaned

    utterance_text = re.sub(r"\s+", " ", utterance.transcript).strip()
    if not utterance_text:
        return cleaned

    # Prefer full utterance when model returns fragments like "I might need..."
    is_fragment = (
        len(cleaned) < 30
        or len(cleaned.split()) < 5
        or cleaned.endswith("...")
        or cleaned.endswith("..")
    )
    if not cleaned or is_fragment:
        return utterance_text

    if cleaned.lower() in utterance_text.lower():
        return utterance_text
    return cleaned


def _sanitize_summary(summary: str, context: dict) -> str:
    diagnostic_terms = [
        r"\bbipolar\b",
        r"\bschizophrenia\b",
        r"\bmajor depressive\b",
        r"\bptsd\b",
        r"\bdiagnos",
    ]
    if any(re.search(pattern, summary, re.IGNORECASE) for pattern in diagnostic_terms):
        ratio = context.get("candidate_divergence_ratio")
        return (
            "Evidence indicates affective strain in portions of the recording. "
            f"Candidate divergence ratio is {ratio}."
        )
    return summary


def _repair_brief_with_evidence(
    brief: CheckinBrief,
    utterances: list[UtteranceExtraction],
    context: dict,
) -> CheckinBrief:
    deduped_themes: list[str] = []
    for theme in brief.key_themes:
        cleaned = theme.strip()
        if cleaned and cleaned not in deduped_themes:
            deduped_themes.append(cleaned)
    if not deduped_themes:
        deduped_themes = ["Affective check-in"]

    repaired_moments = []
    for moment in brief.divergence_moments:
        if _is_supported_snippet(moment.transcript_snippet, utterances):
            matched_utterance = _find_utterance_for_snippet(
                moment.transcript_snippet, utterances
            )
            repaired_moments.append(
                moment.model_copy(
                    update={
                        "transcript_snippet": _normalize_transcript_snippet(
                            moment.transcript_snippet, matched_utterance
                        ),
                        "mismatch_label": _enrich_mismatch_label(
                            moment.mismatch_label,
                            moment.transcript_snippet,
                            utterances,
                        )
                    }
                )
            )

    return CheckinBrief(
        risk_level=brief.risk_level,
        key_themes=deduped_themes[:6],
        divergence_moments=repaired_moments[:6],
        summary=_sanitize_summary(brief.summary.strip(), context),
    )


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
        data_prompt = _build_data_prompt(utterances)
        payload = {
            "systemInstruction": {
                "parts": [{"text": _system_instruction()}],
            },
            "contents": [{"role": "user", "parts": [{"text": data_prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": _gemini_schema(),
                "temperature": 0.3,
                "maxOutputTokens": 2048,
                "thinkingConfig": {"thinkingBudget": 512},
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
        context = build_divergence_context(utterances)
        repaired = _repair_brief_with_evidence(validated, utterances, context)
        logger.info(
            "Gemini brief validated: risk_level=%s themes=%s divergence_moments=%s elapsed_ms=%s",
            repaired.risk_level,
            len(repaired.key_themes),
            len(repaired.divergence_moments),
            int((time.monotonic() - started) * 1000),
        )
        return repaired
