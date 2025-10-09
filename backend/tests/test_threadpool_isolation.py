import asyncio
import time
import pytest

from backend.services.analysis_service import AnalysisService
from backend.models.schemas import UserBackground


@pytest.mark.asyncio
async def test_threadpool_isolation_non_blocking_event_loop(monkeypatch):
    svc = AnalysisService()

    # no similar cases path to keep flow minimal
    monkeypatch.setattr(svc.similarity_matcher, "find_similar_cases", lambda ub, top_n=150: [])

    # blocking sync function to simulate external call (~0.2s)
    def blocking_compet(_):
        time.sleep(0.2)
        return type("X", (), {"strengths":"s","weaknesses":"w","summary":"sum"})()

    monkeypatch.setattr(svc.gemini_service, "analyze_competitiveness", blocking_compet)
    # background improvement quick no-op
    monkeypatch.setattr(svc.gemini_service, "generate_background_improvement", lambda ub, w: None)

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

    # Start analysis task
    task = asyncio.create_task(svc.generate_analysis_report(ub))
    # If event loop is not blocked, this short sleep completes before analysis ends
    await asyncio.sleep(0.01)
    assert not task.done()

    report = await task
    assert report is not None
    assert len(report.radar_scores) == 5
















