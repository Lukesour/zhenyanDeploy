'use client';

import React, { useRef, useState } from 'react';
import {
  Card,
  Row,
  Col,
  Tabs,
  Tag,
  Timeline,
  Button,
  Divider,
  Typography,
  Space,
  Alert,
  Collapse,
} from 'antd';
import {
  DownloadOutlined,
  TrophyOutlined,
  WarningOutlined,
  BookOutlined,
  UserOutlined,
  RocketOutlined,
} from '@ant-design/icons';
import { Radar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import { AnalysisReport as AnalysisReportType } from '../services/api';

// 注册Chart.js组件
ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

const { Title, Paragraph, Text } = Typography;
const { Panel } = Collapse;

interface AnalysisReportProps {
  report: AnalysisReportType;
  onBackToForm: () => void;
}

const AnalysisReport: React.FC<AnalysisReportProps> = ({ report, onBackToForm }) => {
  const reportRef = useRef<HTMLDivElement>(null);
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);

  // 雷达图数据（使用后端返回的动态数据）
  const radarData = {
    labels: ['学术能力', '语言能力', '科研背景', '实习背景', '院校背景'],
    datasets: [
      {
        label: '综合竞争力',
        data: report.radar_scores || [70, 65, 60, 55, 75], // 使用后端返回的评分，如果没有则使用默认值
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 2,
        pointBackgroundColor: 'rgba(54, 162, 235, 1)',
      },
    ],
  };

  const radarOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
    },
    scales: {
      r: {
        beginAtZero: true,
        max: 100,
        ticks: {
          stepSize: 20,
        },
      },
    },
  };

  // 下载PDF功能 - 分别生成四个报告
  const downloadPDF = async () => {
    setIsGeneratingPDF(true);
    try {
      console.log('开始生成PDF报告...');
      
      // 创建临时容器用于PDF生成
      const createTempContainer = (id: string) => {
        const container = document.createElement('div');
        container.id = id;
        container.style.position = 'absolute';
        container.style.left = '-9999px';
        container.style.top = '-9999px';
        container.style.width = '800px';
        container.style.backgroundColor = 'white';
        container.style.padding = '20px';
        container.style.fontFamily = 'Arial, sans-serif';
        return container;
      };

      // 生成PDF的通用函数
      const generatePDF = async (containerId: string, filename: string) => {
        console.log(`正在生成: ${filename}`);
        const container = document.getElementById(containerId);
        if (!container) {
          console.error(`容器 ${containerId} 未找到`);
          return;
        }

        try {
          const canvas = await html2canvas(container, {
            useCORS: true,
            allowTaint: true,
            width: 800,
            height: container.scrollHeight,
          } as any);

          const imgData = canvas.toDataURL('image/png');
          const pdf = new jsPDF('p', 'mm', 'a4');
          const imgWidth = 210;
          const pageHeight = 295;
          const imgHeight = (canvas.height * imgWidth) / canvas.width;
          let heightLeft = imgHeight;

          let position = 0;

          pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
          heightLeft -= pageHeight;

          while (heightLeft >= 0) {
            position = heightLeft - imgHeight;
            pdf.addPage();
            pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
            heightLeft -= pageHeight;
          }

          pdf.save(filename);
          console.log(`成功生成: ${filename}`);
        } catch (error) {
          console.error(`生成${filename}失败:`, error);
        }
      };

      // 1. 生成竞争力评估PDF
      console.log('生成竞争力评估PDF...');
      const competitivenessContainer = createTempContainer('competitiveness-pdf');
      competitivenessContainer.innerHTML = `
        <h1 style="text-align: center; color: #1890ff; margin-bottom: 20px;">竞争力评估报告</h1>
        <div style="margin-bottom: 20px;">
          <h3>核心优势</h3>
          <p>${report.competitiveness.strengths}</p>
        </div>
        <div style="margin-bottom: 20px;">
          <h3>主要短板</h3>
          <p>${report.competitiveness.weaknesses}</p>
        </div>
        <div>
          <h3>综合评价</h3>
          <p>${report.competitiveness.summary}</p>
        </div>
      `;
      document.body.appendChild(competitivenessContainer);
      await generatePDF('competitiveness-pdf', '竞争力评估报告.pdf');
      document.body.removeChild(competitivenessContainer);

      // 2. 生成选校建议PDF
      console.log('生成选校建议PDF...');
      const schoolRecommendationsContainer = createTempContainer('school-recommendations-pdf');
      const schoolRecommendationsHTML = report.school_recommendations.recommendations.map((school) => `
        <div style="margin-bottom: 20px; padding: 15px; border: 1px solid #d9d9d9; border-radius: 8px;">
          <h3>${school.university}</h3>
          <p><strong>专业：</strong>${school.program}</p>
          <p><strong>推荐理由：</strong>${school.reason}</p>
        </div>
      `).join('');
      
      schoolRecommendationsContainer.innerHTML = `
        <h1 style="text-align: center; color: #1890ff; margin-bottom: 20px;">选校建议报告</h1>
        ${schoolRecommendationsHTML}
        <div style="margin-top: 20px;">
          <h3>基于相似案例的整体分析</h3>
          <p>${report.school_recommendations.analysis_summary}</p>
        </div>
      `;
      document.body.appendChild(schoolRecommendationsContainer);
      await generatePDF('school-recommendations-pdf', '选校建议报告.pdf');
      document.body.removeChild(schoolRecommendationsContainer);

      // 3. 生成相似案例PDF
      console.log('生成相似案例PDF...');
      const similarCasesContainer = createTempContainer('similar-cases-pdf');
      const similarCasesHTML = report.similar_cases.map((caseItem) => `
        <div style="margin-bottom: 20px; padding: 15px; border: 1px solid #d9d9d9; border-radius: 8px;">
          <h3>案例 ${caseItem.case_id}</h3>
          <p><strong>录取院校：</strong>${caseItem.admitted_university}</p>
          <p><strong>录取专业：</strong>${caseItem.admitted_program}</p>
          <p><strong>GPA：</strong>${caseItem.gpa}</p>
          <p><strong>语言成绩：</strong>${caseItem.language_score}</p>
          ${caseItem.is_recent_graduate !== undefined ? `<p><strong>应届生状态：</strong>${caseItem.is_recent_graduate ? '应届生' : '往届生'}</p>` : ''}
          <p><strong>本科信息：</strong>${caseItem.undergraduate_info}</p>
          <p><strong>成功因素：</strong>${caseItem.success_factors}</p>
          <p><strong>可借鉴经验：</strong>${caseItem.takeaways}</p>
        </div>
      `).join('');
      
      similarCasesContainer.innerHTML = `
        <h1 style="text-align: center; color: #1890ff; margin-bottom: 20px;">相似案例报告</h1>
        ${similarCasesHTML}
      `;
      document.body.appendChild(similarCasesContainer);
      await generatePDF('similar-cases-pdf', '相似案例报告.pdf');
      document.body.removeChild(similarCasesContainer);

      // 4. 生成背景提升PDF
      if (report.background_improvement) {
        console.log('生成背景提升PDF...');
        const backgroundImprovementContainer = createTempContainer('background-improvement-pdf');
        const actionPlanHTML = report.background_improvement.action_plan.map((plan) => `
          <div style="margin-bottom: 15px; padding: 10px; background-color: #f5f5f5; border-radius: 4px;">
            <h4>${plan.timeframe}</h4>
            <p><strong>行动计划：</strong>${plan.action}</p>
            <p><strong>预期目标：</strong>${plan.goal}</p>
          </div>
        `).join('');
        
        backgroundImprovementContainer.innerHTML = `
          <h1 style="text-align: center; color: #1890ff; margin-bottom: 20px;">背景提升报告</h1>
          <h3>行动计划</h3>
          ${actionPlanHTML}
          <div style="margin-top: 20px;">
            <h3>总体策略建议</h3>
            <p>${report.background_improvement.strategy_summary}</p>
          </div>
        `;
        document.body.appendChild(backgroundImprovementContainer);
        await generatePDF('background-improvement-pdf', '背景提升报告.pdf');
        document.body.removeChild(backgroundImprovementContainer);
      }

      console.log('所有PDF报告生成完成！');
    } catch (error) {
      console.error('PDF生成失败:', error);
    } finally {
      setIsGeneratingPDF(false);
    }
  };

  const renderSchoolRecommendations = () => (
    <Row gutter={[16, 16]}>
      {report.school_recommendations.recommendations.map((school, index) => (
        <Col xs={24} lg={12} key={index}>
          <Card
            title={
              <Space>
                <BookOutlined style={{ color: '#1890ff' }} />
                {school.university}
              </Space>
            }
            size="small"
            style={{ marginBottom: 16 }}
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text strong style={{ fontSize: '16px', color: '#1890ff' }}>
                  {school.program}
                </Text>
              </div>
              
              <div>
                <Text strong>推荐理由：</Text>
                <Paragraph style={{ marginTop: 8, fontSize: '14px', lineHeight: '1.6' }}>
                  {school.reason}
                </Paragraph>
              </div>

              {school.supporting_cases && school.supporting_cases.length > 0 && (
                <Collapse size="small">
                  <Panel header={`支撑案例 (${school.supporting_cases.length}个)`} key="1">
                    <Space direction="vertical" style={{ width: '100%' }}>
                      {school.supporting_cases.map((supportingCase, caseIndex) => (
                        <div key={caseIndex} style={{ padding: '8px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
                          <div>
                            <Text strong>案例ID: </Text>
                            <Text>{supportingCase.case_id}</Text>
                            <Tag color="blue" style={{ marginLeft: 8 }}>
                              相似度: {(supportingCase.similarity_score * 100).toFixed(1)}%
                            </Tag>
                          </div>
                          <div style={{ marginTop: 4 }}>
                            <Text strong>关键相似点: </Text>
                            <Text type="secondary">{supportingCase.key_similarities}</Text>
                          </div>
                        </div>
                      ))}
                    </Space>
                  </Panel>
                </Collapse>
              )}
            </Space>
          </Card>
        </Col>
      ))}
    </Row>
  );

  const renderSimilarCases = () => (
    <Row gutter={[16, 16]}>
      {report.similar_cases.map((caseItem, index) => (
        <Col xs={24} lg={12} key={index}>
          <Card
            title={`案例 ${index + 1}: ${caseItem.admitted_university}`}
            size="small"
            extra={<Tag color="blue">{caseItem.admitted_program}</Tag>}
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text strong>基本信息：</Text>
                <br />
                <Text>GPA: {caseItem.gpa} | 语言: {
                  caseItem.language_test_type === 'IELTS'
                    ? (Number(caseItem.language_score) / 10).toFixed(1)
                    : caseItem.language_score
                }</Text>
                {caseItem.language_test_type && (
                  <>
                    <br />
                    <Text>语言考试类型: <Tag color="blue">{caseItem.language_test_type}</Tag></Text>
                  </>
                )}
                {caseItem.is_recent_graduate !== undefined && (
                  <>
                    <br />
                    <Text>应届生状态: <Tag color={caseItem.is_recent_graduate ? "green" : "orange"}>
                      {caseItem.is_recent_graduate ? "应届生" : "往届生"}
                    </Tag></Text>
                  </>
                )}
                <br />
                <Text type="secondary">{caseItem.undergraduate_info}</Text>
              </div>

              {caseItem.key_experiences && (
                <div>
                  <Text strong>主要经历：</Text>
                  <br />
                  <Text type="secondary">{caseItem.key_experiences}</Text>
                </div>
              )}

              <Collapse size="small">
                <Panel header="详细对比分析" key="1">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Text strong>GPA对比：</Text>
                      <Paragraph>{caseItem.comparison.gpa}</Paragraph>
                    </div>
                    <div>
                      <Text strong>院校对比：</Text>
                      <Paragraph>{caseItem.comparison.university}</Paragraph>
                    </div>
                    <div>
                      <Text strong>经历对比：</Text>
                      <Paragraph>{caseItem.comparison.experience}</Paragraph>
                    </div>
                    <div>
                      <Text strong>成功因素：</Text>
                      <Paragraph>{caseItem.success_factors}</Paragraph>
                    </div>
                    <div>
                      <Text strong>可借鉴经验：</Text>
                      <Paragraph>{caseItem.takeaways}</Paragraph>
                    </div>
                  </Space>
                </Panel>
              </Collapse>
            </Space>
          </Card>
        </Col>
      ))}
    </Row>
  );

    const renderBackgroundImprovement = () => {
    if (!report.background_improvement) {
      return <Alert message="背景提升建议暂时无法生成" type="info" />;
    }

    return (
      <Space direction="vertical" style={{ width: '100%' }}>
        <Timeline>
          {report.background_improvement.action_plan.map((plan, index) => (
            <Timeline.Item key={index}>
              <Card size="small">
                <Title level={5}>{plan.timeframe}</Title>
                <Paragraph>
                  <Text strong>行动计划：</Text>
                  {plan.action}
                </Paragraph>
                <Paragraph>
                  <Text strong>预期目标：</Text>
                  {plan.goal}
                </Paragraph>
              </Card>
            </Timeline.Item>
          ))}
        </Timeline>

        <Divider />

        <Card title="总体策略建议" size="small">
          <Paragraph>{report.background_improvement.strategy_summary}</Paragraph>
        </Card>
      </Space>
    );
  };

  const tabItems = [
    {
      key: '1',
      label: (
        <Space>
          <UserOutlined />
          竞争力评估
        </Space>
      ),
      children: (
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={12}>
            <Card title="综合竞争力雷达图" size="small">
              <div style={{ height: '300px', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                <Radar data={radarData} options={radarOptions} />
              </div>
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Card
                title={
                  <Space>
                    <TrophyOutlined style={{ color: '#52c41a' }} />
                    核心优势
                  </Space>
                }
                size="small"
              >
                <Paragraph>{report.competitiveness.strengths}</Paragraph>
              </Card>

              <Card
                title={
                  <Space>
                    <WarningOutlined style={{ color: '#faad14' }} />
                    主要短板
                  </Space>
                }
                size="small"
              >
                <Paragraph>{report.competitiveness.weaknesses}</Paragraph>
              </Card>
            </Space>
          </Col>
          <Col xs={24}>
            <Card title="综合评价" size="small">
              <Paragraph>{report.competitiveness.summary}</Paragraph>
            </Card>
          </Col>
        </Row>
      ),
    },
    {
      key: '2',
      label: (
        <Space>
          <BookOutlined />
          选校建议
        </Space>
      ),
      children: (
        <Space direction="vertical" style={{ width: '100%' }}>
          {report.school_recommendations.recommendations.length === 0 ? (
            <Alert type="info" message="未找到相似案例，返回空推荐列表" />
          ) : (
            renderSchoolRecommendations()
          )}
          <Divider />
          <Card title="基于相似案例的整体分析" size="small">
            <Paragraph>{report.school_recommendations.analysis_summary}</Paragraph>
          </Card>
        </Space>
      ),
    },
    {
      key: '3',
      label: (
        <Space>
          <UserOutlined />
          相似案例
        </Space>
      ),
      children: (
        report.similar_cases.length === 0 ? (
          <Alert type="info" message="没有可用的相似案例解析" />
        ) : (
          renderSimilarCases()
        )
      ),
    },
    {
      key: '4',
      label: (
        <Space>
          <RocketOutlined />
          背景提升
        </Space>
      ),
      children: renderBackgroundImprovement(),
    },
  ];

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', padding: '20px' }}>
      <div ref={reportRef}>
        <Card
          title="留学定位与选校规划分析报告"
          extra={
            <Space>
              <Button 
                type="primary" 
                icon={<DownloadOutlined />} 
                onClick={downloadPDF}
                loading={isGeneratingPDF}
                disabled={isGeneratingPDF}
              >
                {isGeneratingPDF ? '正在生成PDF...' : '下载四个PDF报告'}
              </Button>
                              <Button onClick={onBackToForm}>返回修改</Button>
            </Space>
          }
        >
          {report.degraded && (
            <Alert
              type="warning"
              message="部分结果生成失败，已返回可用部分"
              description={
                report.partial_failures ? (
                  <ul style={{ paddingLeft: 20, margin: 0 }}>
                    {Object.entries(report.partial_failures).map(([k, v]) => (
                      <li key={k}><Text strong>{k}:</Text> <Text type="secondary">{String(v)}</Text></li>
                    ))}
                  </ul>
                ) : null
              }
              style={{ marginBottom: 16 }}
              showIcon
            />
          )}
          <Tabs items={tabItems} size="large" />
        </Card>
      </div>
    </div>
  );
};

export default AnalysisReport;