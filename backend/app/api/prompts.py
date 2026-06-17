from fastapi import APIRouter

from backend.app.core.security import require_scopes
from backend.app.models.schemas import (
    PromptEstimateRequest,
    PromptEstimateResponse,
    PromptOptimizeRequest,
    PromptOptimizeResponse,
)
from backend.app.services.storage import store
from backend.app.services.token_optimizer import estimate_prompt, optimize_prompt

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.post("/estimate", response_model=PromptEstimateResponse)
async def estimate(req: PromptEstimateRequest, _user=require_scopes("meeting:run")):
    return estimate_prompt(req)


@router.post("/optimize", response_model=PromptOptimizeResponse)
async def optimize(req: PromptOptimizeRequest, _user=require_scopes("meeting:run")):
    result = optimize_prompt(req)
    if result.original.input_tokens:
        reduction = 1 - (result.optimized.input_tokens / result.original.input_tokens)
        store.add_metric("token_reductions", round(max(0, reduction), 2))
    store.add_metric("estimated_ai_cost_saved", result.estimated_savings_usd)
    return result
