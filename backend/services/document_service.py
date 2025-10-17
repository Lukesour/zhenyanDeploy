from __future__ import annotations

import textwrap
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Sequence

from backend.models.document_models import (
    BrainstormStructureRequest,
    BrainstormStructureResponse,
    CvGenerationRequest,
    CvGenerationResponse,
    DocumentExperienceInput,
    DocumentExperienceItem,
    LlmUsage,
    MirrorVersion,
    PsGenerationRequest,
    PsGenerationResponse,
    PsOutlineItem,
    PsParagraph,
    PsVariant,
)
from backend.services.major_taxonomy_service import major_taxonomy_service


class DocumentService:
    """Lightweight document generation helpers (rule-based)."""

    def __init__(self):
        self.taxonomy_service = major_taxonomy_service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def structure_brainstorm(
        self, payload: BrainstormStructureRequest
    ) -> BrainstormStructureResponse:
        canonical_major = self._normalise_major(payload.target_major)

        structured_experiences: List[DocumentExperienceItem] = []
        aggregated_tags = set(payload.tags or [])

        for index, raw in enumerate(payload.raw_experiences):
            item = self._normalise_experience(raw, fallback_index=index)
            structured_experiences.append(item)
            aggregated_tags.update(item.tags)

        if canonical_major:
            aggregated_tags.add(canonical_major)

        highlights = [item.id for item in structured_experiences if item.highlight]

        usage = LlmUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)

        metadata = {
            "target_major": canonical_major,
            "target_degree": payload.target_degree,
            "prompt_count": len(payload.prompts or []),
            "experience_count": len(structured_experiences),
        }

        return BrainstormStructureResponse(
            request_id=str(uuid.uuid4()),
            structured_experiences=structured_experiences,
            tags=sorted(tag for tag in aggregated_tags if tag),
            highlights=highlights,
            merge_suggestions=[],
            usage=usage,
            metadata=metadata,
        )

    def generate_cv(self, payload: CvGenerationRequest) -> CvGenerationResponse:
        canonical_major = self._normalise_major(payload.major)
        experiences = [
            self._normalise_experience(exp, fallback_index=index)
            for index, exp in enumerate(payload.structured_experiences)
        ]

        profile_summary = self._build_profile_summary(experiences, canonical_major, payload.degree)
        experience_sections = self._build_experience_sections(experiences)

        cv_json = {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "template": payload.template_type,
            "language": payload.language,
            "length": payload.length,
            "profile": {
                "targetMajor": canonical_major,
                "degree": payload.degree,
                "summary": profile_summary,
            },
            "sections": experience_sections,
        }

        if payload.include_preferences:
            cv_json["preferences"] = payload.include_preferences.model_dump(exclude_none=True)

        cv_markdown = self._render_cv_markdown(cv_json, experiences)
        cv_plaintext = self._render_cv_plaintext(cv_json, experiences)

        mirror_versions = None
        if payload.mirror_version:
            mirror_versions = [
                MirrorVersion(
                    template_type=f"{payload.template_type}-mirror",
                    markdown=self._render_mirror_markdown(cv_json, experiences),
                )
            ]

        revision_notes = [
            "请核实各段经历的起止时间与职位名称。",
            "确保所有量化成果均可提供佐证（如 KPI、奖项或导师证明）。",
        ]

        usage = LlmUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)

        return CvGenerationResponse(
            request_id=str(uuid.uuid4()),
            cv_json=cv_json,
            cv_markdown=cv_markdown,
            cv_plaintext=cv_plaintext,
            mirror_versions=mirror_versions,
            revision_notes=revision_notes,
            usage=usage,
            export_urls={
                "markdown": None,
                "docx": None,
                "pdf": None,
                "plaintext": None,
            },
        )

    def generate_ps(self, payload: PsGenerationRequest) -> PsGenerationResponse:
        canonical_major = self._normalise_major(payload.target_major)
        experiences = [
            self._normalise_experience(exp, fallback_index=index)
            for index, exp in enumerate(payload.structured_experiences)
        ]

        outline_items = self._build_ps_outline(canonical_major, payload.target_schools, experiences)
        paragraphs = self._build_ps_paragraphs(outline_items, experiences, payload)
        full_text = "\n\n".join(paragraph.content for paragraph in paragraphs)

        revision_suggestions = [
            "核对所有课程/竞赛名称的官方英文译名。",
            "补充一条能体现领导力或团队协作的案例，使结构更完整。",
            "确认段落中的数字、排名和时间线均准确无误。",
        ]

        verification_prompts = [
            "请确认所有科研/实习经历均获得相关导师或主管允许对外分享。",
            "确保 Statement 中引用的课程或项目已经在成绩单或履历中体现。",
        ]

        usage = LlmUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)

        variants = None
        if experiences:
            variants = [
                PsVariant(
                    tone="confident",
                    content=self._render_ps_variant(paragraphs, tone="confident"),
                )
            ]

        return PsGenerationResponse(
            request_id=str(uuid.uuid4()),
            outline_checked=outline_items,
            ps_paragraphs=paragraphs,
            ps_full_text=full_text,
            revision_suggestions=revision_suggestions,
            verification_prompts=verification_prompts,
            usage=usage,
            variants=variants,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _normalise_major(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        canonical = self.taxonomy_service.normalise_direction(value)
        if canonical:
            return canonical
        return value.strip()

    def _normalise_experience(
        self, raw: DocumentExperienceInput, *, fallback_index: int
    ) -> DocumentExperienceItem:
        details = [line.strip() for line in (raw.details or []) if isinstance(line, str) and line.strip()]
        if not details and raw.impact:
            details = [raw.impact.strip()]

        item = DocumentExperienceItem(
            id=raw.id or str(uuid.uuid4()),
            type=(raw.type or "other").lower(),
            title=raw.title.strip() if raw.title else "未命名经历",
            org=raw.org.strip() if raw.org else None,
            timeframe=raw.timeframe,
            details=details,
            impact=raw.impact.strip() if raw.impact else None,
            tags=[tag for tag in (raw.tags or []) if tag],
            attachments=raw.attachments,
            references=raw.references,
            highlight=bool(raw.highlight),
            difficulty=bool(raw.difficulty),
            sort_order=raw.sort_order if raw.sort_order is not None else fallback_index,
            metadata=raw.metadata,
        )
        return item

    def _build_profile_summary(
        self,
        experiences: Sequence[DocumentExperienceItem],
        canonical_major: Optional[str],
        degree: Optional[str],
    ) -> str:
        parts = []
        if canonical_major:
            parts.append(f"申请 {canonical_major} 方向")
        if degree:
            parts.append(f"{degree} 项目")

        if experiences:
            first = experiences[0]
            primary_skill = first.tags[0] if first.tags else first.type
            parts.append(f"核心能力：{primary_skill}")

        return "，".join(parts) or "专注于跨学科背景与应用实践的候选人。"

    def _build_experience_sections(
        self, experiences: Sequence[DocumentExperienceItem]
    ) -> List[dict]:
        sections: List[dict] = []
        for item in experiences:
            description = item.details or []
            if item.impact and item.impact not in description:
                description = description + [item.impact]

            sections.append(
                {
                    "title": item.title,
                    "organization": item.org,
                    "timeframe": item.timeframe.model_dump(exclude_none=True)
                    if item.timeframe
                    else None,
                    "highlights": description,
                    "tags": item.tags,
                    "category": item.type,
                }
            )
        return sections

    def _render_cv_markdown(self, cv_json: dict, experiences: Sequence[DocumentExperienceItem]) -> str:
        lines = [
            "# Curriculum Vitae",
            "",
            f"**目标方向：** {cv_json['profile']['targetMajor'] or '未指定'}",
            f"**目标学位：** {cv_json['profile']['degree'] or '未指定'}",
            "",
            "## 摘要",
            cv_json["profile"]["summary"],
            "",
            "## 核心经历",
        ]

        for item in experiences:
            lines.append(f"### {item.title}")
            if item.org:
                lines.append(f"- 机构：{item.org}")
            if item.details:
                for detail in item.details:
                    lines.append(f"- {detail}")
            if item.impact:
                lines.append(f"- 影响：{item.impact}")
            lines.append("")

        return "\n".join(lines).strip()

    def _render_cv_plaintext(self, cv_json: dict, experiences: Sequence[DocumentExperienceItem]) -> str:
        summary_block = textwrap.dedent(
            f"""
            目标方向: {cv_json['profile']['targetMajor'] or '未指定'}
            目标学位: {cv_json['profile']['degree'] or '未指定'}
            摘要: {cv_json['profile']['summary']}
            """
        ).strip()

        experience_lines = []
        for item in experiences:
            experience_lines.append(f"{item.title} ({item.org or '未注明机构'})")
            for detail in item.details:
                experience_lines.append(f"  - {detail}")
            if item.impact:
                experience_lines.append(f"  * 影响: {item.impact}")

        return summary_block + "\n\n" + "\n".join(experience_lines)

    def _render_mirror_markdown(
        self, cv_json: dict, experiences: Sequence[DocumentExperienceItem]
    ) -> str:
        base = self._render_cv_markdown(cv_json, experiences)
        mirror_intro = "> Mirror Version: 精简版用于 ATS 解析，确保关键词完整保留。\n\n"
        return mirror_intro + base

    def _build_ps_outline(
        self,
        canonical_major: Optional[str],
        target_schools: Sequence[str],
        experiences: Sequence[DocumentExperienceItem],
    ) -> List[PsOutlineItem]:
        related_ids = [exp.id for exp in experiences[:2]]
        school_display = "、".join(target_schools[:2]) if target_schools else "目标学校"
        major_display = canonical_major or "目标专业"

        outline = [
            PsOutlineItem(
                title="引言：求学动机与愿景",
                summary=f"结合个人背景阐述申请 {major_display} 的初衷，并与 {school_display} 的资源产生关联。",
                related_experiences=related_ids[:1],
            ),
            PsOutlineItem(
                title="核心经历：能力与匹配度",
                summary="挑选 2-3 段代表性科研/实习经历，强调方法与量化成果，突出与目标方向的契合度。",
                related_experiences=related_ids,
            ),
            PsOutlineItem(
                title="发展规划：项目收益与长期目标",
                summary="说明拟利用的课程/实验室资源，以及毕业后的学术或职业规划，呼应第一段动机。",
                related_experiences=[exp.id for exp in experiences[2:4]],
            ),
        ]
        return outline

    def _build_ps_paragraphs(
        self,
        outline: Sequence[PsOutlineItem],
        experiences: Sequence[DocumentExperienceItem],
        payload: PsGenerationRequest,
    ) -> List[PsParagraph]:
        canonical_major = self._normalise_major(payload.target_major)
        word_limit = payload.word_limit
        max_words = word_limit[1] if word_limit else 900
        target_schools = ", ".join(payload.target_schools[:2]) or "目标院校"

        paragraphs: List[PsParagraph] = []

        intro = PsParagraph(
            heading="引言：学术动机与起点",
            content=textwrap.dedent(
                f"""
                自本科阶段起，我即聚焦于 {canonical_major or '目标专业'} 的跨学科研究。在校内的课程和竞赛中反复验证理论，并尝试将结果应用于实际项目。
                对于 {target_schools} 的关注，源自其在该领域的系统课程与开放科研生态，我相信这将是我深化研究与形成个人模型的最佳场景。
                """.strip()
            ),
            checklist=[
                "是否明确写出与目标专业的关联？",
                "动机与学校资源之间是否建立直接联系？",
            ],
        )
        paragraphs.append(intro)

        if experiences:
            first_exp = experiences[0]
            body = PsParagraph(
                heading="主体：代表性经历与能力积累",
                content=textwrap.dedent(
                    f"""
                    在 {first_exp.org or '项目团队'} 的经历中，我牵头完成了「{first_exp.title}」，主要负责数据管线搭建与算法实验。
                    通过迭代实验，我将模型准确率提升至行业基准以上，并总结出一套可复用的评估框架。
                    这一过程训练了我在有限资源下快速迭代的能力，也验证了我在 {canonical_major or '目标方向'} 上的长期投入价值。
                    """.strip()
                ),
                checklist=[
                    "是否量化说明过项目成果？",
                    "是否强调个人角色与贡献？",
                ],
            )
            paragraphs.append(body)

        conclusion = PsParagraph(
            heading="结语：项目贡献与长期规划",
            content=textwrap.dedent(
                f"""
                加入 {target_schools} 后，我希望在导师指导下进一步探索与 {canonical_major or '目标专业'} 相关的跨学科课题，
                并在校内创业或研究平台上推动成果落地。中长期来看，我期望以研究驱动的方式在行业中搭建数据驱动的决策系统，
                将论文成果与商业实践相结合，为更多组织提供高可信的智能方案。
                """.strip()
            ),
            checklist=[
                "是否点名了拟加入的课程或实验室？",
                "长期目标是否与开篇动机呼应？",
            ],
        )
        paragraphs.append(conclusion)

        if max_words and max_words > 0:
            for paragraph in paragraphs:
                if len(paragraph.content) > max_words * 5:  # heuristic guard
                    paragraph.content = paragraph.content[: max_words * 5]

        return paragraphs

    def _render_ps_variant(self, paragraphs: Sequence[PsParagraph], tone: str) -> str:
        modifier = "（更自信语气版本）" if tone == "confident" else ""
        lines = [f"# Personal Statement{modifier}", ""]
        for paragraph in paragraphs:
            lines.append(f"## {paragraph.heading}")
            lines.append(paragraph.content)
            lines.append("")
        return "\n".join(lines).strip()
