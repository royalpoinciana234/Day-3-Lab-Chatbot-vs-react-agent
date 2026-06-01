import time
from typing import Dict, Any, Optional, Generator

from google import genai
from google.genai import types

from src.core.llm_provider import LLMProvider


class GeminiProvider(LLMProvider):
    """Gemini provider using the modern `google-genai` SDK.

    System instruction is passed via GenerateContentConfig (no manual prefixing).
    """

    def __init__(self, model_name: str = "gemini-1.5-flash", api_key: Optional[str] = None):
        super().__init__(model_name, api_key)
        self.client = genai.Client(api_key=self.api_key)

    @staticmethod
    def _config(system_prompt: Optional[str]):
        if system_prompt:
            return types.GenerateContentConfig(system_instruction=system_prompt)
        return None

    @staticmethod
    def _usage(response) -> Dict[str, int]:
        meta = getattr(response, "usage_metadata", None)
        return {
            "prompt_tokens": getattr(meta, "prompt_token_count", 0) or 0,
            "completion_tokens": getattr(meta, "candidates_token_count", 0) or 0,
            "total_tokens": getattr(meta, "total_token_count", 0) or 0,
        }

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=self._config(system_prompt),
        )
        latency_ms = int((time.time() - start_time) * 1000)

        return {
            "content": response.text,
            "usage": self._usage(response),
            "latency_ms": latency_ms,
            "provider": "google",
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        stream = self.client.models.generate_content_stream(
            model=self.model_name,
            contents=prompt,
            config=self._config(system_prompt),
        )
        for chunk in stream:
            if chunk.text:
                yield chunk.text
