'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  List,
  Input,
  Button,
  Tag,
  Space,
  Spin,
  Alert,
  Typography,
  Row,
  Col,
  Statistic,
  Select,
  Radio
} from 'antd';
import {
  SearchOutlined,
  BankOutlined,
  BookOutlined,
  ClearOutlined,
  TrophyOutlined,
  FilterOutlined,
  EnvironmentOutlined
} from '@ant-design/icons';
import majorDataService, { SchoolInfo } from '../services/majorDataService';
import './MajorComponents.css';

const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;

interface SchoolListProps {
  onSelectSchool: (schoolName: string) => void;
  onBack?: () => void;
}

const SchoolList: React.FC<SchoolListProps> = ({ onSelectSchool, onBack }) => {
  const [schools, setSchools] = useState<SchoolInfo[]>([]);
  const [filteredSchools, setFilteredSchools] = useState<SchoolInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [qsFilter, setQsFilter] = useState<string>('all');
  const [regionFilter, setRegionFilter] = useState<string>('all');
  const [regions, setRegions] = useState<string[]>([]);

  useEffect(() => {
    loadSchools();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [schools, searchQuery, qsFilter, regionFilter]);

  const loadSchools = async () => {
    try {
      setLoading(true);
      setError(null);

      const schoolsData = await majorDataService.getSchools();
      setSchools(schoolsData);

      // 提取所有地区信息
      const uniqueRegions = Array.from(new Set(schoolsData.map(school => school.location)))
        .filter(location => location && location.trim() !== '')
        .sort();
      setRegions(uniqueRegions);
    } catch (err) {
      console.error('Error loading schools:', err);
      setError('加载学校列表失败');
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...schools];

    // 搜索过滤
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(school =>
        school.school_name.toLowerCase().includes(query) ||
        school.location.toLowerCase().includes(query)
      );
    }

    // QS排名过滤
    if (qsFilter !== 'all') {
      filtered = filtered.filter(school => {
        const ranking = school.qs_2026;
        if (ranking === null) return qsFilter === 'unranked';

        switch (qsFilter) {
          case 'top10':
            return ranking <= 10;
          case 'top50':
            return ranking <= 50;
          case 'top100':
            return ranking <= 100;
          case 'top200':
            return ranking <= 200;
          case 'top500':
            return ranking <= 500;
          case 'beyond500':
            return ranking > 500;
          default:
            return true;
        }
      });
    }

    // 地区过滤
    if (regionFilter !== 'all') {
      filtered = filtered.filter(school => school.location === regionFilter);
    }

    setFilteredSchools(filtered);
  };

  const handleSearch = (value: string) => {
    setSearchQuery(value);
  };

  const clearFilters = () => {
    setSearchQuery('');
    setQsFilter('all');
    setRegionFilter('all');
  };

  const getRankingColor = (ranking: number | null) => {
    if (ranking === null) return 'default';
    if (ranking <= 10) return 'gold';
    if (ranking <= 50) return 'orange';
    if (ranking <= 100) return 'blue';
    return 'default';
  };

  const renderSchoolCard = (school: SchoolInfo) => (
    <List.Item>
      <Card 
        hoverable
        style={{ width: '100%' }}
        onClick={() => onSelectSchool(school.school_name)}
      >
        <Row gutter={[16, 8]}>
          <Col span={24}>
            <Title level={4} style={{ margin: 0, color: '#1890ff' }}>
              <BankOutlined style={{ marginRight: '8px' }} />
              {school.school_name}
            </Title>
          </Col>
          <Col span={24}>
            <Space size="middle" wrap>
              <Tag
                color={getRankingColor(school.qs_2026)}
                icon={<TrophyOutlined />}
              >
                QS 2026: {school.qs_2026 || (school.qs_2026 === null && school.qs_2025 === null ? '300+' : '未排名')}
              </Tag>
              <Tag color="green" icon={<BookOutlined />}>
                {school.major_count} 个专业
              </Tag>
              <Tag color="blue" icon={<EnvironmentOutlined />}>
                {school.location}
              </Tag>
            </Space>
          </Col>
          <Col span={24}>
            <Text type="secondary">
              点击查看该校所有专业
            </Text>
          </Col>
        </Row>
      </Card>
    </List.Item>
  );

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>加载学校列表中...</div>
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
              <Button size="small" onClick={loadSchools}>
                重试
              </Button>
              {onBack && (
                <Button size="small" onClick={onBack}>
                  返回
                </Button>
              )}
            </Space>
          }
        />
      </div>
    );
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>
          <BankOutlined style={{ marginRight: '8px' }} />
          学校浏览
        </Title>
        <Text type="secondary">
          浏览所有学校信息，点击学校卡片查看该校专业
        </Text>
      </div>

      {/* 统计信息 */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col xs={12} sm={8} md={6}>
          <Card>
            <Statistic
              title="总学校数"
              value={schools.length}
              suffix="所"
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6}>
          <Card>
            <Statistic
              title="筛选结果"
              value={filteredSchools.length}
              suffix="所"
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6}>
          <Card>
            <Statistic
              title="总专业数"
              value={schools.reduce((sum, school) => sum + school.major_count, 0)}
              suffix="个"
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6}>
          <Card>
            <Statistic
              title="平均专业数"
              value={Math.round(schools.reduce((sum, school) => sum + school.major_count, 0) / schools.length)}
              suffix="个/校"
            />
          </Card>
        </Col>
      </Row>

      {/* 搜索和筛选 */}
      <Card style={{ marginBottom: '24px' }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={12}>
            <Search
              placeholder="搜索学校名称或地区"
              allowClear
              enterButton={<SearchOutlined />}
              size="large"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onSearch={handleSearch}
            />
          </Col>
          <Col xs={12} lg={4}>
            <Select
              placeholder="QS排名"
              size="large"
              style={{ width: '100%' }}
              value={qsFilter}
              onChange={setQsFilter}
            >
              <Option value="all">全部排名</Option>
              <Option value="top10">QS前10</Option>
              <Option value="top50">QS前50</Option>
              <Option value="top100">QS前100</Option>
              <Option value="top200">QS前200</Option>
              <Option value="top500">QS前500</Option>
              <Option value="beyond500">QS500+</Option>
              <Option value="unranked">未排名</Option>
            </Select>
          </Col>
          <Col xs={12} lg={4}>
            <Select
              placeholder="地区"
              size="large"
              style={{ width: '100%' }}
              value={regionFilter}
              onChange={setRegionFilter}
            >
              <Option value="all">全部地区</Option>
              {regions.map(region => (
                <Option key={region} value={region}>{region}</Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} lg={4}>
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

      {/* 学校列表 */}
      <List
        grid={{
          gutter: 16,
          xs: 1,
          sm: 1,
          md: 2,
          lg: 2,
          xl: 3,
          xxl: 4,
        }}
        dataSource={filteredSchools}
        renderItem={renderSchoolCard}
        pagination={{
          pageSize: 12,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) => 
            `第 ${range[0]}-${range[1]} 条，共 ${total} 所学校`,
        }}
      />
    </div>
  );
};

export default SchoolList;
