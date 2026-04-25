import asyncio
import json
import logging
import time

import httpx

from ..core.config import settings
from .models import EmotionScore, UtteranceExtraction

logger = logging.getLogger(__name__)


def _mock_utterances() -> list[UtteranceExtraction]:
    return [
        UtteranceExtraction(
            timestamp="00:14",
            transcript="I think everything has been okay this week.",
            begin_seconds=14.0,
            end_seconds=18.0,
            duration_seconds=4.0,
            top_emotions=[
                EmotionScore(name="Distress", score=0.79),
                EmotionScore(name="Anxiety", score=0.73),
                EmotionScore(name="Sadness", score=0.44),
                EmotionScore(name="Confusion", score=0.33),
                EmotionScore(name="Calmness", score=0.12),
            ],
            text_sentiment_score=6.4,
            text_sentiment_label="positive",
        ),
        UtteranceExtraction(
            timestamp="00:38",
            transcript="Work was manageable, nothing too bad.",
            begin_seconds=38.0,
            end_seconds=42.0,
            duration_seconds=4.0,
            top_emotions=[
                EmotionScore(name="Fear", score=0.67),
                EmotionScore(name="Doubt", score=0.61),
                EmotionScore(name="Distress", score=0.58),
                EmotionScore(name="Anxiety", score=0.51),
                EmotionScore(name="Calmness", score=0.2),
            ],
            text_sentiment_score=5.8,
            text_sentiment_label="neutral_positive",
        ),
    ]


async def extract_utterances(
    audio_bytes: bytes,
    mime_type: str,
) -> list[UtteranceExtraction]:
    """Extract normalized utterances from audio using Hume.

    For MVP speed, this function currently returns realistic mock utterance data.
    When Hume credentials are configured, this function should be extended to
    submit a batch job, poll completion, and normalize timestamps/transcript/top emotions.
    """
    _ = audio_bytes
    _ = mime_type

    if settings.processing_mode == "mock":
        logger.info("Hume extract skipped (mock mode enabled).")
        return _mock_utterances()

    if not settings.hume_api_key:
        raise RuntimeError("Hume API key missing while PROCESSING_MODE=real.")

    logger.info(
        "Hume extract started: mime_type=%s size_bytes=%s granularity=%s",
        mime_type,
        len(audio_bytes),
        settings.hume_prosody_granularity,
    )
    started = time.monotonic()

    try:
        async with httpx.AsyncClient(
            base_url=settings.hume_base_url,
            timeout=settings.hume_timeout_seconds,
        ) as client:
            job_id = await _start_job(client, audio_bytes=audio_bytes, mime_type=mime_type)
            await _poll_until_terminal(client, job_id=job_id)
            predictions = await _fetch_predictions(client, job_id=job_id)
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Hume HTTP request failed: {exc}") from exc

    utterances = _normalize_utterances(predictions)
    if not utterances:
        raise RuntimeError("Hume returned no prosody utterances.")

    logger.info(
        "Hume extract completed: utterances=%s elapsed_ms=%s",
        len(utterances),
        int((time.monotonic() - started) * 1000),
    )
    return utterances


def _hume_headers() -> dict[str, str]:
    return {"X-Hume-Api-Key": settings.hume_api_key or ""}


async def _start_job(client: httpx.AsyncClient, audio_bytes: bytes, mime_type: str) -> str:
    payload = {
        "models": {
            "prosody": {
                "granularity": settings.hume_prosody_granularity,
                "identify_speakers": False,
            },
            "language": {
                "granularity": settings.hume_prosody_granularity,
                "sentiment": {},
                "identify_speakers": False,
            },
        }
    }
    files = [("file", ("checkin-audio", audio_bytes, mime_type))]
    response = await client.post(
        "/v0/batch/jobs",
        headers=_hume_headers(),
        data={"json": json.dumps(payload)},
        files=files,
    )
    if not response.is_success:
        raise RuntimeError(f"Hume job start failed [{response.status_code}]: {response.text}")

    job_id = response.json().get("job_id")
    if not job_id:
        raise RuntimeError("Hume response did not include job_id.")

    logger.info(
        "Hume job started: job_id=%s mime_type=%s size_bytes=%s",
        job_id,
        mime_type,
        len(audio_bytes),
    )
    return job_id


async def _poll_until_terminal(client: httpx.AsyncClient, job_id: str) -> None:
    deadline = time.monotonic() + settings.hume_max_wait_seconds

    while True:
        response = await client.get(f"/v0/batch/jobs/{job_id}", headers=_hume_headers())
        if not response.is_success:
            raise RuntimeError(f"Hume job details failed [{response.status_code}]: {response.text}")

        details = response.json()
        state = details.get("state", {})
        status = str(state.get("status", "")).upper()
        logger.info("Hume job poll: job_id=%s status=%s", job_id, status)

        if status == "COMPLETED":
            logger.info("Hume job completed: job_id=%s", job_id)
            return
        if status == "FAILED":
            message = state.get("message") or "Unknown Hume job failure."
            logger.warning("Hume job failed: job_id=%s message=%s", job_id, message)
            raise RuntimeError(f"Hume job failed: {message}")

        if time.monotonic() > deadline:
            raise RuntimeError(f"Hume job timed out after {settings.hume_max_wait_seconds}s.")

        await asyncio.sleep(max(1, settings.hume_poll_interval_seconds))


async def _fetch_predictions(client: httpx.AsyncClient, job_id: str) -> list[dict]:
    response = await client.get(f"/v0/batch/jobs/{job_id}/predictions", headers=_hume_headers())
    if not response.is_success:
        raise RuntimeError(f"Hume predictions fetch failed [{response.status_code}]: {response.text}")

    payload = response.json()
    if not isinstance(payload, list):
        raise RuntimeError("Hume predictions payload was not a list.")

    logger.info("Hume predictions fetched: job_id=%s sources=%s", job_id, len(payload))
    return payload


def _normalize_utterances(predictions_payload: list[dict]) -> list[UtteranceExtraction]:
    utterances: list[UtteranceExtraction] = []

    for source in predictions_payload:
        results = source.get("results", {})
        for prediction in results.get("predictions", []):
            models = prediction.get("models", {})
            prosody = models.get("prosody", {})
            language = models.get("language", {})
            language_index = _build_language_index(language.get("grouped_predictions", []))
            groups = prosody.get("grouped_predictions", [])
            for group in groups:
                for item in group.get("predictions", []):
                    text = (item.get("text") or "").strip()
                    if not text:
                        continue

                    time_info = item.get("time", {})
                    begin_seconds = _to_seconds(time_info.get("begin"))
                    end_seconds = _to_seconds(time_info.get("end"))
                    timestamp = _to_mm_ss(begin_seconds)
                    top_emotions = _top_emotions(item.get("emotions", []), limit=6)
                    if not top_emotions:
                        continue

                    sentiment_score, sentiment_label = _lookup_sentiment(
                        language_index=language_index,
                        transcript=text,
                        begin_seconds=begin_seconds,
                        end_seconds=end_seconds,
                    )
                    utterances.append(
                        UtteranceExtraction(
                            timestamp=timestamp,
                            transcript=text,
                            begin_seconds=begin_seconds,
                            end_seconds=end_seconds,
                            duration_seconds=max(0.0, end_seconds - begin_seconds),
                            top_emotions=top_emotions,
                            text_sentiment_score=sentiment_score,
                            text_sentiment_label=sentiment_label,
                        )
                    )

    return utterances


def _top_emotions(raw: list[dict], limit: int) -> list[EmotionScore]:
    scored: list[EmotionScore] = []
    for emotion in raw:
        name = emotion.get("name")
        score = emotion.get("score")
        if not isinstance(name, str):
            continue
        if not isinstance(score, int | float):
            continue
        scored.append(EmotionScore(name=name, score=float(score)))

    scored.sort(key=lambda entry: entry.score, reverse=True)
    return scored[:limit]


def _to_mm_ss(seconds: object) -> str:
    total_seconds = max(0, int(round(_to_seconds(seconds))))
    minutes = total_seconds // 60
    remaining = total_seconds % 60
    return f"{minutes:02d}:{remaining:02d}"


def _to_seconds(value: object) -> float:
    if not isinstance(value, int | float):
        return 0.0
    return max(0.0, float(value))


def _build_language_index(grouped_predictions: list[dict]) -> dict[tuple[str, int, int], dict]:
    index: dict[tuple[str, int, int], dict] = {}
    for group in grouped_predictions:
        for item in group.get("predictions", []):
            text = str(item.get("text", "")).strip()
            if not text:
                continue
            time_info = item.get("time", {})
            begin = int(round(_to_seconds(time_info.get("begin")) * 100))
            end = int(round(_to_seconds(time_info.get("end")) * 100))
            index[(text.lower(), begin, end)] = item
    return index


def _lookup_sentiment(
    language_index: dict[tuple[str, int, int], dict],
    transcript: str,
    begin_seconds: float,
    end_seconds: float,
) -> tuple[float | None, str | None]:
    begin = int(round(begin_seconds * 100))
    end = int(round(end_seconds * 100))
    item = language_index.get((transcript.lower(), begin, end))
    if item is None:
        item = language_index.get((transcript.lower(), begin, begin))
    if item is None:
        return None, None

    score = _sentiment_expected_score(item.get("sentiment", []))
    if score is None:
        return None, None
    return score, _sentiment_label(score)


def _sentiment_expected_score(sentiment_distribution: list[dict]) -> float | None:
    weighted = 0.0
    total = 0.0
    for bucket in sentiment_distribution:
        name = bucket.get("name")
        probability = bucket.get("score")
        if not isinstance(name, str) or not isinstance(probability, int | float):
            continue
        try:
            level = float(name)
        except ValueError:
            continue
        weighted += level * float(probability)
        total += float(probability)

    if total <= 0:
        return None
    return round(weighted / total, 3)


def _sentiment_label(score: float) -> str:
    if score >= 6.0:
        return "positive"
    if score <= 4.0:
        return "negative"
    return "neutral"
