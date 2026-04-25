from ...core.config import settings
from .base import BriefLLMProvider
from .gemini_provider import GeminiLLMProvider
from .mock_provider import MockLLMProvider


def get_llm_provider() -> BriefLLMProvider:
    provider = settings.llm_provider.lower()

    if settings.processing_mode == "mock":
        return MockLLMProvider()

    if provider == "gemini":
        return GeminiLLMProvider()

    if provider in {"openai", "anthropic"}:
        # Keep provider modular and explicit even before additional providers are implemented.
        raise RuntimeError(f"LLM provider '{provider}' is configured but not implemented yet.")

    return MockLLMProvider()
