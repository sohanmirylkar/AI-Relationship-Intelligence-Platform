from typing import Any

from backend.app.models.schemas import AssistantChatRequest, AssistantChatResponse
from backend.app.services.dashboard import dashboard_summary
from backend.app.services.llm_router import llm_router
from backend.app.services.storage import store

MODULE_GUIDE = {
    "Meeting Intelligence": {
        "purpose": "Turn transcripts or pasted notes into summaries, entities, action items, confidence scores, and CRM payloads.",
        "next": "Upload or paste notes, run extraction, review low-confidence fields, then preflight the CRM payload.",
    },
    "Investor Research": {
        "purpose": "Create source-backed pre-meeting briefs from uploaded notes and approved research.",
        "next": "Index relevant research docs, enter the target firm, generate the memo, and review citations.",
    },
    "CRM Autopilot": {
        "purpose": "Validate required CRM fields, detect duplicate-like records, and export CSV or sync to Supabase.",
        "next": "Run preflight, resolve warnings, then export CSV or use Supabase sync when credentials are configured.",
    },
    "Token Optimizer": {
        "purpose": "Estimate AI cost, compress prompts, route tasks to cheaper viable models, and track savings.",
        "next": "Paste a verbose workflow prompt, optimize it, compare cost, then reuse the optimized version.",
    },
    "Deliverables Generator": {
        "purpose": "Draft follow-up emails, FAQs, one-pagers, and pitch outlines from meeting and research context.",
        "next": "Select a deliverable type, reuse extracted/research context, generate, and edit for tone.",
    },
    "Relationship Graph": {
        "purpose": "Show companies, people, interactions, and relationship edges created from workflow activity.",
        "next": "Run meeting extraction first, then inspect nodes and edges for relationship coverage.",
    },
    "Knowledge Base": {
        "purpose": "Upload approved documents, chunk them, and ask source-backed questions over internal context.",
        "next": "Upload research notes or PDFs, index them, then ask a focused question with company names.",
    },
    "Dashboard": {
        "purpose": "Summarize operating metrics across meetings, CRM quality, graph coverage, and AI cost savings.",
        "next": "Use it at the end of the demo to prove measurable business value.",
    },
}


async def chat_with_assistant(req: AssistantChatRequest) -> AssistantChatResponse:
    context = _build_context(req)
    prompt = _build_prompt(req, context)
    llm_result = await llm_router.generate_text(
        req.provider,
        req.model,
        prompt,
        system=(
            "You are IRIP Copilot, a practical internal guide for an asset-management "
            "relationship-intelligence platform. Be concise, specific, and action-oriented. "
            "Use only the provided application context. If something has not been done yet, say so."
        ),
        max_tokens=900,
    )
    fallback = _fallback_answer(req, context)
    answer = llm_result.get("text") or fallback
    steps = _suggest_next_steps(req.current_page, context)
    return AssistantChatResponse(
        answer_markdown=answer,
        current_page=req.current_page,
        suggested_next_steps=steps,
        relevant_modules=_relevant_modules(req.message, req.current_page),
        context_summary=context,
        mode=llm_result.get("mode", "local-fallback"),
    )


def _build_context(req: AssistantChatRequest) -> dict[str, Any]:
    state = store.read()
    dashboard = dashboard_summary().model_dump()
    latest_interaction = (state.get("interactions") or [])[-1] if state.get("interactions") else None
    latest_company = (state.get("companies") or [])[-1] if state.get("companies") else None
    latest_crm_job = (state.get("crm_sync_jobs") or [])[-1] if state.get("crm_sync_jobs") else None
    open_actions = [
        item for item in state.get("action_items", []) if item.get("status") != "done"
    ][:5]
    return {
        "current_page": req.current_page,
        "current_module": MODULE_GUIDE.get(req.current_page or "", {}),
        "dashboard": dashboard,
        "latest_company": latest_company,
        "latest_interaction": latest_interaction,
        "latest_crm_job": latest_crm_job,
        "open_action_items": open_actions,
        "recent_ui_state": _compact(req.recent_state),
        "available_modules": list(MODULE_GUIDE),
        "completed_signals": {
            "has_meetings": dashboard["meetings_processed"] > 0,
            "has_graph_edges": dashboard["graph_coverage"]["edges"] > 0,
            "has_knowledge_chunks": any(
                item["module"] == "Knowledge Base" and item["count"] > 0
                for item in dashboard["module_activity"]
            ),
            "has_crm_jobs": any(
                item["module"] == "CRM Autopilot" and item["count"] > 0
                for item in dashboard["module_activity"]
            ),
        },
    }


def _build_prompt(req: AssistantChatRequest, context: dict[str, Any]) -> str:
    history = "\n".join(
        f"{message.role}: {message.content}" for message in req.conversation[-6:]
    )
    return f"""User question:
{req.message}

Current page:
{req.current_page or "unknown"}

Recent conversation:
{history or "none"}

Application context:
{context}

Answer requirements:
- Explain what the user has done so far when relevant.
- Tell them the next best step.
- Tell them where to do it in the app.
- Mention any missing prerequisite, such as needing indexed docs or Supabase keys.
- Keep the answer friendly and direct."""


def _fallback_answer(req: AssistantChatRequest, context: dict[str, Any]) -> str:
    page = req.current_page or "Dashboard"
    guide = MODULE_GUIDE.get(page, MODULE_GUIDE["Dashboard"])
    completed = context["completed_signals"]
    done_bits = []
    if completed["has_meetings"]:
        done_bits.append("you have at least one extracted meeting")
    if completed["has_crm_jobs"]:
        done_bits.append("you have run CRM preflight or sync")
    if completed["has_knowledge_chunks"]:
        done_bits.append("you have indexed knowledge-base content")
    if completed["has_graph_edges"]:
        done_bits.append("the relationship graph has edges")
    done = ", ".join(done_bits) if done_bits else "you have not created much workflow history yet"
    steps = _suggest_next_steps(page, context)
    return (
        f"On **{page}**, the goal is to {guide['purpose'].lower()}\n\n"
        f"From the current app state, {done}.\n\n"
        f"Best next move: **{steps[0]}**\n\n"
        "After that, use the Dashboard to confirm the workflow created measurable value: "
        "fields avoided, duplicate warnings, graph coverage, and AI cost savings."
    )


def _suggest_next_steps(current_page: str | None, context: dict[str, Any]) -> list[str]:
    page = current_page or "Dashboard"
    completed = context["completed_signals"]
    if page == "Meeting Intelligence" and not completed["has_meetings"]:
        return [
            "Paste or upload a transcript, then click Run extraction.",
            "Review the CRM payload and confidence fields.",
            "Send the payload to CRM Autopilot for preflight.",
        ]
    if page == "Investor Research" and not completed["has_knowledge_chunks"]:
        return [
            "Upload approved research notes in Knowledge Base first.",
            "Return to Investor Research and generate a memo for the target firm.",
            "Check that the memo cites indexed sources.",
        ]
    if page == "CRM Autopilot":
        return [
            "Run preflight on the CRM payload.",
            "Resolve duplicate warnings and missing required fields.",
            "Export CSV or sync to Supabase once the record is valid.",
        ]
    if page == "Token Optimizer":
        return [
            "Paste the verbose workflow prompt.",
            "Run Optimize and compare original versus optimized monthly cost.",
            "Use the optimized prompt in the relevant module.",
        ]
    if page == "Deliverables Generator":
        return [
            "Generate a follow-up email or pitch outline from the latest meeting/research context.",
            "Edit the draft for firm-specific tone.",
            "Save the final version outside IRIP if it becomes client-facing.",
        ]
    if page == "Relationship Graph" and not completed["has_graph_edges"]:
        return [
            "Run Meeting Intelligence first to create people, company, and interaction edges.",
            "Return to Relationship Graph to inspect coverage.",
        ]
    if page == "Knowledge Base":
        return [
            "Upload approved research notes, PDFs, or CRM exports.",
            "Ask a focused question using the target company name.",
            "Use citations to support research memo claims.",
        ]
    return [
        "Run a full demo path: meeting extraction, CRM preflight, research memo, graph, token optimization, then dashboard.",
        "Use the latest dashboard KPIs to explain business value.",
    ]


def _relevant_modules(message: str, current_page: str | None) -> list[str]:
    text = message.lower()
    modules = [current_page] if current_page in MODULE_GUIDE else []
    for module, guide in MODULE_GUIDE.items():
        haystack = f"{module} {guide['purpose']}".lower()
        if any(token in haystack for token in text.split() if len(token) > 4):
            modules.append(module)
    return list(dict.fromkeys(module for module in modules if module))


def _compact(value: Any, limit: int = 1200) -> Any:
    text = str(value)
    if len(text) <= limit:
        return value
    return text[:limit] + "...[truncated]"
