from fastapi import APIRouter

from backend.app.core.security import require_scopes
from backend.app.models.schemas import DeliverableRequest, DeliverableResponse
from backend.app.services.deliverables import generate_deliverable

router = APIRouter(prefix="/deliverables", tags=["deliverables"])


@router.post("/generate", response_model=DeliverableResponse)
async def generate(req: DeliverableRequest, _user=require_scopes("meeting:run")):
    return await generate_deliverable(req)
