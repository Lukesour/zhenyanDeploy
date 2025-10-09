from fastapi.testclient import TestClient
from backend.app.main import app


client = TestClient(app)


def test_similar_cases_endpoint_basic():
    resp = client.get("/api/similar-cases?limit=3")
    # service may be unavailable under unit context; accept 200 or 503
    assert resp.status_code in (200, 503)
    if resp.status_code == 200:
        data = resp.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) <= 3


