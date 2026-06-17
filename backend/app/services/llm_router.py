from typing import Any


class LlmRouter:
    """Provider abstraction with deterministic local behavior for demos and tests."""

    async def generate_structured(
        self, provider: str, model: str, prompt: str, schema_name: str
    ) -> dict[str, Any]:
        return {
            "provider": provider,
            "model": model,
            "schema_name": schema_name,
            "prompt_chars": len(prompt),
            "mode": "local-deterministic",
        }


llm_router = LlmRouter()
