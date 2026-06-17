from io import BytesIO

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def auth_headers() -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "analyst", "password": "indago-demo", "scope": "meeting:run research:run crm:sync"},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_ingest_rag_research_and_deliverable():
    headers = auth_headers()
    content = b"Blackstone notes mention asset-based finance, collateral reporting, and Jane Doe."
    upload = client.post(
        "/api/v1/ingest/document",
        headers=headers,
        files={"file": ("notes.txt", BytesIO(content), "text/plain")},
    )
    assert upload.status_code == 200

    rag = client.post(
        "/api/v1/rag/query",
        headers=headers,
        json={"query": "asset-based finance collateral reporting", "top_k": 3},
    )
    assert rag.status_code == 200
    assert rag.json()["citations"]

    research = client.post(
        "/api/v1/research/company",
        headers=headers,
        json={"company_name": "Blackstone", "approved_sources": ["internal notes"]},
    )
    assert research.status_code == 200
    assert "Firm Snapshot" in research.json()["memo_markdown"]

    deliverable = client.post(
        "/api/v1/deliverables/generate",
        headers=headers,
        json={
            "deliverable_type": "pitch_outline",
            "company_name": "Blackstone",
            "research_memo": research.json()["memo_markdown"],
        },
    )
    assert deliverable.status_code == 200
    assert "Pitch Outline" in deliverable.json()["content_markdown"]
