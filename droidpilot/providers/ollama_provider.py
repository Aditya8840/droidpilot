"""Ollama LLM provider (uses OpenAI-compatible API)."""

import os

from openai import OpenAI

from .base import ToolCall
from .openai_provider import OpenAIProvider


class OllamaProvider(OpenAIProvider):
    """Provider for locally-hosted Ollama models.

    Ollama exposes an OpenAI-compatible API, so we reuse the OpenAI
    provider and just override client initialization.
    """

    def __init__(self, model: str, system_prompt: str, tools: list[dict]) -> None:
        self._model = model
        self._tools = tools
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        self._client = OpenAI(base_url=base_url, api_key="ollama")
        self._messages: list[dict] = [
            {"role": "system", "content": system_prompt},
        ]
        self._last_tool_call_id: str | None = None
