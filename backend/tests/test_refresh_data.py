from fastapi.testclient import TestClient
from backend.app.main import app


client = TestClient(app)


def test_refresh_data_returns_accepted_and_runs_task(monkeypatch):
    # Arrange a dummy service to observe background task execution
    calls = {"ran": False}

    class DummyService:
        def refresh_similarity_data(self):
            calls["ran"] = True

    # Inject dummy analysis_service
    import backend.app.main as main_mod
    main_mod.analysis_service = DummyService()

    # Act
    resp = client.post("/api/refresh-data")

    # Assert response
    assert resp.status_code == 200
    assert "数据刷新任务已启动" in resp.json().get("message", "")
    # BackgroundTasks in TestClient are executed before response is returned, so flag should be True
    assert calls["ran"] is True


def test_refresh_data_returns_accepted_even_without_service(monkeypatch):
    # When service is not available, endpoint still returns accepted message
    import backend.app.main as main_mod
    main_mod.analysis_service = None

    resp = client.post("/api/refresh-data")
    assert resp.status_code == 200
    assert "数据刷新任务已启动" in resp.json().get("message", "")

















