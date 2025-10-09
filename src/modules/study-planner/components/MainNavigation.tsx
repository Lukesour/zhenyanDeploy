'use client';

import React from 'react';
import { Tabs, Card, Typography } from 'antd';
import {
  BankOutlined,
  BookOutlined,
  UserOutlined,
  ExperimentOutlined
} from '@ant-design/icons';
import UserForm from './UserForm';
import SchoolList from './SchoolList';
import MajorList from './MajorList';
import HollandAssessment from './HollandAssessment';
import { UserBackground } from '../services/api';
import './MajorComponents.css';

const { Title, Text } = Typography;

interface MainNavigationProps {
  onFormSubmit: (userBackground: UserBackground) => void;
  onSelectSchool: (schoolName: string) => void;
  onSelectMajor: (majorId: string) => void;
}

const MainNavigation: React.FC<MainNavigationProps> = ({
  onFormSubmit,
  onSelectSchool,
  onSelectMajor
}) => {
  const tabItems = [
    {
      key: 'analysis',
      label: (
        <span>
          <UserOutlined />
          留学分析
        </span>
      ),
      children: (
        <div className="space-y-6">
          <Card className="mb-6 border border-indigo-50/70 bg-white/90 backdrop-blur shadow-none">
            <Title level={3} style={{ marginBottom: 8 }}>
              留学定位与选校规划系统
            </Title>
            <Text type="secondary">
              基于您的个人背景，为您提供个性化的留学申请分析和选校建议
            </Text>
          </Card>
          <UserForm onSubmit={onFormSubmit} />
        </div>
      ),
    },
    {
      key: 'holland',
      label: (
        <span>
          <ExperimentOutlined />
          霍兰德职业兴趣评估
        </span>
      ),
      children: (
        <div className="space-y-6">
          <Card className="mb-6 border border-indigo-50/70 bg-white/90 backdrop-blur shadow-none">
            <Title level={3} style={{ marginBottom: 8 }}>
              霍兰德职业兴趣评估
            </Title>
            <Text type="secondary">
              基于著名的霍兰德职业兴趣理论，帮助您探索自己的兴趣、能力和个性，找到适合的职业方向
            </Text>
          </Card>
          <HollandAssessment />
        </div>
      ),
    },
    {
      key: 'schools',
      label: (
        <span>
          <BankOutlined />
          学校
        </span>
      ),
      children: (
        <div className="space-y-6">
          <Card className="mb-6 border border-indigo-50/70 bg-white/90 backdrop-blur shadow-none">
            <Title level={3} style={{ marginBottom: 8 }}>
              学校信息浏览
            </Title>
            <Text type="secondary">
              浏览所有学校信息，按QS排名排序，支持地区和排名筛选
            </Text>
          </Card>
          <SchoolList onSelectSchool={onSelectSchool} />
        </div>
      ),
    },
    {
      key: 'majors',
      label: (
        <span>
          <BookOutlined />
          专业
        </span>
      ),
      children: (
        <div className="space-y-6">
          <Card className="mb-6 border border-indigo-50/70 bg-white/90 backdrop-blur shadow-none">
            <Title level={3} style={{ marginBottom: 8 }}>
              专业信息浏览
            </Title>
            <Text type="secondary">
              浏览所有专业信息，了解专业详情和申请要求
            </Text>
          </Card>
          <MajorList onSelectMajor={onSelectMajor} />
        </div>
      ),
    },
  ];

  return (
    <section className="max-w-6xl mx-auto rounded-3xl border border-indigo-100/60 bg-white/80 p-6 sm:p-8 shadow-xl shadow-indigo-100/50 backdrop-blur">
      <Tabs
        defaultActiveKey="analysis"
        items={tabItems}
        size="large"
        className="planner-tabs"
        tabBarStyle={{
          marginBottom: 24,
        }}
      />
    </section>
  );
};

export default MainNavigation;
