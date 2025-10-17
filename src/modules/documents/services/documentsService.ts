'use client';

import authService from '@/modules/study-planner/services/authService';
import { getApiBaseUrl } from '@/modules/study-planner/config';

export type DocumentExperienceType =
  | 'internship'
  | 'research'
  | 'project'
  | 'award'
  | 'student_position'
  | 'course'
  | 'skill'
  | 'language'
  | 'certification'
  | 'publication'
  | 'volunteer'
  | 'other';

export interface ExperienceTimeframe {
  start?: string;
  end?: string;
  ongoing?: boolean;
  timezone?: string;
}

export interface DocumentExperienceItem {
  id: string;
  type: DocumentExperienceType;
  title: string;
  org?: string;
  timeframe?: ExperienceTimeframe | null;
  details: string[];
  impact?: string;
  tags: string[];
  attachments?: string[];
  references?: string[];
  highlight?: boolean;
  difficulty?: boolean;
  sortOrder?: number;
  metadata?: Record<string, unknown>;
}

export interface LlmUsage {
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
  cached_tokens?: number;
  [key: string]: number | undefined;
}

export interface BrainstormStructurePayload {
  raw_experiences: Array<
    Partial<DocumentExperienceItem> & {
      source?: string;
      raw_text?: string;
    }
  >;
  target_major?: string | null;
  target_degree?: string | null;
  tags?: string[];
  prompts?: string[];
}

export interface BrainstormStructureResponse {
  request_id: string;
  structured_experiences: DocumentExperienceItem[];
  tags: string[];
  highlights: string[];
  merge_suggestions: string[];
  usage?: LlmUsage;
  metadata?: Record<string, unknown>;
}

export type CvTemplateType = 'academic' | 'research' | 'industry' | 'hybrid';

export interface CvGenerationPayload {
  structured_experiences: DocumentExperienceItem[];
  template_type: CvTemplateType;
  language: 'zh' | 'en';
  length: '1page' | '2pages';
  tone?: 'sincere' | 'confident' | 'academic';
  highlight_ids?: string[];
  tag_preferences?: string[];
  ats_friendly?: boolean;
  mirror_version?: boolean;
  include_preferences?: {
    languages?: string[];
    style?: string;
    length?: string;
    notes?: string;
  };
  major?: string;
  degree?: string;
}

export interface CvGenerationResponse {
  request_id: string;
  cv_json: Record<string, unknown>;
  cv_markdown: string;
  cv_plaintext?: string;
  mirror_versions?: Array<{
    template_type: CvTemplateType;
    markdown: string;
  }>;
  revision_notes?: string[];
  usage?: LlmUsage;
  export_urls?: {
    markdown?: string;
    docx?: string;
    pdf?: string;
    plaintext?: string;
  };
}

export type PsOutlineType = 'standard' | 'research' | 'industry';

export interface PsGenerationPayload {
  structured_experiences: DocumentExperienceItem[];
  target_major: string;
  target_schools: string[];
  outline: PsOutlineType;
  word_limit: [number, number];
  tone: 'sincere' | 'confident' | 'academic';
  emphasis?: {
    research?: boolean;
    career?: boolean;
  };
  preferences?: {
    language?: 'zh' | 'en';
    voice?: string;
    length?: string;
    highlight_ids?: string[];
    gap_ids?: string[];
    tags?: string[];
  };
  imports?: {
    program_brief?: string;
    keywords?: string[];
  };
}

export interface PsOutlineItem {
  title: string;
  summary: string;
  related_experiences: string[];
}

export interface PsParagraph {
  heading: string;
  content: string;
  checklist?: string[];
}

export interface PsGenerationResponse {
  request_id: string;
  outline_checked: PsOutlineItem[];
  ps_paragraphs: PsParagraph[];
  ps_full_text: string;
  revision_suggestions: string[];
  verification_prompts?: string[];
  usage?: LlmUsage;
  variants?: Array<{
    tone: PsGenerationPayload['tone'];
    content: string;
  }>;
}

const withAuthHeaders = () => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  const token = authService.getAccessToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  return headers;
};

const handleResponse = async <T>(response: Response): Promise<T> => {
  if (!response.ok) {
    let detail = await response.text();
    try {
      const parsed = JSON.parse(detail);
      detail = parsed.message || parsed.detail || detail;
    } catch {
      // ignore json parse errors
    }
    throw new Error(detail || '文书服务请求失败');
  }

  return (await response.json()) as T;
};

export const documentsService = {
  async structureBrainstorm(payload: BrainstormStructurePayload): Promise<BrainstormStructureResponse> {
    const response = await fetch(`${getApiBaseUrl()}/documents/brainstorm/structure`, {
      method: 'POST',
      headers: withAuthHeaders(),
      body: JSON.stringify(payload),
    });

    return handleResponse<BrainstormStructureResponse>(response);
  },

  async generateCV(payload: CvGenerationPayload): Promise<CvGenerationResponse> {
    const response = await fetch(`${getApiBaseUrl()}/documents/cv/generate`, {
      method: 'POST',
      headers: withAuthHeaders(),
      body: JSON.stringify(payload),
    });

    return handleResponse<CvGenerationResponse>(response);
  },

  async generatePS(payload: PsGenerationPayload): Promise<PsGenerationResponse> {
    const response = await fetch(`${getApiBaseUrl()}/documents/ps/generate`, {
      method: 'POST',
      headers: withAuthHeaders(),
      body: JSON.stringify(payload),
    });

    return handleResponse<PsGenerationResponse>(response);
  },
};

export default documentsService;
