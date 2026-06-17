MEETING_EXTRACTION_PROMPT_VERSION = "meeting_extraction_v1"
RESEARCH_MEMO_PROMPT_VERSION = "research_memo_v1"


def build_meeting_prompt(
    transcript: str, company_hint: str | None, attendees: list[str], interaction_date: str | None
) -> str:
    attendees_csv = ", ".join(attendees) if attendees else "unknown"
    return f"""SYSTEM
You are an internal investor-relations operations analyst for an asset manager.
Extract factual CRM-ready information from meeting notes. Do not guess. If a field is absent,
return null. Return valid JSON only.

USER
<task>Extract a structured interaction record, action items, and contact/company entities.</task>
<context>
<company_hint>{company_hint or "unknown"}</company_hint>
<attendees>{attendees_csv}</attendees>
<interaction_date>{interaction_date or "unknown"}</interaction_date>
</context>
<schema>
summary, entities.companies, entities.people, action_items, crm_payload, confidence
</schema>
<input>
{transcript}
</input>"""


def build_research_prompt(company_name: str, retrieved_context: str, notes: str | None) -> str:
    return f"""SYSTEM
You are preparing a concise internal pre-meeting brief for senior investor-relations staff.
Use only the provided sources. Separate facts, inferred opportunities, and open questions.

USER
<instructions>
Write: Firm snapshot, Relevant decision makers, Prior relationship history, Potential fit for
asset-based finance discussion, Suggested talking points, Open questions.
</instructions>
<company>{company_name}</company>
<analyst_notes>{notes or ""}</analyst_notes>
<documents>
{retrieved_context}
</documents>"""
