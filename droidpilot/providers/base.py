"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolCall:
    """A normalized tool call returned by any LLM provider."""

    name: str
    arguments: dict[str, Any]


class LLMProvider(ABC):
    """Interface that every LLM provider must implement.

    The provider owns its internal message history and handles all
    format differences (system prompt placement, tool-call schemas,
    response parsing) so the agent loop stays provider-agnostic.
    """

    @abstractmethod
    def __init__(self, model: str, system_prompt: str, tools: list[dict]) -> None:
        """Initialize the provider with model, system prompt, and tool definitions.

        Args:
            model: Model identifier (e.g. "gpt-4o", "claude-sonnet-4-20250514").
            system_prompt: The system-level instruction for the agent.
            tools: Tool definitions in OpenAI function-calling format.
        """

    @abstractmethod
    def add_user_message(self, content: str) -> None:
        """Append a user message to the conversation history."""

    @abstractmethod
    def get_tool_call(self) -> ToolCall | None:
        """Call the LLM and return a parsed tool call, or None if none returned.

        This also appends the assistant's response to the internal history.
        """

    @abstractmethod
    def add_tool_result(self, result: str) -> None:
        """Record a tool execution result in the conversation history."""
