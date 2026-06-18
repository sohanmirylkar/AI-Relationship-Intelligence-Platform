from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def token() -> str:
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "analyst", "password": "irip-demo", "scope": "meeting:run research:run crm:sync"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {token()}"}


def test_meeting_to_crm_flow():
    transcript = (
        "Meeting with Jane Doe, CIO at Blackstone. Discussed residential mortgage finance "
        "allocation appetite. Action: send follow-up deck and schedule second call."
    )
    extraction = client.post(
        "/api/v1/meetings/extract",
        headers=auth_headers(),
        json={
            "transcript_text": transcript,
            "company_hint": "Blackstone",
            "attendees": ["Jane Doe"],
            "interaction_date": "2026-06-16",
        },
    )
    assert extraction.status_code == 200
    payload = extraction.json()["crm_payload"]
    assert payload["CompanyName"] == "Blackstone"
    assert payload["ExternalSystemId"]

    preflight = client.post(
        "/api/v1/crm/preflight",
        headers=auth_headers(),
        json={"target_object": "Interaction", "mode": "csv_export", "records": [payload]},
    )
    assert preflight.status_code == 200
    assert preflight.json()["required_field_status"]["CompanyName"] == "ok"


def test_prompt_optimizer_reduces_cost():
    response = client.post(
        "/api/v1/prompts/optimize",
        headers=auth_headers(),
        json={
            "prompt": "Please very carefully analyze and summarize this transcript and create CRM fields.",
            "model": "claude-sonnet-4-6",
            "expected_output_tokens": 1000,
            "monthly_runs": 100,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["optimized"]["monthly_cost_usd"] <= payload["original"]["monthly_cost_usd"]


def test_dashboard_and_graph_are_available():
    graph = client.get("/api/v1/graph/all", headers=auth_headers())
    assert graph.status_code == 200
    assert "nodes" in graph.json()

    dashboard = client.get("/api/v1/dashboard/summary", headers=auth_headers())
    assert dashboard.status_code == 200
    assert "meetings_processed" in dashboard.json()
