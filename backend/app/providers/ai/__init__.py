"""AI provider factory."""

from __future__ import annotations

from functools import lru_cache

from app.core import settings
from app.providers.ai.base import AIProvider, AIRequest, AIResponse


@lru_cache(maxsize=1)
def get_ai_provider() -> AIProvider:
    name = (settings.ai_provider or "demo").lower()

    if name in ("demo", "offline"):
        from app.providers.ai.demo import DemoAIProvider
        return DemoAIProvider()

    if name == "openai":
        from app.providers.ai.openai import OpenAIProvider
        return OpenAIProvider(default_model=settings.ai_model)

    if name == "anthropic":
        from app.providers.ai.anthropic import AnthropicProvider
        return AnthropicProvider(default_model=settings.ai_model)

    if name == "gemini":
        from app.providers.ai.gemini import GeminiProvider
        return GeminiProvider(default_model=settings.ai_model)

    if name == "openrouter":
        from app.providers.ai.openrouter import OpenRouterProvider
        return OpenRouterProvider(default_model=settings.ai_model)

    if name == "local":
        from app.providers.ai.local import LocalProvider
        return LocalProvider(default_model=settings.ai_model)

    # Unknown → demo fallback (and warn)
    from app.core.logging import get_logger
    from app.providers.ai.demo import DemoAIProvider
    log = get_logger(__name__)
    log.warning("Unknown AI_PROVIDER=%s — falling back to demo", name)
    return DemoAIProvider()


__all__ = ["AIProvider", "AIRequest", "AIResponse", "get_ai_provider"]
