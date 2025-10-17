'use client';

import React, { useState, useEffect, useMemo } from 'react';
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
  Collapse,
  Radio
} from 'antd';
import {
  SearchOutlined,
  BookOutlined,
  GlobalOutlined,
  FilterOutlined,
  ClearOutlined,
  GroupOutlined,
  TrophyOutlined,
  EnvironmentOutlined
} from '@ant-design/icons';
import majorDataService, { MajorData } from '../services/majorDataService';
import dataLoaderService, { MajorDirectionDefinition } from '../services/DataLoaderService';
import './MajorComponents.css';

const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;
const { Panel } = Collapse;

interface MajorListProps {
  onSelectMajor: (majorId: string) => void;
  onBack?: () => void;
}

const MajorList: React.FC<MajorListProps> = ({ onSelectMajor, onBack }) => {
  const [majors, setMajors] = useState<MajorData[]>([]);
  const [filteredMajors, setFilteredMajors] = useState<MajorData[]>([]);
  const [directionDefinitions, setDirectionDefinitions] = useState<MajorDirectionDefinition[]>([]);
  const [locations, setLocations] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 筛选状态
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDirection, setSelectedDirection] = useState<string | undefined>(undefined);
  const [selectedLocation, setSelectedLocation] = useState<string | undefined>(undefined);
  const [viewMode, setViewMode] = useState<'list' | 'group'>('list');
  const [groupBy, setGroupBy] = useState<'qs_ranking' | 'direction' | 'location'>('qs_ranking');
  const [groupedMajors, setGroupedMajors] = useState<{[key: string]: MajorData[]}>({});
  const majorDirectionOptions = useMemo(() => {
    if (directionDefinitions.length === 0) {
      return [];
    }

    const groupsMap = new Map<string, {
      label: string;
      order: number;
      options: { label: string; value: string }[];
    }>();

    directionDefinitions.forEach(direction => {
      if (!groupsMap.has(direction.groupId)) {
        groupsMap.set(direction.groupId, {
          label: direction.groupName,
          order: direction.groupOrder,
          options: []
        });
      }

      const group = groupsMap.get(direction.groupId)!;
      group.options.push({
        label: direction.name,
        value: direction.name
      });
    });

    return Array.from(groupsMap.values())
      .sort((a, b) => a.order - b.order)
      .map(group => ({
        label: group.label,
        options: group.options
      }));
  }, [directionDefinitions]);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [majors, searchQuery, selectedDirection, selectedLocation]);

  useEffect(() => {
    if (viewMode === 'group') {
      loadGroupedData();
    }
  }, [viewMode, groupBy, filteredMajors]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [majorsData, locationsData, directionDefs] = await Promise.all([
        majorDataService.getAllMajors(),
        majorDataService.getLocations(),
        dataLoaderService.loadMajorDirections()
      ]);

      setMajors(majorsData);
      setLocations(locationsData);
      setDirectionDefinitions(directionDefs);
      setFilteredMajors(majorsData);
    } catch (err) {
      console.error('Error loading majors:', err);
      setError('加载专业列表失败');
    } finally {
      setLoading(false);
    }
  };

  const loadGroupedData = async () => {
    try {
      let groups: {[key: string]: MajorData[]} = {};

      switch (groupBy) {
        case 'qs_ranking':
          groups = await majorDataService.getMajorsByQSRanking('qs_2026');
          break;
        case 'direction':
          groups = await majorDataService.getMajorsByDirectionGroup();
          break;
        case 'location':
          groups = await majorDataService.getMajorsByLocationGroup();
          break;
      }

      // 应用当前的过滤条件到分组数据
      const filteredGroups: {[key: string]: MajorData[]} = {};
      Object.keys(groups).forEach(groupKey => {
        const groupMajors = groups[groupKey];
        let filtered = [...groupMajors];

        // 搜索过滤
        if (searchQuery.trim()) {
          const query = searchQuery.toLowerCase();
          filtered = filtered.filter(major =>
            major.major_name_chinese.toLowerCase().includes(query) ||
            major.major_name_english.toLowerCase().includes(query) ||
            major.school_name.toLowerCase().includes(query) ||
            major.major_direction.toLowerCase().includes(query)
          );
        }

        // 专业方向过滤
        if (selectedDirection) {
          filtered = filtered.filter(major => major.major_direction === selectedDirection);
        }

        // 地区过滤
        if (selectedLocation) {
          filtered = filtered.filter(major => major.location === selectedLocation);
        }

        if (filtered.length > 0) {
          filteredGroups[groupKey] = filtered;
        }
      });

      setGroupedMajors(filteredGroups);
    } catch (err) {
      console.error('Error loading grouped data:', err);
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
        major.school_name.toLowerCase().includes(query) ||
        major.major_direction.toLowerCase().includes(query)
      );
    }

    // 专业方向过滤
    if (selectedDirection) {
      filtered = filtered.filter(major => major.major_direction === selectedDirection);
    }

    // 地区过滤
    if (selectedLocation) {
      filtered = filtered.filter(major => major.location === selectedLocation);
    }

    setFilteredMajors(filtered);
  };

  const handleSearch = (value: string) => {
    setSearchQuery(value);
  };



  const clearFilters = () => {
    setSearchQuery('');
    setSelectedDirection(undefined);
    setSelectedLocation(undefined);
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
              <Tag color="blue" icon={<GlobalOutlined />}>
                {major.school_name}
              </Tag>
              <Tag color="green">
                QS 2026: {major.qs_2026 || (major.qs_2026 === null && major.qs_2025 === null ? '300+' : '未排名')}
              </Tag>
              <Tag color="orange">
                {major.major_direction}
              </Tag>
              <Tag color="cyan" icon={<EnvironmentOutlined />}>
                {major.location}
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

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>加载专业列表中...</div>
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
              <Button size="small" onClick={loadData}>
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
          <BookOutlined style={{ marginRight: '8px' }} />
          专业浏览
        </Title>
        <Text type="secondary">
          浏览所有专业信息，点击专业卡片查看详细信息
        </Text>
      </div>

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
              value={directionDefinitions.length}
              suffix="种"
            />
          </Card>
        </Col>
      </Row>

      {/* 搜索和筛选 */}
      <Card style={{ marginBottom: '24px' }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={10}>
            <Search
              placeholder="搜索专业名称、学校名称或专业方向"
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
              placeholder="专业方向"
              allowClear
              size="large"
              style={{ width: '100%' }}
              value={selectedDirection}
              onChange={setSelectedDirection}
              suffixIcon={<FilterOutlined />}
              options={majorDirectionOptions}
              optionFilterProp="label"
            />
          </Col>
          <Col xs={12} lg={4}>
            <Select
              placeholder="地区"
              allowClear
              size="large"
              style={{ width: '100%' }}
              value={selectedLocation}
              onChange={setSelectedLocation}
              suffixIcon={<EnvironmentOutlined />}
            >
              {locations.map(location => (
                <Option key={location} value={location}>
                  {location}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={12} lg={3}>
            <Button
              icon={<ClearOutlined />}
              size="large"
              style={{ width: '100%' }}
              onClick={clearFilters}
            >
              清除筛选
            </Button>
          </Col>
          <Col xs={12} lg={3}>
            <Radio.Group
              value={viewMode}
              onChange={(e) => setViewMode(e.target.value)}
              size="large"
              style={{ width: '100%' }}
            >
              <Radio.Button value="list" style={{ width: '50%', textAlign: 'center' }}>
                列表
              </Radio.Button>
              <Radio.Button value="group" style={{ width: '50%', textAlign: 'center' }}>
                分组
              </Radio.Button>
            </Radio.Group>
          </Col>
        </Row>

        {viewMode === 'group' && (
          <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
            <Col span={24}>
              <Space>
                <Text strong>分组方式：</Text>
                <Radio.Group
                  value={groupBy}
                  onChange={(e) => setGroupBy(e.target.value)}
                >
                  <Radio.Button value="qs_ranking">
                    <TrophyOutlined /> QS排名
                  </Radio.Button>
                  <Radio.Button value="direction">
                    <BookOutlined /> 专业方向
                  </Radio.Button>
                  <Radio.Button value="location">
                    <EnvironmentOutlined /> 地区
                  </Radio.Button>
                </Radio.Group>
              </Space>
            </Col>
          </Row>
        )}
      </Card>

      {/* 专业列表 */}
      {viewMode === 'list' ? (
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
      ) : (
        <Collapse defaultActiveKey={Object.keys(groupedMajors)} ghost>
          {Object.entries(groupedMajors).map(([groupName, groupMajors]) => (
            <Panel
              header={
                <Space>
                  <GroupOutlined />
                  <Text strong>{groupName}</Text>
                  <Tag color="blue">{groupMajors.length} 个专业</Tag>
                </Space>
              }
              key={groupName}
            >
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
                dataSource={groupMajors}
                renderItem={renderMajorCard}
                pagination={{
                  pageSize: 9,
                  showSizeChanger: false,
                  showQuickJumper: false,
                  showTotal: (total, range) =>
                    `第 ${range[0]}-${range[1]} 条，共 ${total} 个专业`,
                }}
              />
            </Panel>
          ))}
        </Collapse>
      )}
    </div>
  );
};

export default MajorList;
