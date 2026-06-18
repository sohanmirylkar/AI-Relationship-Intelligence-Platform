from fastapi import APIRouter

from backend.app.core.security import require_scopes
from backend.app.models.schemas import ResearchCompanyRequest, ResearchCompanyResponse
from backend.app.services.research import generate_research_memo

router = APIRouter(prefix="/research", tags=["research"])


@router.post("/company", response_model=ResearchCompanyResponse)
async def research_company(req: ResearchCompanyRequest, _user=require_scopes("research:run")):
    return await generate_research_memo(req)
