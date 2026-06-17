from uuid import UUID

from fastapi import APIRouter, File, Form, UploadFile

from backend.app.core.security import require_scopes
from backend.app.models.schemas import DocumentRecord
from backend.app.services.ingestion import persist_upload

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/document", response_model=DocumentRecord)
async def upload_document(
    file: UploadFile = File(...),
    company_id: UUID | None = Form(default=None),
    _user=require_scopes("meeting:run"),
) -> DocumentRecord:
    return await persist_upload(file, company_id)


@router.post("/transcript", response_model=DocumentRecord)
async def upload_transcript(
    file: UploadFile = File(...),
    company_id: UUID | None = Form(default=None),
    _user=require_scopes("meeting:run"),
) -> DocumentRecord:
    return await persist_upload(file, company_id)
