import asyncio
import pytest
from backend.services.analysis_service import AnalysisService
from backend.models.schemas import UserBackground, SchoolRecommendations


@pytest.mark.asyncio
async def test_analysis_service_retries_on_runtimeerror(monkeypatch):
    svc = AnalysisService()

    # no similar cases to simplify path
    monkeypatch.setattr(svc.similarity_matcher, "find_similar_cases", lambda ub, top_n=150: [])

    # counters
    calls = {"compet": 0}

    def flaky_compet(ub):
        calls["compet"] += 1
        if calls["compet"] < 3:
            raise RuntimeError("flaky")
        return type("X", (), {"strengths":"s","weaknesses":"w","summary":"sum"})()

    monkeypatch.setattr(svc.gemini_service, "analyze_competitiveness", flaky_compet)

    # empty recs path not used (no similar cases)
    # speed up retry using fake sleep and deterministic rng
    async def fake_sleep(_):
        return None

    def fake_rng():
        return 0.0

    svc._retry_sleep = fake_sleep
    svc._retry_rng = fake_rng

    ub = UserBackground(
        undergraduate_university="U",
        undergraduate_major="M",
        gpa=3.2,
        gpa_scale="4.0",
        graduation_year=2024,
        target_countries=["US"],
        target_majors=["CS"],
        target_degree_type="Master",
    )

    report = await svc.generate_analysis_report(ub)
    assert calls["compet"] == 3
    assert report is not None
















