'use client';

import React from 'react';
import { 
  Card, 
  Typography, 
  Button, 
  Row, 
  Col, 
  Progress,
  Tag,
  Divider,
  Space
} from 'antd';
import { 
  ReloadOutlined, 
  TrophyOutlined,
  BarChartOutlined,
  UserOutlined,
  BulbOutlined
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;

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

interface HollandResultsProps {
  result: HollandResult;
  onRestart: () => void;
}

const HollandResults: React.FC<HollandResultsProps> = ({ result, onRestart }) => {
  // 类型颜色映射
  const typeColors: Record<string, string> = {
    'R': '#ff4d4f',  // 现实型 - 红色
    'I': '#1890ff',  // 研究型 - 蓝色
    'A': '#722ed1',  // 艺术型 - 紫色
    'S': '#52c41a',  // 社会型 - 绿色
    'E': '#fa8c16',  // 企业型 - 橙色
    'C': '#13c2c2'   // 常规型 - 青色
  };

  // 获取类型颜色
  const getTypeColor = (typeCode: string) => typeColors[typeCode] || '#666';

  // 格式化日期
  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('zh-CN');
    } catch {
      return dateString;
    }
  };

  return (
    <div className="holland-results">
      {/* 主要结果卡片 */}
      <div className="holland-code-display">
        <TrophyOutlined style={{ fontSize: '48px', color: 'white', marginBottom: '16px' }} />
        <Title level={2} style={{ marginBottom: '8px', color: 'white' }}>
          您的霍兰德代码是：
        </Title>
        <div className="holland-code-text">
          {result.holland_code}
        </div>
        <Text style={{ fontSize: '16px', color: 'rgba(255, 255, 255, 0.8)' }}>
          评估完成时间：{formatDate(result.assessment_date)}
        </Text>

        {/* 前三名类型标签 */}
        <div style={{ marginTop: '24px' }}>
          <Space size="large">
            {result.top_three_types.map((type, index) => (
              <Tag
                key={type.type_code}
                color={getTypeColor(type.type_code)}
                className="holland-type-tag"
              >
                {index + 1}. {type.name} ({type.nickname})
              </Tag>
            ))}
          </Space>
        </div>
      </div>

      {/* 得分详情 */}
      <Card 
        title={
          <span>
            <BarChartOutlined style={{ marginRight: '8px' }} />
            六维度得分详情
          </span>
        }
        style={{ marginBottom: '24px' }}
      >
        <Row gutter={[16, 16]}>
          {result.type_scores.map(typeScore => (
            <Col key={typeScore.type_code} xs={24} sm={12} md={8} lg={4}>
              <div className="holland-score-item">
                <div
                  className="holland-score-type"
                  style={{ color: getTypeColor(typeScore.type_code) }}
                >
                  {typeScore.type_code}
                </div>
                <div className="holland-score-name">
                  <Text>{typeScore.type_name}</Text>
                </div>
                <Progress
                  type="circle"
                  percent={typeScore.percentage}
                  size={80}
                  strokeColor={getTypeColor(typeScore.type_code)}
                  format={() => `${typeScore.score}`}
                />
                <div className="holland-score-percentage">
                  {typeScore.percentage.toFixed(1)}%
                </div>
              </div>
            </Col>
          ))}
        </Row>
      </Card>

      {/* 详细解析 */}
      <Card 
        title={
          <span>
            <UserOutlined style={{ marginRight: '8px' }} />
            个性特质深度解析
          </span>
        }
        style={{ marginBottom: '24px' }}
      >
        <Row gutter={[24, 24]}>
          {result.top_three_types.map((type, index) => (
            <Col key={type.type_code} xs={24} lg={8}>
              <Card
                size="small"
                title={
                  <div className="holland-interpretation-header">
                    <div
                      className="holland-interpretation-rank"
                      style={{ backgroundColor: getTypeColor(type.type_code) }}
                    >
                      {index + 1}
                    </div>
                    <div className="holland-interpretation-title">
                      <div className="holland-interpretation-name">
                        {type.name}
                      </div>
                      <div className="holland-interpretation-nickname">
                        {type.nickname}
                      </div>
                    </div>
                  </div>
                }
                className="holland-interpretation-card"
              >
                <div style={{ marginBottom: '16px' }}>
                  <Text strong>性格特质：</Text>
                  <Paragraph style={{ marginTop: '8px', marginBottom: '16px' }}>
                    {type.characteristics}
                  </Paragraph>
                </div>
                
                <div>
                  <Text strong>
                    <BulbOutlined style={{ marginRight: '4px' }} />
                    推荐职业：
                  </Text>
                  <div style={{ marginTop: '8px' }}>
                    <Space size={[4, 8]} wrap>
                      {type.typical_careers.map((career, careerIndex) => (
                        <Tag
                          key={careerIndex}
                          color={getTypeColor(type.type_code)}
                          className="holland-career-tag"
                        >
                          {career}
                        </Tag>
                      ))}
                    </Space>
                  </div>
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      </Card>

      {/* 操作按钮 */}
      <Card style={{ textAlign: 'center' }}>
        <Space size="large">
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            size="large"
            onClick={onRestart}
            className="holland-submit-button"
          >
            重新测评
          </Button>
          <Button
            size="large"
            onClick={() => window.print()}
            style={{ minWidth: '120px' }}
          >
            打印结果
          </Button>
        </Space>
        
        <Divider />
        
        <div style={{ color: '#666', fontSize: '14px' }}>
          <Paragraph>
            霍兰德职业兴趣理论将人的性格分为六种类型，每个人都是这六种类型的不同组合。
            了解自己的兴趣类型有助于选择适合的专业和职业方向。
          </Paragraph>
          <Text type="secondary">
            建议将此结果与您的实际经历、能力和价值观相结合，做出最适合自己的选择。
          </Text>
        </div>
      </Card>
    </div>
  );
};

export default HollandResults;
