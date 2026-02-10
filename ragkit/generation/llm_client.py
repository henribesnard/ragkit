"""Unified LLM client for RAG generation."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass

from ragkit.config.schema_v2 import LLMGenerationConfigV2
from ragkit.exceptions import LLMError

logger = logging.getLogger(__name__)


@dataclass
class _CacheEntry:
    value: str
    expires_at: float


class LLMClient:
    """Unified LLM client with retries and caching."""

    def __init__(self, config: LLMGenerationConfigV2) -> None:
        self.config = config
        self._cache: dict[str, _CacheEntry] = {}

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate a response for a prompt."""
        cache_key = self._cache_key(prompt, system_prompt)
        if self.config.cache_responses:
            cached = self._get_cached(cache_key)
            if cached is not None:
                return cached

        response = await self._call_with_retry(prompt, system_prompt)
        if self.config.cache_responses:
            self._cache[cache_key] = _CacheEntry(
                value=response,
                expires_at=time.monotonic() + self.config.cache_ttl,
            )
        return response

    async def generate_stream(
        self, prompt: str, system_prompt: str | None = None
    ) -> AsyncIterator[str]:
        """Stream generation tokens (fallback yields the full response)."""
        if not self.config.stream:
            yield await self.generate(prompt, system_prompt)
            return

        async for chunk in self._call_stream(prompt, system_prompt):
            yield chunk

    async def _call_with_retry(self, prompt: str, system_prompt: str | None) -> str:
        last_exc: Exception | None = None
        for attempt in range(self.config.max_retries + 1):
            try:
                return await asyncio.wait_for(
                    self._call_provider(prompt, system_prompt),
                    timeout=self.config.timeout,
                )
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if attempt >= self.config.max_retries:
                    break
                delay = self.config.retry_delay * (2**attempt)
                await asyncio.sleep(delay)
        raise LLMError("LLM generation failed") from last_exc

    async def _call_stream(self, prompt: str, system_prompt: str | None) -> AsyncIterator[str]:
        """Provider-specific streaming support."""
        provider = self.config.provider
        if provider == "openai":
            async for token in self._openai_stream(prompt, system_prompt):
                yield token
            return
        if provider == "anthropic":
            async for token in self._anthropic_stream(prompt, system_prompt):
                yield token
            return
        if provider == "ollama":
            async for token in self._ollama_stream(prompt, system_prompt):
                yield token
            return
        if provider in {"azure", "together"}:
            yield await self._call_provider(prompt, system_prompt)
            return

        raise LLMError(f"Unsupported provider: {provider}")

    async def _call_provider(self, prompt: str, system_prompt: str | None) -> str:
        provider = self.config.provider
        if provider == "openai":
            return await self._call_openai(prompt, system_prompt)
        if provider == "anthropic":
            return await self._call_anthropic(prompt, system_prompt)
        if provider == "ollama":
            return await self._call_ollama(prompt, system_prompt)
        if provider == "azure":
            return await self._call_azure(prompt, system_prompt)
        if provider == "together":
            return await self._call_together(prompt, system_prompt)

        raise LLMError(f"Unsupported provider: {provider}")

    async def _call_openai(self, prompt: str, system_prompt: str | None) -> str:
        try:
            from openai import AsyncOpenAI
        except Exception as exc:  # noqa: BLE001
            raise LLMError("openai package is required for OpenAI provider") from exc

        api_key = os.getenv("OPENAI_API_KEY")
        client = AsyncOpenAI(api_key=api_key)
        messages = [
            {"role": "system", "content": system_prompt or self.config.system_prompt},
            {"role": "user", "content": prompt},
        ]
        response_format = None
        if self.config.output_format == "json":
            response_format = {"type": "json_object"}

        response = await client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            top_p=self.config.top_p,
            frequency_penalty=self.config.frequency_penalty,
            presence_penalty=self.config.presence_penalty,
            response_format=response_format,
        )
        return response.choices[0].message.content or ""

    async def _openai_stream(self, prompt: str, system_prompt: str | None) -> AsyncIterator[str]:
        try:
            from openai import AsyncOpenAI
        except Exception as exc:  # noqa: BLE001
            raise LLMError("openai package is required for OpenAI provider") from exc

        api_key = os.getenv("OPENAI_API_KEY")
        client = AsyncOpenAI(api_key=api_key)
        messages = [
            {"role": "system", "content": system_prompt or self.config.system_prompt},
            {"role": "user", "content": prompt},
        ]
        response = await client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            top_p=self.config.top_p,
            frequency_penalty=self.config.frequency_penalty,
            presence_penalty=self.config.presence_penalty,
            stream=True,
        )
        async for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content

    async def _call_anthropic(self, prompt: str, system_prompt: str | None) -> str:
        try:
            from anthropic import AsyncAnthropic
        except Exception as exc:  # noqa: BLE001
            raise LLMError("anthropic package is required for Anthropic provider") from exc

        api_key = os.getenv("ANTHROPIC_API_KEY")
        client = AsyncAnthropic(api_key=api_key)
        response = await client.messages.create(
            model=self.config.model,
            system=system_prompt or self.config.system_prompt,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        return response.content[0].text if response.content else ""

    async def _anthropic_stream(self, prompt: str, system_prompt: str | None) -> AsyncIterator[str]:
        try:
            from anthropic import AsyncAnthropic
        except Exception as exc:  # noqa: BLE001
            raise LLMError("anthropic package is required for Anthropic provider") from exc

        api_key = os.getenv("ANTHROPIC_API_KEY")
        client = AsyncAnthropic(api_key=api_key)
        response = await client.messages.create(
            model=self.config.model,
            system=system_prompt or self.config.system_prompt,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            stream=True,
        )
        async for chunk in response:
            if chunk.type == "content_block_delta" and chunk.delta:
                yield chunk.delta.text

    async def _call_ollama(self, prompt: str, system_prompt: str | None) -> str:
        try:
            import httpx
        except Exception as exc:  # noqa: BLE001
            raise LLMError("httpx is required for Ollama provider") from exc

        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "system": system_prompt or self.config.system_prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
            },
        }
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                "http://localhost:11434/api/generate",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")

    async def _ollama_stream(self, prompt: str, system_prompt: str | None) -> AsyncIterator[str]:
        try:
            import httpx
        except Exception as exc:  # noqa: BLE001
            raise LLMError("httpx is required for Ollama provider") from exc

        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "system": system_prompt or self.config.system_prompt,
            "stream": True,
            "options": {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
            },
        }
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            async with client.stream(
                "POST",
                "http://localhost:11434/api/generate",
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    chunk = data.get("response")
                    if chunk:
                        yield chunk

    async def _call_azure(self, prompt: str, system_prompt: str | None) -> str:
        try:
            from openai import AsyncAzureOpenAI
        except Exception as exc:  # noqa: BLE001
            raise LLMError("openai package with Azure support is required") from exc

        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
        if not endpoint:
            raise LLMError("AZURE_OPENAI_ENDPOINT is required for Azure provider")

        client = AsyncAzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version,
        )
        messages = [
            {"role": "system", "content": system_prompt or self.config.system_prompt},
            {"role": "user", "content": prompt},
        ]
        response = await client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            top_p=self.config.top_p,
            frequency_penalty=self.config.frequency_penalty,
            presence_penalty=self.config.presence_penalty,
        )
        return response.choices[0].message.content or ""

    async def _call_together(self, prompt: str, system_prompt: str | None) -> str:
        try:
            import httpx
        except Exception as exc:  # noqa: BLE001
            raise LLMError("httpx is required for Together provider") from exc

        api_key = os.getenv("TOGETHER_API_KEY")
        if not api_key:
            raise LLMError("TOGETHER_API_KEY is required for Together provider")
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt or self.config.system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "top_p": self.config.top_p,
        }
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                "https://api.together.xyz/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
        return ""

    def _cache_key(self, prompt: str, system_prompt: str | None) -> str:
        data = {
            "prompt": prompt,
            "system": system_prompt or self.config.system_prompt,
            "model": self.config.model,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "max_tokens": self.config.max_tokens,
            "provider": self.config.provider,
        }
        digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()
        return digest

    def _get_cached(self, key: str) -> str | None:
        entry = self._cache.get(key)
        if entry is None:
            return None
        if entry.expires_at < time.monotonic():
            self._cache.pop(key, None)
            return None
        return entry.value
