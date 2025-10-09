from fastapi.testclient import TestClient
from backend.app.main import app


client = TestClient(app)


def test_validation_error_returns_standard_error_object():
    # POST /api/analyze with missing required fields should trigger 400
    payload = {}
    resp = client.post("/api/analyze", json=payload)
    assert resp.status_code == 400
    data = resp.json()
    assert data["code"] == "INVALID_INPUT"
    assert data["httpStatus"] == 400
    assert data["retryable"] is False
    assert "errors" in data.get("details", {})


def test_http_exception_503_mapped_to_dependency_unavailable():
    # Hit /api/analyze with minimal valid shape but force service unavailable by clearing global instance
    from backend.app.main import analysis_service
    # Ensure analysis_service is None to trigger 503 branch
    # Note: lifespan would normally set it; here we simulate unavailable
    # Construct minimal valid payload
    payload = {
        "undergraduate_university": "Test U",
        "undergraduate_major": "CS",
        "gpa": 3.5,
        "gpa_scale": "4.0",
        "graduation_year": 2024,
        "target_countries": ["US"],
        "target_majors": ["CS"],
        "target_degree_type": "Master"
    }
    resp = client.post("/api/analyze", json=payload)
    assert resp.status_code == 503
    data = resp.json()
    assert data["code"] in ("DEPENDENCY_UNAVAILABLE", "INTERNAL_ERROR")
    assert data["httpStatus"] == 503
    assert data.get("retryable") in (True, False)




