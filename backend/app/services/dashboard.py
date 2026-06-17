from statistics import mean

from backend.app.models.schemas import DashboardSummary
from backend.app.services.storage import store


def dashboard_summary() -> DashboardSummary:
    state = store.read()
    metrics = state.get("metrics", {})
    sync_jobs = state.get("crm_sync_jobs", [])
    successful = [job for job in sync_jobs if job.get("valid")]
    module_activity = [
        {"module": "Meeting Intelligence", "count": len(state.get("interactions", []))},
        {"module": "Investor Research", "count": len(metrics.get("research_turnaround_minutes", []))},
        {"module": "CRM Autopilot", "count": len(sync_jobs)},
        {"module": "Knowledge Base", "count": len(state.get("chunks", []))},
        {"module": "Relationship Graph", "count": len(state.get("relationships", []))},
        {"module": "Token Optimizer", "count": len(metrics.get("token_reductions", []))},
    ]
    return DashboardSummary(
        meetings_processed=len(state.get("interactions", [])),
        average_manual_fields_avoided=_avg(metrics.get("manual_fields_avoided", [])),
        duplicate_warnings_caught=int(metrics.get("duplicate_warnings_caught", 0)),
        crm_sync_success_rate=round(len(successful) / len(sync_jobs), 2) if sync_jobs else 0.0,
        average_prompt_token_reduction=_avg(metrics.get("token_reductions", [])),
        estimated_ai_cost_saved=round(float(metrics.get("estimated_ai_cost_saved", 0.0)), 4),
        research_turnaround_minutes=_avg(metrics.get("research_turnaround_minutes", [])),
        graph_coverage={
            "companies": len(state.get("companies", [])),
            "people": len(state.get("people", [])),
            "edges": len(state.get("relationships", [])),
        },
        module_activity=module_activity,
    )


def _avg(values: list[float | int]) -> float:
    return round(mean(values), 2) if values else 0.0
