import json
import time
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.ielts.app.core.config import settings
from backend.ielts.app.core.database import get_db
from backend.ielts.app.models.essay import Essay, GradingResult
from backend.ielts.app.services.ai_client import ai_client
from backend.ielts.app.services.comment_formatter import comment_formatter
from backend.ielts.app.services.enhanced_grading_service import enhanced_grading_service
from backend.ielts.app.services.ai_driven_grading_service import ai_driven_grading_service
from backend.ielts.app.services.standards_based_grading_service import standards_based_grading_service
from backend.ielts.app.services.grading_helpers import GradingHelpers

logger = logging.getLogger(__name__)

# 创建独立的数据库会话（用于后台任务）
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class GradingService:
    """评分服务"""
    
    def __init__(self):
        self.dimensions = ["TR", "CC", "LR", "GRA"]
    
    async def grade_essay(self, essay_id: int, use_enhanced: bool = True, use_ai_driven: bool = True, use_standards_based: bool = True) -> Dict[str, Any]:
        """完整的作文评分流程 - 支持多种评分模式，优先使用AI驱动评分"""
        try:
            # 第一优先级：使用AI驱动的评分方法（更依赖大模型）
            if use_ai_driven:
                logger.info(f"Using AI-driven grading service for essay {essay_id}")
                try:
                    return await ai_driven_grading_service.grade_essay_ai_driven(essay_id)
                except Exception as ai_error:
                    logger.warning(f"AI-driven grading failed, falling back to standards-based: {str(ai_error)}")
                    if use_standards_based:
                        return await standards_based_grading_service.grade_essay_standards_based(essay_id)

            # 第二优先级：使用基于官方标准的评分（不依赖AI API，更可靠）
            if use_standards_based:
                logger.info(f"Using standards-based grading service for essay {essay_id}")
                return await standards_based_grading_service.grade_essay_standards_based(essay_id)

            # 第三优先级：备用增强评分方法
            if use_enhanced:
                logger.info(f"Using enhanced grading service for essay {essay_id}")
                return await enhanced_grading_service.grade_essay_enhanced(essay_id)

        except Exception as e:
            logger.error(f"Advanced grading methods failed for essay {essay_id}: {str(e)}")
            logger.info(f"Falling back to basic grading for essay {essay_id}")

        # 原有的基础评分流程
        db = SessionLocal()
        try:
            # 获取作文
            essay = db.query(Essay).filter(Essay.id == essay_id).first()
            if not essay:
                raise ValueError(f"Essay {essay_id} not found")

            logger.info(f"Starting basic grading for essay {essay_id}")
            start_time = time.time()

            # 更新状态为处理中
            essay.grading_status = "processing"
            db.commit()

            # 第一步：题目解析
            logger.info("Step 1: Analyzing prompt")
            prompt_analysis = await self._analyze_prompt(essay)
            essay.prompt_analysis = prompt_analysis
            db.commit()

            # 第二步：预检查
            logger.info("Step 2: Pre-flight check")
            precheck_result = self._precheck_essay(essay)
            if not precheck_result["passed"]:
                logger.warning(f"Pre-check failed: {precheck_result['issues']}")

            # 第三步：四维度评估
            logger.info("Step 3: Four-dimension evaluation")
            dimension_results = await self._evaluate_dimensions(essay, prompt_analysis)

            # 第四步：分数汇总
            logger.info("Step 4: Score aggregation")
            scores = self._calculate_scores(dimension_results)

            # 第五步：生成综合评语
            logger.info("Step 5: Generating overall comment")
            overall_comment_result = await ai_client.generate_overall_comment(
                essay.content,
                essay.title,
                dimension_results,
                scores["overall_score"]
            )

            # 第六步：生成改进建议
            logger.info("Step 6: Generating improvement suggestions")
            suggestions = self._generate_improvement_suggestions(dimension_results)

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
                model_used=overall_comment_result.get("model_used", "basic"),
                processing_time=processing_time
            )

            db.add(grading_result)

            # 更新作文状态
            essay.is_graded = True
            essay.grading_status = "completed"
            db.commit()

            logger.info(f"Basic grading completed for essay {essay_id} in {processing_time:.2f}s")

            return {
                "success": True,
                "essay_id": essay_id,
                "overall_score": scores["overall_score"],
                "processing_time": processing_time
            }

        except Exception as e:
            logger.error(f"Basic grading failed for essay {essay_id}: {str(e)}")

            # 更新状态为失败
            essay.grading_status = "failed"
            db.commit()

            return {
                "success": False,
                "essay_id": essay_id,
                "error": str(e)
            }
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

    async def _analyze_prompt(self, essay: Essay) -> Dict[str, Any]:
        """分析题目"""
        try:
            result = await ai_client.analyze_prompt(essay.title, essay.task_type)
            if result["success"]:
                parsed_result = self._parse_ai_json_response(result["text"])
                if parsed_result:
                    return parsed_result
                else:
                    logger.error("Failed to parse prompt analysis JSON")
                    return {"error": "Failed to parse prompt analysis"}
            else:
                logger.error(f"Prompt analysis failed: {result.get('error')}")
                return {"error": "Prompt analysis failed"}
        except Exception as e:
            logger.error(f"Error in prompt analysis: {str(e)}")
            return {"error": str(e)}
    
    def _precheck_essay(self, essay: Essay) -> Dict[str, Any]:
        """预检查作文"""
        issues = []
        
        # 检查字数
        min_words = 150 if essay.task_type == "task1" else 250
        if essay.word_count < min_words:
            issues.append(f"Word count too low: {essay.word_count} < {min_words}")
        
        # 检查内容长度
        if len(essay.content.strip()) < 100:
            issues.append("Content too short")
        
        # 检查是否有基本结构
        paragraphs = essay.content.split('\n\n')
        if len(paragraphs) < 2:
            issues.append("Insufficient paragraph structure")
        
        return {
            "passed": len(issues) == 0,
            "issues": issues
        }
    
    async def _evaluate_dimensions(self, essay: Essay, prompt_analysis: Dict) -> Dict[str, Any]:
        """评估四个维度"""
        results = {}
        
        for dimension in self.dimensions:
            try:
                logger.info(f"Evaluating dimension: {dimension}")
                result = await ai_client.evaluate_dimension(
                    essay.content,
                    essay.title,
                    dimension,
                    essay.task_type,
                    prompt_analysis
                )
                
                if result["success"]:
                    results[dimension] = json.loads(result["text"])
                else:
                    logger.error(f"Dimension {dimension} evaluation failed: {result.get('error')}")
                    results[dimension] = {"error": f"Evaluation failed: {result.get('error')}"}
                    
            except Exception as e:
                logger.error(f"Error evaluating dimension {dimension}: {str(e)}")
                results[dimension] = {"error": str(e)}
        
        return results
    
    def _calculate_scores(self, dimension_results: Dict[str, Any]) -> Dict[str, float]:
        """计算分数"""
        scores = {}
        
        # 提取各维度分数
        for dimension in self.dimensions:
            result = dimension_results.get(dimension, {})
            if "score" in result:
                scores[f"{dimension.lower()}_score"] = float(result["score"])
            else:
                # 如果某个维度评估失败，给予默认分数
                scores[f"{dimension.lower()}_score"] = 5.0
                logger.warning(f"Using default score for dimension {dimension}")
        
        # 计算总分（四舍五入到0.5）
        total = sum(scores.values())
        average = total / len(scores)
        overall_score = round(average * 2) / 2  # 四舍五入到0.5
        scores["overall_score"] = overall_score
        
        return scores
    
    def _generate_improvement_suggestions(self, dimension_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成改进建议"""
        suggestions = []
        
        for dimension, result in dimension_results.items():
            if "suggestions" in result:
                for suggestion in result["suggestions"]:
                    suggestions.append({
                        "category": dimension,
                        "priority": "medium",  # 可以根据分数差距调整优先级
                        "description": suggestion,
                        "dimension": dimension
                    })
        
        # 按优先级排序（这里简化处理）
        return suggestions[:10]  # 限制建议数量

# 全局评分服务实例
grading_service = GradingService()

def start_grading_task(essay_id: int, use_enhanced: bool = True):
    """启动评分任务（同步包装器）"""
    import asyncio

    try:
        # 在新的事件循环中运行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(grading_service.grade_essay(essay_id, use_enhanced))
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Error in grading task: {str(e)}")
        return {"success": False, "error": str(e)}
