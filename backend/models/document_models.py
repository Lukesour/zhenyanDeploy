from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class ExperienceTimeframe(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None
    ongoing: Optional[bool] = None
    timezone: Optional[str] = None


class DocumentExperienceInput(BaseModel):
    id: Optional[str] = None
    type: Optional[str] = None
    title: Optional[str] = None
    org: Optional[str] = None
    timeframe: Optional[ExperienceTimeframe] = None
    details: Optional[List[str]] = None
    impact: Optional[str] = None
    tags: Optional[List[str]] = None
    attachments: Optional[List[str]] = None
    references: Optional[List[str]] = None
    highlight: Optional[bool] = None
    difficulty: Optional[bool] = None
    sort_order: Optional[int] = Field(default=None, alias="sortOrder")
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        allow_population_by_field_name = True


class DocumentExperienceItem(DocumentExperienceInput):
    id: str
    type: str = "other"
    title: str
    details: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    highlight: bool = False
    difficulty: bool = False


class LlmUsage(BaseModel):
    prompt_tokens: Optional[int] = 0
    completion_tokens: Optional[int] = 0
    total_tokens: Optional[int] = 0
    cached_tokens: Optional[int] = 0


class BrainstormStructureRequest(BaseModel):
    raw_experiences: List[DocumentExperienceInput]
    target_major: Optional[str] = None
    target_degree: Optional[str] = None
    tags: Optional[List[str]] = None
    prompts: Optional[List[str]] = None


class BrainstormStructureResponse(BaseModel):
    request_id: str
    structured_experiences: List[DocumentExperienceItem]
    tags: List[str]
    highlights: List[str]
    merge_suggestions: List[str]
    usage: Optional[LlmUsage] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class CvPreferenceConfig(BaseModel):
    languages: Optional[List[str]] = None
    style: Optional[str] = None
    length: Optional[str] = None
    notes: Optional[str] = None


class CvGenerationRequest(BaseModel):
    structured_experiences: List[DocumentExperienceInput]
    template_type: str
    language: str
    length: str
    tone: Optional[str] = None
    highlight_ids: Optional[List[str]] = None
    tag_preferences: Optional[List[str]] = None
    ats_friendly: Optional[bool] = True
    mirror_version: Optional[bool] = False
    include_preferences: Optional[CvPreferenceConfig] = None
    major: Optional[str] = None
    degree: Optional[str] = None


class MirrorVersion(BaseModel):
    template_type: str
    markdown: str


class CvGenerationResponse(BaseModel):
    request_id: str
    cv_json: Dict[str, Any]
    cv_markdown: str
    cv_plaintext: Optional[str] = None
    mirror_versions: Optional[List[MirrorVersion]] = None
    revision_notes: Optional[List[str]] = None
    usage: Optional[LlmUsage] = None
    export_urls: Optional[Dict[str, Optional[str]]] = None


class PsEmphasisConfig(BaseModel):
    research: Optional[bool] = None
    career: Optional[bool] = None


class PsPreferenceConfig(BaseModel):
    language: Optional[str] = None
    voice: Optional[str] = None
    length: Optional[str] = None
    highlight_ids: Optional[List[str]] = None
    gap_ids: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class PsImportConfig(BaseModel):
    program_brief: Optional[str] = None
    keywords: Optional[List[str]] = None


class PsGenerationRequest(BaseModel):
    structured_experiences: List[DocumentExperienceInput]
    target_major: str
    target_schools: List[str]
    outline: str
    word_limit: Tuple[int, int]
    tone: str
    emphasis: Optional[PsEmphasisConfig] = None
    preferences: Optional[PsPreferenceConfig] = None
    imports: Optional[PsImportConfig] = None


class PsOutlineItem(BaseModel):
    title: str
    summary: str
    related_experiences: List[str]


class PsParagraph(BaseModel):
    heading: str
    content: str
    checklist: Optional[List[str]] = None


class PsVariant(BaseModel):
    tone: str
    content: str


class PsGenerationResponse(BaseModel):
    request_id: str
    outline_checked: List[PsOutlineItem]
    ps_paragraphs: List[PsParagraph]
    ps_full_text: str
    revision_suggestions: List[str]
    verification_prompts: Optional[List[str]] = None
    usage: Optional[LlmUsage] = None
    variants: Optional[List[PsVariant]] = None
