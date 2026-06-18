# AI Relationship Intelligence Platform

IRIP is an end-to-end internal analyst console for investor relations, CRM upkeep, post-meeting execution, research automation, relationship mapping, and AI cost governance.

It implements the report's seven-module platform shape:

1. Meeting Intelligence
2. Investor Research
3. CRM Autopilot
4. Token Optimizer
5. Deliverables Generator
6. Relationship Graph
7. Knowledge Base and RAG
8. IRIP Copilot workflow assistant

The app uses Anthropic and OpenAI when API keys are configured through environment variables. It keeps a local no-key fallback for tests and offline development. CRM export can be downloaded as CSV or synced to Supabase, an open-source Postgres-backed cloud platform.

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn backend.app.main:app --reload
```

In another terminal:

```bash
streamlit run streamlit_app/app.py
```

Open `http://localhost:8501`.

Demo login:

- Username: `analyst`
- Password: `irip-demo`

API docs are available at `http://localhost:8000/docs`.

## API Keys And Cloud Sync

Create a local `.env` from `.env.example` and add your keys:

```bash
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
DEFAULT_LLM_PROVIDER=anthropic
```

Anthropic is the default provider for extraction, research, and deliverables. To use OpenAI for a request, pass `"provider": "openai"` and an OpenAI model in the API payload. The implementation calls the OpenAI Responses API and Anthropic Messages API directly through the provider adapter.

For cloud CRM export, create the `crm_exports` table from `docs/database_schema.sql`, then set:

```bash
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_CRM_TABLE=crm_exports
```

Keep these values in environment variables only. Do not commit real keys.

## Docker

```bash
docker compose up --build
```

Services:

- FastAPI: `http://localhost:8000`
- Streamlit: `http://localhost:8501`
- PostgreSQL: `localhost:5432`

The API uses a local JSON store by default for demo speed. `docs/database_schema.sql` contains the PostgreSQL target schema, including row-level security enablement for sensitive operational tables.

## Demo Flow

1. Open Meeting Intelligence.
2. Use `seed_data/demo_transcript.txt` or the prefilled sample notes.
3. Run extraction and inspect summary, people, action items, CRM payload, confidence, and token estimate.
4. Run CRM preflight to see required-field validation and duplicate warnings.
5. Open Investor Research and generate a source-backed pre-meeting brief.
6. Open Relationship Graph and verify company/contact/interaction edges.
7. Open Token Optimizer and compare original vs optimized prompt cost.
8. Open Deliverables Generator to create a follow-up email, FAQ, one-pager, or pitch outline.
9. Open Knowledge Base, upload `seed_data/company_research_notes.md`, and ask a RAG question.
10. Open Dashboard to show time, cost, data-quality, sync, and graph-coverage KPIs.
11. Use IRIP Copilot in the sidebar during each step to ask what has been done, what should happen next, where to do it, and how to explain the result.

## Business Paper

The visual organization-submission paper is available at:

- `docs/IRIP_Business_Paper_Visual.html`

Open it in a browser to review the full business narrative, product diagrams, workflow charts, KPI visuals, roadmap, risk matrix, and presentation script.

## API Surface

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/auth/token` | OAuth2/JWT demo login |
| `POST` | `/api/v1/assistant/chat` | Workflow-aware assistant guidance |
| `POST` | `/api/v1/ingest/transcript` | Persist transcript uploads |
| `POST` | `/api/v1/ingest/document` | Persist and chunk PDF/DOCX/XLSX/TXT/CSV uploads |
| `POST` | `/api/v1/meetings/extract` | Extract summary, entities, action items, CRM payload |
| `POST` | `/api/v1/research/company` | Generate internal pre-meeting memo |
| `POST` | `/api/v1/rag/query` | Ask source-backed questions over indexed chunks |
| `POST` | `/api/v1/prompts/estimate` | Estimate token and model cost |
| `POST` | `/api/v1/prompts/optimize` | Compress prompt and route to cheaper viable model |
| `POST` | `/api/v1/crm/preflight` | Validate, dedupe, and map CRM-ready records |
| `POST` | `/api/v1/crm/sync` | Export CSV or sync validated payloads to Supabase |
| `GET` | `/api/v1/graph/all` | Get graph projection |
| `POST` | `/api/v1/deliverables/generate` | Generate follow-up material |
| `GET` | `/api/v1/dashboard/summary` | Get operating KPIs |

## Supabase CRM Export Strategy

The implementation defaults to CSV export and supports live Supabase sync when credentials are configured. Supabase is open source, Postgres-backed, and exposes database tables through a REST API, making it a good replacement cloud layer for this prototype.

1. Map logical CRM fields to the export payload.
2. Validate required fields and types.
3. Preflight dedupe.
4. Export CSV or insert into `crm_exports`.
5. Preserve `ExternalSystemId` for idempotent downstream processing.
6. Write a local sync log with response status.

If Supabase credentials are absent, the sync endpoint returns a clear `missing_supabase_credentials` status instead of pretending a live sync occurred.

## Testing

```bash
pytest
ruff check .
```

The tests cover meeting-to-CRM, token optimization, dashboard/graph availability, ingestion/RAG, research memo generation, and deliverable generation.

## IRIP Copilot

The Streamlit sidebar includes an always-available assistant called IRIP Copilot. It receives the current page, recent UI state, stored workflow activity, dashboard metrics, and module guidebook context. It can answer:

- what the analyst has done so far
- what the next best step is
- where to perform that step in the app
- what missing prerequisite is blocking progress
- how to explain a result during a demo

When `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` is configured, the copilot uses the live provider adapter. Without keys, it still returns deterministic workflow guidance for tests and offline demos.

## Demo Data And Evaluation

Synthetic demo/evaluation data lives in `demo_data/`:

- `meeting_transcripts/`: labelled investor/consultant meeting notes.
- `expected_outputs/`: expected companies, people, actions, and required CRM fields.
- `crm_seed.csv`: CRM rows with duplicate-like and missing-field examples.
- `research_docs/`: source notes for RAG and research memo demos.
- `prompt_tests.csv`: verbose prompts for token optimization.

Run the evaluation harness:

```bash
python scripts/evaluate_demo_data.py
```

It writes `reports/demo_eval_report.json` and prints headline metrics:

- meeting extraction average score
- CRM required-field pass rate
- RAG hit rate
- average prompt-token reduction

Use those metrics in the organization demo to show that IRIP is measurable: it is not just producing text, it is being tested for extraction quality, data-quality warnings, retrieval relevance, and AI-cost reduction.

## Project Layout

```text
backend/app/
  api/          FastAPI route modules
  core/         settings and security
  models/       Pydantic contracts
  services/     domain logic
streamlit_app/  analyst console
docs/           architecture and PostgreSQL schema
seed_data/      demo transcript and research notes
demo_data/      labelled synthetic evaluation pack
scripts/        evaluation utilities
tests/          unit/integration smoke tests
```

## Production Notes

- Replace the JSON store with PostgreSQL models and migrations.
- Store uploaded files in object storage instead of local disk.
- Add live Anthropic/OpenAI clients behind `LlmRouter`.
- Add Supabase RLS policies, storage buckets, and authenticated user-scoped CRM export views.
- Use HTTPS-only deployment, secret rotation, row-level security, and audit-log export.
- Do not scrape LinkedIn. Use approved analyst research, licensed data, or lawful user-provided exports.
