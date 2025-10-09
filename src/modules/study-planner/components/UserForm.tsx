'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  App,
  Form,
  Input,
  Select,
  InputNumber,
  Button,
  Card,
  Row,
  Col,
  Space,
  Divider,
  Spin,
  Alert,
} from 'antd';
import { PlusOutlined, MinusCircleOutlined, SendOutlined } from '@ant-design/icons';
import apiService, { UserBackground } from '../services/api';
import dataLoaderService from '../services/DataLoaderService';
import errorHandler from '../services/ErrorHandler';
import authService from '../services/authService';


const { Option } = Select;
const { TextArea } = Input;

interface UserFormProps {
  onSubmit: (data: UserBackground) => void;
  loading?: boolean;
}

// 使用从 DataLoaderService 加载的JSON数据

const UserForm: React.FC<UserFormProps> = ({ onSubmit, loading = false }) => {
  const [form] = Form.useForm();
  const { message: messageApi } = App.useApp();
  const [isClient, setIsClient] = useState(false);
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  useEffect(() => {
    setIsClient(true);
  }, []);
  // 语言考试状态：已考试、未报考、准备考、准备再考、未报考并且不准备考
  const [languageTestStatus, setLanguageTestStatus] = useState('未报考并且不准备考');
  // GRE考试状态
  const [greTestStatus, setGreTestStatus] = useState('未报考并且不准备考');
  // GMAT考试状态
  const [gmatTestStatus, setGmatTestStatus] = useState('未报考并且不准备考');
  
  // 数据状态管理
  const [universities, setUniversities] = useState<string[]>([]);
  const [majors, setMajors] = useState<string[]>([]);
  const [countries, setCountries] = useState<string[]>([]);
  const [targetMajors, setTargetMajors] = useState<string[]>([]);
  // const [majorsByCategory] = useState<Record<string, string[]>>({});
  const [dataLoading, setDataLoading] = useState(true);
  const [dataError, setDataError] = useState<string | null>(null);



  // 数据加载逻辑
  useEffect(() => {
    const loadData = async () => {
      try {
        setDataLoading(true);
        setDataError(null);

        // 并行加载所有数据
        const [universitiesData, majorsData, countriesData, targetMajorsData] = await Promise.all([
          dataLoaderService.loadUniversities(),
          dataLoaderService.loadMajors(),
          dataLoaderService.loadCountries(),
          dataLoaderService.loadTargetMajors(),
        ]);

        setUniversities(universitiesData);
        setMajors(majorsData);
        setCountries(countriesData);
        setTargetMajors(targetMajorsData);


      } catch (error) {
        const { userMessage } = errorHandler.buildUserFacingError(error, {
          component: 'UserForm',
          action: 'initialDataLoad'
        });
        console.error('数据加载失败:', userMessage.title);
        setDataError(userMessage.description);
        messageApi.error(userMessage.title);
      } finally {
        setDataLoading(false);
      }
    };

    loadData();
  }, []);

  // 监听用户认证状态变化，自动填入个人信息
  useEffect(() => {
    if (!isClient) {
      return;
    }

    const authState = authService.getAuthState();
    if (authState.isAuthenticated && authState.user?.profile_data) {
      const profileData = authState.user.profile_data;

      // 自动填入表单数据
      const formValues: any = {};

      // 学术背景
      if (profileData.undergraduate_university) formValues.undergraduate_university = profileData.undergraduate_university;
      if (profileData.undergraduate_major) formValues.undergraduate_major = profileData.undergraduate_major;
      if (profileData.gpa) formValues.gpa = profileData.gpa;
      if (profileData.gpa_scale) formValues.gpa_scale = profileData.gpa_scale;
      if (profileData.graduation_year) formValues.graduation_year = profileData.graduation_year;
      if (profileData.application_year) formValues.application_year = profileData.application_year;

      // 语言成绩状态
      if (profileData.language_test_status) {
        setLanguageTestStatus(profileData.language_test_status);
        formValues.language_test_status = profileData.language_test_status;
      }
      if (profileData.language_test_type) formValues.language_test_type = profileData.language_test_type;
      if (profileData.language_total_score) formValues.language_total_score = profileData.language_total_score;
      if (profileData.language_reading) formValues.language_reading = profileData.language_reading;
      if (profileData.language_listening) formValues.language_listening = profileData.language_listening;
      if (profileData.language_speaking) formValues.language_speaking = profileData.language_speaking;
      if (profileData.language_writing) formValues.language_writing = profileData.language_writing;
      // 目标分数
      if (profileData.language_target_total_score) formValues.language_target_total_score = profileData.language_target_total_score;
      if (profileData.language_target_reading) formValues.language_target_reading = profileData.language_target_reading;
      if (profileData.language_target_listening) formValues.language_target_listening = profileData.language_target_listening;
      if (profileData.language_target_speaking) formValues.language_target_speaking = profileData.language_target_speaking;
      if (profileData.language_target_writing) formValues.language_target_writing = profileData.language_target_writing;
      // 语言考试时间
      if (profileData.language_expected_test_date) formValues.language_expected_test_date = profileData.language_expected_test_date;

      // GRE成绩状态
      if (profileData.gre_test_status) {
        setGreTestStatus(profileData.gre_test_status);
        formValues.gre_test_status = profileData.gre_test_status;
      }
      if (profileData.gre_total) formValues.gre_total = profileData.gre_total;
      if (profileData.gre_verbal) formValues.gre_verbal = profileData.gre_verbal;
      if (profileData.gre_quantitative) formValues.gre_quantitative = profileData.gre_quantitative;
      if (profileData.gre_writing) formValues.gre_writing = profileData.gre_writing;
      // GRE目标分数
      if (profileData.gre_target_total) formValues.gre_target_total = profileData.gre_target_total;
      if (profileData.gre_target_verbal) formValues.gre_target_verbal = profileData.gre_target_verbal;
      if (profileData.gre_target_quantitative) formValues.gre_target_quantitative = profileData.gre_target_quantitative;
      if (profileData.gre_target_writing) formValues.gre_target_writing = profileData.gre_target_writing;
      // GRE考试时间
      if (profileData.gre_expected_test_date) formValues.gre_expected_test_date = profileData.gre_expected_test_date;

      // GMAT成绩状态
      if (profileData.gmat_test_status) {
        setGmatTestStatus(profileData.gmat_test_status);
        formValues.gmat_test_status = profileData.gmat_test_status;
      }
      if (profileData.gmat_total) formValues.gmat_total = profileData.gmat_total;
      // GMAT目标分数
      if (profileData.gmat_target_total) formValues.gmat_target_total = profileData.gmat_target_total;
      // GMAT考试时间
      if (profileData.gmat_expected_test_date) formValues.gmat_expected_test_date = profileData.gmat_expected_test_date;

      // 目标信息
      if (profileData.target_countries) formValues.target_countries = profileData.target_countries;
      if (profileData.target_majors) {
        formValues.target_majors = Array.isArray(profileData.target_majors)
          ? profileData.target_majors[0]
          : profileData.target_majors;
      }
      if (profileData.target_degree_type) formValues.target_degree_type = profileData.target_degree_type;

      // 经历信息
      if (profileData.research_experiences) formValues.research_experiences = profileData.research_experiences;
      if (profileData.internship_experiences) formValues.internship_experiences = profileData.internship_experiences;
      if (profileData.other_experiences) formValues.other_experiences = profileData.other_experiences;

      // 设置表单值
      form.setFieldsValue(formValues);
      messageApi.success('已自动填入您的个人信息');
    }
  }, [form, isClient, messageApi]);

  // 当考试状态变化时，触发相关字段的重新校验
  useEffect(() => {
    form.validateFields(['language_test_status', 'language_test_type', 'language_total_score']);
  }, [languageTestStatus]);

  useEffect(() => {
    form.validateFields(['gre_test_status', 'gre_total']);
  }, [greTestStatus]);

  useEffect(() => {
    form.validateFields(['gmat_test_status', 'gmat_total']);
  }, [gmatTestStatus]);











  // 数据重试功能
  const retryDataLoad = useCallback(async () => {
    setDataError(null);
    setDataLoading(true);
    
    try {
      const [universitiesData, majorsData, countriesData, targetMajorsData] = await Promise.all([
        dataLoaderService.loadUniversities(),
        dataLoaderService.loadMajors(),
        dataLoaderService.loadCountries(),
        dataLoaderService.loadTargetMajors(),
      ]);

      setUniversities(universitiesData);
      setMajors(majorsData);
      setCountries(countriesData);
      setTargetMajors(targetMajorsData);
      
      messageApi.success('数据重新加载成功');
    } catch (error) {
      const { userMessage } = errorHandler.buildUserFacingError(error, {
        component: 'UserForm',
        action: 'retryDataLoad'
      });
      console.error('数据重新加载失败:', userMessage.title);
      setDataError(userMessage.description);
        messageApi.error(userMessage.title);
    } finally {
      setDataLoading(false);
    }
  }, []);

  const handleSubmit = async (values: any) => {
    try {
      // 🔧 添加完整的客户端验证，防止400错误
      console.log('提交前的表单数据:', values);

      // 验证必填字段 - 本科院校
      if (!values.undergraduate_university || values.undergraduate_university.trim() === '') {
        messageApi.error('请填写本科院校');
        return;
      }

      // 验证必填字段 - 本科专业
      if (!values.undergraduate_major || values.undergraduate_major.trim() === '') {
        messageApi.error('请填写本科专业');
        return;
      }

      // 验证必填字段 - 目标国家
      if (!values.target_countries || !Array.isArray(values.target_countries) || values.target_countries.length === 0) {
        messageApi.error('请选择目标国家');
        return;
      }

      // 处理目标专业方向数据 - 现在只支持单选，但转换为数组格式保持后端兼容性
      let targetMajorValue = values.target_majors;
      if (Array.isArray(targetMajorValue)) {
        targetMajorValue = targetMajorValue[0] ?? '';
      }

      if (typeof targetMajorValue !== 'string' || targetMajorValue.trim() === '') {
        messageApi.error('请选择目标专业方向');
        return;
      }

      const target_majors: string[] = [targetMajorValue.trim()];
      
      // 提交前数据完整性检查（不阻断提交，仅提示）
      if (values.undergraduate_university && universities.length > 0 && !universities.includes(values.undergraduate_university)) {
        messageApi.warning('提示：您填写的本科院校不在标准列表中，如有拼写差异请确认');
      }
      if (values.undergraduate_major && majors.length > 0 && !majors.includes(values.undergraduate_major)) {
        messageApi.warning('提示：您填写的本科专业不在标准列表中，如有拼写差异请确认');
      }

      // 处理表单数据
      const formData: UserBackground = {
        undergraduate_university: values.undergraduate_university,
        undergraduate_major: values.undergraduate_major,
        gpa: values.gpa,
        gpa_scale: values.gpa_scale,
        graduation_year: values.graduation_year,
        language_test_status: values.language_test_status,
        target_countries: values.target_countries,
        target_majors: target_majors,
        target_degree_type: values.target_degree_type,
        application_year: values.application_year,
        research_experiences: values.research_experiences || [],
        internship_experiences: values.internship_experiences || [],
        other_experiences: values.other_experiences || [],
      };

      // 添加语言成绩（必选）
      if (values.language_test_type) formData.language_test_type = values.language_test_type;
      if (values.language_total_score) formData.language_total_score = values.language_total_score;
      if (values.language_reading) formData.language_reading = values.language_reading;
      if (values.language_listening) formData.language_listening = values.language_listening;
      if (values.language_speaking) formData.language_speaking = values.language_speaking;
      if (values.language_writing) formData.language_writing = values.language_writing;
      // 目标分数
      if (values.language_target_total_score) formData.language_target_total_score = values.language_target_total_score;
      if (values.language_target_reading) formData.language_target_reading = values.language_target_reading;
      if (values.language_target_listening) formData.language_target_listening = values.language_target_listening;
      if (values.language_target_speaking) formData.language_target_speaking = values.language_target_speaking;
      if (values.language_target_writing) formData.language_target_writing = values.language_target_writing;
      // 语言考试时间
      if (values.language_expected_test_date) formData.language_expected_test_date = values.language_expected_test_date;

      // 添加GRE成绩
      if (values.gre_test_status) {
        formData.gre_test_status = values.gre_test_status;
        if (values.gre_total) formData.gre_total = values.gre_total;
        if (values.gre_verbal) formData.gre_verbal = values.gre_verbal;
        if (values.gre_quantitative) formData.gre_quantitative = values.gre_quantitative;
        if (values.gre_writing) formData.gre_writing = values.gre_writing;
        // GRE目标分数
        if (values.gre_target_total) formData.gre_target_total = values.gre_target_total;
        if (values.gre_target_verbal) formData.gre_target_verbal = values.gre_target_verbal;
        if (values.gre_target_quantitative) formData.gre_target_quantitative = values.gre_target_quantitative;
        if (values.gre_target_writing) formData.gre_target_writing = values.gre_target_writing;
        // GRE考试时间
        if (values.gre_expected_test_date) formData.gre_expected_test_date = values.gre_expected_test_date;
      }

      // 添加GMAT成绩
      if (values.gmat_test_status) {
        formData.gmat_test_status = values.gmat_test_status;
        if (values.gmat_total) formData.gmat_total = values.gmat_total;
        if (values.gmat_target_total) formData.gmat_target_total = values.gmat_target_total;
        // GMAT考试时间
        if (values.gmat_expected_test_date) formData.gmat_expected_test_date = values.gmat_expected_test_date;
      }

      // 🔧 最终验证 - 确保所有必填字段都有值
      if (!formData.undergraduate_university || formData.undergraduate_university.trim() === '') {
        messageApi.error('本科院校信息缺失，请重新填写');
        return;
      }
      if (!formData.undergraduate_major || formData.undergraduate_major.trim() === '') {
        messageApi.error('本科专业信息缺失，请重新填写');
        return;
      }
      if (!formData.target_countries || formData.target_countries.length === 0) {
        messageApi.error('目标国家信息缺失，请重新选择');
        return;
      }
      if (!formData.target_majors || formData.target_majors.length === 0) {
        messageApi.error('目标专业信息缺失，请重新选择');
        return;
      }

      console.log('✅ 表单验证通过，提交数据:', formData);

      if (authService.isAuthenticated()) {
        setIsSavingProfile(true);
        try {
          const updatedUser = await apiService.saveUserProfile(formData);
          authService.updateUserInfo(updatedUser);
          messageApi.success('个人信息已保存');
        } catch (error) {
          const { userMessage } = errorHandler.buildUserFacingError(error, {
            component: 'UserForm',
            action: 'saveProfile',
            userData: formData
          });
          messageApi.error(userMessage.title);
          console.error('保存个人信息失败:', error);
          return;
        } finally {
          setIsSavingProfile(false);
        }
      }

      onSubmit(formData);
    } catch (error) {
      messageApi.error('表单数据处理失败，请检查输入');
      console.error('Form submission error:', error);
    }
  };

  // 数据加载错误处理
  if (dataError) {
    return (
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '20px' }}>
        <Card title="数据加载错误">
          <Alert
            message="数据加载失败"
            description={`错误详情：${dataError}`}
            type="error"
            showIcon
            style={{ marginBottom: '20px' }}
          />
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <Space size="middle">
              <Button 
                type="primary" 
                onClick={retryDataLoad}
                loading={dataLoading}
              >
                重新加载数据
              </Button>
              <Button 
                onClick={() => window.location.reload()}
              >
                刷新页面
              </Button>
            </Space>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '20px' }}>
      {/* 数据加载状态提示 */}
      {dataLoading && (
        <Alert
          message="正在加载数据..."
          description="正在加载院校、专业等基础数据，请稍候..."
          type="info"
          showIcon
          style={{ marginBottom: '20px' }}
        />
      )}
      


      <Spin spinning={dataLoading} tip="正在加载数据...">
        <Card title="留学定位与选校规划 - 个人信息填写">
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          scrollToFirstError
        >
          {/* 第一部分：学术背景 */}
          <Card type="inner" title="第一部分：学术背景" style={{ marginBottom: 24 }}>
            <Row gutter={16}>
              <Col xs={24} sm={12}>
                <Form.Item
                  label="本科院校"
                  name="undergraduate_university"
                  rules={[{ required: true, message: '请输入本科院校' }]}
                >
                  <Select
                    placeholder="请输入或选择本科院校"
                    showSearch
                    filterOption={(input, option) =>
                      (option?.children as unknown as string)?.toLowerCase().includes(input.toLowerCase())
                    }
                    disabled={dataLoading}
                    loading={dataLoading}
                    notFoundContent={dataLoading ? <Spin size="small" /> : '未找到匹配的院校'}
                    allowClear
                  >
                    {universities.map(uni => (
                      <Option key={uni} value={uni}>{uni}</Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
              <Col xs={24} sm={12}>
                <Form.Item
                  label="本科专业"
                  name="undergraduate_major"
                  rules={[{ required: true, message: '请输入本科专业' }]}
                >
                  <Select
                    placeholder="请输入或选择本科专业"
                    showSearch
                    filterOption={(input, option) =>
                      (option?.children as unknown as string)?.toLowerCase().includes(input.toLowerCase())
                    }
                    disabled={dataLoading}
                    loading={dataLoading}
                    notFoundContent={dataLoading ? <Spin size="small" /> : '未找到匹配的专业'}
                    allowClear
                  >
                    {majors.map(major => (
                      <Option key={major} value={major}>{major}</Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col xs={24} sm={8}>
                <Form.Item
                  label="GPA/均分"
                  name="gpa"
                  dependencies={['gpa_scale']}
                  rules={[
                    { required: true, message: '请输入GPA或均分' },
                    {
                      validator: async (_, value) => {
                        if (value === undefined || value === null || value === '') return Promise.resolve();
                        const scale = form.getFieldValue('gpa_scale');
                        if (!scale) return Promise.resolve();
                        const num = Number(value);
                        if (Number.isNaN(num) || num < 0) return Promise.reject(new Error('GPA需为非负数'));
                        if (scale === '4.0' && num > 4.0) return Promise.reject(new Error('GPA与4.0制不匹配，最大为4.0'));
                        if (scale === '5.0' && num > 5.0) return Promise.reject(new Error('GPA与5.0制不匹配，最大为5.0'));
                        if (scale === '100' && num > 100) return Promise.reject(new Error('百分制成绩最大为100'));
                        return Promise.resolve();
                      }
                    }
                  ]}
                >
                  <InputNumber
                    min={0}
                    max={100}
                    step={0.1}
                    placeholder="如：3.8 或 88"
                    style={{ width: '100%' }}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={8}>
                <Form.Item
                  label="GPA制式"
                  name="gpa_scale"
                  rules={[{ required: true, message: '请选择GPA制式' }]}
                >
                  <Select placeholder="请选择制式">
                    <Option value="4.0">4.0制</Option>
                    <Option value="5.0">5.0制</Option>
                    <Option value="100">100分制</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col xs={24} sm={8}>
                <Form.Item
                  label="毕业年份"
                  name="graduation_year"
                  rules={[{ required: true, message: '请选择毕业年份' }]}
                >
                  <Select placeholder="请选择毕业年份">
                    {Array.from({ length: 10 }, (_, i) => {
                      const year = new Date().getFullYear() + i - 5;
                      return <Option key={year} value={year}>{year}</Option>;
                    })}
                  </Select>
                </Form.Item>
              </Col>
            </Row>
          </Card>

          {/* 第二部分：语言和标准化考试成绩 */}
          <Card type="inner" title="第二部分：语言和标准化考试成绩" style={{ marginBottom: 24 }}>
            <Form.Item
              label="语言考试成绩"
              name="language_test_status"
              rules={[{ required: true, message: '请选择语言考试状态' }]}
            >
              <Select
                placeholder="请选择语言考试状态"
                value={languageTestStatus}
                onChange={(value) => setLanguageTestStatus(value)}
              >
                <Option value="已考试">已考试</Option>
                <Option value="未报考、准备考">未报考、准备考</Option>
                <Option value="准备再考">准备再考</Option>
                <Option value="未报考并且不准备考">未报考并且不准备考</Option>
              </Select>
            </Form.Item>

            {/* 根据语言考试状态显示不同的表单字段 */}
            {languageTestStatus && languageTestStatus !== '未报考并且不准备考' && (
              <>
                <Row gutter={16}>
                  <Col xs={24} sm={6}>
                    <Form.Item
                      label="考试类型"
                      name="language_test_type"
                      rules={[{ required: true, message: '请选择语言考试类型' }]}
                    >
                      <Select placeholder="选择考试类型">
                        <Option value="TOEFL">TOEFL</Option>
                        <Option value="IELTS">IELTS</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                </Row>

                {/* 已考试状态：显示已有分数 */}
                {languageTestStatus === '已考试' && (
                  <Row gutter={16}>
                    <Col xs={24} sm={6}>
                      <Form.Item
                        label="总分"
                        name="language_total_score"
                        rules={[{ required: true, message: '请输入语言考试总分' }]}
                      >
                        <InputNumber min={0} max={120} placeholder="总分" style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col xs={24} sm={3}>
                      <Form.Item label="阅读" name="language_reading">
                        <InputNumber min={0} max={30} placeholder="阅读" style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col xs={24} sm={3}>
                      <Form.Item label="听力" name="language_listening">
                        <InputNumber min={0} max={30} placeholder="听力" style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col xs={24} sm={3}>
                      <Form.Item label="口语" name="language_speaking">
                        <InputNumber min={0} max={30} placeholder="口语" style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col xs={24} sm={3}>
                      <Form.Item label="写作" name="language_writing">
                        <InputNumber min={0} max={30} placeholder="写作" style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                  </Row>
                )}

                {/* 未报考、准备考状态：显示目标分数和预期考试时间 */}
                {languageTestStatus === '未报考、准备考' && (
                  <>
                    <Row gutter={16}>
                      <Col xs={24} sm={6}>
                        <Form.Item
                          label="目标总分"
                          name="language_target_total_score"
                          rules={[{ required: true, message: '请输入目标总分' }]}
                        >
                          <InputNumber min={0} max={120} placeholder="目标总分" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                      <Col xs={24} sm={3}>
                        <Form.Item label="目标阅读" name="language_target_reading">
                          <InputNumber min={0} max={30} placeholder="目标阅读" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                      <Col xs={24} sm={3}>
                        <Form.Item label="目标听力" name="language_target_listening">
                          <InputNumber min={0} max={30} placeholder="目标听力" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                      <Col xs={24} sm={3}>
                        <Form.Item label="目标口语" name="language_target_speaking">
                          <InputNumber min={0} max={30} placeholder="目标口语" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                      <Col xs={24} sm={3}>
                        <Form.Item label="目标写作" name="language_target_writing">
                          <InputNumber min={0} max={30} placeholder="目标写作" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                    </Row>
                    <Row gutter={16}>
                      <Col xs={24} sm={6}>
                        <Form.Item
                          label="预期考试时间"
                          name="language_expected_test_date"
                          rules={[{ required: true, message: '请选择预期考试时间' }]}
                        >
                          <Input type="date" placeholder="选择预期考试时间" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                    </Row>
                  </>
                )}

                {/* 准备再考状态：显示已有分数和目标分数 */}
                {languageTestStatus === '准备再考' && (
                  <>
                    <div style={{ marginBottom: 16, fontWeight: 'bold' }}>已有分数：</div>
                    <Row gutter={16}>
                      <Col xs={24} sm={6}>
                        <Form.Item
                          label="总分"
                          name="language_total_score"
                          rules={[{ required: true, message: '请输入当前总分' }]}
                        >
                          <InputNumber min={0} max={120} placeholder="当前总分" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                      <Col xs={24} sm={3}>
                        <Form.Item label="阅读" name="language_reading">
                          <InputNumber min={0} max={30} placeholder="当前阅读" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                      <Col xs={24} sm={3}>
                        <Form.Item label="听力" name="language_listening">
                          <InputNumber min={0} max={30} placeholder="当前听力" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                      <Col xs={24} sm={3}>
                        <Form.Item label="口语" name="language_speaking">
                          <InputNumber min={0} max={30} placeholder="当前口语" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                      <Col xs={24} sm={3}>
                        <Form.Item label="写作" name="language_writing">
                          <InputNumber min={0} max={30} placeholder="当前写作" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                    </Row>

                    <div style={{ marginBottom: 16, marginTop: 24, fontWeight: 'bold' }}>目标分数：</div>
                    <Row gutter={16}>
                      <Col xs={24} sm={6}>
                        <Form.Item
                          label="目标总分"
                          name="language_target_total_score"
                          rules={[{ required: true, message: '请输入目标总分' }]}
                        >
                          <InputNumber min={0} max={120} placeholder="目标总分" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                      <Col xs={24} sm={3}>
                        <Form.Item label="目标阅读" name="language_target_reading">
                          <InputNumber min={0} max={30} placeholder="目标阅读" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                      <Col xs={24} sm={3}>
                        <Form.Item label="目标听力" name="language_target_listening">
                          <InputNumber min={0} max={30} placeholder="目标听力" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                      <Col xs={24} sm={3}>
                        <Form.Item label="目标口语" name="language_target_speaking">
                          <InputNumber min={0} max={30} placeholder="目标口语" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                      <Col xs={24} sm={3}>
                        <Form.Item label="目标写作" name="language_target_writing">
                          <InputNumber min={0} max={30} placeholder="目标写作" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                    </Row>

                    <div style={{ marginBottom: 16, marginTop: 24, fontWeight: 'bold' }}>考试时间：</div>
                    <Row gutter={16}>
                      <Col xs={24} sm={6}>
                        <Form.Item
                          label="预期考试时间"
                          name="language_expected_test_date"
                          rules={[{ required: true, message: '请选择预期考试时间' }]}
                        >
                          <Input type="date" placeholder="选择预期考试时间" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                    </Row>
                  </>
                )}
              </>
            )}

            <Row gutter={16}>
              <Col xs={24} sm={12}>
                <Form.Item
                  label="GRE成绩"
                  name="gre_test_status"
                >
                  <Select
                    placeholder="请选择GRE考试状态"
                    value={greTestStatus}
                    onChange={(value) => setGreTestStatus(value)}
                    allowClear
                  >
                    <Option value="已考试">已考试</Option>
                    <Option value="未报考、准备考">未报考、准备考</Option>
                    <Option value="准备再考">准备再考</Option>
                    <Option value="未报考并且不准备考">未报考并且不准备考</Option>
                  </Select>
                </Form.Item>

                {/* GRE已考试状态 */}
                {greTestStatus === '已考试' && (
                  <Row gutter={8}>
                    <Col span={12}>
                      <Form.Item
                        label="总分"
                        name="gre_total"
                        rules={[{ required: true, message: '请输入GRE总分' }]}
                      >
                        <InputNumber min={260} max={340} placeholder="总分" style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item label="写作" name="gre_writing">
                        <InputNumber min={0} max={6} step={0.5} placeholder="写作" style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                  </Row>
                )}

                {/* GRE未报考、准备考状态 */}
                {greTestStatus === '未报考、准备考' && (
                  <>
                    <Row gutter={8}>
                      <Col span={12}>
                        <Form.Item
                          label="目标总分"
                          name="gre_target_total"
                          rules={[{ required: true, message: '请输入GRE目标总分' }]}
                        >
                          <InputNumber min={260} max={340} placeholder="目标总分" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item label="目标写作" name="gre_target_writing">
                          <InputNumber min={0} max={6} step={0.5} placeholder="目标写作" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                    </Row>
                    <Row gutter={8}>
                      <Col span={12}>
                        <Form.Item
                          label="预期考试时间"
                          name="gre_expected_test_date"
                          rules={[{ required: true, message: '请选择GRE预期考试时间' }]}
                        >
                          <Input type="date" placeholder="选择预期考试时间" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                    </Row>
                  </>
                )}

                {/* GRE准备再考状态 */}
                {greTestStatus === '准备再考' && (
                  <>
                    <div style={{ marginBottom: 8, fontWeight: 'bold', fontSize: '12px' }}>已有分数：</div>
                    <Row gutter={8}>
                      <Col span={12}>
                        <Form.Item
                          label="总分"
                          name="gre_total"
                          rules={[{ required: true, message: '请输入当前GRE总分' }]}
                        >
                          <InputNumber min={260} max={340} placeholder="当前总分" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item label="写作" name="gre_writing">
                          <InputNumber min={0} max={6} step={0.5} placeholder="当前写作" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                    </Row>
                    <div style={{ marginBottom: 8, marginTop: 16, fontWeight: 'bold', fontSize: '12px' }}>目标分数：</div>
                    <Row gutter={8}>
                      <Col span={12}>
                        <Form.Item
                          label="目标总分"
                          name="gre_target_total"
                          rules={[{ required: true, message: '请输入GRE目标总分' }]}
                        >
                          <InputNumber min={260} max={340} placeholder="目标总分" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item label="目标写作" name="gre_target_writing">
                          <InputNumber min={0} max={6} step={0.5} placeholder="目标写作" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                    </Row>
                    <div style={{ marginBottom: 8, marginTop: 16, fontWeight: 'bold', fontSize: '12px' }}>考试时间：</div>
                    <Row gutter={8}>
                      <Col span={12}>
                        <Form.Item
                          label="预期考试时间"
                          name="gre_expected_test_date"
                          rules={[{ required: true, message: '请选择GRE预期考试时间' }]}
                        >
                          <Input type="date" placeholder="选择预期考试时间" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                    </Row>
                  </>
                )}
              </Col>
              <Col xs={24} sm={12}>
                <Form.Item
                  label="GMAT成绩"
                  name="gmat_test_status"
                >
                  <Select
                    placeholder="请选择GMAT考试状态"
                    value={gmatTestStatus}
                    onChange={(value) => setGmatTestStatus(value)}
                    allowClear
                  >
                    <Option value="已考试">已考试</Option>
                    <Option value="未报考、准备考">未报考、准备考</Option>
                    <Option value="准备再考">准备再考</Option>
                    <Option value="未报考并且不准备考">未报考并且不准备考</Option>
                  </Select>
                </Form.Item>

                {/* GMAT已考试状态 */}
                {gmatTestStatus === '已考试' && (
                  <Form.Item
                    label="总分"
                    name="gmat_total"
                    rules={[{ required: true, message: '请输入GMAT总分' }]}
                  >
                    <InputNumber min={200} max={800} placeholder="总分" style={{ width: '100%' }} />
                  </Form.Item>
                )}

                {/* GMAT未报考、准备考状态 */}
                {gmatTestStatus === '未报考、准备考' && (
                  <>
                    <Form.Item
                      label="目标总分"
                      name="gmat_target_total"
                      rules={[{ required: true, message: '请输入GMAT目标总分' }]}
                    >
                      <InputNumber min={200} max={800} placeholder="目标总分" style={{ width: '100%' }} />
                    </Form.Item>
                    <Form.Item
                      label="预期考试时间"
                      name="gmat_expected_test_date"
                      rules={[{ required: true, message: '请选择GMAT预期考试时间' }]}
                    >
                      <Input type="date" placeholder="选择预期考试时间" style={{ width: '100%' }} />
                    </Form.Item>
                  </>
                )}

                {/* GMAT准备再考状态 */}
                {gmatTestStatus === '准备再考' && (
                  <>
                    <div style={{ marginBottom: 8, fontWeight: 'bold', fontSize: '12px' }}>已有分数：</div>
                    <Form.Item
                      label="总分"
                      name="gmat_total"
                      rules={[{ required: true, message: '请输入当前GMAT总分' }]}
                    >
                      <InputNumber min={200} max={800} placeholder="当前总分" style={{ width: '100%' }} />
                    </Form.Item>
                    <div style={{ marginBottom: 8, marginTop: 16, fontWeight: 'bold', fontSize: '12px' }}>目标分数：</div>
                    <Form.Item
                      label="目标总分"
                      name="gmat_target_total"
                      rules={[{ required: true, message: '请输入GMAT目标总分' }]}
                    >
                      <InputNumber min={200} max={800} placeholder="目标总分" style={{ width: '100%' }} />
                    </Form.Item>
                    <div style={{ marginBottom: 8, marginTop: 16, fontWeight: 'bold', fontSize: '12px' }}>考试时间：</div>
                    <Form.Item
                      label="预期考试时间"
                      name="gmat_expected_test_date"
                      rules={[{ required: true, message: '请选择GMAT预期考试时间' }]}
                    >
                      <Input type="date" placeholder="选择预期考试时间" style={{ width: '100%' }} />
                    </Form.Item>
                  </>
                )}
              </Col>
            </Row>
          </Card>

          {/* 第三部分：申请意向 */}
          <Card type="inner" title="第三部分：申请意向" style={{ marginBottom: 24 }}>
            <Row gutter={16}>
              <Col xs={24} sm={12}>
                <Form.Item
                  label="目标国家/地区 (可多选)"
                  name="target_countries"
                  rules={[{ required: true, message: '请选择目标国家/地区' }]}
                >
                  <Select
                    mode="multiple"
                    placeholder="请选择目标国家/地区"
                    options={countries.map(country => ({ label: country, value: country }))}
                    disabled={dataLoading}
                    showSearch
                    filterOption={(input, option) =>
                      (option?.label as string)?.toLowerCase().indexOf(input.toLowerCase()) !== -1
                    }
                    allowClear
                    maxTagCount="responsive"
                    notFoundContent={dataLoading ? <Spin size="small" /> : '未找到匹配的国家/地区'}
                    loading={dataLoading}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12}>
                <Form.Item
                  label="目标专业方向"
                  name="target_majors"
                  rules={[{ required: true, message: '请选择目标专业方向' }]}
                >
                  <Select
                    placeholder="请选择目标专业方向"
                    showSearch
                    filterOption={(input, option) =>
                      (option?.label as string)?.toLowerCase().indexOf(input.toLowerCase()) !== -1
                    }
                    options={targetMajors.map(major => ({
                      label: major,
                      value: major
                    }))}
                    disabled={dataLoading}
                    allowClear
                    notFoundContent={dataLoading ? <Spin size="small" /> : '未找到匹配的专业方向'}
                    loading={dataLoading}
                  />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col xs={24} sm={12}>
                <Form.Item
                  label="目标学位类型"
                  name="target_degree_type"
                  rules={[{ required: true, message: '请选择目标学位类型' }]}
                >
                  <Select placeholder="请选择学位类型">
                    <Option value="Master">硕士 (Master)</Option>
                    <Option value="PhD">博士 (PhD)</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col xs={24} sm={12}>
                <Form.Item
                  label="申请年份"
                  name="application_year"
                  rules={[{ required: true, message: '请选择申请年份' }]}
                >
                  <Select placeholder="请选择申请年份">
                    {Array.from({ length: 6 }, (_, i) => {
                      const year = new Date().getFullYear() + i;
                      return <Option key={year} value={year}>{year}</Option>;
                    })}
                  </Select>
                </Form.Item>
              </Col>
            </Row>
          </Card>

          {/* 第四部分：实践背景 */}
          <Card type="inner" title="第四部分：实践背景（选填）" style={{ marginBottom: 24 }}>
            {/* 科研经历 */}
            <Form.Item label="科研经历">
              <Form.List name="research_experiences">
                {(fields, { add, remove }) => (
                  <>
                    {fields.map(({ key, name, ...restField }) => (
                      <Card key={key} size="small" style={{ marginBottom: 8 }}>
                        <Row gutter={16}>
                          <Col xs={24} sm={8}>
                            <Form.Item
                              {...restField}
                              name={[name, 'name']}
                              label="项目名称"
                            >
                              <Input placeholder="项目名称" />
                            </Form.Item>
                          </Col>
                          <Col xs={24} sm={8}>
                            <Form.Item
                              {...restField}
                              name={[name, 'role']}
                              label="担任角色"
                            >
                              <Input placeholder="如：核心成员、负责人" />
                            </Form.Item>
                          </Col>
                          <Col xs={24} sm={6}>
                            <Form.Item
                              {...restField}
                              name={[name, 'description']}
                              label="项目描述"
                            >
                              <TextArea rows={2} placeholder="简要描述项目内容和成果" />
                            </Form.Item>
                          </Col>
                          <Col xs={24} sm={2}>
                            <MinusCircleOutlined onClick={() => remove(name)} />
                          </Col>
                        </Row>
                      </Card>
                    ))}
                    <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                      添加科研经历
                    </Button>
                  </>
                )}
              </Form.List>
            </Form.Item>

            <Divider />

            {/* 实习经历 */}
            <Form.Item label="实习/工作经历">
              <Form.List name="internship_experiences">
                {(fields, { add, remove }) => (
                  <>
                    {fields.map(({ key, name, ...restField }) => (
                      <Card key={key} size="small" style={{ marginBottom: 8 }}>
                        <Row gutter={16}>
                          <Col xs={24} sm={8}>
                            <Form.Item
                              {...restField}
                              name={[name, 'company']}
                              label="公司名称"
                            >
                              <Input placeholder="公司名称" />
                            </Form.Item>
                          </Col>
                          <Col xs={24} sm={8}>
                            <Form.Item
                              {...restField}
                              name={[name, 'position']}
                              label="职位"
                            >
                              <Input placeholder="实习/工作职位" />
                            </Form.Item>
                          </Col>
                          <Col xs={24} sm={6}>
                            <Form.Item
                              {...restField}
                              name={[name, 'description']}
                              label="工作描述"
                            >
                              <TextArea rows={2} placeholder="简要描述工作内容和成果" />
                            </Form.Item>
                          </Col>
                          <Col xs={24} sm={2}>
                            <MinusCircleOutlined onClick={() => remove(name)} />
                          </Col>
                        </Row>
                      </Card>
                    ))}
                    <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                      添加实习/工作经历
                    </Button>
                  </>
                )}
              </Form.List>
            </Form.Item>

            <Divider />

            {/* 其他经历 */}
            <Form.Item label="其他经历（竞赛、活动等）">
              <Form.List name="other_experiences">
                {(fields, { add, remove }) => (
                  <>
                    {fields.map(({ key, name, ...restField }) => (
                      <Card key={key} size="small" style={{ marginBottom: 8 }}>
                        <Row gutter={16}>
                          <Col xs={24} sm={10}>
                            <Form.Item
                              {...restField}
                              name={[name, 'name']}
                              label="活动名称"
                            >
                              <Input placeholder="竞赛、活动名称" />
                            </Form.Item>
                          </Col>
                          <Col xs={24} sm={12}>
                            <Form.Item
                              {...restField}
                              name={[name, 'description']}
                              label="描述"
                            >
                              <TextArea rows={2} placeholder="简要描述活动内容和收获" />
                            </Form.Item>
                          </Col>
                          <Col xs={24} sm={2}>
                            <MinusCircleOutlined onClick={() => remove(name)} />
                          </Col>
                        </Row>
                      </Card>
                    ))}
                    <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                      添加其他经历
                    </Button>
                  </>
                )}
              </Form.List>
            </Form.Item>
          </Card>

          {/* 提交按钮 */}
          <Form.Item>
            <Space size="large" style={{ width: '100%', justifyContent: 'center' }}>
              <Button
                type="primary"
                htmlType="submit"
                size="large"
                icon={<SendOutlined />}
                loading={loading || dataLoading || isSavingProfile}
                disabled={loading || dataLoading || isSavingProfile}
              >
                {loading ? '正在分析中...' : '完成并开始分析'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
      </Spin>
    </div>
  );
};

export default UserForm;
