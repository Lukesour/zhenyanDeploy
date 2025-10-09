"""
超详细改进建议服务 - 整合所有改进分析功能的统一接口
"""

import logging
from typing import Dict, Any, Optional
from .ai_client import ai_client
from .comprehensive_data_loader import comprehensive_data_loader
from .step_by_step_improvement_service import step_by_step_improvement_service

logger = logging.getLogger(__name__)

class UltraDetailedImprovementService:
    """超详细改进建议服务"""
    
    def __init__(self):
        self.ai_client = ai_client
        self.data_loader = comprehensive_data_loader
    
    async def generate_complete_improvement_analysis(
        self,
        essay_content: str,
        essay_title: str,
        dimension_scores: Dict[str, float],
        overall_score: float,
        target_score: Optional[float] = None,
        analysis_type: str = "complete"
    ) -> Dict[str, Any]:
        """
        生成完整的改进分析
        
        Args:
            essay_content: 作文内容
            essay_title: 作文题目
            dimension_scores: 各维度分数
            overall_score: 总分
            target_score: 目标分数
            analysis_type: 分析类型 ("complete", "comprehensive", "sentence", "error", "comparison", "learning")
        
        Returns:
            详细的改进建议分析结果
        """
        
        logger.info(f"Starting {analysis_type} improvement analysis for essay: {essay_title}")
        
        try:
            if analysis_type == "complete":
                # 生成完整的改进建议包 - 使用分步骤服务
                result = await step_by_step_improvement_service.generate_step_by_step_improvements(
                    essay_content, essay_title, dimension_scores, overall_score, target_score
                )

            elif analysis_type == "comprehensive":
                # 生成综合详细改进建议 - 使用分步骤服务
                result = await step_by_step_improvement_service.generate_comprehensive_analysis(
                    essay_content, essay_title, dimension_scores, overall_score
                )

            elif analysis_type == "sentence":
                # 生成逐句详细分析 - 使用分步骤服务
                result = await step_by_step_improvement_service.generate_sentence_analysis(
                    essay_content, essay_title, dimension_scores
                )

            elif analysis_type == "error":
                # 生成错误分析 - 使用分步骤服务
                result = await step_by_step_improvement_service.generate_error_analysis(
                    essay_content, dimension_scores
                )

            elif analysis_type == "comparison":
                # 生成范文对比分析 - 使用分步骤服务
                result = await step_by_step_improvement_service.generate_comparison_analysis(
                    essay_content, essay_title, overall_score
                )

            elif analysis_type == "learning":
                # 生成学习计划 - 使用分步骤服务
                result = await step_by_step_improvement_service.generate_learning_plan(
                    essay_title, dimension_scores, overall_score, target_score
                )

            else:
                raise ValueError(f"Unknown analysis type: {analysis_type}")
            
            # 添加元数据
            if isinstance(result, dict) and "success" in result and result["success"]:
                result["analysis_metadata"] = {
                    "analysis_type": analysis_type,
                    "essay_title": essay_title,
                    "current_score": overall_score,
                    "target_score": target_score,
                    "dimension_scores": dimension_scores
                }
            
            logger.info(f"Successfully completed {analysis_type} improvement analysis")
            return result
            
        except Exception as e:
            logger.error(f"Error in {analysis_type} improvement analysis: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "analysis_type": analysis_type,
                "essay_title": essay_title
            }
    
    def get_available_analysis_types(self) -> Dict[str, str]:
        """获取可用的分析类型"""
        return {
            "complete": "完整改进建议包 - 包含所有类型的详细分析",
            "comprehensive": "综合详细改进建议 - 基于所有数据资源的深度分析",
            "sentence": "逐句详细分析 - 对每个句子进行深度分析和改进",
            "error": "全面错误分析 - 识别和修正所有类型的错误",
            "comparison": "范文对比分析 - 与高分范文的详细对比学习",
            "learning": "个性化学习计划 - 基于具体问题的学习规划"
        }
    
    async def generate_improvement_summary(
        self,
        essay_content: str,
        essay_title: str,
        dimension_scores: Dict[str, float],
        overall_score: float
    ) -> Dict[str, Any]:
        """生成改进建议摘要"""
        
        try:
            # 快速分析主要问题
            main_issues = []
            
            # 基于分数识别主要问题
            if dimension_scores.get("TR", 0) < 6.0:
                main_issues.append("任务回应需要重点改进")
            if dimension_scores.get("CC", 0) < 6.0:
                main_issues.append("连贯性和衔接需要加强")
            if dimension_scores.get("LR", 0) < 6.0:
                main_issues.append("词汇使用需要提升")
            if dimension_scores.get("GRA", 0) < 6.0:
                main_issues.append("语法准确性需要改进")
            
            # 确定改进优先级
            priority_order = sorted(
                dimension_scores.items(), 
                key=lambda x: x[1]
            )
            
            improvement_priorities = [
                f"{dim}维度 (当前{score:.1f}分)" 
                for dim, score in priority_order[:2]
            ]
            
            # 估算改进潜力
            improvement_potential = min(9.0, overall_score + 1.5)
            
            return {
                "success": True,
                "summary": {
                    "current_score": overall_score,
                    "improvement_potential": improvement_potential,
                    "main_issues": main_issues,
                    "improvement_priorities": improvement_priorities,
                    "recommended_analysis": "complete" if overall_score < 7.0 else "comprehensive",
                    "estimated_improvement_time": "4-8周" if overall_score < 6.0 else "2-4周"
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating improvement summary: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_data_resources_info(self) -> Dict[str, Any]:
        """获取数据资源信息"""
        try:
            return {
                "available_resources": {
                    "scoring_criteria": "官方IELTS评分标准",
                    "sample_essays": "高质量范文数据库",
                    "vocabulary_resources": "词汇升级和学术词汇库",
                    "grammar_resources": "语法规则和错误模式库",
                    "writing_techniques": "写作技巧和方法指导",
                    "improvement_templates": "改进建议模板库"
                },
                "data_coverage": {
                    "essay_types": ["同意不同意", "讨论双方观点", "优缺点分析", "问题解决", "双问题"],
                    "score_ranges": "4.0-9.0分全覆盖",
                    "vocabulary_levels": ["基础", "中级", "高级", "学术"],
                    "grammar_complexity": ["简单句", "复合句", "复杂句", "高级结构"]
                }
            }
        except Exception as e:
            logger.error(f"Error getting data resources info: {str(e)}")
            return {"error": str(e)}

# 创建全局服务实例
ultra_detailed_improvement_service = UltraDetailedImprovementService()
