import json
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.ielts.app.core.config import settings
from backend.ielts.app.models.essay import Essay, GradingResult
from backend.ielts.app.services.ai_client import ai_client
from backend.ielts.app.services.comment_formatter import comment_formatter
from backend.ielts.app.services.enhanced_grading_service import enhanced_grading_service
from backend.ielts.app.services.grading_helpers import GradingHelpers

logger = logging.getLogger(__name__)

# 创建独立的数据库会话（用于后台任务）
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class AIDriverGradingService:
    """AI驱动的评分服务 - 优先使用LLM进行评分，规则评分作为备选"""
    
    def __init__(self):
        self.dimensions = ["TR", "CC", "LR", "GRA"]
        # 加载官方评分标准
        self.scoring_criteria = self._load_scoring_criteria()
        
    def _load_scoring_criteria(self) -> Dict[str, Any]:
        """加载官方IELTS评分标准"""
        try:
            import os
            criteria_path = os.path.join(settings.base_dir, "data", "1. 核心评分标准数据", "cleaned_ielts_scoring_criteria.json")
            with open(criteria_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load scoring criteria: {str(e)}")
            return {}
    
    async def grade_essay_ai_driven(self, essay_id: int) -> Dict[str, Any]:
        """AI驱动的作文评分流程"""
        db = SessionLocal()
        try:
            # 获取作文
            essay = db.query(Essay).filter(Essay.id == essay_id).first()
            if not essay:
                raise ValueError(f"Essay {essay_id} not found")

            logger.info(f"Starting AI-driven grading for essay {essay_id}")
            start_time = time.time()

            # 更新状态为处理中
            essay.grading_status = "processing"
            db.commit()

            # 第一步：AI题目解析
            logger.info("Step 1: AI-driven prompt analysis")
            prompt_analysis = await self._analyze_prompt_ai_driven(essay)
            essay.prompt_analysis = prompt_analysis
            db.commit()

            # 第二步：预检查
            logger.info("Step 2: Pre-flight check")
            precheck_result = self._precheck_essay(essay)

            # 第三步：AI驱动的四维度评估
            logger.info("Step 3: AI-driven dimension evaluation")
            dimension_results = await self._evaluate_dimensions_ai_driven(essay, prompt_analysis)

            # 第四步：分数汇总和验证
            logger.info("Step 4: Score aggregation and validation")
            scores = self._calculate_and_validate_scores(dimension_results, essay)

            # 第五步：生成AI综合评语
            logger.info("Step 5: Generating AI comprehensive comment")
            overall_comment_result = await self._generate_ai_comprehensive_comment(
                essay, dimension_results, scores, prompt_analysis
            )

            # 第六步：生成改进建议
            logger.info("Step 6: Generating improvement suggestions")
            suggestions = self._generate_ai_improvement_suggestions(dimension_results)

            # 计算处理时间
            processing_time = time.time() - start_time

            # 格式化评语 - 将JSON格式转换为用户友好的显示格式
            raw_comment = overall_comment_result.get("text", "")
            formatted_comment_result = comment_formatter.parse_and_format_comment(raw_comment)

            # 使用格式化后的评语，如果格式化失败则使用原始评语
            final_comment = formatted_comment_result.get("formatted_comment", raw_comment)

            logger.info(f"Comment formatting: {'✅ Success' if formatted_comment_result.get('is_formatted') else '❌ Failed'}")

            # 保存评分结果
            grading_result = GradingResult(
                essay_id=essay_id,
                tr_score=scores["tr_score"],
                cc_score=scores["cc_score"],
                lr_score=scores["lr_score"],
                gra_score=scores["gra_score"],
                overall_score=scores["overall_score"],
                tr_analysis=dimension_results.get("TR"),
                cc_analysis=dimension_results.get("CC"),
                lr_analysis=dimension_results.get("LR"),
                gra_analysis=dimension_results.get("GRA"),
                overall_comment=final_comment,  # 使用格式化后的评语
                improvement_suggestions=suggestions,
                model_used=overall_comment_result.get("model_used", "ai_driven"),
                processing_time=processing_time
            )

            db.add(grading_result)
            essay.is_graded = True
            essay.grading_status = "completed"
            essay.grading_result_id = grading_result.id
            db.commit()

            logger.info(f"AI-driven grading completed for essay {essay_id} in {processing_time:.2f}s")

            return {
                "success": True,
                "essay_id": essay_id,
                "scores": scores,
                "dimension_results": dimension_results,
                "overall_comment": overall_comment_result.get("text"),
                "suggestions": suggestions,
                "processing_time": processing_time,
                "model_used": overall_comment_result.get("model_used", "ai_driven")
            }

        except Exception as e:
            logger.error(f"AI-driven grading failed for essay {essay_id}: {str(e)}")
            if 'essay' in locals():
                essay.grading_status = "failed"
                db.commit()
            
            # 如果AI驱动评分失败，回退到增强评分服务
            logger.info(f"Falling back to enhanced grading service for essay {essay_id}")
            return await enhanced_grading_service.grade_essay_enhanced(essay_id)
            
        finally:
            db.close()

    def _parse_ai_json_response(self, text: str) -> Dict[str, Any]:
        """解析AI的JSON响应，处理各种格式问题"""
        if not text:
            return {}

        try:
            # 直接尝试解析
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                # 清理文本后再次尝试
                cleaned_text = text.strip()

                # 移除markdown代码块标记
                if cleaned_text.startswith('```json'):
                    cleaned_text = cleaned_text[7:]
                elif cleaned_text.startswith('```'):
                    cleaned_text = cleaned_text[3:]

                if cleaned_text.endswith('```'):
                    cleaned_text = cleaned_text[:-3]

                cleaned_text = cleaned_text.strip()

                return json.loads(cleaned_text)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse AI JSON response: {e}")
                logger.debug(f"Raw response text: {repr(text)}")
                return {}

    async def _analyze_prompt_ai_driven(self, essay: Essay) -> Dict[str, Any]:
        """AI驱动的题目解析"""
        try:
            # 使用增强的AI提示进行题目分析
            result = await ai_client.analyze_prompt_with_standards(essay.title, essay.task_type, self.scoring_criteria)

            if result.get("success") and result.get("text"):
                parsed_result = self._parse_ai_json_response(result["text"])
                if parsed_result:
                    return parsed_result
                else:
                    logger.warning("Failed to parse AI prompt analysis, using fallback")
                    return self._get_fallback_prompt_analysis(essay.title, essay.task_type)
            else:
                logger.warning("AI prompt analysis failed, using fallback")
                return self._get_fallback_prompt_analysis(essay.title, essay.task_type)
                
        except Exception as e:
            logger.error(f"Error in AI-driven prompt analysis: {str(e)}")
            return self._get_fallback_prompt_analysis(essay.title, essay.task_type)

    def _get_fallback_prompt_analysis(self, title: str, task_type: str) -> Dict[str, Any]:
        """备用题目分析"""
        return {
            "essay_type": "general_discussion",
            "key_instructions": ["分析题目", "提出观点", "论证支持"],
            "question_points": ["主要论点", "支持论据"],
            "required_elements": ["引言", "主体段落", "结论"],
            "task_requirements": {
                "minimum_words": 250 if task_type == "task2" else 150,
                "structure_suggestion": "四段式结构",
                "key_focus": "论证充分性和逻辑性"
            }
        }

    def _precheck_essay(self, essay: Essay) -> Dict[str, Any]:
        """预检查作文"""
        issues = []
        warnings = []
        
        # 字数检查
        min_words = 250 if essay.task_type == "task2" else 150
        if essay.word_count < min_words:
            issues.append(f"字数不足：{essay.word_count} < {min_words}")
        elif essay.word_count < min_words * 1.2:
            warnings.append(f"字数偏少：{essay.word_count}")
            
        # 段落检查
        paragraphs = [p.strip() for p in essay.content.split('\n\n') if p.strip()]
        if len(paragraphs) < 3:
            issues.append(f"段落数量不足：{len(paragraphs)} < 3")
        elif len(paragraphs) < 4:
            warnings.append(f"建议增加段落数量：{len(paragraphs)}")
            
        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }

    async def _evaluate_dimensions_ai_driven(self, essay: Essay, prompt_analysis: Dict) -> Dict[str, Any]:
        """AI驱动的四维度评估"""
        results = {}
        
        for dimension in self.dimensions:
            try:
                logger.info(f"AI evaluating dimension: {dimension}")

                # 使用增强的AI评估，包含官方标准和评分案例
                ai_result = await ai_client.evaluate_dimension_with_standards(
                    essay.content,
                    essay.title,
                    dimension,
                    essay.task_type,
                    prompt_analysis,
                    self.scoring_criteria
                )

                if ai_result.get("success") and ai_result.get("text"):
                    ai_analysis = self._parse_ai_json_response(ai_result["text"])
                    if ai_analysis:
                        # 验证AI评分结果
                        validated_result = self._validate_ai_dimension_result(
                            dimension, ai_analysis, essay
                        )
                        dimension_result = validated_result
                    else:
                        logger.warning(f"Failed to parse AI result for {dimension}, using fallback")
                        dimension_result = await self._fallback_dimension_evaluation(
                            dimension, essay, prompt_analysis
                        )
                else:
                    logger.warning(f"AI evaluation failed for {dimension}, using fallback")
                    dimension_result = await self._fallback_dimension_evaluation(
                        dimension, essay, prompt_analysis
                    )

            except Exception as e:
                logger.error(f"Error evaluating dimension {dimension}: {str(e)}")
                dimension_result = await self._fallback_dimension_evaluation(
                    dimension, essay, prompt_analysis
                )
            if dimension == "TR" and isinstance(dimension_result, dict):
                dimension_result = enhanced_grading_service.enrich_tr_analysis(
                    essay, prompt_analysis, dimension_result
                )

            results[dimension] = dimension_result

        return results

    def _validate_ai_dimension_result(self, dimension: str, ai_result: Dict, essay: Essay) -> Dict[str, Any]:
        """验证AI维度评估结果"""
        # 确保分数在合理范围内
        score = ai_result.get("score", 5.0)
        if not isinstance(score, (int, float)) or score < 1.0 or score > 9.0:
            logger.warning(f"Invalid AI score for {dimension}: {score}, using 5.0")
            score = 5.0
        
        # 四舍五入到0.5
        score = round(score * 2) / 2
        
        # 确保必要字段存在
        validated_result = {
            "score": score,
            "strengths": ai_result.get("strengths", []),
            "weaknesses": ai_result.get("weaknesses", []),
            "evidence": ai_result.get("evidence", []),
            "suggestions": ai_result.get("suggestions", []),
            "detailed_analysis": ai_result.get("detailed_analysis", ""),
            "ai_confidence": ai_result.get("confidence", 0.8),
            "evaluation_method": "ai_driven"
        }
        
        return validated_result

    async def _fallback_dimension_evaluation(self, dimension: str, essay: Essay, prompt_analysis: Dict) -> Dict[str, Any]:
        """备用维度评估（使用规则评分）"""
        logger.info(f"Using rule-based fallback for dimension: {dimension}")
        
        # 使用增强评分服务的规则评分作为备选
        try:
            # 首先尝试使用慷慨AI提示进行回退评分
            ai_fallback_result = await self._ai_generous_fallback(dimension, essay, prompt_analysis)
            if ai_fallback_result:
                return ai_fallback_result

            # 计算量化指标
            quantitative_metrics = self._calculate_basic_metrics(essay)
            
            # 获取维度标准
            criteria = self._get_dimension_criteria(dimension, essay.task_type)
            
            # 使用规则评分
            if hasattr(enhanced_grading_service, '_evaluate_dimension_rule_based'):
                rule_result = enhanced_grading_service._evaluate_dimension_rule_based(
                    dimension, essay, prompt_analysis, quantitative_metrics, criteria
                )
                
                # 标记为规则评分
                rule_result["evaluation_method"] = "rule_based_fallback"
                rule_result["ai_confidence"] = 0.6  # 较低的置信度
                
                return rule_result
            else:
                # 基础备用评分
                return self._get_basic_fallback_evaluation(dimension)
                
        except Exception as e:
            logger.error(f"Fallback evaluation failed for {dimension}: {str(e)}")
            return self._get_basic_fallback_evaluation(dimension)

    async def _ai_generous_fallback(self, dimension: str, essay: Essay, prompt_analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """AI慷慨评分回退，避免使用规则评分"""
        try:
            prompt = ai_client._get_generous_fallback_prompt(
                essay.content,
                essay.title,
                dimension,
                essay.task_type,
                prompt_analysis
            )
            ai_result = await ai_client.generate_text(prompt)
            if ai_result.get("success") and ai_result.get("text"):
                parsed = json.loads(ai_result["text"])
                corrected = ai_client._correct_underestimated_scores(
                    parsed, essay.content, dimension, essay.task_type
                )
                score = corrected.get("score", 8.0)
                score = round(score * 2) / 2
                return {
                    "score": score,
                    "strengths": corrected.get("strengths", []),
                    "weaknesses": corrected.get("weaknesses", []),
                    "evidence": corrected.get("evidence", []),
                    "suggestions": corrected.get("suggestions", []),
                    "detailed_analysis": corrected.get("detailed_analysis", ""),
                    "evaluation_method": "ai_generous_fallback",
                    "ai_confidence": corrected.get("confidence", 0.78)
                }
        except Exception as e:
            logger.warning(f"AI generous fallback failed for {dimension}: {e}")
        return None

    def _get_basic_fallback_evaluation(self, dimension: str) -> Dict[str, Any]:
        """基础备用评估"""
        return {
            "score": 5.0,
            "strengths": ["基本满足要求"],
            "weaknesses": ["需要进一步改进"],
            "evidence": ["评估系统暂时无法提供详细分析"],
            "suggestions": ["建议寻求专业指导"],
            "detailed_analysis": "系统评估暂时不可用",
            "evaluation_method": "basic_fallback",
            "ai_confidence": 0.3
        }

    def _calculate_basic_metrics(self, essay: Essay) -> Dict[str, Any]:
        """计算基础量化指标"""
        content = essay.content
        sentences = [s.strip() for s in content.replace('!', '.').replace('?', '.').split('.') if s.strip()]
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        words = content.split()

        return {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "paragraph_count": len(paragraphs),
            "avg_sentence_length": len(words) / len(sentences) if sentences else 0,
            "avg_paragraph_length": len(words) / len(paragraphs) if paragraphs else 0
        }

    def _get_dimension_criteria(self, dimension: str, task_type: str) -> Dict[str, Any]:
        """获取维度评分标准"""
        try:
            return self.scoring_criteria.get(task_type, {}).get(dimension, {})
        except:
            return {}

    def _calculate_and_validate_scores(self, dimension_results: Dict, essay: Essay) -> Dict[str, float]:
        """计算并验证分数"""
        scores = {}

        # 提取各维度分数
        for dimension in self.dimensions:
            result = dimension_results.get(dimension, {})
            score = result.get("score", 5.0)

            # 验证分数合理性
            if not isinstance(score, (int, float)) or score < 1.0 or score > 9.0:
                logger.warning(f"Invalid score for {dimension}: {score}, using 5.0")
                score = 5.0

            # 四舍五入到0.5
            score = round(score * 2) / 2
            scores[f"{dimension.lower()}_score"] = score

        # 计算总分
        total = sum(scores.values())
        average = total / len(scores)
        overall_score = round(average * 2) / 2
        scores["overall_score"] = overall_score

        # 分数一致性检查
        self._validate_score_consistency(scores, essay)

        return scores

    def _validate_score_consistency(self, scores: Dict[str, float], essay: Essay):
        """验证分数一致性"""
        overall = scores["overall_score"]
        individual_scores = [scores[f"{dim.lower()}_score"] for dim in self.dimensions]

        # 检查是否有异常的分数差异
        max_diff = max(individual_scores) - min(individual_scores)
        if max_diff > 3.0:
            logger.warning(f"Large score variance detected: {max_diff}")

        # 检查总分是否与个别分数一致
        expected_overall = sum(individual_scores) / len(individual_scores)
        if abs(overall - expected_overall) > 0.5:
            logger.warning(f"Overall score inconsistency: {overall} vs expected {expected_overall}")

    async def _generate_ai_comprehensive_comment(self, essay: Essay, dimension_results: Dict,
                                               scores: Dict, prompt_analysis: Dict) -> Dict[str, Any]:
        """生成AI综合评语"""
        try:
            # 使用增强的AI评语生成
            result = await ai_client.generate_comprehensive_comment_with_standards(
                essay.content,
                essay.title,
                dimension_results,
                scores["overall_score"],
                self.scoring_criteria,
                prompt_analysis
            )

            if result.get("success") and result.get("text"):
                return result
            else:
                logger.warning("AI comment generation failed, using fallback")
                return self._generate_fallback_comment(scores["overall_score"])

        except Exception as e:
            logger.error(f"Error generating AI comprehensive comment: {str(e)}")
            return self._generate_fallback_comment(scores["overall_score"])

    def _generate_fallback_comment(self, overall_score: float) -> Dict[str, Any]:
        """生成备用评语"""
        if overall_score >= 8.0:
            comment = "这是一篇高质量的作文，在各个维度都表现出色。"
        elif overall_score >= 7.0:
            comment = "这是一篇良好的作文，大部分维度表现较好，但仍有改进空间。"
        elif overall_score >= 6.0:
            comment = "这是一篇中等水平的作文，基本满足要求，但需要在多个方面进行改进。"
        elif overall_score >= 5.0:
            comment = "这篇作文达到了基本要求，但在各个维度都需要显著改进。"
        else:
            comment = "这篇作文需要在所有维度进行大幅改进才能达到合格水平。"

        return {
            "text": comment,
            "model_used": "fallback_system",
            "success": True
        }

    def _generate_ai_improvement_suggestions(self, dimension_results: Dict) -> List[str]:
        """生成AI改进建议"""
        suggestions = []

        for dimension, result in dimension_results.items():
            dimension_suggestions = result.get("suggestions", [])
            if dimension_suggestions:
                suggestions.extend(dimension_suggestions[:2])  # 每个维度最多2个建议

        # 如果没有足够的建议，添加通用建议
        if len(suggestions) < 3:
            suggestions.extend([
                "增加具体例子和细节支持",
                "改善文章的逻辑结构",
                "丰富词汇使用和句式变化"
            ])

        return suggestions[:5]  # 最多5个建议

# 创建全局实例
ai_driven_grading_service = AIDriverGradingService()
