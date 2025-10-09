'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  Descriptions,
  Tag,
  Button,
  Spin,
  Alert,
  Typography,
  Row,
  Col,
  Space,
  List
} from 'antd';
import {
  ArrowLeftOutlined,
  GlobalOutlined,
  ClockCircleOutlined,
  DollarOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons';
import majorDataService, { MajorData } from '../services/majorDataService';
import './MajorComponents.css';

const { Title, Text, Paragraph } = Typography;

interface MajorDetailProps {
  majorId: string;
  onBack: () => void;
}

const MajorDetail: React.FC<MajorDetailProps> = ({ majorId, onBack }) => {
  const [major, setMajor] = useState<MajorData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadMajorDetail();
  }, [majorId]);

  const loadMajorDetail = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const majorData = await majorDataService.getMajorById(majorId);
      if (!majorData) {
        setError('未找到该专业信息');
        return;
      }
      
      setMajor(majorData);
    } catch (err) {
      console.error('Error loading major detail:', err);
      setError('加载专业详情失败');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>加载专业详情中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="加载失败"
          description={error}
          type="error"
          showIcon
          action={
            <Space>
              <Button size="small" onClick={loadMajorDetail}>
                重试
              </Button>
              <Button size="small" onClick={onBack}>
                返回
              </Button>
            </Space>
          }
        />
      </div>
    );
  }

  if (!major) {
    return null;
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* 返回按钮 */}
      <Button 
        icon={<ArrowLeftOutlined />} 
        onClick={onBack}
        style={{ marginBottom: '16px' }}
      >
        返回
      </Button>

      {/* 专业标题 */}
      <Card style={{ marginBottom: '24px' }}>
        <Row gutter={[24, 16]}>
          <Col span={24}>
            <Title level={2} style={{ margin: 0, color: '#1890ff' }}>
              {major.major_name_chinese}
            </Title>
            <Text type="secondary" style={{ fontSize: '16px' }}>
              {major.major_name_english}
            </Text>
          </Col>
          <Col span={24}>
            <Space size="middle">
              <Tag color="blue" icon={<GlobalOutlined />}>
                {major.school_name}
              </Tag>
              <Tag color="green">
                QS 2026: {major.qs_2026 || (major.qs_2026 === null && major.qs_2025 === null ? '300+' : '未排名')}
              </Tag>
              <Tag color="orange">
                {major.major_direction}
              </Tag>
              <Tag color="cyan">
                {major.location}
              </Tag>
              {major.project_category && (
                <Tag color="purple">
                  {major.project_category}
                </Tag>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 基本信息 */}
      <Card title="基本信息" style={{ marginBottom: '24px' }}>
        <Descriptions column={2} bordered>
          <Descriptions.Item label="专业ID" span={1}>
            {major.major_id}
          </Descriptions.Item>
          <Descriptions.Item label="专业方向" span={1}>
            {major.major_direction || '未指定'}
          </Descriptions.Item>
          <Descriptions.Item label="入学时间" span={1}>
            <Space>
              <ClockCircleOutlined />
              {major.admission_time || '未指定'}
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="项目时长" span={1}>
            {major.project_duration || '未指定'}
          </Descriptions.Item>
          <Descriptions.Item label="学费" span={2}>
            <Space>
              <DollarOutlined />
              {major.tuition || '未指定'}
            </Space>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 项目介绍 */}
      {major.project_introduction && (
        <Card title="项目介绍" style={{ marginBottom: '24px' }}>
          <Paragraph>
            {major.project_introduction}
          </Paragraph>
        </Card>
      )}

      {/* 申请要求 */}
      {major.application_requirements && (
        <Card title="申请要求" style={{ marginBottom: '24px' }}>
          <Paragraph>
            {major.application_requirements}
          </Paragraph>
        </Card>
      )}

      {/* 语言要求 */}
      <Card title="语言要求" style={{ marginBottom: '24px' }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Card size="small" title="TOEFL">
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  {major.language_requirements.toefl.accepted ? (
                    <Tag color="green" icon={<CheckCircleOutlined />}>接受</Tag>
                  ) : (
                    <Tag color="red" icon={<CloseCircleOutlined />}>不接受</Tag>
                  )}
                </div>
                {major.language_requirements.toefl.total_score && (
                  <Text>总分要求: {major.language_requirements.toefl.total_score}</Text>
                )}
                {major.language_requirements.toefl.sub_scores && (
                  <Text>单项要求: {major.language_requirements.toefl.sub_scores}</Text>
                )}
              </Space>
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card size="small" title="IELTS">
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  {major.language_requirements.ielts.accepted ? (
                    <Tag color="green" icon={<CheckCircleOutlined />}>接受</Tag>
                  ) : (
                    <Tag color="red" icon={<CloseCircleOutlined />}>不接受</Tag>
                  )}
                </div>
                {major.language_requirements.ielts.total_score && (
                  <Text>总分要求: {major.language_requirements.ielts.total_score}</Text>
                )}
                {major.language_requirements.ielts.sub_scores && (
                  <Text>单项要求: {major.language_requirements.ielts.sub_scores}</Text>
                )}
              </Space>
            </Card>
          </Col>
        </Row>
      </Card>

      {/* 考试要求 */}
      <Card title="标准化考试要求" style={{ marginBottom: '24px' }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Space>
              <Text strong>GRE:</Text>
              {major.gre_required ? (
                <Tag color="orange">必需</Tag>
              ) : (
                <Tag color="default">不需要</Tag>
              )}
            </Space>
          </Col>
          <Col xs={24} md={12}>
            <Space>
              <Text strong>GMAT:</Text>
              {major.gmat_required ? (
                <Tag color="orange">必需</Tag>
              ) : (
                <Tag color="default">不需要</Tag>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 申请轮次 */}
      {major.application_rounds && major.application_rounds.length > 0 && (
        <Card title="申请轮次" style={{ marginBottom: '24px' }}>
          <List
            dataSource={major.application_rounds}
            renderItem={(round, index) => (
              <List.Item>
                <Space>
                  <Tag color="blue">第{round.round}轮</Tag>
                  <Text>{round.timeline}</Text>
                </Space>
              </List.Item>
            )}
          />
        </Card>
      )}

      {/* 课程设置 */}
      {major.curriculum && major.curriculum.length > 0 && (
        <Card title={`课程设置 (${major.curriculum_count}门)`} style={{ marginBottom: '24px' }}>
          <List
            dataSource={major.curriculum}
            renderItem={(course, index) => (
              <List.Item>
                <Space direction="vertical" style={{ width: '100%' }}>
                  {course.chinese_name && (
                    <Text>{course.chinese_name}</Text>
                  )}
                  {course.english_name && (
                    <Text type="secondary" style={{ fontStyle: 'italic' }}>
                      {course.english_name}
                    </Text>
                  )}
                </Space>
              </List.Item>
            )}
          />
        </Card>
      )}
    </div>
  );
};

export default MajorDetail;
