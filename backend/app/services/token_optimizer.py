import re

from backend.app.models.schemas import (
    PromptEstimateRequest,
    PromptEstimateResponse,
    PromptOptimizeRequest,
    PromptOptimizeResponse,
)

MODEL_PRICING = {
    "claude-sonnet-4-6": {"input": 3.0, "cached_input": 0.3, "output": 15.0},
    "claude-haiku-4-5": {"input": 1.0, "cached_input": 0.1, "output": 5.0},
    "claude-opus-4-8": {"input": 5.0, "cached_input": 0.5, "output": 25.0},
    "gpt-5.5": {"input": 5.0, "cached_input": 0.5, "output": 30.0},
}


def estimate_tokens(text: str) -> int:
    words = re.findall(r"\S+", text or "")
    punctuation_bonus = max(0, len(text) // 90)
    return max(1, int(len(words) * 1.33) + punctuation_bonus)


def estimate_cost_usd(
    model: str, input_tokens: int, output_tokens: int, cached_input_tokens: int = 0
) -> float:
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["claude-sonnet-4-6"])
    uncached = max(0, input_tokens - cached_input_tokens)
    return round(
        (uncached / 1_000_000) * pricing["input"]
        + (cached_input_tokens / 1_000_000) * pricing["cached_input"]
        + (output_tokens / 1_000_000) * pricing["output"],
        6,
    )


def estimate_prompt(req: PromptEstimateRequest) -> PromptEstimateResponse:
    input_tokens = estimate_tokens(req.prompt)
    cost = estimate_cost_usd(
        req.model, input_tokens, req.expected_output_tokens, req.cached_input_tokens
    )
    return PromptEstimateResponse(
        model=req.model,
        input_tokens=input_tokens,
        cached_input_tokens=min(req.cached_input_tokens, input_tokens),
        output_tokens=req.expected_output_tokens,
        estimated_cost_usd=cost,
        monthly_cost_usd=round(cost * max(1, req.monthly_runs), 6),
    )


def optimize_prompt(req: PromptOptimizeRequest) -> PromptOptimizeResponse:
    original = estimate_prompt(req)
    optimized_prompt = _compress_prompt(req.prompt)
    optimized_model = _recommend_model(req.model, optimized_prompt)
    optimized = estimate_prompt(
        PromptEstimateRequest(
            prompt=optimized_prompt,
            model=optimized_model,
            expected_output_tokens=max(250, int(req.expected_output_tokens * 0.75)),
            cached_input_tokens=min(original.input_tokens, req.cached_input_tokens),
            monthly_runs=req.monthly_runs,
        )
    )
    savings = round(original.monthly_cost_usd - optimized.monthly_cost_usd, 6)
    return PromptOptimizeResponse(
        original=original,
        optimized_prompt=optimized_prompt,
        optimized=optimized,
        estimated_savings_usd=max(0.0, savings),
        routing_recommendation={
            "default_model": optimized_model,
            "escalate_when": "confidence is below threshold, source evidence conflicts, or tone risk is high",
            "cache": "Cache the system role, XML schema, and few-shot examples.",
            "batch": "Use batch processing for bulk memo refreshes or CRM cleanup.",
        },
    )


def _compress_prompt(prompt: str) -> str:
    prompt = re.sub(r"\s+", " ", prompt).strip()
    prompt = re.sub(r"\b(please|kindly|basically|really|very|just)\b", "", prompt, flags=re.I)
    prompt = prompt.replace("I want you to", "")
    sections = [
        "Role: internal investor-relations operations analyst.",
        "Task: produce the requested structured output using only supplied context.",
        "Rules: do not guess; return null for absent fields; cite source ids; score confidence.",
        f"Context: {prompt}",
    ]
    return "\n".join(sections)


def _recommend_model(current_model: str, prompt: str) -> str:
    lower = prompt.lower()
    if any(term in lower for term in ["extract", "dedupe", "classify", "tag"]):
        return "claude-haiku-4-5"
    if current_model == "claude-opus-4-8" and len(prompt) < 5000:
        return "claude-sonnet-4-6"
    return current_model
