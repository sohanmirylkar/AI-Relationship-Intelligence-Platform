from fastapi import APIRouter

from backend.app.core.security import require_scopes
from backend.app.models.schemas import DashboardSummary
from backend.app.services.dashboard import dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def summary(_user=require_scopes("meeting:run")):
    return dashboard_summary()
