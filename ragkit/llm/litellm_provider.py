"""LiteLLM wrapper and router."""

from __future__ import annotations

import json
import warnings
from collections.abc import AsyncIterator
from typing import Any

from ragkit.config.schema import LLMConfig, LLMModelConfig
from ragkit.exceptions import LLMError
from ragkit.utils.async_utils import retry_async, run_with_timeout


class LLMProvider:
    """Unified LLM provider wrapper using LiteLLM."""

    def __init__(self, config: LLMModelConfig):
        if config.provider == "deepseek":
            _suppress_pydantic_warnings()
        self.config = config
        self.model = _resolve_model_name(config)
        self.params = config.params.model_dump(exclude_none=True)
        self.timeout = config.timeout
        self.max_retries = config.max_retries or 0

    async def complete(self, messages: list[dict[str, str]]) -> str:
        response = await self._call(messages)
        return _extract_content(response)

    async def complete_json(
        self, messages: list[dict[str, str]], schema: dict[str, Any]
    ) -> dict[str, Any]:
        system = {
            "role": "system",
            "content": "Return only valid JSON that matches the given schema.",
        }
        payload = [system, *messages]
        response = await self._call(payload, response_format={"type": "json_object"})
        content = _extract_content(response)
        parsed = _parse_json(content)
        if not isinstance(parsed, dict):
            raise LLMError("Expected JSON object in LLM response")
        return parsed

    async def complete_stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        """Stream completion tokens as they arrive."""
        try:
            import litellm
        except Exception as exc:  # noqa: BLE001
            raise LLMError("litellm is required for LLM calls") from exc

        kwargs = dict(self.params)
        response = await litellm.acompletion(
            model=self.model,
            messages=messages,
            api_key=self.config.api_key,
            stream=True,
            **kwargs,
        )
        async for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content

    async def _call(
        self,
        messages: list[dict[str, str]],
        response_format: dict[str, Any] | None = None,
    ) -> Any:
        try:
            import litellm
        except Exception as exc:  # noqa: BLE001
            raise LLMError("litellm is required for LLM calls") from exc

        async def _invoke() -> Any:
            kwargs = dict(self.params)
            if response_format is not None:
                kwargs["response_format"] = response_format
            return await litellm.acompletion(
                model=self.model,
                messages=messages,
                api_key=self.config.api_key,
                **kwargs,
            )

        async def _run() -> Any:
            result = await retry_async(_invoke, max_retries=self.max_retries + 1, delay=1)
            return result

        if self.timeout:
            return await run_with_timeout(_run(), timeout=self.timeout)
        return await _run()


class LLMRouter:
    """Route LLM calls to configured providers."""

    def __init__(self, config: LLMConfig):
        self.primary = LLMProvider(config.primary)
        self.secondary = LLMProvider(config.secondary) if config.secondary else None
        self.fast = LLMProvider(config.fast) if config.fast else None

    def get(self, model_ref: str) -> LLMProvider:
        if model_ref == "primary":
            return self.primary
        if model_ref == "secondary" and self.secondary:
            return self.secondary
        if model_ref == "fast" and self.fast:
            return self.fast
        raise LLMError(f"Unknown or unavailable model reference: {model_ref}")


def _resolve_model_name(config: LLMModelConfig) -> str:
    if "/" in config.model:
        return config.model
    prefix = _PROVIDER_PREFIXES.get(config.provider, "")
    return f"{prefix}{config.model}"


_PROVIDER_PREFIXES: dict[str, str] = {
    "ollama": "ollama/",
    "anthropic": "anthropic/",
    "deepseek": "deepseek/",
    "groq": "groq/",
    "mistral": "mistral/",
}


def _extract_content(response: Any) -> str:
    if hasattr(response, "choices"):
        choice = response.choices[0]
        message = getattr(choice, "message", None)
        if message is not None:
            return message.content
        return str(choice)
    if isinstance(response, dict):
        choices = response.get("choices", [])
        if choices:
            message = choices[0].get("message") or {}
            return message.get("content", "")
    return str(response)


def _parse_json(content: str) -> Any:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start : end + 1])
        raise


_WARNINGS_CONFIGURED = False


def _suppress_pydantic_warnings() -> None:
    global _WARNINGS_CONFIGURED
    if _WARNINGS_CONFIGURED:
        return
    try:
        from pydantic.warnings import PydanticSerializationUnexpectedValue

        warnings.filterwarnings(
            "ignore",
            category=PydanticSerializationUnexpectedValue,
        )
    except Exception:
        warnings.filterwarnings(
            "ignore",
            message=".*PydanticSerializationUnexpectedValue.*",
        )
    _WARNINGS_CONFIGURED = True
