'use client';

import { useState, useCallback, useMemo } from 'react';
import { UserBackground } from '../services/api';

// 表单验证错误类型
export interface FormFieldError {
  field: string;
  message: string;
}

// 表单状态接口
export interface FormState {
  // 表单数据
  data: Partial<UserBackground>;
  
  // 验证状态
  errors: FormFieldError[];
  isValid: boolean;
  touchedFields: Set<string>;
  
  // 提交状态
  isSubmitting: boolean;
  hasSubmitted: boolean;
  
  // 附加状态
  hasLanguageScore: boolean;
  hasGRE: boolean;
  hasGMAT: boolean;
}

// 表单操作接口
export interface FormActions {
  // 数据操作
  updateField: (field: string, value: any) => void;
  updateFields: (fields: Partial<UserBackground>) => void;
  resetForm: () => void;
  
  // 验证操作
  validateField: (field: string) => boolean;
  validateForm: () => boolean;
  clearError: (field: string) => void;
  clearAllErrors: () => void;
  
  // 提交操作
  setSubmitting: (submitting: boolean) => void;
  markAsSubmitted: () => void;
  
  // 附加状态操作
  setHasLanguageScore: (has: boolean) => void;
  setHasGRE: (has: boolean) => void;
  setHasGMAT: (has: boolean) => void;
  
  // 字段操作
  markFieldAsTouched: (field: string) => void;
  isFieldTouched: (field: string) => boolean;
}

// 验证规则类型
interface ValidationRule {
  required: boolean;
  message: string;
  min?: number;
  max?: number;
  minLength?: number;
  minItems?: number;
  requiredIf?: string;
}

// 表单验证规则
const VALIDATION_RULES: Record<string, ValidationRule> = {
  undergraduate_university: {
    required: true,
    minLength: 2,
    message: '请输入本科院校'
  },
  undergraduate_major: {
    required: true,
    minLength: 2,
    message: '请输入本科专业'
  },
  gpa: {
    required: true,
    min: 0,
    max: 4.0,
    message: 'GPA必须在0-4.0之间'
  },
  gpa_scale: {
    required: true,
    message: '请选择GPA制度'
  },
  graduation_year: {
    required: true,
    min: 1990,
    max: new Date().getFullYear() + 10,
    message: '请输入正确的毕业年份'
  },
  target_countries: {
    required: true,
    minItems: 1,
    message: '请至少选择一个目标国家'
  },
  target_majors: {
    required: true,
    minItems: 1,
    message: '请至少选择一个目标专业'
  },
  target_degree_type: {
    required: true,
    message: '请选择学位类型'
  },
  // 语言成绩验证（必选）
  language_test_status: {
    required: true,
    message: '请选择语言考试状态'
  },
  language_test_type: {
    required: true,
    message: '请选择语言考试类型'
  },
  language_total_score: {
    required: false,
    requiredIf: 'languageTestStatus === "已考试" || languageTestStatus === "准备再考"',
    min: 0,
    message: '请输入语言考试总分'
  },
  language_target_total_score: {
    required: false,
    requiredIf: 'languageTestStatus === "未报考" || languageTestStatus === "准备再考"',
    min: 0,
    message: '请输入目标总分'
  },
  // GRE验证（条件性）
  gre_test_status: {
    required: false,
    message: '请选择GRE考试状态'
  },
  gre_total: {
    required: false,
    requiredIf: 'greTestStatus === "已考试" || greTestStatus === "准备再考"',
    min: 260,
    max: 340,
    message: 'GRE总分必须在260-340之间'
  },
  gre_target_total: {
    required: false,
    requiredIf: 'greTestStatus === "未报考" || greTestStatus === "准备再考"',
    min: 260,
    max: 340,
    message: 'GRE目标总分必须在260-340之间'
  },
  // GMAT验证（条件性）
  gmat_test_status: {
    required: false,
    message: '请选择GMAT考试状态'
  },
  gmat_total: {
    required: false,
    requiredIf: 'gmatTestStatus === "已考试" || gmatTestStatus === "准备再考"',
    min: 200,
    max: 800,
    message: 'GMAT总分必须在200-800之间'
  },
  gmat_target_total: {
    required: false,
    requiredIf: 'gmatTestStatus === "未报考" || gmatTestStatus === "准备再考"',
    min: 200,
    max: 800,
    message: 'GMAT目标总分必须在200-800之间'
  }
};

// 初始表单状态
const INITIAL_STATE: FormState = {
  data: {
    target_countries: [],
    target_majors: [],
    research_experiences: [],
    internship_experiences: [],
    other_experiences: []
  },
  errors: [],
  isValid: false,
  touchedFields: new Set(),
  isSubmitting: false,
  hasSubmitted: false,
  hasLanguageScore: false,
  hasGRE: false,
  hasGMAT: false
};

/**
 * 表单状态管理Hook
 * 基于Linus原则：简洁、清晰、无特殊情况
 */
export const useFormState = (): [FormState, FormActions] => {
  const [state, setState] = useState<FormState>(INITIAL_STATE);

  // 验证单个字段（使用函数式更新避免stale state问题）
  const validateField = useCallback((field: string): boolean => {
    const rule = VALIDATION_RULES[field as keyof typeof VALIDATION_RULES];
    if (!rule) return true;

    // 直接从当前state获取值进行验证
    const value = state.data[field as keyof UserBackground];
    const errors: FormFieldError[] = [];

    // 必填验证
    if (rule.required && (!value || (Array.isArray(value) && value.length === 0))) {
      errors.push({ field, message: rule.message });
    }

    // 条件必填验证
    if (rule.requiredIf && !rule.required) {
      const condition = state[rule.requiredIf as keyof FormState];
      if (condition && (!value || (Array.isArray(value) && value.length === 0))) {
        errors.push({ field, message: rule.message });
      }
    }

    // 数值范围验证
    if (typeof value === 'number') {
      if (rule.min !== undefined && value < rule.min) {
        errors.push({ field, message: rule.message });
      }
      if (rule.max !== undefined && value > rule.max) {
        errors.push({ field, message: rule.message });
      }
    }

    // 字符串长度验证
    if (typeof value === 'string') {
      if (rule.minLength && value.length < rule.minLength) {
        errors.push({ field, message: rule.message });
      }
    }

    // 数组长度验证
    if (Array.isArray(value)) {
      if (rule.minItems && value.length < rule.minItems) {
        errors.push({ field, message: rule.message });
      }
    }

    // 更新错误状态
    setState(prev => ({
      ...prev,
      errors: [
        ...prev.errors.filter(e => e.field !== field),
        ...errors
      ]
    }));

    return errors.length === 0;
  }, [state]);

  // 验证整个表单
  const validateForm = useCallback((): boolean => {
    const fieldsToValidate = Object.keys(VALIDATION_RULES);
    let isValid = true;
    const allErrors: FormFieldError[] = [];

    fieldsToValidate.forEach(field => {
      const rule = VALIDATION_RULES[field as keyof typeof VALIDATION_RULES];
      if (!rule) return;

      const value = state.data[field as keyof UserBackground];
      const errors: FormFieldError[] = [];

      // 必填验证
      if (rule.required && (!value || (Array.isArray(value) && value.length === 0))) {
        errors.push({ field, message: rule.message });
      }

      // 条件必填验证
      if (rule.requiredIf && !rule.required) {
        const condition = state[rule.requiredIf as keyof FormState];
        if (condition && (!value || (Array.isArray(value) && value.length === 0))) {
          errors.push({ field, message: rule.message });
        }
      }

      // 数值范围验证
      if (typeof value === 'number') {
        if (rule.min !== undefined && value < rule.min) {
          errors.push({ field, message: rule.message });
        }
        if (rule.max !== undefined && value > rule.max) {
          errors.push({ field, message: rule.message });
        }
      }

      // 字符串长度验证
      if (typeof value === 'string') {
        if (rule.minLength && value.length < rule.minLength) {
          errors.push({ field, message: rule.message });
        }
      }

      // 数组长度验证
      if (Array.isArray(value)) {
        if (rule.minItems && value.length < rule.minItems) {
          errors.push({ field, message: rule.message });
        }
      }

      if (errors.length > 0) {
        allErrors.push(...errors);
        isValid = false;
      }
    });

    setState(prev => ({ ...prev, errors: allErrors, isValid }));
    return isValid;
  }, [state]);

  // 更新单个字段
  const updateField = useCallback((field: string, value: any) => {
    setState(prev => ({
      ...prev,
      data: { ...prev.data, [field]: value },
      touchedFields: new Set(Array.from(prev.touchedFields).concat(field))
    }));
  }, []);

  // 更新多个字段
  const updateFields = useCallback((fields: Partial<UserBackground>) => {
    setState(prev => ({
      ...prev,
      data: { ...prev.data, ...fields },
      touchedFields: new Set(Array.from(prev.touchedFields).concat(Object.keys(fields)))
    }));
  }, []);

  // 重置表单
  const resetForm = useCallback(() => {
    setState(INITIAL_STATE);
  }, []);

  // 清除字段错误
  const clearError = useCallback((field: string) => {
    setState(prev => ({
      ...prev,
      errors: prev.errors.filter(e => e.field !== field)
    }));
  }, []);

  // 清除所有错误
  const clearAllErrors = useCallback(() => {
    setState(prev => ({ ...prev, errors: [] }));
  }, []);

  // 设置提交状态
  const setSubmitting = useCallback((submitting: boolean) => {
    setState(prev => ({ ...prev, isSubmitting: submitting }));
  }, []);

  // 标记为已提交
  const markAsSubmitted = useCallback(() => {
    setState(prev => ({ ...prev, hasSubmitted: true }));
  }, []);

  // 设置语言成绩状态
  const setHasLanguageScore = useCallback((has: boolean) => {
    setState(prev => ({ ...prev, hasLanguageScore: has }));
  }, []);

  // 设置GRE状态
  const setHasGRE = useCallback((has: boolean) => {
    setState(prev => ({ ...prev, hasGRE: has }));
  }, []);

  // 设置GMAT状态
  const setHasGMAT = useCallback((has: boolean) => {
    setState(prev => ({ ...prev, hasGMAT: has }));
  }, []);

  // 标记字段为已触摸
  const markFieldAsTouched = useCallback((field: string) => {
    setState(prev => ({
      ...prev,
      touchedFields: new Set(Array.from(prev.touchedFields).concat(field))
    }));
  }, []);

  // 检查字段是否已触摸
  const isFieldTouched = useCallback((field: string): boolean => {
    return state.touchedFields.has(field);
  }, [state.touchedFields]);

  // Actions对象
  const actions = useMemo<FormActions>(() => ({
    updateField,
    updateFields,
    resetForm,
    validateField,
    validateForm,
    clearError,
    clearAllErrors,
    setSubmitting,
    markAsSubmitted,
    setHasLanguageScore,
    setHasGRE,
    setHasGMAT,
    markFieldAsTouched,
    isFieldTouched
  }), [
    updateField,
    updateFields,
    resetForm,
    validateField,
    validateForm,
    clearError,
    clearAllErrors,
    setSubmitting,
    markAsSubmitted,
    setHasLanguageScore,
    setHasGRE,
    setHasGMAT,
    markFieldAsTouched,
    isFieldTouched
  ]);

  return [state, actions];
};

export default useFormState;
