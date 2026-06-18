from backend.app.models.schemas import DeliverableRequest, DeliverableResponse
from backend.app.services.llm_router import llm_router


async def generate_deliverable(req: DeliverableRequest) -> DeliverableResponse:
    prompt = f"""Create a polished {req.deliverable_type} for an asset-management investor-relations team.

Company: {req.company_name}
Meeting summary: {req.meeting_summary or "not supplied"}
Research memo: {req.research_memo or "not supplied"}
CRM payload: {req.crm_payload}

Use only the supplied information. If a fact is unavailable, phrase it as an analyst-review open item.
Return Markdown only."""
    llm_result = await llm_router.generate_text(
        req.provider,
        req.model,
        prompt,
        system="You prepare concise, professional investor-relations deliverables.",
        max_tokens=1400,
    )
    if llm_result.get("text"):
        return DeliverableResponse(
            title=f"{req.company_name} {req.deliverable_type.replace('_', ' ').title()}",
            content_markdown=llm_result["text"],
            source_fields=[k for k, v in req.model_dump().items() if v],
        )
    if req.deliverable_type == "follow_up_email":
        title = f"Follow-up email for {req.company_name}"
        content = f"""Subject: Follow-up from our discussion

Hi,

Thank you for the time today. Based on our discussion, the most relevant next step is:
{req.crm_payload.get("NextAction") or "share a concise follow-up pack and confirm the right diligence path"}.

Brief recap:
{req.meeting_summary or req.crm_payload.get("Summary") or "Meeting summary pending analyst review."}

Best,
Analyst Demo User
"""
    elif req.deliverable_type == "faq":
        title = f"{req.company_name} FAQ"
        content = f"""## Likely Questions

### What problem does this strategy solve?
It gives the investor a focused way to evaluate asset-based finance exposure with documented follow-up ownership.

### What should we send next?
Send the strategy overview, relevant case studies, and a short diligence checklist.

### What remains open?
{req.research_memo or "Confirm mandate timing, decision makers, and consultant influence."}
"""
    elif req.deliverable_type == "one_pager":
        title = f"{req.company_name} one-pager"
        content = f"""# {req.company_name} Relationship One-Pager

## Relationship Status
{req.meeting_summary or "No meeting summary supplied."}

## Current Opportunity
{req.research_memo or "Potential fit should be validated through approved research and prior notes."}

## Next Action
{req.crm_payload.get("NextAction") or "Analyst review required."}
"""
    else:
        title = f"{req.company_name} pitch outline"
        content = f"""# Pitch Outline

## 1. Context
{req.research_memo or req.meeting_summary or "Use approved research and prior relationship history."}

## 2. Investor Pain Point
Clarify allocation objective, risk controls, and operational constraints.

## 3. Platform Angle
Connect asset-based finance expertise to the investor's current diligence needs.

## 4. Proof Points
Use internal case studies, prior meeting evidence, and source-backed facts only.

## 5. Close
Confirm next meeting, materials, and CRM owner.
"""
    return DeliverableResponse(
        title=title,
        content_markdown=content,
        source_fields=[k for k, v in req.model_dump().items() if v],
    )
