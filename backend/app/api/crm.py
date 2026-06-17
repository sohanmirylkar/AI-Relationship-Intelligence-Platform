from fastapi import APIRouter

from backend.app.core.security import require_scopes
from backend.app.models.schemas import (
    CrmPreflightRequest,
    CrmPreflightResponse,
    CrmSyncRequest,
    CrmSyncResponse,
)
from backend.app.services.crm import preflight, sync

router = APIRouter(prefix="/crm", tags=["crm"])


@router.post("/preflight", response_model=CrmPreflightResponse)
async def crm_preflight(req: CrmPreflightRequest, _user=require_scopes("crm:sync")):
    return preflight(req)


@router.post("/sync", response_model=CrmSyncResponse)
async def crm_sync(req: CrmSyncRequest, _user=require_scopes("crm:sync")):
    return sync(req)
