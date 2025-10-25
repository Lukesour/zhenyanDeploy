'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  App as AntdApp,
  Alert,
  AutoComplete,
  Button,
  Card,
  Checkbox,
  Col,
  ConfigProvider,
  Divider,
  Empty,
  Input,
  InputNumber,
  message,
  Radio,
  Row,
  Select,
  Space,
  Spin,
  Steps,
  Tabs,
  Tag,
  Tooltip,
  Typography,
} from 'antd';
import type { TabsProps } from 'antd';
import {
  CloudUploadOutlined,
  DownloadOutlined,
  HighlightOutlined,
  MergeCellsOutlined,
  PlusOutlined,
  ReloadOutlined,
  ScissorOutlined,
  StarOutlined,
} from '@ant-design/icons';
import zhCN from 'antd/locale/zh_CN';

import authService, { type AuthState } from '@/modules/study-planner/services/authService';
import dataLoaderService, {
  type MajorDirectionDefinition,
} from '@/modules/study-planner/services/DataLoaderService';
import errorHandler from '@/modules/study-planner/services/ErrorHandler';
import type { UserBackground } from '@/modules/study-planner/services/api';
import documentsService, {
  type BrainstormStructureResponse,
  type CvGenerationResponse,
  type CvTemplateType,
  type DocumentExperienceItem,
  type DocumentExperienceType,
  type LlmUsage,
  type PsGenerationResponse,
  type PsOutlineItem,
  type PsParagraph,
} from '@/modules/documents/services/documentsService';

const { Title, Paragraph, Text } = Typography;

const themeTokens = {
  token: {
    colorPrimary: '#4f46e5',
    colorInfo: '#4f46e5',
    colorSuccess: '#059669',
    colorWarning: '#d97706',
    colorError: '#dc2626',
    borderRadius: 12,
    fontSize: 14,
    fontFamily: 'var(--font-geist-sans)',
    controlHeight: 42,
    colorBgLayout: '#f5f7ff',
  },
  components: {
    Card: {
      borderRadiusLG: 16,
      paddingLG: 24,
      boxShadow:
        '0 12px 32px rgba(79, 70, 229, 0.08), 0 4px 16px rgba(79, 70, 229, 0.04)',
      colorBorderSecondary: '#e0e7ff',
    },
    Button: {
      borderRadius: 999,
      controlHeight: 44,
      paddingInline: 18,
      controlHeightLG: 52,
    },
    Tabs: {
      inkBarColor: '#4f46e5',
      itemSelectedColor: '#4f46e5',
      itemHoverColor: '#4338ca',
    },
  },
};

const DRAFT_STORAGE_KEY = 'documents:draft:v1';

type DegreeType = 'Master' | 'PhD' | 'Other' | '';

interface MajorTarget {
  id: string;
  name: string;
  isPrimary: boolean;
}

interface PersonalPreference {
  tone: 'sincere' | 'confident' | 'academic' | 'story';
  styleKeywords: string[];
  language: 'zh' | 'en';
  length: '1page' | '2pages';
  notes: string;
}

interface BrainstormState {
  targetDegree: DegreeType;
  targetMajors: MajorTarget[];
  targetSchools: string[];
  applicationSeason?: string;
  applicationYear?: number | null;
  experiences: DocumentExperienceItem[];
  highlights: string[];
  gaps: string[];
  tags: string[];
  preferences: PersonalPreference;
  lastStructuredAt?: string | null;
}

interface StructuringMeta {
  requestId: string;
  usage?: LlmUsage;
  mergeSuggestions: string[];
}

interface CvConfig {
  templateType: CvTemplateType;
  language: 'zh' | 'en';
  length: '1page' | '2pages';
  atsFriendly: boolean;
  mirrorVersion: boolean;
  autoQuantify: boolean;
  emphasizeHighlights: boolean;
}

interface CvPreview {
  requestId: string;
  generatedAt: string;
  cvJson: Record<string, unknown>;
  cvMarkdown: string;
  cvPlaintext?: string;
  mirrorVersions?: CvGenerationResponse['mirror_versions'];
  revisionNotes?: string[];
  usage?: LlmUsage;
}

type PsTone = 'sincere' | 'confident' | 'academic';
type PsOutline = 'standard' | 'research' | 'industry';

const mapPreferenceToneToServiceTone = (tone: PersonalPreference['tone']): PsTone => {
  return tone === 'story' ? 'sincere' : tone;
};

interface PsConfig {
  outline: PsOutline;
  tone: PsTone;
  targetMajor: string;
  targetSchools: string[];
  wordLimit: [number, number];
  emphasizeResearch: boolean;
  emphasizeCareer: boolean;
  includeChecklist: boolean;
  programBrief: string;
  customKeywords: string[];
}

interface PsDraft {
  requestId: string;
  generatedAt: string;
  outline: PsOutlineItem[];
  paragraphs: PsParagraph[];
  fullText: string;
  revisionSuggestions: string[];
  verificationPrompts?: string[];
  usage?: LlmUsage;
}

interface DraftStoragePayload {
  version: number;
  updatedAt: string;
  brainstorm: BrainstormState;
  cvConfig: CvConfig;
  psConfig: PsConfig;
  cvPreview?: CvPreview | null;
  psDraft?: PsDraft | null;
  structuringMeta?: StructuringMeta | null;
}

interface ExperienceSection {
  type: DocumentExperienceType;
  title: string;
  description: string;
  tagRecommendations: string[];
}

const EXPERIENCE_SECTIONS: ExperienceSection[] = [
  {
    type: 'internship',
    title: '实习经历',
    description: '公司/部门、岗位、时间段、职责、量化成果、技能标签',
    tagRecommendations: ['实习', '行业经验', '量化成果'],
  },
  {
    type: 'research',
    title: '科研课题',
    description: '课题名称、角色、方法、贡献、成果、影响',
    tagRecommendations: ['科研', '实验', '数据分析'],
  },
  {
    type: 'project',
    title: '项目实践',
    description: '项目目标、技术栈、职责、成果、影响范围',
    tagRecommendations: ['项目', '产品', '技术'],
  },
  {
    type: 'award',
    title: '获奖/竞赛',
    description: '奖项名称、级别、排名、机构、时间、关联主题',
    tagRecommendations: ['竞赛', '奖项', '荣誉'],
  },
  {
    type: 'student_position',
    title: '学生工作/社团',
    description: '组织/职位、职责范围、规模、成效与领导力体现',
    tagRecommendations: ['领导力', '组织', '活动'],
  },
  {
    type: 'course',
    title: '课程/技能',
    description: '关键课程（成绩/排名）、专业技能、工具使用',
    tagRecommendations: ['课程', '技能', '工具'],
  },
  {
    type: 'language',
    title: '语言能力',
    description: '语言水平、考试成绩、证书、使用场景',
    tagRecommendations: ['语言', '国际交流'],
  },
  {
    type: 'certification',
    title: '资格认证',
    description: '认证名称、颁发机构、时间、覆盖技能',
    tagRecommendations: ['认证', '资格'],
  },
  {
    type: 'publication',
    title: '发表成果',
    description: '论文/专利/发布渠道、摘要、影响力',
    tagRecommendations: ['论文', '发表', '成果'],
  },
  {
    type: 'volunteer',
    title: '志愿/公益',
    description: '组织、职责、服务对象、持续时间、影响',
    tagRecommendations: ['公益', '志愿'],
  },
  {
    type: 'other',
    title: '其他经历',
    description: '创业、交换、海外经历、短期课程等',
    tagRecommendations: ['其他', '跨文化'],
  },
];

const CV_TEMPLATE_OPTIONS: Array<{ label: string; value: CvTemplateType; description: string }> = [
  {
    label: 'Academic（学术导向）',
    value: 'academic',
    description: '强调学术成果、科研经历与发表记录',
  },
  {
    label: 'Research（科研导向）',
    value: 'research',
    description: '突出科研方法、实验设计与研究兴趣',
  },
  {
    label: 'Industry（求职导向）',
    value: 'industry',
    description: '强调实习与项目成果，ATS 友好排版',
  },
  {
    label: 'Hybrid（申研+求职）',
    value: 'hybrid',
    description: '兼顾科研亮点与行业实习，双重目标适配',
  },
];

const PS_STRUCTURE_OPTIONS: Array<{ label: string; value: PsOutline; description: string }> = [
  {
    label: '标准版',
    value: 'standard',
    description: '动机启蒙 → 学术与项目 → 实习影响 → 与项目契合 → 职业规划',
  },
  {
    label: '研究导向版',
    value: 'research',
    description: '学术准备 → 研究经历 → 方法兴趣 → Faculty/实验室契合 → 研究愿景',
  },
  {
    label: '职业导向版',
    value: 'industry',
    description: '行业痛点 → 能力积累 → 影响力 → 项目补齐 → 职业目标',
  },
];

const DEFAULT_BRAINSTORM_STATE: BrainstormState = {
  targetDegree: 'Master',
  targetMajors: [],
  targetSchools: [],
  applicationSeason: 'Fall',
  applicationYear: null,
  experiences: [],
  highlights: [],
  gaps: [],
  tags: [],
  preferences: {
    tone: 'sincere',
    styleKeywords: ['专业', '量化', '结构化'],
    language: 'en',
    length: '1page',
    notes: '',
  },
  lastStructuredAt: null,
};

const DEFAULT_CV_CONFIG: CvConfig = {
  templateType: 'academic',
  language: 'en',
  length: '1page',
  atsFriendly: true,
  mirrorVersion: true,
  autoQuantify: true,
  emphasizeHighlights: true,
};

const DEFAULT_PS_CONFIG: PsConfig = {
  outline: 'standard',
  tone: 'sincere',
  targetMajor: '',
  targetSchools: [],
  wordLimit: [700, 1000],
  emphasizeResearch: true,
  emphasizeCareer: false,
  includeChecklist: true,
  programBrief: '',
  customKeywords: [],
};

const createId = (): string => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `exp_${Math.random().toString(36).slice(2, 10)}`;
};

const formatTimeframeValue = (experience: DocumentExperienceItem): string => {
  if (experience?.metadata && typeof experience.metadata === 'object') {
    const raw = (experience.metadata as Record<string, unknown>).raw_timeframe;
    if (typeof raw === 'string' && raw.trim().length > 0) {
      return raw;
    }
  }

  const timeframe = experience.timeframe;
  if (!timeframe) {
    return '';
  }

  const parts = [];
  if (timeframe.start) {
    parts.push(timeframe.start);
  }
  if (timeframe.end) {
    parts.push(timeframe.end);
  } else if (timeframe.ongoing) {
    parts.push('Present');
  }

  return parts.join(' - ');
};

const parseTimeframeInput = (input: string) => {
  if (!input || !input.trim()) {
    return {
      timeframe: null,
      raw: '',
    };
  }

  const normalized = input.replace(/~|—|–|to|至/g, '-');
  const [startRaw, endRaw] = normalized.split('-').map((part) => part.trim());
  const timeframe: DocumentExperienceItem['timeframe'] = {};

  if (startRaw) {
    timeframe.start = startRaw;
  }

  if (endRaw) {
    const lower = endRaw.toLowerCase();
    if (lower === 'present' || lower === 'now' || lower === '至今') {
      timeframe.ongoing = true;
    } else {
      timeframe.end = endRaw;
    }
  }

  return {
    timeframe,
    raw: input,
  };
};

const normalizeExperience = (experience: Partial<DocumentExperienceItem>): DocumentExperienceItem => {
  return {
    id: experience.id ?? createId(),
    type: experience.type ?? 'other',
    title: experience.title ?? '',
    org: experience.org ?? '',
    timeframe: experience.timeframe ?? null,
    details: Array.isArray(experience.details)
      ? experience.details
      : experience.details
      ? [String(experience.details)]
      : [],
    impact: experience.impact ?? '',
    tags: Array.isArray(experience.tags) ? experience.tags : experience.tags ? [String(experience.tags)] : [],
    attachments: Array.isArray(experience.attachments) ? experience.attachments : [],
    references: Array.isArray(experience.references) ? experience.references : [],
    highlight: Boolean(experience.highlight),
    difficulty: Boolean(experience.difficulty),
    sortOrder: typeof experience.sortOrder === 'number' ? experience.sortOrder : undefined,
    metadata: experience.metadata ?? {},
  };
};

const mergeExperiences = (
  existing: DocumentExperienceItem[],
  incoming: DocumentExperienceItem[],
): DocumentExperienceItem[] => {
  const dedupeMap = new Map<string, DocumentExperienceItem>();

  const buildKey = (exp: DocumentExperienceItem) => {
    const name = exp.title?.trim().toLowerCase() || '';
    const org = exp.org?.trim().toLowerCase() || '';
    return `${exp.type}_${name}_${org}`;
  };

  existing.forEach((exp) => {
    dedupeMap.set(buildKey(exp), exp);
  });

  incoming.forEach((exp) => {
    const normalized = normalizeExperience(exp);
    const key = buildKey(normalized);
    if (!dedupeMap.has(key)) {
      dedupeMap.set(key, normalized);
    } else {
      const merged = dedupeMap.get(key)!;
      dedupeMap.set(key, {
        ...merged,
        ...normalized,
        details: Array.from(new Set([...(merged.details ?? []), ...(normalized.details ?? [])])),
        tags: Array.from(new Set([...(merged.tags ?? []), ...(normalized.tags ?? [])])),
        highlight: merged.highlight || normalized.highlight,
        difficulty: merged.difficulty || normalized.difficulty,
      });
    }
  });

  return Array.from(dedupeMap.values());
};

const deriveTimeline = (experiences: DocumentExperienceItem[]): string[] => {
  return experiences
    .map((exp) => {
      const timeframe = formatTimeframeValue(exp);
      if (!timeframe) {
        return '';
      }
      const label = exp.title || exp.org || exp.tags?.[0] || '未命名经历';
      return `${timeframe} · ${label}`;
    })
    .filter((item) => Boolean(item));
};

const formatUsage = (usage?: LlmUsage) => {
  if (!usage) {
    return '';
  }
  const total = usage.total_tokens ?? usage.prompt_tokens ?? usage.completion_tokens;
  if (!total) {
    return '';
  }
  const prompt = usage.prompt_tokens ? `提示 ${usage.prompt_tokens}` : '';
  const completion = usage.completion_tokens ? `生成 ${usage.completion_tokens}` : '';
  const segments = [prompt, completion].filter(Boolean);
  return segments.length ? `${segments.join(' / ')}，总计 ${total}` : `总计 ${total}`;
};

const normalizeMajorKey = (value: string): string =>
  value.trim().toLowerCase().replace(/\s+/g, '');

type ActiveStep = 'brainstorm' | 'cv' | 'ps';

export default function DocumentsPage() {
  const [authState, setAuthState] = useState<AuthState>(authService.getAuthState());
  const [activeStep, setActiveStep] = useState<ActiveStep>('brainstorm');
  const [isClient, setIsClient] = useState(false);

  const [brainstorm, setBrainstorm] = useState<BrainstormState>(DEFAULT_BRAINSTORM_STATE);
  const [structuringMeta, setStructuringMeta] = useState<StructuringMeta | null>(null);

  const [cvConfig, setCvConfig] = useState<CvConfig>(DEFAULT_CV_CONFIG);
  const [cvPreview, setCvPreview] = useState<CvPreview | null>(null);
  const [psConfig, setPsConfig] = useState<PsConfig>(DEFAULT_PS_CONFIG);
  const [psDraft, setPsDraft] = useState<PsDraft | null>(null);

  const [isStructuring, setIsStructuring] = useState(false);
  const [isGeneratingCv, setIsGeneratingCv] = useState(false);
  const [isGeneratingPs, setIsGeneratingPs] = useState(false);
  const [draftSavedAt, setDraftSavedAt] = useState<string | null>(null);

  const [majorDirectionDefinitions, setMajorDirectionDefinitions] = useState<MajorDirectionDefinition[]>([]);
  const [majorOptionsLoading, setMajorOptionsLoading] = useState(false);
  const [majorSearchValue, setMajorSearchValue] = useState('');

  useEffect(() => {
    let mounted = true;

    const loadDirections = async () => {
      setMajorOptionsLoading(true);
      try {
        const directions = await dataLoaderService.loadMajorDirections();
        if (mounted) {
          setMajorDirectionDefinitions(directions);
        }
      } catch (error) {
        console.warn('Failed to load major taxonomy for documents module:', error);
      } finally {
        if (mounted) {
          setMajorOptionsLoading(false);
        }
      }
    };

    loadDirections();

    return () => {
      mounted = false;
    };
  }, []);

  const majorAliasMap = useMemo(() => {
    const map = new Map<string, string>();
    majorDirectionDefinitions.forEach((direction) => {
      const canonicalKey = normalizeMajorKey(direction.name);
      if (!map.has(canonicalKey)) {
        map.set(canonicalKey, direction.name);
      }

      (direction.aliases ?? []).forEach((alias) => {
        const aliasKey = normalizeMajorKey(alias);
        if (!map.has(aliasKey)) {
          map.set(aliasKey, direction.name);
        }
      });
    });
    return map;
  }, [majorDirectionDefinitions]);

  const resolveMajorName = useCallback(
    (input: string) => {
      const key = normalizeMajorKey(input);
      return majorAliasMap.get(key) ?? input.trim();
    },
    [majorAliasMap]
  );

  const normalizeMajorTargets = useCallback(
    (majors: MajorTarget[]): MajorTarget[] => {
      if (!majors || majors.length === 0) {
        return majors;
      }

      const seen = new Map<string, MajorTarget>();
      majors.forEach((major) => {
        const canonicalName = resolveMajorName(major.name);
        const key = normalizeMajorKey(canonicalName);
        const existing = seen.get(key);
        if (!existing) {
          seen.set(key, { ...major, name: canonicalName });
        } else if (!existing.isPrimary && major.isPrimary) {
          seen.set(key, { ...existing, isPrimary: true });
        }
      });

      const normalized = Array.from(seen.values());
      if (!normalized.some((major) => major.isPrimary) && normalized.length > 0) {
        normalized[0] = { ...normalized[0], isPrimary: true };
      }

      return normalized;
    },
    [resolveMajorName]
  );

  const selectedMajorKeys = useMemo(() => {
    return new Set(brainstorm.targetMajors.map((major) => normalizeMajorKey(major.name)));
  }, [brainstorm.targetMajors]);

  const majorAutoCompleteOptions = useMemo(() => {
    if (majorDirectionDefinitions.length === 0) {
      return [] as { value: string; label: string }[];
    }

    const options: { value: string; label: string }[] = [];
    const seen = new Set<string>();

    majorDirectionDefinitions.forEach((direction) => {
      const canonicalKey = normalizeMajorKey(direction.name);
      if (!selectedMajorKeys.has(canonicalKey)) {
        if (!seen.has(direction.name)) {
          options.push({
            value: direction.name,
            label: `${direction.groupName}｜${direction.name}`,
          });
          seen.add(direction.name);
        }

        (direction.aliases ?? []).forEach((alias) => {
          const aliasValue = alias.trim();
          if (!aliasValue) {
            return;
          }

          const aliasKey = normalizeMajorKey(aliasValue);
          if (selectedMajorKeys.has(aliasKey)) {
            return;
          }

          const label = `${direction.groupName}｜${direction.name}（${aliasValue}）`;
          if (!seen.has(label)) {
            options.push({
              value: aliasValue,
              label,
            });
            seen.add(label);
          }
        });
      }
    });

    return options;
  }, [majorDirectionDefinitions, selectedMajorKeys]);

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    const handleAuthChange = (nextState: AuthState) => {
      setAuthState(nextState);
    };

    authService.addListener(handleAuthChange);
    return () => {
      authService.removeListener(handleAuthChange);
    };
  }, []);

  useEffect(() => {
    if (!isClient) {
      return;
    }

    try {
      const raw = window.localStorage.getItem(DRAFT_STORAGE_KEY);
      if (!raw) {
        return;
      }
      const parsed = JSON.parse(raw) as DraftStoragePayload;
      setBrainstorm((prev) => ({
        ...prev,
        ...(parsed.brainstorm ? {
          ...parsed.brainstorm,
          targetMajors: Array.isArray(parsed.brainstorm.targetMajors)
            ? normalizeMajorTargets(
                parsed.brainstorm.targetMajors.map((major) => ({
                  id: major.id ?? createId(),
                  name: major.name,
                  isPrimary: Boolean(major.isPrimary),
                }))
              )
            : prev.targetMajors,
          experiences: Array.isArray(parsed.brainstorm.experiences)
            ? parsed.brainstorm.experiences.map(normalizeExperience)
            : prev.experiences,
          highlights: Array.isArray(parsed.brainstorm.highlights)
            ? parsed.brainstorm.highlights
            : prev.highlights,
          gaps: Array.isArray(parsed.brainstorm.gaps) ? parsed.brainstorm.gaps : prev.gaps,
          tags: Array.isArray(parsed.brainstorm.tags) ? parsed.brainstorm.tags : prev.tags,
          preferences: {
            ...prev.preferences,
            ...(parsed.brainstorm.preferences ?? {}),
            styleKeywords: Array.isArray(parsed.brainstorm.preferences?.styleKeywords)
              ? parsed.brainstorm.preferences?.styleKeywords
              : prev.preferences.styleKeywords,
          },
        } : prev),
      }));

      if (parsed.cvConfig) {
        setCvConfig({
          ...DEFAULT_CV_CONFIG,
          ...parsed.cvConfig,
        });
      }

      if (parsed.psConfig) {
        setPsConfig({
          ...DEFAULT_PS_CONFIG,
          ...parsed.psConfig,
          customKeywords: Array.isArray(parsed.psConfig.customKeywords)
            ? parsed.psConfig.customKeywords
            : DEFAULT_PS_CONFIG.customKeywords,
          targetSchools: Array.isArray(parsed.psConfig.targetSchools)
            ? parsed.psConfig.targetSchools
            : DEFAULT_PS_CONFIG.targetSchools,
        });
      }

      if (parsed.cvPreview) {
        setCvPreview(parsed.cvPreview);
      }

      if (parsed.psDraft) {
        setPsDraft(parsed.psDraft);
      }

      if (parsed.structuringMeta) {
        setStructuringMeta(parsed.structuringMeta);
      }

      setDraftSavedAt(parsed.updatedAt);
    } catch (error) {
      console.warn('Failed to restore documents draft:', error);
    }
  }, [isClient, normalizeMajorTargets]);

  useEffect(() => {
    if (!isClient) {
      return;
    }

    const payload: DraftStoragePayload = {
      version: 1,
      updatedAt: new Date().toISOString(),
      brainstorm,
      cvConfig,
      psConfig,
      cvPreview,
      psDraft,
      structuringMeta,
    };

    try {
      window.localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(payload));
      setDraftSavedAt(payload.updatedAt);
    } catch (error) {
      console.warn('Failed to persist documents draft:', error);
    }
  }, [brainstorm, cvConfig, psConfig, cvPreview, psDraft, structuringMeta, isClient]);

  useEffect(() => {
    if (majorDirectionDefinitions.length === 0) {
      return;
    }

    setBrainstorm((prev) => {
      if (prev.targetMajors.length === 0) {
        return prev;
      }

      const normalized = normalizeMajorTargets(prev.targetMajors);
      const unchanged =
        normalized.length === prev.targetMajors.length &&
        normalized.every(
          (major, index) =>
            major.name === prev.targetMajors[index].name &&
            major.isPrimary === prev.targetMajors[index].isPrimary
        );

      if (unchanged) {
        return prev;
      }

      return {
        ...prev,
        targetMajors: normalized,
      };
    });
  }, [majorDirectionDefinitions, normalizeMajorTargets]);

  useEffect(() => {
    if (majorDirectionDefinitions.length === 0) {
      return;
    }

    setPsConfig((prev) => {
      if (!prev.targetMajor) {
        return prev;
      }

      const canonical = resolveMajorName(prev.targetMajor);
      if (canonical === prev.targetMajor) {
        return prev;
      }

      return {
        ...prev,
        targetMajor: canonical,
      };
    });
  }, [majorDirectionDefinitions, resolveMajorName]);

  useEffect(() => {
    if (brainstorm.targetMajors.length === 0) {
      return;
    }

    const primary = brainstorm.targetMajors.find((major) => major.isPrimary) ?? brainstorm.targetMajors[0];
    if (primary && !psConfig.targetMajor) {
      setPsConfig((prev) => ({
        ...prev,
        targetMajor: primary.name,
      }));
    }
  }, [brainstorm.targetMajors, psConfig.targetMajor]);

  useEffect(() => {
    if (brainstorm.targetSchools.length === 0) {
      return;
    }

    if (psConfig.targetSchools.length === 0) {
      setPsConfig((prev) => ({
        ...prev,
        targetSchools: Array.from(new Set([...prev.targetSchools, ...brainstorm.targetSchools])),
      }));
    }
  }, [brainstorm.targetSchools, psConfig.targetSchools]);

  const derivedTimeline = useMemo(() => deriveTimeline(brainstorm.experiences), [brainstorm.experiences]);

  const primaryMajor = useMemo(
    () => brainstorm.targetMajors.find((major) => major.isPrimary) ?? brainstorm.targetMajors[0] ?? null,
    [brainstorm.targetMajors],
  );

  const highlightIds = useMemo(
    () => brainstorm.experiences.filter((exp) => exp.highlight).map((exp) => exp.id),
    [brainstorm.experiences],
  );

  const gapIds = useMemo(
    () => brainstorm.experiences.filter((exp) => exp.difficulty).map((exp) => exp.id),
    [brainstorm.experiences],
  );

  const stepIndex = useMemo(() => {
    switch (activeStep) {
      case 'brainstorm':
        return 0;
      case 'cv':
        return 1;
      case 'ps':
        return 2;
      default:
        return 0;
    }
  }, [activeStep]);

  const handleAddMajor = useCallback(
    (name: string) => {
      const trimmed = name.trim();
      if (!trimmed) {
        return;
      }

      const canonical = resolveMajorName(trimmed);
      const canonicalKey = normalizeMajorKey(canonical);

      setBrainstorm((prev) => {
        if (prev.targetMajors.some((major) => normalizeMajorKey(major.name) === canonicalKey)) {
          return prev;
        }

        const newMajor: MajorTarget = {
          id: createId(),
          name: canonical,
          isPrimary: prev.targetMajors.length === 0,
        };

        return {
          ...prev,
          targetMajors: [...prev.targetMajors, newMajor],
        };
      });

      setMajorSearchValue('');
    },
    [resolveMajorName, setMajorSearchValue],
  );

  const handleSetPrimaryMajor = useCallback((id: string) => {
    setBrainstorm((prev) => ({
      ...prev,
      targetMajors: prev.targetMajors.map((major) => ({
        ...major,
        isPrimary: major.id === id,
      })),
    }));
  }, []);

  const handleRemoveMajor = useCallback((id: string) => {
    setBrainstorm((prev) => {
      const remaining = prev.targetMajors.filter((major) => major.id !== id);
      if (remaining.length === 0) {
        return {
          ...prev,
          targetMajors: [],
        };
      }
      if (remaining.some((major) => major.isPrimary)) {
        return {
          ...prev,
          targetMajors: remaining,
        };
      }
      return {
        ...prev,
        targetMajors: remaining.map((major, index) => ({
          ...major,
          isPrimary: index === 0,
        })),
      };
    });
  }, []);

  const handleAddExperience = useCallback((type: DocumentExperienceType) => {
    const section = EXPERIENCE_SECTIONS.find((item) => item.type === type);
    const newExperience: DocumentExperienceItem = {
      id: createId(),
      type,
      title: '',
      org: '',
      timeframe: null,
      details: [],
      impact: '',
      tags: section ? [section.title] : [],
      metadata: {
        created_at: new Date().toISOString(),
      },
    };

    setBrainstorm((prev) => ({
      ...prev,
      experiences: [...prev.experiences, newExperience],
    }));
  }, []);

  const handleUpdateExperience = useCallback(
    (id: string, updater: (experience: DocumentExperienceItem) => DocumentExperienceItem) => {
      setBrainstorm((prev) => ({
        ...prev,
        experiences: prev.experiences.map((experience) =>
          experience.id === id ? normalizeExperience(updater(experience)) : experience,
        ),
      }));
    },
    [],
  );

  const handleRemoveExperience = useCallback((id: string) => {
    setBrainstorm((prev) => ({
      ...prev,
      experiences: prev.experiences.filter((experience) => experience.id !== id),
      highlights: prev.highlights.filter((item) => !item.includes(id)),
      gaps: prev.gaps.filter((item) => !item.includes(id)),
    }));
  }, []);

  const handleToggleHighlight = useCallback((id: string) => {
    setBrainstorm((prev) => {
      let label = '';
      const experiences = prev.experiences.map((experience) => {
        if (experience.id !== id) {
          return experience;
        }
        const nextHighlight = !experience.highlight;
        label =
          experience.title?.trim() ||
          (experience.org ? `${experience.org} · ${experience.type}` : experience.type) ||
          `经历-${experience.id.slice(-4)}`;
        return {
          ...experience,
          highlight: nextHighlight,
        };
      });

      if (!label) {
        return {
          ...prev,
          experiences,
        };
      }

      const targetExperience = experiences.find((experience) => experience.id === id);
      const highlights = targetExperience?.highlight
        ? Array.from(new Set([...prev.highlights, label]))
        : prev.highlights.filter((item) => item !== label);

      return {
        ...prev,
        experiences,
        highlights,
      };
    });
  }, []);

  const handleToggleGap = useCallback((id: string) => {
    setBrainstorm((prev) => {
      let label = '';
      const experiences = prev.experiences.map((experience) => {
        if (experience.id !== id) {
          return experience;
        }
        const nextDifficulty = !experience.difficulty;
        label =
          experience.title?.trim() ||
          (experience.org ? `${experience.org} · ${experience.type}` : experience.type) ||
          `经历-${experience.id.slice(-4)}`;
        return {
          ...experience,
          difficulty: nextDifficulty,
        };
      });

      if (!label) {
        return {
          ...prev,
          experiences,
        };
      }

      const targetExperience = experiences.find((experience) => experience.id === id);
      const gaps = targetExperience?.difficulty
        ? Array.from(new Set([...prev.gaps, label]))
        : prev.gaps.filter((item) => item !== label);

      return {
        ...prev,
        experiences,
        gaps,
      };
    });
  }, []);

  const handleImportFromPlanner = useCallback(() => {
    if (!authState.isAuthenticated) {
      message.warning('请先登录后再导入留学规划档案');
      return;
    }

    const currentUser = authService.getCurrentUser();
    if (!currentUser?.profile_data) {
      message.info('当前账号暂无留学档案，请先在留学规划助手中填写');
      return;
    }

    const profile = currentUser.profile_data as Partial<Omit<UserBackground, 'other_experiences'>> & {
      other_experiences?: Array<Record<string, any>>;
      target_schools?: string[];
    };

    const rawTargetMajors = Array.isArray(profile.target_majors)
      ? profile.target_majors.filter(Boolean)
      : [];

    const importedMajors = normalizeMajorTargets(
      rawTargetMajors.map((name, index) => ({
        id: createId(),
        name,
        isPrimary: index === 0,
      }))
    );
    const canonicalTargetMajorStrings = rawTargetMajors.map(resolveMajorName);

    const importedExperiences: DocumentExperienceItem[] = [];

    if (Array.isArray(profile.internship_experiences)) {
      profile.internship_experiences.forEach((experience, index) => {
        importedExperiences.push(
          normalizeExperience({
            id: createId(),
            type: 'internship',
            title: experience.position || experience.company || `实习经历 ${index + 1}`,
            org: experience.company,
            details: experience.description ? [experience.description] : [],
            tags: ['实习', experience.company].filter(Boolean) as string[],
          }),
        );
      });
    }

    if (Array.isArray(profile.research_experiences)) {
      profile.research_experiences.forEach((experience, index) => {
        importedExperiences.push(
          normalizeExperience({
            id: createId(),
            type: 'research',
            title: experience.name || `科研课题 ${index + 1}`,
            org: experience.role,
            details: experience.description ? [experience.description] : [],
            tags: ['科研', experience.role].filter(Boolean) as string[],
          }),
        );
      });
    }

    if (Array.isArray(profile.other_experiences)) {
      profile.other_experiences.forEach((experience) => {
        const rawType = (experience as any).type as DocumentExperienceType | undefined;
        importedExperiences.push(
          normalizeExperience({
            id: experience.id ?? createId(),
            type: rawType ?? 'other',
            title: (experience as any).title || experience.name || '其他经历',
            org: (experience as any).org,
            timeframe: (experience as any).timeframe ?? null,
            details: Array.isArray((experience as any).details)
              ? (experience as any).details
              : (experience.description ? [experience.description] : []),
            impact: (experience as any).impact,
            tags: Array.isArray((experience as any).tags)
              ? (experience as any).tags
              : [],
            metadata: experience,
          }),
        );
      });
    }

    setBrainstorm((prev) => ({
      ...prev,
      targetDegree: (profile.target_degree_type as DegreeType) || prev.targetDegree,
      targetMajors: mergeMajors(prev.targetMajors, importedMajors),
      targetSchools: mergeStrings(prev.targetSchools, [
        ...(Array.isArray(profile.target_schools) ? profile.target_schools : []),
        ...(Array.isArray(profile.target_countries) ? profile.target_countries : []),
      ]),
      applicationYear: profile.application_year ?? prev.applicationYear ?? null,
      experiences: mergeExperiences(prev.experiences, importedExperiences),
      tags: mergeStrings(prev.tags, canonicalTargetMajorStrings),
      highlights: prev.highlights,
      gaps: prev.gaps,
    }));

    message.success('已从留学规划档案导入，可继续补充文书信息');
  }, [authState.isAuthenticated, normalizeMajorTargets, resolveMajorName]);

  const handleStructureBrainstorm = useCallback(async () => {
    if (!authState.isAuthenticated) {
      message.warning('登录后即可使用 AI 结构化与去重功能');
      return;
    }

    if (brainstorm.experiences.length === 0) {
      message.warning('请先录入或导入至少一条经历');
      return;
    }

    setIsStructuring(true);
    try {
      const canonicalTargetMajor = primaryMajor ? resolveMajorName(primaryMajor.name) : null;

      const payload = {
        raw_experiences: brainstorm.experiences.map((experience) => ({
          id: experience.id,
          type: experience.type,
          title: experience.title,
          org: experience.org,
          timeframe: experience.timeframe,
          details: experience.details,
          impact: experience.impact,
          tags: experience.tags,
          metadata: experience.metadata,
          highlight: experience.highlight,
          difficulty: experience.difficulty,
        })),
        target_major: canonicalTargetMajor,
        target_degree: brainstorm.targetDegree || null,
        tags: brainstorm.tags,
        prompts: brainstorm.preferences.styleKeywords,
      };

      const response: BrainstormStructureResponse = await documentsService.structureBrainstorm(payload);

      setBrainstorm((prev) => ({
        ...prev,
        experiences: mergeExperiences(prev.experiences, response.structured_experiences),
        tags: mergeStrings(prev.tags, response.tags),
        highlights: mergeStrings(prev.highlights, response.highlights),
        lastStructuredAt: new Date().toISOString(),
      }));

      setStructuringMeta({
        requestId: response.request_id,
        usage: response.usage,
        mergeSuggestions: response.merge_suggestions,
      });

      message.success('结构化成功，已自动合并重复条目');
    } catch (error) {
      const { userMessage } = errorHandler.buildUserFacingError(error, {
        component: 'DocumentsPage',
        action: 'structureBrainstorm',
      });
      message.error(userMessage.title);
    } finally {
      setIsStructuring(false);
    }
  }, [authState.isAuthenticated, brainstorm.experiences, brainstorm.preferences.styleKeywords, brainstorm.tags, brainstorm.targetDegree, primaryMajor, resolveMajorName]);

  const handleGenerateCv = useCallback(async () => {
    if (!authState.isAuthenticated) {
      message.warning('登录后才可调用云端生成与导出简历，当前草稿已在本地保存');
      return;
    }

    if (brainstorm.experiences.length === 0) {
      message.warning('请先完成头脑风暴并整理经历');
      return;
    }

    setIsGeneratingCv(true);
    try {
      const result = await documentsService.generateCV({
        structured_experiences: brainstorm.experiences.map(normalizeExperience),
        template_type: cvConfig.templateType,
        language: cvConfig.language,
        length: cvConfig.length,
        tone: mapPreferenceToneToServiceTone(brainstorm.preferences.tone),
        highlight_ids: cvConfig.emphasizeHighlights ? highlightIds : [],
        tag_preferences: brainstorm.tags,
        ats_friendly: cvConfig.atsFriendly,
        mirror_version: cvConfig.mirrorVersion,
        include_preferences: {
          languages: [brainstorm.preferences.language],
          style: brainstorm.preferences.styleKeywords.join(' / ') || undefined,
          length: brainstorm.preferences.length,
          notes: brainstorm.preferences.notes || undefined,
        },
        major: primaryMajor?.name,
        degree: brainstorm.targetDegree || undefined,
      });

      const preview: CvPreview = {
        requestId: result.request_id,
        generatedAt: new Date().toISOString(),
        cvJson: result.cv_json,
        cvMarkdown: result.cv_markdown,
        cvPlaintext: result.cv_plaintext,
        mirrorVersions: result.mirror_versions,
        revisionNotes: result.revision_notes,
        usage: result.usage,
      };

      setCvPreview(preview);
      message.success('CV 生成完成，可在右侧预览与导出');
    } catch (error) {
      const { userMessage } = errorHandler.buildUserFacingError(error, {
        component: 'DocumentsPage',
        action: 'generateCV',
      });
      message.error(userMessage.title);
    } finally {
      setIsGeneratingCv(false);
    }
  }, [
    authState.isAuthenticated,
    brainstorm.experiences,
    brainstorm.preferences.language,
    brainstorm.preferences.length,
    brainstorm.preferences.notes,
    brainstorm.preferences.styleKeywords,
    brainstorm.preferences.tone,
    brainstorm.tags,
    brainstorm.targetDegree,
    cvConfig.atsFriendly,
    cvConfig.emphasizeHighlights,
    cvConfig.language,
    cvConfig.length,
    cvConfig.mirrorVersion,
    cvConfig.templateType,
    highlightIds,
    primaryMajor,
  ]);

  const handleGeneratePs = useCallback(async () => {
    if (!authState.isAuthenticated) {
      message.warning('请登录后再生成 PS 草稿，可先在本地调整提纲');
      return;
    }

    if (!psConfig.targetMajor) {
      message.warning('请先设置目标专业与院校信息');
      return;
    }

    if (brainstorm.experiences.length === 0) {
      message.warning('至少需要一条结构化经历才可生成 PS');
      return;
    }

    setIsGeneratingPs(true);
    try {
      const canonicalTargetMajor = psConfig.targetMajor ? resolveMajorName(psConfig.targetMajor) : '';

      if (canonicalTargetMajor !== psConfig.targetMajor) {
        setPsConfig((prev) => ({
          ...prev,
          targetMajor: canonicalTargetMajor,
        }));
      }

      const response: PsGenerationResponse = await documentsService.generatePS({
        structured_experiences: brainstorm.experiences.map(normalizeExperience),
        target_major: canonicalTargetMajor,
        target_schools: psConfig.targetSchools,
        outline: psConfig.outline,
        word_limit: psConfig.wordLimit,
        tone: psConfig.tone,
        emphasis: {
          research: psConfig.emphasizeResearch,
          career: psConfig.emphasizeCareer,
        },
        preferences: {
          language: brainstorm.preferences.language,
          voice: brainstorm.preferences.styleKeywords.join(', ') || undefined,
          length: brainstorm.preferences.length,
          highlight_ids: highlightIds,
          gap_ids: gapIds,
          tags: brainstorm.tags,
        },
        imports: {
          program_brief: psConfig.programBrief || undefined,
          keywords: psConfig.customKeywords.length ? psConfig.customKeywords : undefined,
        },
      });

      const draft: PsDraft = {
        requestId: response.request_id,
        generatedAt: new Date().toISOString(),
        outline: response.outline_checked,
        paragraphs: response.ps_paragraphs,
        fullText: response.ps_full_text,
        revisionSuggestions: response.revision_suggestions,
        verificationPrompts: response.verification_prompts,
        usage: response.usage,
      };

      setPsDraft(draft);
      message.success('PS 草稿已生成，可逐段修订与导出');
    } catch (error) {
      const { userMessage } = errorHandler.buildUserFacingError(error, {
        component: 'DocumentsPage',
        action: 'generatePS',
      });
      message.error(userMessage.title);
    } finally {
      setIsGeneratingPs(false);
    }
  }, [
    authState.isAuthenticated,
    brainstorm.experiences,
    brainstorm.preferences.language,
    brainstorm.preferences.length,
    brainstorm.preferences.styleKeywords,
    brainstorm.tags,
    gapIds,
    highlightIds,
    psConfig.customKeywords,
    psConfig.emphasizeCareer,
    psConfig.emphasizeResearch,
    psConfig.outline,
    psConfig.programBrief,
    psConfig.targetMajor,
    psConfig.targetSchools,
    psConfig.tone,
    psConfig.wordLimit,
    resolveMajorName,
  ]);

  const handleDownloadText = useCallback((content: string, filename: string, mime: string) => {
    if (!content) {
      message.warning('暂无可导出的内容');
      return;
    }

    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  }, []);

  const handleParagraphAction = useCallback((action: string, index: number) => {
    const actionName =
      action === 'rewrite'
        ? '重写'
        : action === 'quantify'
        ? '加强量化'
        : action === 'condense'
        ? '压缩篇幅'
        : '微调';
    message.info(`段落 ${index + 1} 的“${actionName}”操作将接入后端后可用`);
  }, []);

  const renderExperienceSection = (section: ExperienceSection) => {
    const experiences = brainstorm.experiences.filter((experience) => experience.type === section.type);
    return (
      <Card
        key={section.type}
        title={section.title}
        extra={
          <Space>
            <Tooltip title={section.description}>
              <InfoBadge />
            </Tooltip>
            <Button type="link" icon={<PlusOutlined />} onClick={() => handleAddExperience(section.type)}>
              新增条目
            </Button>
          </Space>
        }
        bodyStyle={{ paddingTop: 12 }}
      >
        {experiences.length === 0 ? (
          <Empty description="暂未添加条目" image={Empty.PRESENTED_IMAGE_SIMPLE}>
            <Button type="primary" onClick={() => handleAddExperience(section.type)}>
              添加{section.title}
            </Button>
          </Empty>
        ) : (
          <Space direction="vertical" style={{ width: '100%' }} size={16}>
            {experiences.map((experience) => {
              const timeframeValue = formatTimeframeValue(experience);
              return (
                <Card
                  key={experience.id}
                  type="inner"
                  title={
                    <Space>
                      <Text strong>{experience.title || '未命名经历'}</Text>
                      {experience.highlight && <Tag color="gold">亮点</Tag>}
                      {experience.difficulty && <Tag color="red">难点</Tag>}
                    </Space>
                  }
                  extra={
                    <Space size="small">
                      <Tooltip title="加入亮点清单">
                        <Button
                          type="text"
                          icon={<StarOutlined />}
                          onClick={() => handleToggleHighlight(experience.id)}
                          style={{ color: experience.highlight ? '#f59e0b' : undefined }}
                        />
                      </Tooltip>
                      <Tooltip title="标记为难点或待补充">
                        <Button
                          type="text"
                          icon={<HighlightOutlined />}
                          onClick={() => handleToggleGap(experience.id)}
                          style={{ color: experience.difficulty ? '#dc2626' : undefined }}
                        />
                      </Tooltip>
                      <Tooltip title="删除条目">
                        <Button type="text" danger icon={<ScissorOutlined />} onClick={() => handleRemoveExperience(experience.id)} />
                      </Tooltip>
                    </Space>
                  }
                >
                  <Space direction="vertical" style={{ width: '100%' }} size={12}>
                    <Input
                      value={experience.title}
                      placeholder="标题（如：字节跳动数据分析实习生）"
                      onChange={(event) =>
                        handleUpdateExperience(experience.id, (prevExp) => ({
                          ...prevExp,
                          title: event.target.value,
                        }))
                      }
                    />
                    <Input
                      value={experience.org}
                      placeholder="机构 / 部门 / 职位"
                      onChange={(event) =>
                        handleUpdateExperience(experience.id, (prevExp) => ({
                          ...prevExp,
                          org: event.target.value,
                        }))
                      }
                    />
                    <Input
                      value={timeframeValue}
                      placeholder="时间范围（例：2023.06 - 2023.12）"
                      onChange={(event) => {
                        const { timeframe, raw } = parseTimeframeInput(event.target.value);
                        handleUpdateExperience(experience.id, (prevExp) => ({
                          ...prevExp,
                          timeframe,
                          metadata: {
                            ...(prevExp.metadata ?? {}),
                            raw_timeframe: raw,
                          },
                        }));
                      }}
                    />
                    <Select
                      mode="tags"
                      value={experience.tags}
                      placeholder="标签（例：数据科学、量化、产品）"
                      options={section.tagRecommendations.map((tag) => ({ label: tag, value: tag }))}
                      onChange={(value) =>
                        handleUpdateExperience(experience.id, (prevExp) => ({
                          ...prevExp,
                          tags: value,
                        }))
                      }
                    />
                    <Input.TextArea
                      value={experience.details.join('\n')}
                      placeholder="关键细节（每行一条，可包含职责、行动、成果、指标等）"
                      autoSize={{ minRows: 3, maxRows: 8 }}
                      onChange={(event) => {
                        const lines = event.target.value
                          .split('\n')
                          .map((line) => line.trim())
                          .filter(Boolean);
                        handleUpdateExperience(experience.id, (prevExp) => ({
                          ...prevExp,
                          details: lines,
                        }));
                      }}
                    />
                    <Input.TextArea
                      value={experience.impact}
                      placeholder="重点成果或量化影响（用于自动生成 STAR/CAR 要点）"
                      autoSize={{ minRows: 2, maxRows: 4 }}
                      onChange={(event) =>
                        handleUpdateExperience(experience.id, (prevExp) => ({
                          ...prevExp,
                          impact: event.target.value,
                        }))
                      }
                    />
                  </Space>
                </Card>
              );
            })}
          </Space>
        )}
      </Card>
    );
  };

  const tabItems: TabsProps['items'] = [
    {
      key: 'brainstorm',
      label: '头脑风暴',
      children: (
        <Space direction="vertical" size={20} style={{ width: '100%' }}>
          <Card
            title="Step 1 · 信息采集与结构化"
            extra={
              <Space>
                <Button icon={<CloudUploadOutlined />} onClick={handleImportFromPlanner}>
                  从留学规划导入
                </Button>
                <Tooltip title="使用 LLM 自动去重、结构化并补充缺失字段">
                  <Button
                    type="primary"
                    icon={<MergeCellsOutlined />}
                    loading={isStructuring}
                    onClick={handleStructureBrainstorm}
                  >
                    结构化与去重
                  </Button>
                </Tooltip>
              </Space>
            }
          >
            <Row gutter={20}>
              <Col xs={24} md={12}>
                <Space direction="vertical" size={16} style={{ width: '100%' }}>
                  <Card type="inner" title="目标信息">
                    <Space direction="vertical" size={12} style={{ width: '100%' }}>
                      <div>
                        <Text type="secondary">目标学位</Text>
                        <Radio.Group
                          value={brainstorm.targetDegree}
                          onChange={(event) =>
                            setBrainstorm((prev) => ({
                              ...prev,
                              targetDegree: event.target.value,
                            }))
                          }
                          style={{ marginTop: 8 }}
                        >
                          <Radio.Button value="Master">Master</Radio.Button>
                          <Radio.Button value="PhD">PhD</Radio.Button>
                          <Radio.Button value="Other">Other</Radio.Button>
                        </Radio.Group>
                      </div>
                      <div>
                        <Text type="secondary">申请季 / 年</Text>
                        <Space direction="horizontal" size={12} style={{ marginTop: 8 }}>
                          <Select
                            style={{ width: 120 }}
                            value={brainstorm.applicationSeason}
                            onChange={(value) =>
                              setBrainstorm((prev) => ({
                                ...prev,
                                applicationSeason: value,
                              }))
                            }
                            options={[
                              { label: 'Fall', value: 'Fall' },
                              { label: 'Spring', value: 'Spring' },
                              { label: 'Rolling', value: 'Rolling' },
                            ]}
                          />
                          <InputNumber
                            style={{ width: 120 }}
                            placeholder="年份"
                            value={brainstorm.applicationYear ?? undefined}
                            min={2023}
                            max={2035}
                            onChange={(value) =>
                              setBrainstorm((prev) => ({
                                ...prev,
                                applicationYear: value ?? null,
                              }))
                            }
                          />
                        </Space>
                      </div>
                      <div>
                        <Text type="secondary">目标专业（可多选，标主攻方向）</Text>
                        <Space direction="vertical" style={{ width: '100%', marginTop: 8 }} size={8}>
                      <AutoComplete
                        value={majorSearchValue}
                        options={majorAutoCompleteOptions}
                        onSearch={(value) => setMajorSearchValue(value)}
                        onChange={(value) => setMajorSearchValue(value)}
                        onSelect={(value) => handleAddMajor(value)}
                        notFoundContent={majorOptionsLoading ? <Spin size="small" /> : null}
                        style={{ width: '100%' }}
                      >
                            <Input.Search
                              placeholder="输入后回车添加，如 Data Science"
                              enterButton="添加"
                              value={majorSearchValue}
                              onChange={(event) => setMajorSearchValue(event.target.value)}
                              onSearch={(value) => handleAddMajor(value)}
                              loading={majorOptionsLoading}
                            />
                          </AutoComplete>
                          {brainstorm.targetMajors.length === 0 ? (
                            <Alert
                              message="尚未添加目标专业，可先导入或手动输入"
                              type="info"
                              showIcon
                            />
                          ) : (
                            <Space wrap>
                              {brainstorm.targetMajors.map((major) => (
                                <Tag key={major.id} color={major.isPrimary ? 'geekblue' : 'default'}>
                                  <Space size={4}>
                                    <span>{major.name}</span>
                                    {major.isPrimary ? (
                                      <Text style={{ fontSize: 12, color: '#e0e7ff' }}>主攻</Text>
                                    ) : (
                                      <Button
                                        size="small"
                                        type="link"
                                        onClick={() => handleSetPrimaryMajor(major.id)}
                                      >
                                        设为主攻
                                      </Button>
                                    )}
                                    <Button
                                      size="small"
                                      type="link"
                                      danger
                                      onClick={() => handleRemoveMajor(major.id)}
                                    >
                                      移除
                                    </Button>
                                  </Space>
                                </Tag>
                              ))}
                            </Space>
                          )}
                        </Space>
                      </div>
                      <div>
                        <Text type="secondary">目标院校（可选）</Text>
                        <Select
                          mode="tags"
                          placeholder="输入后回车添加，例如 MIT、CMU"
                          value={brainstorm.targetSchools}
                          onChange={(value) =>
                            setBrainstorm((prev) => ({
                              ...prev,
                              targetSchools: value,
                            }))
                          }
                          style={{ marginTop: 8 }}
                        />
                      </div>
                    </Space>
                  </Card>
                  <Card type="inner" title="派生元数据">
                    <Space direction="vertical" size={12} style={{ width: '100%' }}>
                      <div>
                        <Text type="secondary">主题标签</Text>
                        <Select
                          mode="tags"
                          value={brainstorm.tags}
                          placeholder="示例：数据科学、金融、产品、公共政策"
                          onChange={(value) =>
                            setBrainstorm((prev) => ({
                              ...prev,
                              tags: value,
                            }))
                          }
                          style={{ marginTop: 8 }}
                        />
                      </div>
                      <div>
                        <Text type="secondary">亮点清单</Text>
                        <Input.TextArea
                          autoSize={{ minRows: 2, maxRows: 4 }}
                          value={brainstorm.highlights.join('\n')}
                          placeholder="每行一条亮点，可通过经历卡片快捷添加"
                          onChange={(event) =>
                            setBrainstorm((prev) => ({
                              ...prev,
                              highlights: event.target.value
                                .split('\n')
                                .map((item) => item.trim())
                                .filter(Boolean),
                            }))
                          }
                        />
                      </div>
                      <div>
                        <Text type="secondary">难点/待补充清单</Text>
                        <Input.TextArea
                          autoSize={{ minRows: 2, maxRows: 4 }}
                          value={brainstorm.gaps.join('\n')}
                          placeholder="每行一条难点，可用于生成时提醒补充细节"
                          onChange={(event) =>
                            setBrainstorm((prev) => ({
                              ...prev,
                              gaps: event.target.value
                                .split('\n')
                                .map((item) => item.trim())
                                .filter(Boolean),
                            }))
                          }
                        />
                      </div>
                      <div>
                        <Text type="secondary">个人偏好</Text>
                        <Space direction="vertical" size={8} style={{ width: '100%', marginTop: 8 }}>
                          <Select
                            value={brainstorm.preferences.tone}
                            onChange={(value) =>
                              setBrainstorm((prev) => ({
                                ...prev,
                                preferences: { ...prev.preferences, tone: value },
                              }))
                            }
                            options={[
                              { label: '真诚', value: 'sincere' },
                              { label: '自信', value: 'confident' },
                              { label: '学术', value: 'academic' },
                              { label: '故事化', value: 'story' },
                            ]}
                          />
                          <Select
                            mode="tags"
                            value={brainstorm.preferences.styleKeywords}
                            placeholder="风格关键词（如：量化、结构化、故事性）"
                            onChange={(value) =>
                              setBrainstorm((prev) => ({
                                ...prev,
                                preferences: { ...prev.preferences, styleKeywords: value },
                              }))
                            }
                          />
                          <Space>
                            <Select
                              style={{ width: 160 }}
                              value={brainstorm.preferences.language}
                              onChange={(value) =>
                                setBrainstorm((prev) => ({
                                  ...prev,
                                  preferences: { ...prev.preferences, language: value },
                                }))
                              }
                              options={[
                                { label: '英文', value: 'en' },
                                { label: '中文', value: 'zh' },
                              ]}
                            />
                            <Select
                              style={{ width: 160 }}
                              value={brainstorm.preferences.length}
                              onChange={(value) =>
                                setBrainstorm((prev) => ({
                                  ...prev,
                                  preferences: { ...prev.preferences, length: value },
                                }))
                              }
                              options={[
                                { label: '1 页', value: '1page' },
                                { label: '2 页', value: '2pages' },
                              ]}
                            />
                          </Space>
                          <Input.TextArea
                            autoSize={{ minRows: 2, maxRows: 4 }}
                            placeholder="补充其他偏好或禁忌（例如：避免提及某段经历、突出非营利背景）"
                            value={brainstorm.preferences.notes}
                            onChange={(event) =>
                              setBrainstorm((prev) => ({
                                ...prev,
                                preferences: { ...prev.preferences, notes: event.target.value },
                              }))
                            }
                          />
                        </Space>
                      </div>
                    </Space>
                  </Card>
                </Space>
              </Col>
              <Col xs={24} md={12}>
                <Space direction="vertical" size={16} style={{ width: '100%' }}>
                  {EXPERIENCE_SECTIONS.map(renderExperienceSection)}
                </Space>
              </Col>
            </Row>
            <Divider />
            <Row gutter={20}>
              <Col xs={24} md={12}>
                <Card type="inner" title="时间线预览">
                  {derivedTimeline.length === 0 ? (
                    <Empty description="待补充经历信息后自动生成" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                  ) : (
                    <Space direction="vertical" size={8}>
                      {derivedTimeline.map((item) => (
                        <Tag key={item} color="processing">
                          {item}
                        </Tag>
                      ))}
                    </Space>
                  )}
                </Card>
              </Col>
              <Col xs={24} md={12}>
                <Card
                  type="inner"
                  title="合并与补全建议"
                  extra={
                    structuringMeta?.usage ? (
                      <Text type="secondary">Tokens: {formatUsage(structuringMeta.usage)}</Text>
                    ) : null
                  }
                >
                  {structuringMeta?.mergeSuggestions && structuringMeta.mergeSuggestions.length > 0 ? (
                    <Space direction="vertical" size={8}>
                      {structuringMeta.mergeSuggestions.map((suggestion, index) => (
                        <Alert
                          key={`${suggestion}-${index}`}
                          type="info"
                          message={suggestion}
                          showIcon
                        />
                      ))}
                    </Space>
                  ) : (
                    <Empty description="暂未生成合并建议" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                  )}
                </Card>
              </Col>
            </Row>
          </Card>
        </Space>
      ),
    },
    {
      key: 'cv',
      label: 'CV 生成',
      children: (
        <Space direction="vertical" size={20} style={{ width: '100%' }}>
          <Card
            title="Step 2 · 模板选择与简历生成"
            extra={
              <Button
                type="primary"
                icon={<ReloadOutlined />}
                loading={isGeneratingCv}
                onClick={handleGenerateCv}
              >
                生成 CV
              </Button>
            }
          >
            <Row gutter={20}>
              <Col xs={24} lg={10}>
                <Card type="inner" title="模板与输出设置">
                  <Space direction="vertical" size={16} style={{ width: '100%' }}>
                    <div>
                      <Text type="secondary">模板类型</Text>
                      <Select
                        value={cvConfig.templateType}
                        options={CV_TEMPLATE_OPTIONS}
                        optionRender={(option) => (
                          <Space direction="vertical" size={0}>
                            <Text strong>{option.data.label}</Text>
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              {option.data.description}
                            </Text>
                          </Space>
                        )}
                        style={{ width: '100%', marginTop: 8 }}
                        onChange={(value) =>
                          setCvConfig((prev) => ({
                            ...prev,
                            templateType: value,
                          }))
                        }
                      />
                    </div>
                    <Space>
                      <Select
                        value={cvConfig.language}
                        style={{ width: 160 }}
                        onChange={(value) =>
                          setCvConfig((prev) => ({
                            ...prev,
                            language: value,
                          }))
                        }
                        options={[
                          { label: '英文', value: 'en' },
                          { label: '中文', value: 'zh' },
                        ]}
                      />
                      <Select
                        value={cvConfig.length}
                        style={{ width: 160 }}
                        onChange={(value) =>
                          setCvConfig((prev) => ({
                            ...prev,
                            length: value,
                          }))
                        }
                        options={[
                          { label: '1 页', value: '1page' },
                          { label: '2 页', value: '2pages' },
                        ]}
                      />
                    </Space>
                    <Checkbox
                      checked={cvConfig.atsFriendly}
                      onChange={(event) =>
                        setCvConfig((prev) => ({
                          ...prev,
                          atsFriendly: event.target.checked,
                        }))
                      }
                    >
                      ATS 友好排版（保持纯文本分隔，避免复杂布局）
                    </Checkbox>
                    <Checkbox
                      checked={cvConfig.autoQuantify}
                      onChange={(event) =>
                        setCvConfig((prev) => ({
                          ...prev,
                          autoQuantify: event.target.checked,
                        }))
                      }
                    >
                      自动强化量化动词与指标
                    </Checkbox>
                    <Checkbox
                      checked={cvConfig.emphasizeHighlights}
                      onChange={(event) =>
                        setCvConfig((prev) => ({
                          ...prev,
                          emphasizeHighlights: event.target.checked,
                        }))
                      }
                    >
                      优先展示亮点经历（共 {highlightIds.length} 条）
                    </Checkbox>
                    <Checkbox
                      checked={cvConfig.mirrorVersion}
                      onChange={(event) =>
                        setCvConfig((prev) => ({
                          ...prev,
                          mirrorVersion: event.target.checked,
                        }))
                      }
                    >
                      同步生成镜像版本（Academic / Industry）
                    </Checkbox>
                    <Alert
                      type="info"
                      showIcon
                      message="未登录时可继续编辑草稿；点击生成需要登录后调用云端文书服务。"
                    />
                  </Space>
                </Card>
                <Card type="inner" title="结构树概览" style={{ marginTop: 16 }}>
                  {brainstorm.experiences.length === 0 ? (
                    <Empty description="请先完成头脑风暴" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                  ) : (
                    <Space direction="vertical" size={12}>
                      {EXPERIENCE_SECTIONS.map((section) => {
                        const experiences = brainstorm.experiences.filter(
                          (experience) => experience.type === section.type,
                        );
                        if (experiences.length === 0) {
                          return null;
                        }
                        return (
                          <div key={section.type}>
                            <Text strong>{section.title}</Text>
                            <ul className="list-disc pl-5 text-sm text-slate-600">
                              {experiences.map((experience) => (
                                <li key={experience.id}>
                                  {experience.title || '未命名经历'}{' '}
                                  {experience.highlight && <Tag color="gold">亮点</Tag>}
                                  {experience.difficulty && <Tag color="red">难点</Tag>}
                                </li>
                              ))}
                            </ul>
                          </div>
                        );
                      })}
                    </Space>
                  )}
                </Card>
              </Col>
              <Col xs={24} lg={14}>
                <Card
                  type="inner"
                  title="实时预览"
                  extra={
                    cvPreview ? (
                      <Space>
                        <Tooltip title="导出 Markdown 文件">
                          <Button
                            icon={<DownloadOutlined />}
                            onClick={() =>
                              handleDownloadText(
                                cvPreview.cvMarkdown,
                                `cv-${cvPreview.requestId}.md`,
                                'text/markdown;charset=utf-8',
                              )
                            }
                          >
                            导出 Markdown
                          </Button>
                        </Tooltip>
                        {cvPreview.cvPlaintext && (
                          <Tooltip title="导出纯文本文件">
                            <Button
                              icon={<DownloadOutlined />}
                              onClick={() =>
                                handleDownloadText(
                                  cvPreview.cvPlaintext ?? '',
                                  `cv-${cvPreview.requestId}.txt`,
                                  'text/plain;charset=utf-8',
                                )
                              }
                            >
                              导出 Text
                            </Button>
                          </Tooltip>
                        )}
                      </Space>
                    ) : null
                  }
                >
                  {cvPreview ? (
                    <Space direction="vertical" size={12} style={{ width: '100%' }}>
                      <Alert
                        type="success"
                        showIcon
                        message={`生成于 ${new Date(cvPreview.generatedAt).toLocaleString()}（Request ID: ${cvPreview.requestId}${
                          cvPreview.usage ? `，Tokens：${formatUsage(cvPreview.usage)}` : ''
                        }）`}
                      />
                      <pre className="bg-slate-900 text-indigo-100 p-4 rounded-xl overflow-auto max-h-[480px] text-sm">
                        {cvPreview.cvMarkdown}
                      </pre>
                      {cvPreview.mirrorVersions && cvPreview.mirrorVersions.length > 0 && (
                        <Card type="inner" title="镜像版本">
                          <Space direction="vertical" size={12} style={{ width: '100%' }}>
                            {cvPreview.mirrorVersions.map((variant) => (
                              <Card
                                key={variant.template_type}
                                type="inner"
                                title={CV_TEMPLATE_OPTIONS.find((item) => item.value === variant.template_type)?.label}
                                extra={
                                  <Button
                                    size="small"
                                    icon={<DownloadOutlined />}
                                    onClick={() =>
                                      handleDownloadText(
                                        variant.markdown,
                                        `cv-${cvPreview.requestId}-${variant.template_type}.md`,
                                        'text/markdown;charset=utf-8',
                                      )
                                    }
                                  >
                                    下载
                                  </Button>
                                }
                              >
                                <pre className="bg-slate-900 text-indigo-100 p-3 rounded-lg overflow-auto max-h-[260px] text-sm">
                                  {variant.markdown}
                                </pre>
                              </Card>
                            ))}
                          </Space>
                        </Card>
                      )}
                      {cvPreview.revisionNotes && cvPreview.revisionNotes.length > 0 && (
                        <Card type="inner" title="质量自检清单">
                          <ul className="list-disc pl-5 text-sm text-slate-600">
                            {cvPreview.revisionNotes.map((note, index) => (
                              <li key={`${note}-${index}`}>{note}</li>
                            ))}
                          </ul>
                        </Card>
                      )}
                    </Space>
                  ) : (
                    <Empty description="生成后将在此展示 Markdown 预览" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                  )}
                </Card>
              </Col>
            </Row>
          </Card>
        </Space>
      ),
    },
    {
      key: 'ps',
      label: 'PS 生成',
      children: (
        <Space direction="vertical" size={20} style={{ width: '100%' }}>
          <Card
            title="Step 3 · PS 提纲与终稿生成"
            extra={
              <Button
                type="primary"
                icon={<ReloadOutlined />}
                loading={isGeneratingPs}
                onClick={handleGeneratePs}
              >
                生成 PS 草稿
              </Button>
            }
          >
            <Row gutter={20}>
              <Col xs={24} lg={10}>
                <Card type="inner" title="输入与约束">
                  <Space direction="vertical" size={16} style={{ width: '100%' }}>
                    <div>
                      <Text type="secondary">目标结构骨架</Text>
                      <Select
                        value={psConfig.outline}
                        options={PS_STRUCTURE_OPTIONS}
                        optionRender={(option) => (
                          <Space direction="vertical" size={0}>
                            <Text strong>{option.data.label}</Text>
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              {option.data.description}
                            </Text>
                          </Space>
                        )}
                        style={{ width: '100%', marginTop: 8 }}
                        onChange={(value) =>
                          setPsConfig((prev) => ({
                            ...prev,
                            outline: value,
                          }))
                        }
                      />
                    </div>
                    <div>
                      <Text type="secondary">目标专业与院校</Text>
                      <AutoComplete
                        style={{ marginTop: 8 }}
                        value={psConfig.targetMajor}
                        options={majorAutoCompleteOptions}
                        onSearch={(value) =>
                          setPsConfig((prev) => ({
                            ...prev,
                            targetMajor: value,
                          }))
                        }
                        onChange={(value) =>
                          setPsConfig((prev) => ({
                            ...prev,
                            targetMajor: value,
                          }))
                        }
                        onSelect={(value) =>
                          setPsConfig((prev) => ({
                            ...prev,
                            targetMajor: resolveMajorName(value),
                          }))
                        }
                        onBlur={() =>
                          setPsConfig((prev) => ({
                            ...prev,
                            targetMajor: prev.targetMajor ? resolveMajorName(prev.targetMajor) : '',
                          }))
                        }
                        notFoundContent={majorOptionsLoading ? <Spin size="small" /> : null}
                        placeholder="目标专业（支持多方向，以逗号分隔）"
                      />
                      <Select
                        mode="tags"
                        value={psConfig.targetSchools}
                        placeholder="目标院校（例：MIT MFin, CMU MCDS）"
                        style={{ marginTop: 8 }}
                        onChange={(value) =>
                          setPsConfig((prev) => ({
                            ...prev,
                            targetSchools: value,
                          }))
                        }
                      />
                    </div>
                    <div>
                      <Text type="secondary">字数范围（英文词数）</Text>
                      <Space style={{ marginTop: 8 }}>
                        <InputNumber
                          value={psConfig.wordLimit[0]}
                          min={300}
                          max={2000}
                          onChange={(value) =>
                            setPsConfig((prev) => ({
                              ...prev,
                              wordLimit: [value ?? prev.wordLimit[0], prev.wordLimit[1]],
                            }))
                          }
                        />
                        <Text>至</Text>
                        <InputNumber
                          value={psConfig.wordLimit[1]}
                          min={psConfig.wordLimit[0] ?? 300}
                          max={3000}
                          onChange={(value) =>
                            setPsConfig((prev) => ({
                              ...prev,
                              wordLimit: [prev.wordLimit[0], value ?? prev.wordLimit[1]],
                            }))
                          }
                        />
                      </Space>
                    </div>
                    <div>
                      <Text type="secondary">语气偏好</Text>
                      <Select
                        value={psConfig.tone}
                        style={{ width: '100%', marginTop: 8 }}
                        options={[
                          { label: '真诚', value: 'sincere' },
                          { label: '自信', value: 'confident' },
                          { label: '学术', value: 'academic' },
                        ]}
                        onChange={(value) =>
                          setPsConfig((prev) => ({
                            ...prev,
                            tone: value,
                          }))
                        }
                      />
                    </div>
                    <Checkbox
                      checked={psConfig.emphasizeResearch}
                      onChange={(event) =>
                        setPsConfig((prev) => ({
                          ...prev,
                          emphasizeResearch: event.target.checked,
                        }))
                      }
                    >
                      强调科研导向
                    </Checkbox>
                    <Checkbox
                      checked={psConfig.emphasizeCareer}
                      onChange={(event) =>
                        setPsConfig((prev) => ({
                          ...prev,
                          emphasizeCareer: event.target.checked,
                        }))
                      }
                    >
                      强调职业导向与行业痛点
                    </Checkbox>
                    <Checkbox
                      checked={psConfig.includeChecklist}
                      onChange={(event) =>
                        setPsConfig((prev) => ({
                          ...prev,
                          includeChecklist: event.target.checked,
                        }))
                      }
                    >
                      输出证据核查提示（提醒事实核对）
                    </Checkbox>
                    <Input.TextArea
                      autoSize={{ minRows: 2, maxRows: 4 }}
                      placeholder="可选：粘贴项目官网要点/培养目标/课程列表"
                      value={psConfig.programBrief}
                      onChange={(event) =>
                        setPsConfig((prev) => ({
                          ...prev,
                          programBrief: event.target.value,
                        }))
                      }
                    />
                    <Select
                      mode="tags"
                      value={psConfig.customKeywords}
                      placeholder="可选：输入关键词让模型生成“院校契合点”草案"
                      onChange={(value) =>
                        setPsConfig((prev) => ({
                          ...prev,
                          customKeywords: value,
                        }))
                      }
                    />
                    <Alert
                      type="info"
                      showIcon
                      message="未登录用户可继续完善提纲，生成整稿需登录后调用云端模型服务。"
                    />
                  </Space>
                </Card>
              </Col>
              <Col xs={24} lg={14}>
                <Card
                  type="inner"
                  title="提纲与段落预览"
                  extra={
                    psDraft ? (
                      <Space>
                        <Button
                          icon={<DownloadOutlined />}
                          onClick={() =>
                            handleDownloadText(
                              psDraft.fullText,
                              `ps-${psDraft.requestId}.md`,
                              'text/markdown;charset=utf-8',
                            )
                          }
                        >
                          导出 Markdown
                        </Button>
                        <Button
                          icon={<DownloadOutlined />}
                          onClick={() =>
                            handleDownloadText(
                              psDraft.fullText,
                              `ps-${psDraft.requestId}.txt`,
                              'text/plain;charset=utf-8',
                            )
                          }
                        >
                          导出 Text
                        </Button>
                      </Space>
                    ) : null
                  }
                >
                  {psDraft ? (
                    <Space direction="vertical" size={16} style={{ width: '100%' }}>
                      <Alert
                        type="success"
                        showIcon
                        message={`生成于 ${new Date(psDraft.generatedAt).toLocaleString()}（Request ID: ${
                          psDraft.requestId
                        }${psDraft.usage ? `，Tokens：${formatUsage(psDraft.usage)}` : ''}）`}
                      />
                      <Card type="inner" title="段落提纲">
                        <Space direction="vertical" size={8}>
                          {psDraft.outline.map((item, index) => (
                            <Card key={`${item.title}-${index}`} type="inner" size="small">
                              <Space direction="vertical" size={4}>
                                <Text strong>
                                  {index + 1}. {item.title}
                                </Text>
                                <Text type="secondary">{item.summary}</Text>
                                {item.related_experiences.length > 0 && (
                                  <Space wrap>
                                    {item.related_experiences.map((expId) => {
                                      const experience = brainstorm.experiences.find((exp) => exp.id === expId);
                                      return (
                                        <Tag key={expId} color="blue">
                                          {experience?.title || `经历 ${expId.slice(-4)}`}
                                        </Tag>
                                      );
                                    })}
                                  </Space>
                                )}
                              </Space>
                            </Card>
                          ))}
                        </Space>
                      </Card>
                      <Card type="inner" title="段落详情">
                        <Space direction="vertical" size={12} style={{ width: '100%' }}>
                          {psDraft.paragraphs.map((paragraph, index) => (
                            <Card
                              key={`${paragraph.heading}-${index}`}
                              type="inner"
                              title={`${index + 1}. ${paragraph.heading}`}
                              extra={
                                <Space size="small">
                                  <Tooltip title="更学术">
                                    <Button size="small" onClick={() => handleParagraphAction('academic', index)}>
                                      更学术
                                    </Button>
                                  </Tooltip>
                                  <Tooltip title="加强量化">
                                    <Button size="small" onClick={() => handleParagraphAction('quantify', index)}>
                                      量化增强
                                    </Button>
                                  </Tooltip>
                                  <Tooltip title="更故事化">
                                    <Button size="small" onClick={() => handleParagraphAction('story', index)}>
                                      故事化
                                    </Button>
                                  </Tooltip>
                                  <Tooltip title="缩短到指定字数">
                                    <Button size="small" onClick={() => handleParagraphAction('condense', index)}>
                                      控字
                                    </Button>
                                  </Tooltip>
                                </Space>
                              }
                            >
                              <Paragraph>{paragraph.content}</Paragraph>
                              {paragraph.checklist && paragraph.checklist.length > 0 && (
                                <Alert
                                  type="warning"
                                  showIcon
                                  message="证据核查提示"
                                  description={
                                    <ul className="list-disc pl-5 text-sm text-slate-600">
                                      {paragraph.checklist.map((item, itemIndex) => (
                                        <li key={`${item}-${itemIndex}`}>{item}</li>
                                      ))}
                                    </ul>
                                  }
                                />
                              )}
                            </Card>
                          ))}
                        </Space>
                      </Card>
                      <Card type="inner" title="整稿预览（Markdown）">
                        <pre className="bg-slate-900 text-indigo-100 p-4 rounded-xl overflow-auto max-h-[480px] text-sm">
                          {psDraft.fullText}
                        </pre>
                      </Card>
                      {psDraft.revisionSuggestions.length > 0 && (
                        <Card type="inner" title="自检清单">
                          <ul className="list-disc pl-5 text-sm text-slate-600">
                            {psDraft.revisionSuggestions.map((suggestion, index) => (
                              <li key={`${suggestion}-${index}`}>{suggestion}</li>
                            ))}
                          </ul>
                        </Card>
                      )}
                      {psDraft.verificationPrompts && psDraft.verificationPrompts.length > 0 && (
                        <Card type="inner" title="事实核查提醒">
                          <ul className="list-disc pl-5 text-sm text-slate-600">
                            {psDraft.verificationPrompts.map((item, index) => (
                              <li key={`${item}-${index}`}>{item}</li>
                            ))}
                          </ul>
                        </Card>
                      )}
                    </Space>
                  ) : (
                    <Empty description="生成后可在此查看提纲与整稿" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                  )}
                </Card>
              </Col>
            </Row>
          </Card>
        </Space>
      ),
    },
  ];

  return (
    <ConfigProvider locale={zhCN} theme={themeTokens}>
      <AntdApp>
        <div className="py-10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
            <Card>
              <Space direction="vertical" size={16} style={{ width: '100%' }}>
                <div>
                  <Title level={3} style={{ marginBottom: 4 }}>
                    文书生成工作台
                  </Title>
                  <Text type="secondary">
                    三步完成头脑风暴、CV 生成与 PS 草稿。未登录可编辑草稿，登录后可调用生成与云端保存。
                  </Text>
                </div>
                <Steps
                  current={stepIndex}
                  onChange={(index) => setActiveStep(index === 0 ? 'brainstorm' : index === 1 ? 'cv' : 'ps')}
                  items={[
                    {
                      title: '头脑风暴',
                      description: '导入资料、结构化、亮点提炼',
                    },
                    {
                      title: 'CV 生成',
                      description: '模板选择、要点生成、镜像版本',
                    },
                    {
                      title: 'PS 生成',
                      description: '提纲确认、逐段修订、终稿导出',
                    },
                  ]}
                />
                <Alert
                  type={authState.isAuthenticated ? 'success' : 'info'}
                  showIcon
                  message={
                    authState.isAuthenticated
                      ? `已登录，可生成与云端保存文书（最近保存：${draftSavedAt ? new Date(draftSavedAt).toLocaleString() : '暂无'}）`
                      : '未登录状态下仅保存本地草稿，登录后可生成 CV / PS 并写入云端档案'
                  }
                />
              </Space>
            </Card>
            <Card>
              <Tabs
                items={tabItems}
                activeKey={activeStep}
                onChange={(key) => setActiveStep(key as ActiveStep)}
                destroyInactiveTabPane={false}
              />
            </Card>
          </div>
        </div>
      </AntdApp>
    </ConfigProvider>
  );
}

const mergeStrings = (existing: string[], incoming: string[]) => {
  return Array.from(new Set([...(existing ?? []), ...(incoming ?? [])].filter(Boolean)));
};

const mergeMajors = (existing: MajorTarget[], incoming: MajorTarget[]): MajorTarget[] => {
  if (incoming.length === 0) {
    return existing;
  }

  const merged = [...existing];
  const keyIndexMap = new Map<string, number>();

  merged.forEach((major, index) => {
    keyIndexMap.set(normalizeMajorKey(major.name), index);
  });

  incoming.forEach((major) => {
    const key = normalizeMajorKey(major.name);
    if (keyIndexMap.has(key)) {
      const index = keyIndexMap.get(key)!;
      if (!merged[index].isPrimary && major.isPrimary) {
        merged[index] = { ...merged[index], isPrimary: true };
      }
    } else {
      merged.push(major);
      keyIndexMap.set(key, merged.length - 1);
    }
  });

  if (!merged.some((major) => major.isPrimary) && merged.length > 0) {
    merged[0] = { ...merged[0], isPrimary: true };
  }

  return merged;
};

const InfoBadge = () => (
  <span
    style={{
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: 22,
      height: 22,
      borderRadius: '999px',
      background: 'rgba(79, 70, 229, 0.1)',
      color: '#4f46e5',
      fontSize: 12,
    }}
  >
    i
  </span>
);
