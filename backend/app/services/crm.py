import csv
import re
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from backend.app.core.config import get_settings
from backend.app.models.schemas import (
    CrmPreflightRequest,
    CrmPreflightResponse,
    CrmSyncRequest,
    CrmSyncResponse,
)
from backend.app.services.storage import store

DEFAULT_FIELD_MAPPING = {
    "ExternalSystemId": "ExternalSystemId",
    "CompanyName": "CompanyName",
    "ContactName": "Name",
    "MeetingDate": "InteractionDate",
    "Summary": "Summary",
    "NextAction": "NextStep",
    "Owner": "Owner",
}

REQUIRED_FIELDS = ["ExternalSystemId", "CompanyName", "MeetingDate", "Summary"]


def preflight(req: CrmPreflightRequest) -> CrmPreflightResponse:
    warnings: list[dict[str, Any]] = []
    status = {}
    for field in REQUIRED_FIELDS:
        status[field] = "ok" if all(record.get(field) for record in req.records) else "missing"
    for record in req.records:
        warnings.extend(_duplicate_warnings(record))
        warnings.extend(_type_warnings(record))
    valid = all(value == "ok" for value in status.values()) and not any(
        warning["type"].endswith("_error") for warning in warnings
    )
    if warnings:
        store.add_metric("duplicate_warnings_caught", len([w for w in warnings if "duplicate" in w["type"]]))
    return CrmPreflightResponse(
        valid=valid,
        warnings=warnings,
        required_field_status=status,
        field_mapping=DEFAULT_FIELD_MAPPING,
        recommended_action=_recommended_action(valid, warnings, req.mode),
        records=[_normalize_record(record) for record in req.records],
    )


def sync(req: CrmSyncRequest) -> CrmSyncResponse:
    review = preflight(req)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    sync_log = {
        "target_object": req.target_object,
        "mode": req.mode,
        "record_count": len(req.records),
        "valid": review.valid,
        "warnings": review.warnings,
        "created_at": timestamp,
    }
    export_path = None
    status = "blocked_preflight" if not review.valid else "ready"
    if req.mode == "csv_export" and review.valid:
        export_path = str(_write_csv(review.records, req.export_filename or f"dealcloud_export_{timestamp}.csv"))
        status = "exported"
    elif req.mode in {"sdk_sync", "rest_api"} and review.valid:
        status = "mock_synced"
        sync_log["note"] = "Live DealCloud sync requires credentials and schema discovery."
    store.append("crm_sync_jobs", sync_log)
    return CrmSyncResponse(mode=req.mode, status=status, export_path=export_path, sync_log=sync_log)


def _normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized = {field: record.get(field) for field in DEFAULT_FIELD_MAPPING}
    if not normalized.get("ExternalSystemId"):
        normalized["ExternalSystemId"] = f"irip_{_slug(normalized.get('CompanyName') or 'unknown')}_{datetime.utcnow().timestamp():.0f}"
    return normalized


def _duplicate_warnings(record: dict[str, Any]) -> list[dict[str, Any]]:
    state = store.read()
    warnings = []
    company_name = record.get("CompanyName") or ""
    contact_name = record.get("ContactName") or ""
    for company in state.get("companies", []):
        score = SequenceMatcher(None, _norm(company_name), _norm(company.get("name", ""))).ratio()
        if company_name and score > 0.88:
            warnings.append(
                {
                    "type": "possible_duplicate_company",
                    "match_score": round(score, 2),
                    "existing_record": {"name": company.get("name"), "external_system_id": company.get("external_system_id")},
                }
            )
    for person in state.get("people", []):
        score = SequenceMatcher(None, _norm(contact_name), _norm(person.get("full_name", ""))).ratio()
        if contact_name and score > 0.86:
            warnings.append(
                {
                    "type": "possible_duplicate_person",
                    "match_score": round(score, 2),
                    "existing_record": {"name": person.get("full_name"), "company_id": person.get("company_id")},
                }
            )
    return warnings[:6]


def _type_warnings(record: dict[str, Any]) -> list[dict[str, Any]]:
    warnings = []
    email = record.get("Email")
    if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        warnings.append({"type": "email_type_error", "field": "Email", "value": email})
    date_value = record.get("MeetingDate")
    if date_value:
        try:
            datetime.fromisoformat(str(date_value)[:10])
        except ValueError:
            warnings.append({"type": "date_type_error", "field": "MeetingDate", "value": date_value})
    return warnings


def _recommended_action(valid: bool, warnings: list[dict[str, Any]], mode: str) -> str:
    if not valid:
        return "fix_required_fields_before_sync"
    if warnings:
        return "review_duplicate_then_sync"
    return "export_csv" if mode == "csv_export" else "sync_to_dealcloud"


def _write_csv(records: list[dict[str, Any]], filename: str) -> Path:
    settings = get_settings()
    path = settings.export_dir / re.sub(r"[^A-Za-z0-9_.-]+", "_", filename)
    fieldnames = list(DEFAULT_FIELD_MAPPING.keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    return path


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
