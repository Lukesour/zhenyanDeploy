import pytest
from backend.models.schemas import UserBackground, AnalysisReport, CompetitivenessAnalysis, SchoolRecommendations, SchoolRecommendation, CaseComparison, CaseAnalysis


def test_userbackground_list_defaults_are_independent():
    a = UserBackground(
        undergraduate_university="U1",
        undergraduate_major="CS",
        gpa=3.0,
        gpa_scale="4.0",
        graduation_year=2024,
        target_countries=["US"],
        target_majors=["CS"],
        target_degree_type="Master",
        application_year=2024,
    )
    b = UserBackground(
        undergraduate_university="U2",
        undergraduate_major="EE",
        gpa=3.5,
        gpa_scale="4.0",
        graduation_year=2025,
        target_countries=["US"],
        target_majors=["EE"],
        target_degree_type="Master",
        application_year=2026,
    )
    a.research_experiences.append({"title": "r1"})
    assert len(a.research_experiences) == 1
    assert len(b.research_experiences) == 0

    # 测试应届生判断逻辑
    assert a.is_recent_graduate() == True  # 申请年份和毕业年份相同
    assert b.is_recent_graduate() == False  # 申请年份和毕业年份不同


def test_analysisreport_radar_scores_constraints():
    comp = CompetitivenessAnalysis(strengths="s", weaknesses="w", summary="sum")
    rec = SchoolRecommendations(
        recommendations=[
            SchoolRecommendation(
                university="X", program="Y", reason="because", supporting_cases=[]
            )
        ],
        analysis_summary="ok",
    )
    case = CaseAnalysis(
        case_id=1,
        admitted_university="A",
        admitted_program="B",
        gpa="3.5/4.0",
        language_score="100",
        undergraduate_info="U",
        is_recent_graduate=True,
        comparison=CaseComparison(gpa="3.5", university="U", experience="E"),
        success_factors="F",
        takeaways="T",
    )

    # valid
    AnalysisReport(
        competitiveness=comp,
        school_recommendations=rec,
        similar_cases=[case],
        radar_scores=[0, 50, 100, 75, 10],
    )

    # invalid length
    with pytest.raises(Exception):
        AnalysisReport(
            competitiveness=comp,
            school_recommendations=rec,
            similar_cases=[case],
            radar_scores=[0, 50, 100, 75],
        )

    # out of range
    with pytest.raises(Exception):
        AnalysisReport(
            competitiveness=comp,
            school_recommendations=rec,
            similar_cases=[case],
            radar_scores=[-1, 0, 0, 0, 0],
        )




