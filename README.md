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

The app runs in a local deterministic demo mode, so it works without Anthropic, OpenAI, or DealCloud credentials. The code keeps provider and CRM adapter boundaries so production credentials can be added without rewriting the workflow.

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
- Password: `indago-demo`

API docs are available at `http://localhost:8000/docs`.

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

## API Surface

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/auth/token` | OAuth2/JWT demo login |
| `POST` | `/api/v1/ingest/transcript` | Persist transcript uploads |
| `POST` | `/api/v1/ingest/document` | Persist and chunk PDF/DOCX/XLSX/TXT/CSV uploads |
| `POST` | `/api/v1/meetings/extract` | Extract summary, entities, action items, CRM payload |
| `POST` | `/api/v1/research/company` | Generate internal pre-meeting memo |
| `POST` | `/api/v1/rag/query` | Ask source-backed questions over indexed chunks |
| `POST` | `/api/v1/prompts/estimate` | Estimate token and model cost |
| `POST` | `/api/v1/prompts/optimize` | Compress prompt and route to cheaper viable model |
| `POST` | `/api/v1/crm/preflight` | Validate, dedupe, and map DealCloud-ready records |
| `POST` | `/api/v1/crm/sync` | Export CSV or mock live SDK/REST sync |
| `GET` | `/api/v1/graph/all` | Get graph projection |
| `POST` | `/api/v1/deliverables/generate` | Generate follow-up material |
| `GET` | `/api/v1/dashboard/summary` | Get operating KPIs |

## DealCloud Strategy

The implementation defaults to CSV export because live API access and Indago's schema are unspecified. The CRM service still reflects the production flow:

1. Discover schema.
2. Map logical fields to site-specific API names.
3. Validate required fields and types.
4. Preflight dedupe.
5. Upsert with `ExternalSystemId`.
6. Write sync log.
7. Pull history for confirmation.

Live SDK/REST sync is represented as a safe mock path until credentials and schema access are configured.

## Testing

```bash
pytest
ruff check .
```

The tests cover meeting-to-CRM, token optimization, dashboard/graph availability, ingestion/RAG, research memo generation, and deliverable generation.

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
tests/          unit/integration smoke tests
```

## Production Notes

- Replace the JSON store with PostgreSQL models and migrations.
- Store uploaded files in object storage instead of local disk.
- Add live Anthropic/OpenAI clients behind `LlmRouter`.
- Add live DealCloud schema discovery and OAuth2 token handling behind the CRM service.
- Use HTTPS-only deployment, secret rotation, row-level security, and audit-log export.
- Do not scrape LinkedIn. Use approved analyst research, licensed data, or lawful user-provided exports.
