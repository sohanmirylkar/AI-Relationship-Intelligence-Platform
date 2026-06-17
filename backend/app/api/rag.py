from fastapi import APIRouter

from backend.app.core.security import require_scopes
from backend.app.models.schemas import RagQueryRequest, RagQueryResponse
from backend.app.services.rag import answer_query

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/query", response_model=RagQueryResponse)
async def query(req: RagQueryRequest, _user=require_scopes("research:run")):
    return answer_query(req)
