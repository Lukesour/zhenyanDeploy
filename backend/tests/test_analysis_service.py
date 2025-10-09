from backend.services.analysis_service import AnalysisService
from backend.models.schemas import UserBackground, AnalysisReport, CompetitivenessAnalysis, SchoolRecommendations
from backend.tests.utils_spec import todo_spec


def test_no_similar_cases_returns_empty_structures(monkeypatch):
    svc = AnalysisService()

    # mock similarity matcher to return empty list
    monkeypatch.setattr(svc.similarity_matcher, "find_similar_cases", lambda ub, top_n=150: [])

    # mock gemini methods to still return reasonable defaults
    monkeypatch.setattr(svc.gemini_service, "analyze_competitiveness", lambda ub: type("X", (), {"strengths":"s","weaknesses":"w","summary":"sum"})())
    monkeypatch.setattr(svc.gemini_service, "generate_school_recommendations", lambda ub, cases: None)
    monkeypatch.setattr(svc.gemini_service, "analyze_single_case", lambda ub, case: None)
    monkeypatch.setattr(svc.gemini_service, "generate_background_improvement", lambda ub, w: None)

    ub = UserBackground(
        undergraduate_university="",
        undergraduate_major="",
        gpa=0,
        gpa_scale="4.0",
        graduation_year=2024,
        target_countries=["US"],
        target_majors=["CS"],
        target_degree_type="Master",
    )

    report = svc.radar_scoring_service.calculate_radar_scores(ub)  # ensure service usable
    assert len(report) == 5

    # Now run main report
    report = __import__("asyncio").run(svc.generate_analysis_report(ub))

    assert report is not None
    assert report.similar_cases == []
    assert report.school_recommendations.recommendations == []
    assert "未找到相似案例" in report.school_recommendations.analysis_summary

    # 如果未来需要在无相似且模型不可用时返回200或503的明确规范，使用TODO-SPEC提前标注
    # todo_spec("Define expected behavior when no similar cases AND model unavailable simultaneously")


def test_partial_failures_sets_degraded_and_collects_reasons(monkeypatch):
    svc = AnalysisService()

    # two fake similar cases to iterate
    monkeypatch.setattr(svc.similarity_matcher, "find_similar_cases", lambda ub, top_n=150: [{"case_data": {}} for _ in range(2)])

    # competitiveness ok
    monkeypatch.setattr(svc.gemini_service, "analyze_competitiveness", lambda ub: type("X", (), {"strengths":"s","weaknesses":"w","summary":"sum"})())
    # recommendations ok
    monkeypatch.setattr(svc.gemini_service, "generate_school_recommendations", lambda ub, cases: SchoolRecommendations(recommendations=[], analysis_summary="ok"))
    # first case fails, second succeeds with a simple object having required fields
    def analyze_case(ub, case):
        if not hasattr(analyze_case, "called"):
            analyze_case.called = True
            raise RuntimeError("boom")
        return type("C", (), {
            "case_id": 1,
            "admitted_university": "A",
            "admitted_program": "B",
            "gpa": "3.5/4.0",
            "language_score": "100",
            "language_test_type": None,
            "key_experiences": None,
            "undergraduate_info": "U",
            "comparison": type("Cmp", (), {"gpa":"3.5","university":"U","experience":"E"})(),
            "success_factors": "F",
            "takeaways": "T",
        })()
    monkeypatch.setattr(svc.gemini_service, "analyze_single_case", analyze_case)
    # background improvement fails
    def bg_fail(ub, w):
        raise RuntimeError("bg_fail")
    monkeypatch.setattr(svc.gemini_service, "generate_background_improvement", bg_fail)

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

    report = __import__("asyncio").run(svc.generate_analysis_report(ub))
    assert report.degraded is True
    assert report.partial_failures is not None
    assert "case_1" in report.partial_failures
    assert "background_improvement" in report.partial_failures


def test_analysis_report_serialization_excludes_none_fields():
    comp = CompetitivenessAnalysis(strengths="s", weaknesses="w", summary="sum")
    rec = SchoolRecommendations(recommendations=[], analysis_summary="sum")
    # Build with None optional fields
    ar = AnalysisReport(
        competitiveness=comp,
        school_recommendations=rec,
        similar_cases=[],
        radar_scores=[0,0,0,0,0],
        degraded=None,
        partial_failures=None,
    )
    payload = ar.model_dump(exclude_none=True)
    assert "degraded" not in payload
    assert "partial_failures" not in payload



