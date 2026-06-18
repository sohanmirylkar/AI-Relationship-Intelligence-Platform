# AI Relationship Intelligence Platform

## A Business Paper For Organizational Review

### Prepared Product Name

**IRIP: AI Relationship Intelligence Platform**

### Product Category

Internal AI operating platform for investor relations, relationship intelligence, CRM quality, research automation, client deliverables, and AI cost governance.

---

## 1. Executive Summary

The AI Relationship Intelligence Platform, referred to as IRIP, is an internal business operations platform designed for asset-management and private-credit teams that need to convert relationship activity into structured, reliable, and actionable intelligence.

The product addresses a practical operational problem: relationship teams spend significant time after meetings summarizing notes, identifying action items, preparing follow-up materials, updating CRM records, researching prospective investors, searching internal knowledge, and managing AI usage manually. This creates delays, inconsistent data quality, duplicate records, missed follow-ups, and limited visibility into the real business value of AI.

IRIP solves this by creating a single analyst console where users can:

- Upload or paste meeting notes and transcripts.
- Extract summaries, attendees, action items, entities, and CRM-ready payloads.
- Validate CRM records before export or cloud sync.
- Detect possible duplicate companies and contacts.
- Generate investor research briefs from approved documents.
- Search internal notes and research with source-backed retrieval.
- Generate follow-up emails, FAQs, pitch outlines, and one-pagers.
- Visualize relationships between companies, people, meetings, and interactions.
- Estimate, optimize, and track AI token costs.
- Use an embedded intelligent assistant, IRIP Copilot, to guide the user through every step.
- Track management-level KPIs through an operational dashboard.

The platform is designed to be business-first and human-reviewed. It is not a black-box chatbot. It is a controlled internal workflow layer that supports the analyst, improves productivity, improves data quality, and gives management measurable visibility into AI-driven operational improvement.

---

## 2. Business Problem

Investor relations and business development workflows in asset management rely heavily on unstructured information. Important details often live in meeting notes, emails, PDFs, research memos, CRM exports, and analyst memory. Even when a firm uses a CRM, the quality of that CRM depends on consistent manual upkeep.

The main business problems are:

### 2.1 Manual Post-Meeting Work

After each investor or consultant meeting, analysts often need to:

- Write a meeting summary.
- Identify follow-up tasks.
- Prepare email drafts.
- Update CRM records.
- Assign next steps.
- Record relationship context.
- Create or update research notes.

This is repetitive and time-consuming.

### 2.2 CRM Data Quality Risk

CRM systems are only valuable when the data is complete, consistent, and current. Common issues include:

- Missing required fields.
- Duplicate contacts.
- Duplicate companies.
- Inconsistent company names.
- Incomplete meeting summaries.
- Poorly tracked follow-up items.
- Lack of source traceability.
- Repeated manual entry.

These issues make reporting unreliable and reduce confidence in relationship intelligence.

### 2.3 Fragmented Research Workflow

Research often requires analysts to search across internal notes, uploaded documents, public filings, prior meeting records, and manually prepared memos. Without a centralized retrieval layer, analysts lose time locating the right context and risk using outdated or incomplete information.

### 2.4 Limited Visibility Into AI Value

Many organizations experiment with AI tools but struggle to answer basic management questions:

- How much time did AI save?
- How many fields were generated instead of manually typed?
- How much did AI usage cost?
- Was the prompt optimized?
- Which model should be used for which task?
- Did AI improve data quality or only produce text?

IRIP is designed to answer these questions directly.

### 2.5 Lack Of User Guidance

Even a strong workflow platform can fail if users do not know what to do next. Analysts need contextual guidance:

- What have I already completed?
- What should I do next?
- Where should I do it in the application?
- What does this warning mean?
- What is missing before CRM sync?
- How should I explain this result to management?

IRIP Copilot was added to solve this adoption and usability challenge.

---

## 3. Product Vision

IRIP is designed as an internal analyst console for relationship-driven asset-management operations.

The vision is to make every investor interaction immediately useful, structured, searchable, validated, and measurable.

The product is built around a simple business principle:

> One meeting should not create avoidable manual work, duplicate records, inconsistent follow-up, or untracked AI spend.

Instead, one meeting should become:

- A structured summary.
- A set of action items.
- A CRM-ready record.
- A source for future research.
- A relationship graph update.
- A follow-up deliverable.
- A measurable contribution to productivity metrics.

---

## 4. Product Overview

IRIP includes the following core modules:

1. Meeting Intelligence
2. Investor Research
3. CRM Autopilot
4. Token Optimizer
5. Deliverables Generator
6. Relationship Graph
7. Knowledge Base and RAG
8. Dashboard
9. IRIP Copilot

Each module is business-oriented and supports a specific operational need.

---

## 5. Module Details

## 5.1 Meeting Intelligence

### Business Purpose

Meeting Intelligence converts raw meeting notes or transcripts into structured outputs that can be reviewed and used immediately.

### Inputs

- Pasted meeting notes.
- Uploaded transcript files.
- Company hint.
- Attendee list.
- Meeting date.

### Outputs

- Meeting summary.
- Extracted companies.
- Extracted people.
- Action items.
- CRM-ready payload.
- Confidence scores.
- Token estimate.

### Business Value

This module reduces manual post-meeting work and gives the analyst a high-quality draft instead of a blank page.

### Example Use

An analyst uploads a transcript from an allocator meeting. IRIP identifies the target firm, attendees, meeting summary, action items, and a CRM payload. The analyst reviews the result before moving it to CRM Autopilot.

---

## 5.2 Investor Research

### Business Purpose

Investor Research creates a source-backed pre-meeting brief using uploaded internal notes and approved research documents.

### Inputs

- Company name.
- Analyst notes.
- Approved source list.
- Indexed research documents.

### Outputs

- Firm snapshot.
- Relevant decision makers.
- Prior relationship history.
- Potential fit for asset-based finance discussion.
- Suggested talking points.
- Open questions.
- Source citations.

### Business Value

This reduces preparation time and improves meeting quality by giving the analyst a structured research memo.

---

## 5.3 CRM Autopilot

### Business Purpose

CRM Autopilot prepares and validates CRM records before export or sync.

### Inputs

- CRM payload from Meeting Intelligence.
- Manually edited CRM rows.
- CRM seed data.

### Outputs

- Required-field status.
- Duplicate warnings.
- Field mapping.
- Recommended action.
- CSV export.
- Supabase cloud sync result.
- Sync log.

### Validation Checks

The module checks:

- Company name.
- Meeting date.
- Summary.
- ExternalSystemId.
- Email format.
- Date format.
- Possible duplicate companies.
- Possible duplicate people.

### Business Value

CRM Autopilot improves data quality and reduces the risk of creating duplicate or incomplete records.

### Cloud Sync

The product uses Supabase as the open-source cloud provider. Supabase is Postgres-backed and supports REST access to database tables. IRIP can insert validated CRM payloads into a `crm_exports` table.

If Supabase credentials are not configured, IRIP returns a clear missing-credentials status rather than pretending a live sync occurred.

---

## 5.4 Token Optimizer

### Business Purpose

Token Optimizer connects prompt engineering to measurable cost control.

### Inputs

- Original prompt.
- Model selection.
- Expected output tokens.
- Cached input tokens.
- Monthly run estimate.

### Outputs

- Estimated input tokens.
- Estimated output tokens.
- Estimated cost.
- Monthly cost estimate.
- Optimized prompt.
- Recommended model routing.
- Estimated savings.

### Business Value

This module helps management understand AI cost and helps analysts use cheaper models where appropriate.

### Practical Example

A long, vague prompt can be compressed into a clearer operational prompt. The platform estimates the cost difference and logs the savings.

---

## 5.5 Deliverables Generator

### Business Purpose

Deliverables Generator creates polished business materials from meeting and research context.

### Deliverable Types

- Follow-up email.
- Pitch outline.
- FAQ.
- One-pager.

### Inputs

- Company name.
- Meeting summary.
- Research memo.
- CRM payload.

### Outputs

- Markdown business draft.
- Source field list.
- Title.

### Business Value

This helps analysts produce consistent follow-up material faster while keeping human review in the process.

---

## 5.6 Relationship Graph

### Business Purpose

Relationship Graph visualizes the connections between companies, people, meetings, and relationship events.

### Nodes

- Company
- Person
- Interaction

### Edges

- Person works at company.
- Person attended interaction.
- Interaction is about company.

### Business Value

This makes relationship intelligence visible instead of buried in notes or CRM text fields.

---

## 5.7 Knowledge Base And RAG

### Business Purpose

The Knowledge Base lets users upload approved documents and ask source-backed questions.

### Inputs

- TXT
- Markdown
- JSON
- CSV
- PDF
- DOCX
- XLSX

### Processing

Uploaded documents are persisted, parsed, chunked, and made searchable through a lightweight retrieval service.

### Outputs

- Answer.
- Citations.
- Retrieved chunks.
- Source titles.

### Business Value

This improves research quality and reduces the risk of unsupported claims.

---

## 5.8 Dashboard

### Business Purpose

The Dashboard gives management visibility into platform activity and business value.

### KPIs

- Meetings processed.
- Average manual fields avoided.
- Duplicate warnings caught.
- CRM sync success rate.
- Average prompt token reduction.
- Estimated AI cost saved.
- Research turnaround time.
- Graph coverage.
- Module activity.

### Business Value

The dashboard turns AI from an experimental tool into an accountable operating capability.

---

## 5.9 IRIP Copilot

### Business Purpose

IRIP Copilot is the intelligent assistant embedded across the entire platform.

It helps the user understand:

- What they are trying to do.
- What they have already done.
- What they should do next.
- Where to do it in the application.
- How to complete the step.
- What warnings mean.
- What is missing before continuing.
- How to explain results to the organization.

### Context Used By The Copilot

IRIP Copilot uses:

- Current Streamlit page.
- Recent UI state.
- Dashboard metrics.
- Latest company.
- Latest interaction.
- Latest CRM sync job.
- Open action items.
- Module guidebook.
- Conversation history.

### Provider Support

The assistant uses Anthropic or OpenAI when API keys are configured. It also has a deterministic local fallback so that tests and offline demos remain useful.

### Business Value

This reduces user confusion and improves adoption. It makes the product feel like a guided operating system rather than a set of disconnected tools.

---

## 6. End-To-End User Workflow

### Step 1: Upload Or Paste Meeting Notes

The analyst begins in Meeting Intelligence. They paste a transcript or upload notes.

### Step 2: Run Extraction

IRIP generates a summary, action items, entities, confidence scores, and CRM payload.

### Step 3: Review Results

The analyst reviews extracted fields and edits as needed.

### Step 4: Run CRM Preflight

The CRM payload is checked for required fields, formatting issues, and duplicate risks.

### Step 5: Export Or Sync CRM Record

If valid, the analyst can export a CSV or sync to Supabase.

### Step 6: Generate Research Memo

The analyst uses the Knowledge Base and Investor Research module to create a source-backed brief.

### Step 7: Generate Deliverables

The analyst creates a follow-up email, FAQ, one-pager, or pitch outline.

### Step 8: View Relationship Graph

The analyst checks how the meeting updated the relationship map.

### Step 9: Optimize AI Usage

The analyst uses Token Optimizer to reduce prompt cost and improve model routing.

### Step 10: Review Dashboard

Management can view operational impact through measurable KPIs.

### Step 11: Ask IRIP Copilot

At any step, the user can ask the Copilot what to do next.

---

## 7. AI Strategy

IRIP uses a provider abstraction layer so the organization is not locked into a single model provider.

### Supported Providers

- Anthropic
- OpenAI
- Local fallback

### Anthropic Usage

Anthropic models are used for:

- Structured meeting extraction.
- Research synthesis.
- Deliverable generation.
- IRIP Copilot guidance.

### OpenAI Usage

OpenAI models are supported through the Responses API for:

- General text generation.
- Research and synthesis.
- Assistant responses.
- Future workflow expansion.

### Local Fallback

If no API keys are configured, IRIP still runs in local deterministic mode for:

- Development.
- Testing.
- Offline demonstration.

### Business Reasoning

This design gives the organization flexibility. It can compare providers, control cost, and avoid dependency on one AI vendor.

---

## 8. Data Strategy

IRIP uses several types of data.

### Operational Data

- Companies
- People
- Interactions
- Action items
- Documents
- Chunks
- Prompt runs
- CRM sync jobs
- Relationship edges

### Uploaded Data

- Meeting transcripts
- Research notes
- PDFs
- Spreadsheets
- CRM exports
- Internal documents

### Evaluation Data

The project includes synthetic evaluation data under `demo_data/`.

This includes:

- Meeting transcripts.
- Expected extraction outputs.
- CRM seed records.
- Research documents.
- Prompt tests.

The data is synthetic and does not expose real investor or CRM information.

---

## 9. Evaluation And Testing

IRIP includes a repeatable evaluation harness.

### Evaluation Script

The evaluation script is:

`scripts/evaluate_demo_data.py`

### What It Scores

- Meeting extraction quality.
- CRM preflight behavior.
- RAG retrieval hit rate.
- Prompt-token reduction.

### Current Evaluation Metrics

The current evaluation run produced:

- Meeting extraction average score: 0.722
- CRM required-field pass rate: 0.5
- RAG hit rate: 1.0
- Prompt average reduction: 0.299

### Interpretation

These metrics are not intended to claim production-grade accuracy. They are intended to show that the product is measurable and can be improved through an evaluation process.

This is important because many AI prototypes are judged only by subjective impressions. IRIP includes a path toward objective testing.

---

## 10. Security And Governance

IRIP is designed with security and governance concerns in mind.

### Key Principles

- Do not commit API keys.
- Use environment variables or deployment secrets.
- Keep raw transcripts separate from generated summaries.
- Avoid logging full transcript bodies.
- Use human review before CRM export or sync.
- Use source-backed answers for research.
- Do not scrape restricted sites such as LinkedIn.
- Use approved data sources only.

### Authentication

The prototype includes OAuth2/JWT-style authentication with demo users.

### Authorization

The platform includes scopes for:

- Meeting workflows.
- Research workflows.
- CRM sync workflows.
- Admin configuration.

### Cloud Data

Supabase sync should use secure service-role credentials stored outside source code. In production, row-level security policies should be configured carefully.

---

## 11. Technology Architecture

### Front End

Streamlit is used for the analyst console because it enables rapid development of internal tools and data workflows.

### Back End

FastAPI is used for clean service boundaries and API-driven design.

### Storage

The prototype uses a local JSON store for speed and testability. The target production architecture is PostgreSQL.

### Cloud Provider

Supabase is used as the open-source cloud provider for CRM export and future database-backed workflows.

### Retrieval

The current retrieval implementation uses lightweight local embeddings and chunk search. The architecture can be upgraded to FAISS or pgvector.

### Graph

NetworkX-style graph modeling is used to represent companies, people, and interactions.

### AI Layer

The AI layer is abstracted through `LlmRouter`, which supports Anthropic, OpenAI, and local fallback.

---

## 12. Business Value

IRIP creates value in several ways.

### 12.1 Productivity

It reduces manual work after meetings by generating summaries, action items, CRM payloads, and deliverables.

### 12.2 Data Quality

It improves CRM quality through validation, duplicate warnings, and required-field checks.

### 12.3 Research Quality

It helps analysts generate source-backed research memos instead of relying only on memory or scattered notes.

### 12.4 Relationship Intelligence

It converts individual meetings into a relationship graph that can support future outreach and business development.

### 12.5 AI Cost Governance

It estimates and optimizes AI usage so the organization can manage cost.

### 12.6 Adoption

IRIP Copilot lowers the learning curve by guiding users through each workflow step.

---

## 13. Organizational Presentation Narrative

The product should be presented as an operational platform, not as a chatbot.

### Opening Statement

IRIP was built to solve a practical asset-management operations problem: one investor meeting should not create manual CRM upkeep, duplicate records, delayed follow-up, scattered research, and invisible AI spend.

### Demo Sequence

1. Start with Meeting Intelligence.
2. Upload a sample transcript.
3. Show extracted summary, action items, entities, and CRM payload.
4. Ask IRIP Copilot what to do next.
5. Move to CRM Autopilot.
6. Show duplicate warnings and required-field status.
7. Export or sync to Supabase.
8. Move to Knowledge Base and Investor Research.
9. Generate a source-backed memo.
10. Move to Deliverables Generator.
11. Create a follow-up email or pitch outline.
12. Move to Relationship Graph.
13. Show relationships created from the workflow.
14. Move to Token Optimizer.
15. Show prompt reduction and cost savings.
16. End with Dashboard.

### Closing Message

The key message is that IRIP turns unstructured relationship activity into structured, reviewable, CRM-ready, source-backed, measurable intelligence.

---

## 14. Implementation Status

The product currently includes:

- FastAPI backend.
- Streamlit front end.
- OAuth2/JWT demo authentication.
- Meeting extraction.
- Research memo generation.
- RAG knowledge base.
- CRM preflight.
- CSV export.
- Supabase sync.
- Token optimization.
- Deliverables generation.
- Relationship graph.
- Dashboard metrics.
- IRIP Copilot.
- Synthetic demo dataset.
- Evaluation harness.
- Automated tests.
- Docker support.
- GitHub Actions CI.

---

## 15. Future Roadmap

### Phase 1: Production Data Layer

- Replace local JSON store with PostgreSQL.
- Add migrations.
- Add pgvector or FAISS-backed retrieval.
- Add object storage for uploaded files.

### Phase 2: Supabase Hardening

- Add row-level security.
- Add authenticated user mapping.
- Add audit tables.
- Add secure storage buckets.

### Phase 3: Evaluation Expansion

- Increase evaluation set from 3 meetings to 25 or more.
- Add labelled research memo tests.
- Add duplicate-detection benchmarks.
- Add human review scoring.

### Phase 4: Workflow Automation

- Add background jobs.
- Add retry queues.
- Add notification triggers.
- Add scheduled CRM quality reviews.

### Phase 5: Enterprise Readiness

- Add SSO.
- Add role-based access policies.
- Add deployment monitoring.
- Add audit log export.
- Add production secrets management.

---

## 16. Risks And Mitigations

### Risk: Incorrect AI Extraction

Mitigation:

- Confidence scores.
- Human review.
- Evaluation harness.
- Source traceability.

### Risk: CRM Data Pollution

Mitigation:

- Preflight validation.
- Duplicate warnings.
- Required-field checks.
- Manual review before sync.

### Risk: Sensitive Data Exposure

Mitigation:

- Environment-based secrets.
- Avoid logging raw transcripts.
- Use approved data sources.
- Production RLS policies.

### Risk: User Confusion

Mitigation:

- IRIP Copilot.
- Module-specific next-step guidance.
- Dashboard feedback.

### Risk: AI Cost Growth

Mitigation:

- Token Optimizer.
- Model routing.
- Cost estimates.
- Dashboard metrics.

---

## 17. Conclusion

IRIP is a business-focused AI platform for relationship-driven asset-management operations. It is not merely a chatbot or a document summarizer. It is an integrated workflow system that connects meetings, research, CRM quality, deliverables, relationship intelligence, AI cost governance, and guided user support.

The product demonstrates how AI can be used responsibly inside an organization:

- It keeps humans in the loop.
- It validates data before sync.
- It uses source-backed research.
- It tracks cost and operational value.
- It guides users through complex workflows.
- It is measurable through evaluation and dashboard metrics.

For an organization, the main value of IRIP is that it turns relationship activity into structured business intelligence while reducing manual effort and improving data quality.

The recommended next step is to pilot IRIP with a small set of synthetic and approved internal data, evaluate extraction quality, validate the CRM sync process, and then determine which production workflows should be prioritized first.
