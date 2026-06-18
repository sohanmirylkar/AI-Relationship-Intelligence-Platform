import json
import re
from typing import Any

import httpx

from backend.app.core.config import get_settings


class LlmRouter:
    """Provider abstraction for Anthropic, OpenAI, and local no-key fallback."""

    async def generate_text(
        self,
        provider: str,
        model: str,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 1600,
    ) -> dict[str, Any]:
        provider = self._resolve_provider(provider)
        if provider == "anthropic":
            return await self._anthropic_text(model, prompt, system, max_tokens)
        if provider == "openai":
            return await self._openai_text(model, prompt, system, max_tokens)
        return self._local_text(model, prompt)

    async def generate_structured(
        self,
        provider: str,
        model: str,
        prompt: str,
        schema_name: str,
        *,
        max_tokens: int = 1800,
    ) -> dict[str, Any]:
        result = await self.generate_text(
            provider,
            model,
            prompt,
            system="Return valid JSON only. Do not include markdown fences.",
            max_tokens=max_tokens,
        )
        parsed = _parse_json_object(result.get("text", ""))
        return {
            **result,
            "schema_name": schema_name,
            "structured": parsed,
            "json_parse_ok": parsed is not None,
        }

    def _resolve_provider(self, provider: str) -> str:
        settings = get_settings()
        requested = (provider or settings.default_llm_provider).lower()
        if requested in {"anthropic", "claude"} and settings.anthropic_api_key:
            return "anthropic"
        if requested == "openai" and settings.openai_api_key:
            return "openai"
        if settings.anthropic_api_key:
            return "anthropic"
        if settings.openai_api_key:
            return "openai"
        return "local"

    async def _openai_text(
        self, model: str, prompt: str, system: str | None, max_tokens: int
    ) -> dict[str, Any]:
        settings = get_settings()
        selected_model = model if model and model.startswith("gpt") else settings.openai_model
        payload: dict[str, Any] = {
            "model": selected_model,
            "input": prompt,
            "max_output_tokens": max_tokens,
        }
        if system:
            payload["instructions"] = system
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{settings.openai_base_url.rstrip('/')}/responses",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
        data = response.json()
        return {
            "provider": "openai",
            "model": selected_model,
            "text": _extract_openai_text(data),
            "usage": data.get("usage", {}),
            "raw_response_id": data.get("id"),
            "mode": "live-openai",
        }

    async def _anthropic_text(
        self, model: str, prompt: str, system: str | None, max_tokens: int
    ) -> dict[str, Any]:
        settings = get_settings()
        selected_model = model or settings.default_synthesis_model
        payload: dict[str, Any] = {
            "model": selected_model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            payload["system"] = system
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{settings.anthropic_base_url.rstrip('/')}/messages",
                headers={
                    "x-api-key": settings.anthropic_api_key or "",
                    "anthropic-version": settings.anthropic_version,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
        data = response.json()
        return {
            "provider": "anthropic",
            "model": selected_model,
            "text": _extract_anthropic_text(data),
            "usage": data.get("usage", {}),
            "raw_response_id": data.get("id"),
            "mode": "live-anthropic",
        }

    def _local_text(self, model: str, prompt: str) -> dict[str, Any]:
        return {
            "provider": "local",
            "model": model,
            "text": "",
            "usage": {},
            "prompt_chars": len(prompt),
            "mode": "local-fallback-no-api-key",
        }


def _extract_openai_text(data: dict[str, Any]) -> str:
    if data.get("output_text"):
        return str(data["output_text"])
    parts: list[str] = []
    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"}:
                parts.append(content.get("text", ""))
    return "\n".join(part for part in parts if part)


def _extract_anthropic_text(data: dict[str, Any]) -> str:
    parts: list[str] = []
    for block in data.get("content", []):
        if block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "\n".join(part for part in parts if part)


def _parse_json_object(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.I | re.M).strip()
    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.S)
        if not match:
            return None
        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None


llm_router = LlmRouter()
