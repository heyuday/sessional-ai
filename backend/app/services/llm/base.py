from abc import ABC, abstractmethod

from ...schemas.brief import CheckinBrief
from ..models import UtteranceExtraction


class BriefLLMProvider(ABC):
    @abstractmethod
    async def generate_brief(self, utterances: list[UtteranceExtraction]) -> CheckinBrief:
        raise NotImplementedError
