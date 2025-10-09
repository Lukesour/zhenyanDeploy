'use client';

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  List, 
  Input, 
  Select, 
  Button, 
  Tag, 
  Space, 
  Spin, 
  Alert, 
  Typography,
  Row,
  Col,
  Statistic,
  Breadcrumb
} from 'antd';
import {
  SearchOutlined,
  BankOutlined,
  FilterOutlined,
  ClearOutlined,
  ArrowLeftOutlined,
  HomeOutlined
} from '@ant-design/icons';
import majorDataService, { MajorData, SchoolInfo } from '../services/majorDataService';
import './MajorComponents.css';

const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;

interface SchoolMajorListProps {
  schoolName: string;
  onSelectMajor: (majorId: string) => void;
  onBack: () => void;
  onBackToHome?: () => void;
}

const SchoolMajorList: React.FC<SchoolMajorListProps> = ({ 
  schoolName, 
  onSelectMajor, 
  onBack,
  onBackToHome 
}) => {
  const [school, setSchool] = useState<SchoolInfo | null>(null);
  const [majors, setMajors] = useState<MajorData[]>([]);
  const [filteredMajors, setFilteredMajors] = useState<MajorData[]>([]);
  const [directions, setDirections] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // 筛选状态
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDirection, setSelectedDirection] = useState<string | undefined>(undefined);

  useEffect(() => {
    loadSchoolMajors();
  }, [schoolName]);

  useEffect(() => {
    applyFilters();
  }, [majors, searchQuery, selectedDirection]);

  const loadSchoolMajors = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [schoolData, majorsData] = await Promise.all([
        majorDataService.getSchoolByName(schoolName),
        majorDataService.getMajorsBySchool(schoolName)
      ]);
      
      if (!schoolData) {
        setError('未找到该学校信息');
        return;
      }
      
      setSchool(schoolData);
      setMajors(majorsData);
      
      // 提取该学校的专业方向
      const directionsSet = new Set(majorsData.map(major => major.major_direction));
      const schoolDirections = Array.from(directionsSet)
        .filter(direction => direction.trim() !== '')
        .sort();
      setDirections(schoolDirections);
      
    } catch (err) {
      console.error('Error loading school majors:', err);
      setError('加载学校专业失败');
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...majors];

    // 搜索过滤
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(major => 
        major.major_name_chinese.toLowerCase().includes(query) ||
        major.major_name_english.toLowerCase().includes(query) ||
        major.major_direction.toLowerCase().includes(query)
      );
    }

    // 专业方向过滤
    if (selectedDirection) {
      filtered = filtered.filter(major => major.major_direction === selectedDirection);
    }

    setFilteredMajors(filtered);
  };

  const handleSearch = (value: string) => {
    setSearchQuery(value);
  };

  const handleDirectionChange = (value: string | undefined) => {
    setSelectedDirection(value);
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedDirection(undefined);
  };

  const renderMajorCard = (major: MajorData) => (
    <List.Item>
      <Card 
        hoverable
        style={{ width: '100%' }}
        onClick={() => onSelectMajor(major.major_id)}
      >
        <Row gutter={[16, 8]}>
          <Col span={24}>
            <Title level={4} style={{ margin: 0, color: '#1890ff' }}>
              {major.major_name_chinese}
            </Title>
            <Text type="secondary" style={{ fontSize: '14px' }}>
              {major.major_name_english}
            </Text>
          </Col>
          <Col span={24}>
            <Space size="small" wrap>
              <Tag color="orange">
                {major.major_direction}
              </Tag>
              {major.project_category && (
                <Tag color="purple">
                  {major.project_category}
                </Tag>
              )}
            </Space>
          </Col>
          {major.tuition && (
            <Col span={24}>
              <Text type="secondary">
                学费: {major.tuition}
              </Text>
            </Col>
          )}
          {major.admission_time && (
            <Col span={24}>
              <Text type="secondary">
                入学时间: {major.admission_time}
              </Text>
            </Col>
          )}
        </Row>
      </Card>
    </List.Item>
  );

  const breadcrumbItems = [
    ...(onBackToHome
      ? [{
          key: 'home',
          title: (
            <Button type="link" icon={<HomeOutlined />} onClick={onBackToHome}>
              首页
            </Button>
          ),
        }]
      : []),
    {
      key: 'list',
      title: (
        <Button type="link" icon={<BankOutlined />} onClick={onBack}>
          学校列表
        </Button>
      ),
    },
    {
      key: 'current',
      title: (
        <span>
          <BankOutlined style={{ marginRight: '4px' }} />
          {schoolName}
        </span>
      ),
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>加载学校专业中...</div>
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
              <Button size="small" onClick={loadSchoolMajors}>
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

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* 面包屑导航 */}
      <Breadcrumb style={{ marginBottom: '16px' }} items={breadcrumbItems} />

      {/* 返回按钮 */}
      <Button 
        icon={<ArrowLeftOutlined />} 
        onClick={onBack}
        style={{ marginBottom: '16px' }}
      >
        返回学校列表
      </Button>

      {/* 学校信息 */}
      {school && (
        <Card style={{ marginBottom: '24px' }}>
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Title level={2} style={{ margin: 0, color: '#1890ff' }}>
                <BankOutlined style={{ marginRight: '8px' }} />
                {school.school_name}
              </Title>
            </Col>
            <Col span={24}>
              <Space size="middle">
                <Tag color="gold">
                  QS 2026: {school.qs_2026 || (school.qs_2026 === null && school.qs_2025 === null ? '300+' : '未排名')}
                </Tag>
                <Tag color="green">
                  {school.major_count} 个专业
                </Tag>
              </Space>
            </Col>
          </Row>
        </Card>
      )}

      {/* 统计信息 */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col xs={12} sm={8} md={6}>
          <Card>
            <Statistic
              title="总专业数"
              value={majors.length}
              suffix="个"
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6}>
          <Card>
            <Statistic
              title="筛选结果"
              value={filteredMajors.length}
              suffix="个"
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6}>
          <Card>
            <Statistic
              title="专业方向"
              value={directions.length}
              suffix="种"
            />
          </Card>
        </Col>
      </Row>

      {/* 搜索和筛选 */}
      <Card style={{ marginBottom: '24px' }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Search
              placeholder="搜索专业名称或专业方向"
              allowClear
              enterButton={<SearchOutlined />}
              size="large"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onSearch={handleSearch}
            />
          </Col>
          <Col xs={24} md={8}>
            <Select
              placeholder="选择专业方向"
              allowClear
              size="large"
              style={{ width: '100%' }}
              value={selectedDirection}
              onChange={handleDirectionChange}
              suffixIcon={<FilterOutlined />}
            >
              {directions.map(direction => (
                <Option key={direction} value={direction}>
                  {direction}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} md={4}>
            <Button
              icon={<ClearOutlined />}
              size="large"
              style={{ width: '100%' }}
              onClick={clearFilters}
            >
              清除筛选
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 专业列表 */}
      <List
        grid={{
          gutter: 16,
          xs: 1,
          sm: 1,
          md: 2,
          lg: 2,
          xl: 3,
          xxl: 3,
        }}
        dataSource={filteredMajors}
        renderItem={renderMajorCard}
        pagination={{
          pageSize: 12,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) => 
            `第 ${range[0]}-${range[1]} 条，共 ${total} 个专业`,
        }}
      />
    </div>
  );
};

export default SchoolMajorList;
