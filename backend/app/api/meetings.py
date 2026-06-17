from fastapi import APIRouter

from backend.app.core.security import require_scopes
from backend.app.models.schemas import MeetingExtractRequest, MeetingExtractResponse
from backend.app.services.meeting_intelligence import extract_meeting

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.post("/extract", response_model=MeetingExtractResponse)
async def extract(req: MeetingExtractRequest, _user=require_scopes("meeting:run")):
    return await extract_meeting(req)
