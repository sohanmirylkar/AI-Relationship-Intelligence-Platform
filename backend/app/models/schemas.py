from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    username: str
    full_name: str
    scopes: list[str] = []


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    scopes: list[str]


class Company(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    domain: str | None = None
    headquarters: str | None = None
    investment_focus: str | None = None
    external_system_id: str | None = None
    confidence_score: float = 0.75
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Person(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    company_id: UUID | None = None
    full_name: str
    title: str | None = None
    email: EmailStr | None = None
    linkedin_url: str | None = None
    confidence_score: float = 0.75
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Interaction(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    company_id: UUID | None = None
    source_document_id: UUID | None = None
    interaction_type: str = "meeting"
    interaction_date: date | None = None
    summary: str
    sentiment: str | None = None
    crm_record_ref: str | None = None
    contains_pii: bool = False
    metadata: dict[str, Any] = {}


class ActionItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    interaction_id: UUID | None = None
    owner: str | None = None
    due_date: str | None = None
    description: str
    status: Literal["open", "in_progress", "done"] = "open"


class DocumentRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    company_id: UUID | None = None
    interaction_id: UUID | None = None
    file_name: str
    mime_type: str
    storage_uri: str
    source: str = "upload"
    hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Chunk(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    chunk_index: int
    content: str
    metadata: dict[str, Any] = {}


class MeetingExtractRequest(BaseModel):
    transcript_text: str = Field(..., min_length=50)
    company_hint: str | None = None
    attendees: list[str] = []
    interaction_date: str | None = None
    provider: str = "local"
    model: str = "claude-haiku-4-5"


class MeetingExtractResponse(BaseModel):
    summary: str
    action_items: list[dict[str, Any]]
    extracted_entities: dict[str, Any]
    crm_payload: dict[str, Any]
    confidence: dict[str, float]
    token_estimate: dict[str, Any]
    prompt_version: str
    interaction_id: UUID


class ResearchCompanyRequest(BaseModel):
    company_name: str
    approved_sources: list[str] = []
    notes: str | None = None
    provider: str = "local"
    model: str = "claude-sonnet-4-6"


class ResearchCompanyResponse(BaseModel):
    memo_markdown: str
    decision_makers: list[dict[str, Any]]
    sources: list[dict[str, Any]]
    confidence: dict[str, float]
    token_estimate: dict[str, Any]


class RagQueryRequest(BaseModel):
    query: str = Field(..., min_length=3)
    company_id: UUID | None = None
    source_type: str | None = None
    top_k: int = 5


class RagQueryResponse(BaseModel):
    answer: str
    citations: list[dict[str, Any]]
    chunks: list[dict[str, Any]]


class PromptEstimateRequest(BaseModel):
    prompt: str
    model: str = "claude-sonnet-4-6"
    expected_output_tokens: int = 1200
    cached_input_tokens: int = 0
    monthly_runs: int = 1


class PromptEstimateResponse(BaseModel):
    model: str
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    monthly_cost_usd: float


class PromptOptimizeRequest(PromptEstimateRequest):
    target_reduction: float = 0.35


class PromptOptimizeResponse(BaseModel):
    original: PromptEstimateResponse
    optimized_prompt: str
    optimized: PromptEstimateResponse
    estimated_savings_usd: float
    routing_recommendation: dict[str, Any]


class CrmPreflightRequest(BaseModel):
    target_object: str = "Interaction"
    mode: Literal["csv_export", "sdk_sync", "rest_api"] = "csv_export"
    records: list[dict[str, Any]]


class CrmPreflightResponse(BaseModel):
    valid: bool
    warnings: list[dict[str, Any]]
    required_field_status: dict[str, str]
    field_mapping: dict[str, str]
    recommended_action: str
    records: list[dict[str, Any]]


class CrmSyncRequest(CrmPreflightRequest):
    export_filename: str | None = None


class CrmSyncResponse(BaseModel):
    mode: str
    status: str
    export_path: str | None = None
    sync_log: dict[str, Any]


class GraphResponse(BaseModel):
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]


class DeliverableRequest(BaseModel):
    deliverable_type: Literal["follow_up_email", "pitch_outline", "faq", "one_pager"]
    company_name: str
    meeting_summary: str | None = None
    research_memo: str | None = None
    crm_payload: dict[str, Any] = {}


class DeliverableResponse(BaseModel):
    title: str
    content_markdown: str
    source_fields: list[str]


class DashboardSummary(BaseModel):
    meetings_processed: int
    average_manual_fields_avoided: float
    duplicate_warnings_caught: int
    crm_sync_success_rate: float
    average_prompt_token_reduction: float
    estimated_ai_cost_saved: float
    research_turnaround_minutes: float
    graph_coverage: dict[str, int]
    module_activity: list[dict[str, Any]]
