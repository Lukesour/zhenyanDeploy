from fastapi.testclient import TestClient
from backend.app.main import app


client = TestClient(app)


def test_health_returns_partitioned_status():
    resp = client.get("/health")
    assert resp.status_code in (200, 503)
    data = resp.json()
    if resp.status_code == 200:
        assert "app" in data and isinstance(data["app"], dict)
        assert "model_available" in data and isinstance(data["model_available"], dict)
        assert "similarity_data_loaded" in data and isinstance(data["similarity_data_loaded"], dict)
        assert "config_ok" in data and isinstance(data["config_ok"], dict)
        # ensure no sensitive quota-like fields
        flat = str(data).lower()
        assert "quota" not in flat and "limit" not in flat
















