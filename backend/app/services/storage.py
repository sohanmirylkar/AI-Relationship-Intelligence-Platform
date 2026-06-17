import json
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from backend.app.core.config import get_settings


class JsonStore:
    """Small durable store for the demo; production swaps this for PostgreSQL."""

    def __init__(self, path: Path | None = None) -> None:
        settings = get_settings()
        self.path = path or settings.data_dir / "irip_state.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        if not self.path.exists():
            self.path.write_text(json.dumps(self._empty_state(), indent=2), encoding="utf-8")

    @staticmethod
    def _empty_state() -> dict[str, Any]:
        return {
            "companies": [],
            "people": [],
            "interactions": [],
            "action_items": [],
            "documents": [],
            "chunks": [],
            "prompt_runs": [],
            "crm_sync_jobs": [],
            "relationships": [],
            "metrics": {
                "duplicate_warnings_caught": 0,
                "estimated_ai_cost_saved": 0.0,
                "manual_fields_avoided": [],
                "token_reductions": [],
                "research_turnaround_minutes": [],
            },
        }

    def read(self) -> dict[str, Any]:
        with self._lock:
            return json.loads(self.path.read_text(encoding="utf-8"))

    def write(self, state: dict[str, Any]) -> None:
        with self._lock:
            self.path.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")

    def append(self, collection: str, item: BaseModel | dict[str, Any]) -> dict[str, Any]:
        state = self.read()
        payload = item.model_dump(mode="json") if isinstance(item, BaseModel) else item
        state.setdefault(collection, []).append(payload)
        self.write(state)
        return payload

    def upsert_by_name(self, collection: str, name_field: str, item: dict[str, Any]) -> dict[str, Any]:
        state = self.read()
        normalized = _norm(item.get(name_field, ""))
        for existing in state.setdefault(collection, []):
            if _norm(existing.get(name_field, "")) == normalized:
                existing.update({k: v for k, v in item.items() if v is not None})
                self.write(state)
                return existing
        state[collection].append(item)
        self.write(state)
        return item

    def get(self, collection: str, item_id: UUID | str) -> dict[str, Any] | None:
        item_id = str(item_id)
        return next((item for item in self.read().get(collection, []) if item.get("id") == item_id), None)

    def add_metric(self, key: str, value: Any) -> None:
        state = self.read()
        metrics = state.setdefault("metrics", {})
        if isinstance(metrics.get(key), list):
            metrics[key].append(value)
        elif isinstance(value, (int, float)):
            metrics[key] = float(metrics.get(key, 0)) + value
        else:
            metrics[key] = value
        self.write(state)


def _norm(value: str) -> str:
    return "".join(ch.lower() for ch in value if ch.isalnum())


store = JsonStore()
