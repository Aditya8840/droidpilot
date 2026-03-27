"""LLM provider registry."""

from .base import LLMProvider, ToolCall
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .ollama_provider import OllamaProvider

PROVIDERS: dict[str, type[LLMProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "ollama": OllamaProvider,
}

# Default model per provider so users don't have to specify both
DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o",
    "anthropic": "claude-sonnet-4-20250514",
    "ollama": "llama3",
}


def create_provider(
    provider_name: str, model: str | None, system_prompt: str, tools: list[dict]
) -> LLMProvider:
    """Create an LLM provider instance.

    Args:
        provider_name: One of "openai", "anthropic", "ollama".
        model: Model identifier, or None to use the provider's default.
        system_prompt: System prompt for the agent.
        tools: Tool definitions in OpenAI function-calling format.

    Returns:
        An initialized LLMProvider.

    Raises:
        ValueError: If the provider name is not recognized.
    """
    if provider_name not in PROVIDERS:
        supported = ", ".join(sorted(PROVIDERS))
        raise ValueError(f"Unknown provider '{provider_name}'. Supported: {supported}")

    resolved_model = model or DEFAULT_MODELS[provider_name]
    return PROVIDERS[provider_name](resolved_model, system_prompt, tools)


__all__ = [
    "LLMProvider",
    "ToolCall",
    "OpenAIProvider",
    "AnthropicProvider",
    "OllamaProvider",
    "PROVIDERS",
    "DEFAULT_MODELS",
    "create_provider",
]
