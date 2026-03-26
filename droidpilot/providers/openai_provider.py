"""OpenAI LLM provider."""

import json

from openai import OpenAI

from .base import LLMProvider, ToolCall


class OpenAIProvider(LLMProvider):
    """Provider for OpenAI models (GPT-4o, etc.)."""

    def __init__(self, model: str, system_prompt: str, tools: list[dict]) -> None:
        self._model = model
        self._tools = tools
        self._client = OpenAI()
        self._messages: list[dict] = [
            {"role": "system", "content": system_prompt},
        ]
        self._last_tool_call_id: str | None = None

    def add_user_message(self, content: str) -> None:
        self._messages.append({"role": "user", "content": content})

    def get_tool_call(self) -> ToolCall | None:
        response = self._client.chat.completions.create(  # type: ignore[call-overload]
            model=self._model,
            messages=self._messages,
            tools=self._tools,
            tool_choice="required",
        )

        message = response.choices[0].message
        self._messages.append(message.model_dump(exclude_none=True))

        if not message.tool_calls:
            return None

        tc = message.tool_calls[0]
        self._last_tool_call_id = tc.id
        return ToolCall(
            name=tc.function.name,
            arguments=json.loads(tc.function.arguments),
        )

    def add_tool_result(self, result: str) -> None:
        self._messages.append(
            {
                "role": "tool",
                "tool_call_id": self._last_tool_call_id,
                "content": result,
            }
        )
