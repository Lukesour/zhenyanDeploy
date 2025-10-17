from datetime import datetime, timezone

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.api.auth import get_current_user
from backend.models.user_models import UserInfo, UserStatus


def override_current_user():
    return UserInfo(
        id=1,
        phone="13100000000",
        email="test@example.com",
        status=UserStatus.ACTIVE,
        remaining_analyses=5,
        total_analyses_used=0,
        invitation_code=None,
        invited_count=0,
        created_at=datetime.now(timezone.utc),
        last_login_at=datetime.now(timezone.utc),
        profile_data=None,
    )


app.dependency_overrides[get_current_user] = override_current_user
client = TestClient(app)


def teardown_module(_):
    app.dependency_overrides.pop(get_current_user, None)


def test_structure_brainstorm_endpoint_returns_canonical_major():
    payload = {
        "raw_experiences": [
            {
                "id": "exp-1",
                "type": "internship",
                "title": "Data Science Intern",
                "org": "TechCorp",
                "details": ["Developed ML pipeline", "Improved accuracy by 8%"],
                "tags": ["数据科学", "机器学习"],
                "highlight": True,
            }
        ],
        "target_major": "CS",
        "target_degree": "Master",
        "tags": ["机器学习"],
        "prompts": ["focus on research"],
    }

    response = client.post("/documents/brainstorm/structure", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["request_id"]
    assert len(data["structured_experiences"]) == 1
    assert "计算机" in data["tags"]
    assert data["highlights"] == ["exp-1"]


def test_generate_cv_endpoint_returns_markdown():
    payload = {
        "structured_experiences": [
            {
                "id": "exp-1",
                "type": "research",
                "title": "AI Research Project",
                "org": "University Lab",
                "details": ["Published one IEEE paper"],
                "tags": ["AI", "Research"],
            }
        ],
        "template_type": "academic",
        "language": "en",
        "length": "1page",
        "tone": "sincere",
        "highlight_ids": ["exp-1"],
        "tag_preferences": ["AI"],
        "ats_friendly": True,
        "mirror_version": True,
        "include_preferences": {
            "languages": ["en"],
            "style": "formal",
            "length": "1 page",
            "notes": "Keep concise",
        },
        "major": "CS",
        "degree": "Master",
    }

    response = client.post("/documents/cv/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["request_id"]
    assert "cv_markdown" in data and data["cv_markdown"].startswith("# Curriculum Vitae")
    assert data["cv_json"]["profile"]["targetMajor"] == "计算机"
    assert data["cv_plaintext"]
    assert data["mirror_versions"]


def test_generate_ps_endpoint_returns_paragraphs():
    payload = {
        "structured_experiences": [
            {
                "id": "exp-1",
                "type": "internship",
                "title": "Software Engineer Intern",
                "org": "InnovateX",
                "details": ["Built internal tooling"],
                "tags": ["Software", "Teamwork"],
            }
        ],
        "target_major": "Computer Science",
        "target_schools": ["MIT", "CMU"],
        "outline": "standard",
        "word_limit": [700, 900],
        "tone": "sincere",
        "emphasis": {"research": True, "career": False},
        "preferences": {
            "language": "en",
            "voice": "professional",
            "length": "1page",
            "highlight_ids": ["exp-1"],
            "gap_ids": [],
            "tags": ["innovation"],
        },
        "imports": {"program_brief": "Leading AI program", "keywords": ["AI", "innovation"]},
    }

    response = client.post("/documents/ps/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["request_id"]
    assert len(data["outline_checked"]) == 3
    assert len(data["ps_paragraphs"]) >= 3
    assert "计算机" in data["ps_full_text"]
    assert data["revision_suggestions"]
