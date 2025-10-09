import json
import time
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.ielts.app.core.config import settings
from backend.ielts.app.models.essay import Essay, GradingResult
from backend.ielts.app.services.ai_client import ai_client
from backend.ielts.app.services.enhanced_grading_service import enhanced_grading_service

logger = logging.getLogger(__name__)

# 创建独立的数据库会话（用于后台任务）
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class StandardsBasedGradingService:
    """基于官方标准的评分服务 - 不依赖AI API，更可靠"""
    
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
    
    async def grade_essay_standards_based(self, essay_id: int) -> Dict[str, Any]:
        """基于官方标准的作文评分流程"""
        db = SessionLocal()
        try:
            # 获取作文
            essay = db.query(Essay).filter(Essay.id == essay_id).first()
            if not essay:
                raise ValueError(f"Essay {essay_id} not found")

            logger.info(f"Starting standards-based grading for essay {essay_id}")
            start_time = time.time()

            # 更新状态为处理中
            essay.grading_status = "processing"
            db.commit()

            # 第一步：标准化题目解析
            logger.info("Step 1: Standards-based prompt analysis")
            prompt_analysis = self._analyze_prompt_standards_based(essay)
            essay.prompt_analysis = prompt_analysis
            db.commit()

            # 第二步：预检查
            logger.info("Step 2: Pre-flight check")
            precheck_result = self._precheck_essay(essay)

            # 第三步：基于官方标准的四维度评估
            logger.info("Step 3: Standards-based dimension evaluation")
            dimension_results = self._evaluate_dimensions_standards_based(essay, prompt_analysis)

            # 第四步：分数计算
            logger.info("Step 4: Score calculation")
            scores = self._calculate_scores(dimension_results)

            # 第五步：生成标准化评语
            logger.info("Step 5: Generating standards-based comment")
            overall_comment_result = self._generate_standards_based_comment(
                essay, dimension_results, scores, prompt_analysis
            )

            # 第六步：生成改进建议
            logger.info("Step 6: Generating improvement suggestions")
            suggestions = self._generate_standards_based_suggestions(dimension_results)

            # 计算处理时间
            processing_time = time.time() - start_time

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
                overall_comment=overall_comment_result.get("text"),
                improvement_suggestions=suggestions,
                model_used="standards_based",
                processing_time=processing_time
            )

            db.add(grading_result)
            essay.is_graded = True
            essay.grading_status = "completed"
            essay.grading_result_id = grading_result.id
            db.commit()

            logger.info(f"Standards-based grading completed for essay {essay_id} in {processing_time:.2f}s")

            return {
                "success": True,
                "essay_id": essay_id,
                "scores": scores,
                "dimension_results": dimension_results,
                "overall_comment": overall_comment_result.get("text"),
                "suggestions": suggestions,
                "processing_time": processing_time,
                "model_used": "standards_based"
            }

        except Exception as e:
            logger.error(f"Standards-based grading failed for essay {essay_id}: {str(e)}")
            if 'essay' in locals():
                essay.grading_status = "failed"
                db.commit()
            
            # 如果标准化评分失败，回退到增强评分服务
            logger.info(f"Falling back to enhanced grading service for essay {essay_id}")
            return await enhanced_grading_service.grade_essay_enhanced(essay_id)
            
        finally:
            db.close()

    def _analyze_prompt_standards_based(self, essay: Essay) -> Dict[str, Any]:
        """基于标准的题目解析"""
        # 不依赖AI，使用规则分析
        title_lower = essay.title.lower()
        
        # 题型识别
        essay_type = "general_discussion"
        if any(word in title_lower for word in ["agree", "disagree"]):
            essay_type = "agree_disagree"
        elif any(word in title_lower for word in ["discuss", "both"]):
            essay_type = "discuss_both"
        elif any(word in title_lower for word in ["problem", "solution"]):
            essay_type = "problem_solution"
        elif any(word in title_lower for word in ["cause", "effect"]):
            essay_type = "cause_effect"
        
        # 关键指令词识别
        key_instructions = []
        if "discuss" in title_lower:
            key_instructions.append("讨论")
        if "agree" in title_lower or "disagree" in title_lower:
            key_instructions.append("表明立场")
        if "example" in title_lower:
            key_instructions.append("提供例子")
        if "reason" in title_lower:
            key_instructions.append("给出原因")
        
        # 必需要素
        required_elements = ["引言", "主体段落", "结论"]
        if essay_type == "agree_disagree":
            required_elements.extend(["明确立场", "支持论据"])
        elif essay_type == "discuss_both":
            required_elements.extend(["双方观点", "个人观点"])
        elif essay_type == "problem_solution":
            required_elements.extend(["问题分析", "解决方案"])
        
        return {
            "essay_type": essay_type,
            "key_instructions": key_instructions,
            "question_points": ["主要论点", "支持论据"],
            "required_elements": required_elements,
            "task_requirements": {
                "minimum_words": 250 if essay.task_type == "task2" else 150,
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

    def _evaluate_dimensions_standards_based(self, essay: Essay, prompt_analysis: Dict) -> Dict[str, Any]:
        """基于官方标准的四维度评估"""
        results = {}
        
        # 计算量化指标
        quantitative_metrics = self._calculate_quantitative_metrics(essay)
        
        for dimension in self.dimensions:
            try:
                logger.info(f"Standards-based evaluating dimension: {dimension}")
                
                # 获取该维度的官方标准
                criteria = self.scoring_criteria.get(essay.task_type, {}).get(dimension, {})
                
                # 基于标准进行评估
                if dimension == "TR":
                    result = self._evaluate_tr_standards_based(essay, prompt_analysis, quantitative_metrics, criteria)
                elif dimension == "CC":
                    result = self._evaluate_cc_standards_based(essay, quantitative_metrics, criteria)
                elif dimension == "LR":
                    result = self._evaluate_lr_standards_based(essay, quantitative_metrics, criteria)
                elif dimension == "GRA":
                    result = self._evaluate_gra_standards_based(essay, quantitative_metrics, criteria)
                else:
                    result = {"score": 5.0, "evidence": [], "suggestions": []}
                
                result["evaluation_method"] = "standards_based"
                results[dimension] = result
                
            except Exception as e:
                logger.error(f"Error evaluating dimension {dimension}: {str(e)}")
                results[dimension] = {
                    "score": 5.0,
                    "evidence": ["评估出现错误"],
                    "suggestions": ["请重新提交评分"],
                    "evaluation_method": "error_fallback"
                }
        
        return results

    def _calculate_quantitative_metrics(self, essay: Essay) -> Dict[str, Any]:
        """计算量化指标"""
        content = essay.content
        sentences = [s.strip() for s in content.replace('!', '.').replace('?', '.').split('.') if s.strip()]
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        words = content.split()
        
        return {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "paragraph_count": len(paragraphs),
            "avg_sentence_length": len(words) / len(sentences) if sentences else 0,
            "avg_paragraph_length": len(words) / len(paragraphs) if paragraphs else 0,
            "unique_words": len(set(word.lower() for word in words if word.isalpha())),
            "lexical_diversity": len(set(word.lower() for word in words if word.isalpha())) / len(words) if words else 0
        }

    def _evaluate_tr_standards_based(self, essay: Essay, prompt_analysis: Dict,
                                   quantitative_metrics: Dict, criteria: Dict) -> Dict[str, Any]:
        """基于官方标准评估TR维度"""
        score_indicators = []
        evidence = []
        suggestions = []

        content_lower = essay.content.lower()
        required_elements = prompt_analysis.get("required_elements", [])

        # 检查任务完成度
        elements_addressed = 0
        for element in required_elements:
            if self._check_element_presence(element, content_lower):
                elements_addressed += 1
                evidence.append(f"包含了要求的要素：{element}")
            else:
                suggestions.append(f"需要更好地体现：{element}")

        response_completeness = elements_addressed / len(required_elements) if required_elements else 0.5

        # 基于官方标准评分
        if response_completeness >= 0.9 and quantitative_metrics["word_count"] >= 280:
            if self._has_strong_arguments(essay.content):
                score_indicators.append(8.5)
                evidence.append("恰当且充分地回应了问题，论点相关且充分扩展")
            else:
                score_indicators.append(7.5)
                evidence.append("恰当地回应了问题的主要部分")
        elif response_completeness >= 0.7:
            score_indicators.append(6.5)
            evidence.append("回应了问题的主要部分")
        elif response_completeness >= 0.5:
            score_indicators.append(5.5)
            evidence.append("部分回应了问题")
        else:
            score_indicators.append(4.0)
            suggestions.append("需要更完整地回应题目要求")

        final_score = sum(score_indicators) / len(score_indicators) if score_indicators else 5.0
        final_score = round(final_score * 2) / 2

        return {
            "score": final_score,
            "evidence": evidence,
            "suggestions": suggestions,
            "response_completeness": response_completeness
        }

    def _evaluate_cc_standards_based(self, essay: Essay, quantitative_metrics: Dict, criteria: Dict) -> Dict[str, Any]:
        """基于官方标准评估CC维度"""
        score_indicators = []
        evidence = []
        suggestions = []

        content = essay.content
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        # 段落结构评估
        if len(paragraphs) >= 4:
            score_indicators.append(7.0)
            evidence.append("文章有清晰的段落结构")
        elif len(paragraphs) >= 3:
            score_indicators.append(6.0)
            evidence.append("文章有基本的段落结构")
        else:
            score_indicators.append(4.0)
            suggestions.append("需要改善段落结构")

        # 连接词使用评估
        cohesive_devices = ["firstly", "secondly", "however", "moreover", "furthermore",
                           "in addition", "on the other hand", "in conclusion", "therefore"]
        found_devices = sum(1 for device in cohesive_devices if device in content.lower())

        if found_devices >= 5:
            score_indicators.append(7.5)
            evidence.append("恰当使用了多种衔接手段")
        elif found_devices >= 3:
            score_indicators.append(6.5)
            evidence.append("使用了一些衔接手段")
        elif found_devices >= 1:
            score_indicators.append(5.5)
            evidence.append("使用了基本的衔接手段")
        else:
            score_indicators.append(4.0)
            suggestions.append("需要增加连接词的使用")

        # 逻辑流畅性评估
        logical_flow = self._assess_logical_flow(content)
        if logical_flow >= 0.8:
            score_indicators.append(8.0)
            evidence.append("文章逻辑清晰，行文流畅")
        elif logical_flow >= 0.6:
            score_indicators.append(6.5)
            evidence.append("文章逻辑基本清晰")
        else:
            score_indicators.append(5.0)
            suggestions.append("需要改善文章的逻辑性")

        final_score = sum(score_indicators) / len(score_indicators) if score_indicators else 5.0
        final_score = round(final_score * 2) / 2

        return {
            "score": final_score,
            "evidence": evidence,
            "suggestions": suggestions,
            "cohesive_devices_count": found_devices
        }

    def _evaluate_lr_standards_based(self, essay: Essay, quantitative_metrics: Dict, criteria: Dict) -> Dict[str, Any]:
        """基于官方标准评估LR维度"""
        score_indicators = []
        evidence = []
        suggestions = []

        content = essay.content
        words = content.split()
        unique_words = set(word.lower() for word in words if word.isalpha())

        # 词汇多样性评估
        lexical_diversity = len(unique_words) / len(words) if words else 0
        if lexical_diversity >= 0.6:
            score_indicators.append(8.0)
            evidence.append("词汇使用丰富多样")
        elif lexical_diversity >= 0.5:
            score_indicators.append(7.0)
            evidence.append("词汇使用较为丰富")
        elif lexical_diversity >= 0.4:
            score_indicators.append(6.0)
            evidence.append("词汇使用基本充足")
        else:
            score_indicators.append(5.0)
            suggestions.append("需要增加词汇的多样性")

        # 学术词汇使用评估
        academic_words = ["significant", "considerable", "substantial", "furthermore", "moreover",
                         "consequently", "nevertheless", "demonstrate", "illustrate", "indicate"]
        found_academic = sum(1 for word in academic_words if word in content.lower())

        if found_academic >= 5:
            score_indicators.append(7.5)
            evidence.append("恰当使用了学术词汇")
        elif found_academic >= 3:
            score_indicators.append(6.5)
            evidence.append("使用了一些学术词汇")
        elif found_academic >= 1:
            score_indicators.append(5.5)
            evidence.append("使用了少量学术词汇")
        else:
            suggestions.append("建议增加学术词汇的使用")

        # 词汇准确性评估（简化版）
        word_length_avg = sum(len(word) for word in words if word.isalpha()) / len([w for w in words if w.isalpha()]) if words else 0
        if word_length_avg >= 5.5:
            score_indicators.append(7.0)
            evidence.append("词汇使用较为精确")
        elif word_length_avg >= 4.5:
            score_indicators.append(6.0)
            evidence.append("词汇使用基本准确")
        else:
            score_indicators.append(5.0)
            suggestions.append("可以使用更精确的词汇")

        final_score = sum(score_indicators) / len(score_indicators) if score_indicators else 5.0
        final_score = round(final_score * 2) / 2

        return {
            "score": final_score,
            "evidence": evidence,
            "suggestions": suggestions,
            "lexical_diversity": lexical_diversity,
            "academic_words_count": found_academic
        }

    def _evaluate_gra_standards_based(self, essay: Essay, quantitative_metrics: Dict, criteria: Dict) -> Dict[str, Any]:
        """基于官方标准评估GRA维度"""
        score_indicators = []
        evidence = []
        suggestions = []

        content = essay.content
        sentences = [s.strip() for s in content.replace('!', '.').replace('?', '.').split('.') if s.strip()]

        # 句式多样性评估
        avg_sentence_length = quantitative_metrics.get("avg_sentence_length", 0)
        if avg_sentence_length >= 20:
            score_indicators.append(7.5)
            evidence.append("使用了丰富多样的句子结构")
        elif avg_sentence_length >= 15:
            score_indicators.append(6.5)
            evidence.append("句子结构有一定变化")
        elif avg_sentence_length >= 10:
            score_indicators.append(5.5)
            evidence.append("句子结构基本合理")
        else:
            score_indicators.append(4.0)
            suggestions.append("需要增加句子的复杂性")

        # 复杂句使用评估
        complex_indicators = ["which", "that", "although", "because", "since", "while", "whereas"]
        complex_count = sum(1 for indicator in complex_indicators if indicator in content.lower())

        if complex_count >= 8:
            score_indicators.append(8.0)
            evidence.append("熟练使用复杂句型")
        elif complex_count >= 5:
            score_indicators.append(7.0)
            evidence.append("较好使用复杂句型")
        elif complex_count >= 3:
            score_indicators.append(6.0)
            evidence.append("使用了一些复杂句型")
        else:
            score_indicators.append(5.0)
            suggestions.append("建议增加复杂句型的使用")

        # 语法准确性评估（简化版）
        # 检查常见错误模式
        error_patterns = ["a informations", "many money", "less people", "more better"]
        error_count = sum(1 for pattern in error_patterns if pattern in content.lower())

        if error_count == 0:
            score_indicators.append(7.5)
            evidence.append("语法使用基本准确")
        elif error_count <= 2:
            score_indicators.append(6.0)
            evidence.append("语法使用大体准确")
        else:
            score_indicators.append(4.5)
            suggestions.append("需要注意语法准确性")

        final_score = sum(score_indicators) / len(score_indicators) if score_indicators else 5.0
        final_score = round(final_score * 2) / 2

        return {
            "score": final_score,
            "evidence": evidence,
            "suggestions": suggestions,
            "complex_sentences_count": complex_count,
            "grammar_errors": error_count
        }

    def _check_element_presence(self, element: str, content_lower: str) -> bool:
        """检查要素是否存在"""
        element_lower = element.lower()

        if "引言" in element_lower or "introduction" in element_lower:
            return len(content_lower.split('\n\n')) >= 1
        elif "结论" in element_lower or "conclusion" in element_lower:
            return any(word in content_lower for word in ["in conclusion", "to conclude", "in summary", "therefore"])
        elif "立场" in element_lower or "position" in element_lower:
            return any(word in content_lower for word in ["i agree", "i disagree", "i believe", "in my opinion"])
        elif "论据" in element_lower or "argument" in element_lower:
            return any(word in content_lower for word in ["because", "since", "due to", "as a result"])
        elif "例子" in element_lower or "example" in element_lower:
            return any(word in content_lower for word in ["for example", "for instance", "such as"])
        else:
            return True  # 默认认为存在

    def _has_strong_arguments(self, content: str) -> bool:
        """检查是否有强有力的论证"""
        content_lower = content.lower()

        # 检查具体例子
        specific_examples = ["for example", "for instance", "such as", "like", "including"]
        example_count = sum(1 for ex in specific_examples if ex in content_lower)

        # 检查因果关系
        causal_words = ["because", "since", "due to", "as a result", "therefore", "consequently"]
        causal_count = sum(1 for word in causal_words if word in content_lower)

        # 检查论证深度
        argument_words = ["furthermore", "moreover", "in addition", "additionally", "however"]
        argument_count = sum(1 for word in argument_words if word in content_lower)

        return example_count >= 2 and causal_count >= 3 and argument_count >= 2

    def _assess_logical_flow(self, content: str) -> float:
        """评估逻辑流畅性"""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        if len(paragraphs) < 3:
            return 0.3

        # 检查段落间的连接
        transition_words = ["firstly", "secondly", "however", "moreover", "in conclusion"]
        transition_count = sum(1 for word in transition_words if word in content.lower())

        # 检查段落长度一致性
        paragraph_lengths = [len(p.split()) for p in paragraphs]
        if paragraph_lengths:
            avg_length = sum(paragraph_lengths) / len(paragraph_lengths)
            length_variance = sum((length - avg_length) ** 2 for length in paragraph_lengths) / len(paragraph_lengths)
            consistency_score = 1.0 / (1.0 + length_variance / 100)  # 归一化
        else:
            consistency_score = 0.5

        # 综合评分
        transition_score = min(1.0, transition_count / 3)
        logical_flow = (transition_score * 0.6 + consistency_score * 0.4)

        return logical_flow

    def _calculate_scores(self, dimension_results: Dict) -> Dict[str, float]:
        """计算分数"""
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

        return scores

    def _generate_standards_based_comment(self, essay: Essay, dimension_results: Dict,
                                        scores: Dict, prompt_analysis: Dict) -> Dict[str, Any]:
        """生成基于标准的评语"""
        overall_score = scores["overall_score"]

        # 基于分数生成评语
        if overall_score >= 8.0:
            comment = "这是一篇优秀的作文。在任务回应、连贯衔接、词汇资源和语法准确性方面都表现出色，"
            comment += "能够恰当且充分地回应题目要求，论证清晰有力，词汇使用丰富准确，语法结构多样且基本无误。"
        elif overall_score >= 7.0:
            comment = "这是一篇良好的作文。基本能够恰当地回应题目要求，文章结构清晰，"
            comment += "词汇使用较为丰富，语法掌握较好，但在某些方面仍有改进空间。"
        elif overall_score >= 6.0:
            comment = "这是一篇中等水平的作文。能够回应题目的主要部分，文章有基本的组织结构，"
            comment += "词汇使用基本充足，语法使用大体正确，但需要在多个方面进行改进。"
        elif overall_score >= 5.0:
            comment = "这篇作文达到了基本要求。部分回应了题目要求，文章有一定的组织性，"
            comment += "词汇使用有限但基本能完成任务，语法有一些错误但不影响整体理解。"
        else:
            comment = "这篇作文需要显著改进。在任务回应、文章组织、词汇使用和语法准确性方面"
            comment += "都存在较大问题，需要加强练习和指导。"

        # 添加具体的维度分析
        dimension_comments = []
        for dimension, result in dimension_results.items():
            score = result.get("score", 5.0)
            if score >= 7.0:
                dimension_comments.append(f"{dimension}维度表现良好")
            elif score >= 6.0:
                dimension_comments.append(f"{dimension}维度基本合格")
            else:
                dimension_comments.append(f"{dimension}维度需要改进")

        if dimension_comments:
            comment += " 具体来说，" + "，".join(dimension_comments) + "。"

        return {
            "text": comment,
            "model_used": "standards_based",
            "success": True
        }

    def _generate_standards_based_suggestions(self, dimension_results: Dict) -> List[str]:
        """生成基于标准的改进建议"""
        suggestions = []

        for dimension, result in dimension_results.items():
            dimension_suggestions = result.get("suggestions", [])
            if dimension_suggestions:
                suggestions.extend(dimension_suggestions[:2])  # 每个维度最多2个建议

        # 如果没有足够的建议，添加通用建议
        if len(suggestions) < 3:
            suggestions.extend([
                "加强论证的逻辑性和说服力",
                "增加具体例子和细节支持",
                "改善文章的整体结构和连贯性",
                "丰富词汇使用，提高表达准确性",
                "注意语法的准确性和句式的多样性"
            ])

        return suggestions[:5]  # 最多5个建议

# 创建全局实例
standards_based_grading_service = StandardsBasedGradingService()
