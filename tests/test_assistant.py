from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def auth_headers() -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "analyst",
            "password": "irip-demo",
            "scope": "meeting:run research:run crm:sync",
        },
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_assistant_guides_current_workflow():
    response = client.post(
        "/api/v1/assistant/chat",
        headers=auth_headers(),
        json={
            "message": "What should I do next on this page?",
            "current_page": "Meeting Intelligence",
            "recent_state": {},
            "conversation": [],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer_markdown"]
    assert payload["suggested_next_steps"]
    assert "Meeting Intelligence" in payload["relevant_modules"]
    assert payload["context_summary"]["current_page"] == "Meeting Intelligence"
