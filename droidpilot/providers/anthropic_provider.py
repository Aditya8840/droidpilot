"""Anthropic LLM provider."""

import anthropic

from .base import LLMProvider, ToolCall


def _convert_tools(openai_tools: list[dict]) -> list[dict]:
    """Convert OpenAI function-calling tool format to Anthropic tool format."""
    converted = []
    for tool in openai_tools:
        func = tool["function"]
        converted.append(
            {
                "name": func["name"],
                "description": func.get("description", ""),
                "input_schema": func.get(
                    "parameters", {"type": "object", "properties": {}}
                ),
            }
        )
    return converted


class AnthropicProvider(LLMProvider):
    """Provider for Anthropic models (Claude)."""

    def __init__(self, model: str, system_prompt: str, tools: list[dict]) -> None:
        self._model = model
        self._system_prompt = system_prompt
        self._tools = _convert_tools(tools)
        self._client = anthropic.Anthropic()
        self._messages: list[dict] = []
        self._last_tool_use_id: str | None = None

    def add_user_message(self, content: str) -> None:
        self._messages.append({"role": "user", "content": content})

    def get_tool_call(self) -> ToolCall | None:
        response = self._client.messages.create(  # type: ignore[call-overload]
            model=self._model,
            max_tokens=1024,
            system=self._system_prompt,
            messages=self._messages,
            tools=self._tools,
            tool_choice={"type": "any"},
        )

        # Build assistant content blocks for history
        assistant_content = []
        tool_call: ToolCall | None = None

        for block in response.content:
            if block.type == "text":
                assistant_content.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                assistant_content.append(
                    {
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    }
                )
                if tool_call is None:
                    self._last_tool_use_id = block.id
                    tool_call = ToolCall(name=block.name, arguments=block.input)

        self._messages.append({"role": "assistant", "content": assistant_content})
        return tool_call

    def add_tool_result(self, result: str) -> None:
        self._messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": self._last_tool_use_id,
                        "content": result,
                    }
                ],
            }
        )
