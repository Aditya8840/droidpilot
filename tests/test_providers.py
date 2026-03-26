"""Tests for the LLM provider abstraction."""

import json
from unittest.mock import MagicMock, patch

import pytest

from droidpilot.actions import TOOLS
from droidpilot.providers import (
    DEFAULT_MODELS,
    PROVIDERS,
    AnthropicProvider,
    OllamaProvider,
    OpenAIProvider,
    ToolCall,
    create_provider,
)
from droidpilot.providers.anthropic_provider import _convert_tools

# ---------------------------------------------------------------------------
# create_provider registry
# ---------------------------------------------------------------------------


class TestCreateProvider:
    def test_unknown_provider_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown provider 'bogus'"):
            create_provider("bogus", None, "sys", TOOLS)

    @patch("droidpilot.providers.openai_provider.OpenAI")
    def test_creates_openai_with_default_model(self, mock_openai: MagicMock) -> None:
        provider = create_provider("openai", None, "sys", TOOLS)
        assert isinstance(provider, OpenAIProvider)
        assert provider._model == DEFAULT_MODELS["openai"]  # type: ignore[union-attr]

    @patch("droidpilot.providers.openai_provider.OpenAI")
    def test_creates_openai_with_explicit_model(self, mock_openai: MagicMock) -> None:
        provider = create_provider("openai", "gpt-4-turbo", "sys", TOOLS)
        assert isinstance(provider, OpenAIProvider)
        assert provider._model == "gpt-4-turbo"

    @patch("droidpilot.providers.anthropic_provider.anthropic")
    def test_creates_anthropic(self, mock_anthropic: MagicMock) -> None:
        provider = create_provider("anthropic", None, "sys", TOOLS)
        assert isinstance(provider, AnthropicProvider)
        assert provider._model == DEFAULT_MODELS["anthropic"]

    @patch("droidpilot.providers.openai_provider.OpenAI")
    def test_creates_ollama(self, mock_openai: MagicMock) -> None:
        provider = create_provider("ollama", None, "sys", TOOLS)
        assert isinstance(provider, OllamaProvider)

    def test_all_providers_registered(self) -> None:
        assert set(PROVIDERS.keys()) == {"openai", "anthropic", "ollama"}

    def test_all_providers_have_default_model(self) -> None:
        for name in PROVIDERS:
            assert name in DEFAULT_MODELS, f"No default model for '{name}'"


# ---------------------------------------------------------------------------
# Tool format conversion
# ---------------------------------------------------------------------------


class TestConvertTools:
    def test_converts_tap_tool(self) -> None:
        tap_tool = TOOLS[0]  # tap is first
        converted = _convert_tools([tap_tool])
        assert len(converted) == 1
        assert converted[0]["name"] == "tap"
        assert "input_schema" in converted[0]
        assert converted[0]["input_schema"]["properties"]["ref"]["type"] == "integer"

    def test_converts_all_tools(self) -> None:
        converted = _convert_tools(TOOLS)
        assert len(converted) == len(TOOLS)
        names = {t["name"] for t in converted}
        expected_names = {t["function"]["name"] for t in TOOLS}  # type: ignore[index]
        assert names == expected_names


# ---------------------------------------------------------------------------
# OpenAI provider
# ---------------------------------------------------------------------------


class TestOpenAIProvider:
    @patch("droidpilot.providers.openai_provider.OpenAI")
    def test_add_user_message(self, mock_openai: MagicMock) -> None:
        provider = OpenAIProvider("gpt-4o", "system prompt", TOOLS)
        provider.add_user_message("hello")
        assert provider._messages[-1] == {"role": "user", "content": "hello"}

    @patch("droidpilot.providers.openai_provider.OpenAI")
    def test_get_tool_call(self, mock_openai_cls: MagicMock) -> None:
        mock_client = mock_openai_cls.return_value
        mock_tc = MagicMock()
        mock_tc.id = "call_123"
        mock_tc.function.name = "tap"
        mock_tc.function.arguments = json.dumps({"ref": 5})
        mock_message = MagicMock()
        mock_message.tool_calls = [mock_tc]
        mock_message.model_dump.return_value = {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "call_123",
                    "function": {"name": "tap", "arguments": '{"ref": 5}'},
                }
            ],
        }
        mock_client.chat.completions.create.return_value.choices = [
            MagicMock(message=mock_message)
        ]

        provider = OpenAIProvider("gpt-4o", "sys", TOOLS)
        provider.add_user_message("test")
        result = provider.get_tool_call()

        assert result is not None
        assert result.name == "tap"
        assert result.arguments == {"ref": 5}
        assert provider._last_tool_call_id == "call_123"

    @patch("droidpilot.providers.openai_provider.OpenAI")
    def test_get_tool_call_returns_none_when_no_tools(
        self, mock_openai_cls: MagicMock
    ) -> None:
        mock_client = mock_openai_cls.return_value
        mock_message = MagicMock()
        mock_message.tool_calls = None
        mock_message.model_dump.return_value = {"role": "assistant", "content": "hi"}
        mock_client.chat.completions.create.return_value.choices = [
            MagicMock(message=mock_message)
        ]

        provider = OpenAIProvider("gpt-4o", "sys", TOOLS)
        provider.add_user_message("test")
        result = provider.get_tool_call()
        assert result is None

    @patch("droidpilot.providers.openai_provider.OpenAI")
    def test_add_tool_result(self, mock_openai: MagicMock) -> None:
        provider = OpenAIProvider("gpt-4o", "sys", TOOLS)
        provider._last_tool_call_id = "call_abc"
        provider.add_tool_result("Tapped [5]")
        assert provider._messages[-1] == {
            "role": "tool",
            "tool_call_id": "call_abc",
            "content": "Tapped [5]",
        }


# ---------------------------------------------------------------------------
# Anthropic provider
# ---------------------------------------------------------------------------


class TestAnthropicProvider:
    @patch("droidpilot.providers.anthropic_provider.anthropic")
    def test_system_prompt_stored_separately(self, mock_anthropic: MagicMock) -> None:
        provider = AnthropicProvider(
            "claude-sonnet-4-20250514", "my system prompt", TOOLS
        )
        assert provider._system_prompt == "my system prompt"
        # system prompt should NOT be in messages
        assert len(provider._messages) == 0

    @patch("droidpilot.providers.anthropic_provider.anthropic")
    def test_add_user_message(self, mock_anthropic: MagicMock) -> None:
        provider = AnthropicProvider("claude-sonnet-4-20250514", "sys", TOOLS)
        provider.add_user_message("hello")
        assert provider._messages[-1] == {"role": "user", "content": "hello"}

    @patch("droidpilot.providers.anthropic_provider.anthropic")
    def test_get_tool_call(self, mock_anthropic_mod: MagicMock) -> None:
        mock_client = mock_anthropic_mod.Anthropic.return_value

        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.id = "tu_123"
        mock_tool_block.name = "press_back"
        mock_tool_block.input = {}

        mock_response = MagicMock()
        mock_response.content = [mock_tool_block]
        mock_client.messages.create.return_value = mock_response

        provider = AnthropicProvider("claude-sonnet-4-20250514", "sys", TOOLS)
        provider.add_user_message("test")
        result = provider.get_tool_call()

        assert result is not None
        assert result.name == "press_back"
        assert result.arguments == {}
        assert provider._last_tool_use_id == "tu_123"

    @patch("droidpilot.providers.anthropic_provider.anthropic")
    def test_add_tool_result_format(self, mock_anthropic: MagicMock) -> None:
        provider = AnthropicProvider("claude-sonnet-4-20250514", "sys", TOOLS)
        provider._last_tool_use_id = "tu_abc"
        provider.add_tool_result("Pressed back")
        msg = provider._messages[-1]
        assert msg["role"] == "user"
        assert msg["content"][0]["type"] == "tool_result"
        assert msg["content"][0]["tool_use_id"] == "tu_abc"
        assert msg["content"][0]["content"] == "Pressed back"


# ---------------------------------------------------------------------------
# Ollama provider
# ---------------------------------------------------------------------------


class TestOllamaProvider:
    @patch("droidpilot.providers.openai_provider.OpenAI")
    def test_inherits_openai(self, mock_openai: MagicMock) -> None:
        provider = OllamaProvider("llama3", "sys", TOOLS)
        assert isinstance(provider, OpenAIProvider)

    @patch("droidpilot.providers.ollama_provider.OpenAI")
    def test_uses_ollama_base_url(self, mock_openai_cls: MagicMock) -> None:
        OllamaProvider("llama3", "sys", TOOLS)
        mock_openai_cls.assert_called_with(
            base_url="http://localhost:11434/v1", api_key="ollama"
        )

    @patch.dict("os.environ", {"OLLAMA_BASE_URL": "http://custom:1234/v1"})
    @patch("droidpilot.providers.ollama_provider.OpenAI")
    def test_custom_base_url(self, mock_openai_cls: MagicMock) -> None:
        OllamaProvider("llama3", "sys", TOOLS)
        mock_openai_cls.assert_called_with(
            base_url="http://custom:1234/v1", api_key="ollama"
        )
