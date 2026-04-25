import logging

from ..schemas.brief import CheckinBrief
from .llm import get_llm_provider
from .models import UtteranceExtraction

logger = logging.getLogger(__name__)


async def generate_brief(utterances: list[UtteranceExtraction]) -> CheckinBrief:
    provider = get_llm_provider()
    logger.info(
        "Synthesis started: provider=%s utterances=%s",
        provider.__class__.__name__,
        len(utterances),
    )
    return await provider.generate_brief(utterances)
