import { getApiBaseUrl } from '../config';

// 答案接口
interface Answer {
  question_id: number;
  score: number;
}

// 霍兰德数据接口
interface HollandData {
  title: string;
  description: string;
  instructions: {
    intro: string;
    scoring_guide: string;
    scale: Array<{
      score: number;
      label: string;
    }>;
  };
  sections: Array<{
    title: string;
    description: string;
    questions: Array<{
      id: number;
      text: string;
      type: string;
    }>;
  }>;
}

// 评估结果接口
interface HollandResult {
  holland_code: string;
  type_scores: Array<{
    type_code: string;
    type_name: string;
    score: number;
    percentage: number;
  }>;
  top_three_types: Array<{
    type_code: string;
    name: string;
    nickname: string;
    characteristics: string;
    typical_careers: string[];
  }>;
  assessment_date: string;
}

class HollandService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = getApiBaseUrl();
  }

  /**
   * 获取霍兰德问卷数据
   */
  async getHollandData(): Promise<HollandData> {
    try {
      const response = await fetch(`${this.baseUrl}/api/holland/data`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Failed to fetch Holland data:', error);
      throw new Error(error instanceof Error ? error.message : '获取问卷数据失败');
    }
  }

  /**
   * 提交霍兰德评估
   */
  async submitAssessment(answers: Answer[]): Promise<HollandResult> {
    try {
      const response = await fetch(`${this.baseUrl}/api/holland/assess`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          answers: answers
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Failed to submit Holland assessment:', error);
      throw new Error(error instanceof Error ? error.message : '提交评估失败');
    }
  }

  /**
   * 验证答案完整性
   */
  validateAnswers(answers: Answer[], totalQuestions: number): boolean {
    // 检查答案数量
    if (answers.length !== totalQuestions) {
      return false;
    }

    // 检查每个答案的有效性
    for (const answer of answers) {
      if (!Number.isInteger(answer.question_id) || answer.question_id <= 0) {
        return false;
      }
      if (!Number.isInteger(answer.score) || answer.score < 1 || answer.score > 5) {
        return false;
      }
    }

    // 检查是否有重复的问题ID
    const questionIds = answers.map(a => a.question_id);
    const uniqueQuestionIds = new Set(questionIds);
    if (questionIds.length !== uniqueQuestionIds.size) {
      return false;
    }

    return true;
  }

  /**
   * 获取类型颜色映射
   */
  getTypeColors(): Record<string, string> {
    return {
      'R': '#ff4d4f',  // 现实型 - 红色
      'I': '#1890ff',  // 研究型 - 蓝色
      'A': '#722ed1',  // 艺术型 - 紫色
      'S': '#52c41a',  // 社会型 - 绿色
      'E': '#fa8c16',  // 企业型 - 橙色
      'C': '#13c2c2'   // 常规型 - 青色
    };
  }

  /**
   * 获取类型描述
   */
  getTypeDescriptions(): Record<string, { name: string; nickname: string }> {
    return {
      'R': { name: '现实型', nickname: '操作者' },
      'I': { name: '研究型', nickname: '思考者' },
      'A': { name: '艺术型', nickname: '创造者' },
      'S': { name: '社会型', nickname: '助人者' },
      'E': { name: '企业型', nickname: '说服者' },
      'C': { name: '常规型', nickname: '组织者' }
    };
  }
}

// 导出单例实例
export const hollandService = new HollandService();
export default hollandService;
