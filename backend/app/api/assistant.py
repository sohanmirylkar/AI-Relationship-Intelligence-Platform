from fastapi import APIRouter

from backend.app.core.security import require_scopes
from backend.app.models.schemas import AssistantChatRequest, AssistantChatResponse
from backend.app.services.assistant import chat_with_assistant

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/chat", response_model=AssistantChatResponse)
async def chat(req: AssistantChatRequest, _user=require_scopes("meeting:run")):
    return await chat_with_assistant(req)
