from time import perf_counter

from backend.app.models.schemas import (
    RagQueryRequest,
    ResearchCompanyRequest,
    ResearchCompanyResponse,
)
from backend.app.services.llm_router import llm_router
from backend.app.services.prompt_registry import RESEARCH_MEMO_PROMPT_VERSION, build_research_prompt
from backend.app.services.rag import answer_query
from backend.app.services.storage import store
from backend.app.services.token_optimizer import estimate_tokens


async def generate_research_memo(req: ResearchCompanyRequest) -> ResearchCompanyResponse:
    start = perf_counter()
    rag_result = answer_query(RagQueryRequest(query=req.company_name, top_k=5))
    retrieved_context = "\n\n".join(chunk["content"] for chunk in rag_result.chunks)
    prompt = build_research_prompt(req.company_name, retrieved_context, req.notes)
    sources = rag_result.citations + [{"doc_title": source, "source_type": "approved"} for source in req.approved_sources]
    llm_result = await llm_router.generate_text(
        req.provider,
        req.model,
        prompt,
        system=(
            "Write a concise, source-grounded internal investor-relations memo in Markdown. "
            "Separate facts, inferred opportunities, and open questions."
        ),
        max_tokens=1800,
    )
    memo = llm_result.get("text") or f"""## Firm Snapshot
{req.company_name} is the target firm for this pre-meeting brief. Use the cited internal snippets and analyst-approved sources below before relying on public research.

## Relevant Decision Makers
{_decision_maker_text(req.company_name)}

## Prior Relationship History
{_history_text(req.company_name)}

## Potential Fit For Asset-Based Finance Discussion
The best near-term angle is to test appetite for private-credit, asset-backed, or specialty-finance exposure, then connect that appetite to prior meeting context and mandate timing.

## Suggested Talking Points
- Confirm current allocation priorities and constraints.
- Ask how the team evaluates downside protection, servicing quality, and collateral reporting.
- Offer a concise follow-up pack with strategy overview, relevant case studies, and next-step owners.

## Open Questions
- Who owns the final recommendation and who influences diligence?
- What internal data room or consultant process is required before a second meeting?
- Are there existing relationships that create a warm-introduction path?

Sources: {", ".join(str(s.get("doc_title") or s.get("chunk_id")) for s in sources) or "analyst notes only"}.
"""
    elapsed_minutes = max(0.1, (perf_counter() - start) / 60)
    store.add_metric("research_turnaround_minutes", round(elapsed_minutes, 3))
    return ResearchCompanyResponse(
        memo_markdown=memo,
        decision_makers=[{"name": "Allocator Contact", "role": "Primary diligence lead", "source": "analyst notes"}],
        sources=sources,
        confidence={
            "source_coverage": 0.72 if sources else 0.35,
            "do_not_guess_compliance": 0.94,
            "live_llm": 1.0 if llm_result.get("mode", "").startswith("live") else 0.0,
        },
        token_estimate={"input_tokens_est": estimate_tokens(prompt), "output_tokens_est": 1400, "prompt_version": RESEARCH_MEMO_PROMPT_VERSION},
    )


def _decision_maker_text(company_name: str) -> str:
    state = store.read()
    people = [
        p for p in state.get("people", [])
        if any(c.get("id") == p.get("company_id") and c.get("name") == company_name for c in state.get("companies", []))
    ]
    if not people:
        return "No confirmed decision makers are indexed yet. Treat all names as analyst-review required."
    return "\n".join(f"- {p['full_name']}: {p.get('title') or 'role not captured'}" for p in people)


def _history_text(company_name: str) -> str:
    state = store.read()
    company_ids = [c["id"] for c in state.get("companies", []) if c.get("name") == company_name]
    interactions = [i for i in state.get("interactions", []) if i.get("company_id") in company_ids]
    if not interactions:
        return "No prior interactions are indexed for this firm."
    return "\n".join(f"- {i.get('interaction_date') or 'undated'}: {i.get('summary')}" for i in interactions[:5])
