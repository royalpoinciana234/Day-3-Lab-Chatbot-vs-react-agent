"""
Provider factory — selects an LLMProvider from environment config so the rest
of the app (CLI, UI, agent) never hardcodes a provider.

Env vars (.env):
    DEFAULT_PROVIDER   openai | google | local
    DEFAULT_MODEL      model name (provider-specific)
    OPENAI_API_KEY / GEMINI_API_KEY / LOCAL_MODEL_PATH
"""
import os
from typing import Optional
from dotenv import load_dotenv
from src.core.llm_provider import LLMProvider

load_dotenv()

_DEFAULT_MODELS = {
    "openai": "gpt-4o",
    "google": "gemini-1.5-flash",
}


def get_provider(provider: Optional[str] = None, model: Optional[str] = None) -> LLMProvider:
    """Build an LLMProvider based on args or .env defaults."""
    provider = (provider or os.getenv("DEFAULT_PROVIDER", "openai")).lower()
    model = model or os.getenv("DEFAULT_MODEL") or _DEFAULT_MODELS.get(provider)

    if provider == "openai":
        from src.core.openai_provider import OpenAIProvider
        key = os.getenv("OPENAI_API_KEY")
        if not key or key.startswith("your_"):
            raise ValueError("OPENAI_API_KEY chưa được cấu hình trong .env")
        return OpenAIProvider(model_name=model, api_key=key)

    if provider in ("google", "gemini"):
        from src.core.gemini_provider import GeminiProvider
        key = os.getenv("GEMINI_API_KEY")
        if not key or key.startswith("your_"):
            raise ValueError("GEMINI_API_KEY chưa được cấu hình trong .env")
        return GeminiProvider(model_name=model, api_key=key)

    if provider == "local":
        from src.core.local_provider import LocalProvider
        path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")
        return LocalProvider(model_path=path)

    raise ValueError(f"Unknown provider: {provider!r} (dùng: openai | google | local)")
