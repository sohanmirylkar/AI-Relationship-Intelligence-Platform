from uuid import UUID

from fastapi import APIRouter

from backend.app.core.security import require_scopes
from backend.app.models.schemas import GraphResponse
from backend.app.services.relationship_graph import graph_for_company

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/company/{company_id}", response_model=GraphResponse)
async def company_graph(company_id: UUID, _user=require_scopes("research:run")):
    return graph_for_company(company_id)


@router.get("/all", response_model=GraphResponse)
async def full_graph(_user=require_scopes("research:run")):
    return graph_for_company()
