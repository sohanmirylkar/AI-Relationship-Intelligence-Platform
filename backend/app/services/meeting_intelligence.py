import re
from datetime import date
from typing import Any
from uuid import uuid4

from backend.app.models.schemas import (
    ActionItem,
    Company,
    Interaction,
    MeetingExtractRequest,
    MeetingExtractResponse,
    Person,
)
from backend.app.services.llm_router import llm_router
from backend.app.services.prompt_registry import (
    MEETING_EXTRACTION_PROMPT_VERSION,
    build_meeting_prompt,
)
from backend.app.services.storage import store
from backend.app.services.token_optimizer import estimate_tokens

ACTION_PATTERNS = [
    r"(?:action|next step|follow up|to do)[:\-]\s*(.+)",
    r"(?:we should|please|can you|will)\s+(.+?)(?:\.|\n|$)",
    r"(?:send|schedule|prepare|share|introduce|confirm)\s+(.+?)(?:\.|\n|$)",
]


async def extract_meeting(req: MeetingExtractRequest) -> MeetingExtractResponse:
    prompt = build_meeting_prompt(
        req.transcript_text, req.company_hint, req.attendees, req.interaction_date
    )
    llm_result = await llm_router.generate_structured(
        provider=req.provider,
        model=req.model,
        prompt=prompt,
        schema_name=MEETING_EXTRACTION_PROMPT_VERSION,
    )
    structured = llm_result.get("structured") or {}
    company = _company_from_structured(structured) or _extract_company(
        req.transcript_text, req.company_hint
    )
    people = _people_from_structured(structured, company["name"]) or _extract_people(
        req.transcript_text, req.attendees, company["name"]
    )
    action_items = _actions_from_structured(structured) or _extract_action_items(req.transcript_text)
    summary = structured.get("summary") or _summarize(
        req.transcript_text, company["name"], action_items
    )
    interaction_date = _parse_date(req.interaction_date)
    external_id = _external_id(company["name"], interaction_date)

    company_record = Company(
        name=company["name"],
        domain=company.get("domain"),
        external_system_id=f"company_{_slug(company['name'])}",
        confidence_score=company["confidence"],
    )
    company_saved = store.upsert_by_name("companies", "name", company_record.model_dump(mode="json"))

    saved_people = []
    for person in people:
        person_record = Person(
            company_id=company_saved["id"],
            full_name=person["full_name"],
            title=person.get("title"),
            email=person.get("email"),
            confidence_score=person["confidence"],
        )
        saved_people.append(store.upsert_by_name("people", "full_name", person_record.model_dump(mode="json")))

    interaction = Interaction(
        company_id=company_saved["id"],
        interaction_date=interaction_date,
        summary=summary,
        crm_record_ref=external_id,
        contains_pii=bool(re.search(r"[\w.\-]+@[\w.\-]+\.\w+", req.transcript_text)),
        metadata={"source": "meeting_extraction", "prompt_version": MEETING_EXTRACTION_PROMPT_VERSION},
    )
    interaction_saved = store.append("interactions", interaction)

    saved_actions = []
    for item in action_items:
        saved_actions.append(
            store.append(
                "action_items",
                ActionItem(
                    interaction_id=interaction_saved["id"],
                    owner=item.get("owner"),
                    due_date=item.get("due_date"),
                    description=item["description"],
                ),
            )
        )

    _record_relationships(company_saved, saved_people, interaction_saved)

    crm_payload = {
        "ExternalSystemId": external_id,
        "CompanyName": company["name"],
        "ContactName": saved_people[0]["full_name"] if saved_people else None,
        "MeetingDate": str(interaction_date) if interaction_date else None,
        "Summary": summary,
        "NextAction": saved_actions[0]["description"] if saved_actions else None,
        "Owner": "Analyst Demo User",
    }
    if isinstance(structured.get("crm_payload"), dict):
        crm_payload.update(
            {key: value for key, value in structured["crm_payload"].items() if value is not None}
        )
        crm_payload["ExternalSystemId"] = crm_payload.get("ExternalSystemId") or external_id
    confidence = {
        "company": company["confidence"],
        "contact": max([p["confidence"] for p in people], default=0.4),
        "next_action": 0.86 if saved_actions else 0.45,
        "source_traceability": 0.92,
        "live_llm": 1.0 if llm_result.get("mode", "").startswith("live") else 0.0,
    }
    if isinstance(structured.get("confidence"), dict):
        confidence.update(
            {
                key: _float_or_default(value, confidence.get(key, 0.7))
                for key, value in structured["confidence"].items()
            }
        )
    token_estimate = {
        "input_tokens_est": estimate_tokens(prompt),
        "output_tokens_est": 1200,
    }
    store.add_metric("manual_fields_avoided", len([v for v in crm_payload.values() if v]))
    return MeetingExtractResponse(
        summary=summary,
        action_items=saved_actions,
        extracted_entities={"companies": [company], "people": people},
        crm_payload=crm_payload,
        confidence=confidence,
        token_estimate=token_estimate,
        prompt_version=MEETING_EXTRACTION_PROMPT_VERSION,
        interaction_id=interaction_saved["id"],
    )


def _company_from_structured(payload: dict[str, Any]) -> dict[str, Any] | None:
    companies = payload.get("entities", {}).get("companies", [])
    if not companies:
        return None
    company = companies[0]
    name = company.get("name") or company.get("CompanyName")
    if not name:
        return None
    return {
        "name": name,
        "domain": company.get("domain"),
        "confidence": _float_or_default(company.get("confidence"), 0.9),
    }


def _people_from_structured(payload: dict[str, Any], company_name: str) -> list[dict[str, Any]]:
    people = payload.get("entities", {}).get("people", [])
    normalized = []
    for person in people:
        full_name = person.get("full_name") or person.get("name") or person.get("ContactName")
        if full_name:
            normalized.append(
                {
                    "full_name": full_name,
                    "title": person.get("title"),
                    "email": person.get("email"),
                    "company": person.get("company") or company_name,
                    "confidence": _float_or_default(person.get("confidence"), 0.88),
                }
            )
    return normalized


def _actions_from_structured(payload: dict[str, Any]) -> list[dict[str, Any]]:
    actions = payload.get("action_items", [])
    normalized = []
    for action in actions:
        if isinstance(action, str):
            normalized.append({"description": action, "owner": None, "due_date": None})
        elif action.get("description"):
            normalized.append(
                {
                    "description": action["description"],
                    "owner": action.get("owner"),
                    "due_date": action.get("due_date"),
                }
            )
    return normalized


def _float_or_default(value: Any, default: float) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


def _extract_company(text: str, hint: str | None) -> dict[str, Any]:
    if hint:
        name = hint.strip()
    else:
        candidates = re.findall(r"\b([A-Z][A-Za-z&.\-]+(?:\s+[A-Z][A-Za-z&.\-]+){0,3})\b", text)
        stop = {"Action", "Meeting", "Summary", "Next", "Follow", "Indago", "We", "The"}
        filtered = [candidate for candidate in candidates if candidate.split()[0] not in stop]
        name = filtered[0] if filtered else "Unknown Target Firm"
    domain_match = re.search(r"\b(?:https?://)?(?:www\.)?([a-z0-9\-]+\.[a-z]{2,})\b", text, re.I)
    return {"name": name, "domain": domain_match.group(1).lower() if domain_match else None, "confidence": 0.9 if hint else 0.72}


def _extract_people(text: str, attendees: list[str], company_name: str) -> list[dict[str, Any]]:
    people: list[dict[str, Any]] = []
    for attendee in attendees:
        if attendee.strip():
            people.append({"full_name": attendee.strip(), "company": company_name, "confidence": 0.92})
    email_matches = re.findall(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)?\s*<?([\w.\-]+@[\w.\-]+\.\w+)>?", text)
    for name, email in email_matches:
        full_name = name.strip() if name else email.split("@")[0].replace(".", " ").title()
        people.append({"full_name": full_name, "email": email, "company": company_name, "confidence": 0.88})
    title_matches = re.findall(
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+),?\s+(CIO|CEO|CFO|Partner|Principal|Director|Allocator|Analyst)",
        text,
    )
    for full_name, title in title_matches:
        people.append({"full_name": full_name, "title": title, "company": company_name, "confidence": 0.84})
    deduped = {}
    for person in people:
        deduped.setdefault(person["full_name"].lower(), person).update(person)
    return list(deduped.values())[:8]


def _extract_action_items(text: str) -> list[dict[str, Any]]:
    items = []
    for pattern in ACTION_PATTERNS:
        for match in re.findall(pattern, text, flags=re.I):
            description = match.strip(" -:\n\t")
            if len(description) > 8:
                items.append({"description": description[:240], "owner": "Analyst Demo User", "due_date": None})
    if not items and "follow" in text.lower():
        items.append({"description": "Send follow-up materials and confirm next meeting.", "owner": "Analyst Demo User", "due_date": None})
    return items[:6]


def _summarize(text: str, company_name: str, action_items: list[dict[str, Any]]) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    useful = [s for s in sentences if len(s) > 30][:3]
    summary = " ".join(useful) if useful else text[:420]
    next_action = f" Next action: {action_items[0]['description']}" if action_items else ""
    return f"{company_name} meeting summary: {summary[:700]}{next_action}"


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _external_id(company_name: str, interaction_date: date | None) -> str:
    return f"meet_{interaction_date or 'undated'}_{_slug(company_name)}_{uuid4().hex[:6]}"


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "unknown"


def _record_relationships(company: dict[str, Any], people: list[dict[str, Any]], interaction: dict[str, Any]) -> None:
    state = store.read()
    relationships = state.setdefault("relationships", [])
    for person in people:
        relationships.append(
            {
                "source_id": person["id"],
                "source_type": "Person",
                "target_id": company["id"],
                "target_type": "Company",
                "relationship_type": "WORKS_AT",
                "strength": 0.8,
            }
        )
        relationships.append(
            {
                "source_id": person["id"],
                "source_type": "Person",
                "target_id": interaction["id"],
                "target_type": "Interaction",
                "relationship_type": "ATTENDED",
                "strength": 0.75,
            }
        )
    relationships.append(
        {
            "source_id": interaction["id"],
            "source_type": "Interaction",
            "target_id": company["id"],
            "target_type": "Company",
            "relationship_type": "ABOUT",
            "strength": 0.9,
        }
    )
    store.write(state)
