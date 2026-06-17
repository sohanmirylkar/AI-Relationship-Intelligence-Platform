from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import (
    auth,
    crm,
    dashboard,
    deliverables,
    graph,
    ingest,
    meetings,
    prompts,
    rag,
    research,
)
from backend.app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Internal analyst console API for relationship intelligence, CRM upkeep, RAG, and AI cost governance.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in [
    auth.router,
    ingest.router,
    meetings.router,
    research.router,
    rag.router,
    prompts.router,
    crm.router,
    graph.router,
    deliverables.router,
    dashboard.router,
]:
    app.include_router(router, prefix=settings.api_prefix)


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}
