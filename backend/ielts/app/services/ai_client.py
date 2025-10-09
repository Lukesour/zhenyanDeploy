import google.generativeai as genai
from typing import Optional, List, Dict, Any
import logging
import asyncio
import json
import re
from datetime import datetime
from backend.ielts.app.core.config import settings
from .comprehensive_data_loader import comprehensive_data_loader
from .comprehensive_improvement_analyzer import comprehensive_improvement_analyzer
from .detailed_error_detector import detailed_error_detector
from .sentence_improvement_generator import sentence_improvement_generator

logger = logging.getLogger(__name__)

class AIClient:
    """Google AI API客户端"""
    
    def __init__(self):
        genai.configure(api_key=settings.google_api_key)
        self.primary_model = settings.primary_model
        self.fallback_models = settings.fallback_models.split(',') if settings.fallback_models else []

        # 加载数据资源
        self.data_loader = comprehensive_data_loader
        self.comprehensive_data = self.data_loader.get_comprehensive_data()
    
    def _clean_ai_response(self, text: str) -> str:
        """清理AI响应文本，移除markdown标记"""
        if not text:
            return text

        # 移除markdown代码块标记
        cleaned_text = text.strip()

        # 移除开头的```json或```
        if cleaned_text.startswith('```json'):
            cleaned_text = cleaned_text[7:]
        elif cleaned_text.startswith('```'):
            cleaned_text = cleaned_text[3:]

        # 移除结尾的```
        if cleaned_text.endswith('```'):
            cleaned_text = cleaned_text[:-3]

        return cleaned_text.strip()

    async def generate_text(
        self,
        prompt: str,
        model_name: Optional[str] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """生成文本，支持模型降级"""
        models_to_try = [model_name] if model_name else [self.primary_model] + self.fallback_models

        for model in models_to_try:
            for attempt in range(max_retries):
                try:
                    logger.info(f"Attempting to use model: {model}, attempt: {attempt + 1}")

                    # 创建模型实例
                    model_instance = genai.GenerativeModel(model)

                    # 生成内容
                    response = await asyncio.to_thread(
                        model_instance.generate_content,
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.3,
                            max_output_tokens=2048,
                        )
                    )

                    if response.text:
                        # 清理响应文本
                        cleaned_text = self._clean_ai_response(response.text)
                        logger.info(f"Successfully generated text using model: {model}")
                        return {
                            "text": cleaned_text,
                            "model_used": model,
                            "success": True
                        }
                    else:
                        logger.warning(f"Empty response from model: {model}")

                except Exception as e:
                    logger.error(f"Error with model {model}, attempt {attempt + 1}: {str(e)}")
                    if attempt == max_retries - 1:
                        logger.error(f"All attempts failed for model: {model}")
                    else:
                        await asyncio.sleep(1)  # 短暂等待后重试

        # 所有模型都失败
        logger.error("All models failed to generate text")
        return {
            "text": None,
            "model_used": None,
            "success": False,
            "error": "All AI models failed to respond"
        }
    
    async def analyze_prompt(self, essay_title: str, task_type: str) -> Dict[str, Any]:
        """分析作文题目"""
        prompt = f"""
        作为雅思写作专家，请用中文分析以下{task_type.upper()}题目：

        题目：{essay_title}

        请严格按以下JSON格式用中文返回分析结果，不要包含markdown标记：
        {{
            "essay_type": "题型分类（如agree_disagree, discuss_both等）",
            "key_instructions": ["用中文列出的关键指令词"],
            "question_points": ["用中文列出必须回应的问题点"],
            "required_elements": ["用中文列出必需包含的要素"],
            "task_requirements": {{
                "minimum_words": 数字,
                "structure_suggestion": "用中文写的建议结构",
                "key_focus": "用中文写的重点关注内容"
            }}
        }}

        要求：所有内容必须用中文书写，分析要准确且符合雅思官方标准，返回纯JSON格式。
        """

        result = await self.generate_text(prompt)

        # 如果API调用失败，提供默认的题目分析
        if not result.get("success", False) or not result.get("text"):
            logger.warning(f"AI prompt analysis failed, using fallback for {task_type}")
            fallback_analysis = self._get_fallback_prompt_analysis(essay_title, task_type)
            return {
                "text": fallback_analysis,
                "model_used": "fallback_system",
                "success": True
            }

        # 对结果进行高分校正
        if result.get("success") and result.get("text"):
            try:
                parsed_result = json.loads(result["text"])
                corrected_result = self._correct_underestimated_scores(
                    parsed_result, essay_content, dimension, task_type
                )
                if corrected_result != parsed_result:
                    result["text"] = json.dumps(corrected_result, ensure_ascii=False)
                    result["score_corrected"] = True
                    logger.info(f"[Generous Correction] {dimension}: {parsed_result.get('score')} -> {corrected_result.get('score')}")
            except Exception as e:
                logger.warning(f"Generous score correction failed for {dimension}: {e}")

        return result
    
    async def evaluate_dimension(
        self, 
        essay_content: str, 
        essay_title: str,
        dimension: str, 
        task_type: str,
        prompt_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """评估单个维度"""
        
        dimension_prompts = {
            "TR": self._get_tr_prompt(essay_content, essay_title, task_type, prompt_analysis),
            "CC": self._get_cc_prompt(essay_content, task_type),
            "LR": self._get_lr_prompt(essay_content, task_type),
            "GRA": self._get_gra_prompt(essay_content, task_type)
        }
        
        prompt = dimension_prompts.get(dimension)
        if not prompt:
            raise ValueError(f"Unknown dimension: {dimension}")
        
        result = await self.generate_text(prompt)

        # 如果API调用失败，提供默认的维度评估
        if not result.get("success", False) or not result.get("text"):
            logger.warning(f"AI dimension evaluation failed for {dimension}, using fallback")
            fallback_evaluation = self._get_fallback_dimension_evaluation(dimension)
            return {
                "text": fallback_evaluation,
                "model_used": "fallback_system",
                "success": True
            }

        return result
    
    def _get_tr_prompt(self, content: str, title: str, task_type: str, analysis: Dict) -> str:
        """TR/TA维度评估提示"""
        return f"""
        作为雅思考官，请用中文评估以下{task_type.upper()}作文的任务回应(Task Response/Achievement)：

        题目：{title}
        题目分析：{analysis}

        作文内容：
        {content}

        请严格按以下JSON格式用中文返回评估结果，不要包含markdown标记：
        {{
            "score": 分数(1.0-9.0),
            "strengths": ["用中文列出的优点"],
            "weaknesses": ["用中文列出的缺点"],
            "evidence": ["用中文描述的从原文中的证据"],
            "suggestions": ["用中文写的改进建议"],
            "detailed_analysis": "用中文写的详细分析文本"
        }}

        评估标准：
        - 是否完全回应了题目要求
        - 观点是否清晰一致
        - 论证是否充分
        - 是否包含所有必需要素
        - 如果作文整体表现出色且符合高分标准，应当慷慨地给出8分以上

        评分哲学：
        - 你是一位专业但宽松（generous）的雅思考官，遇到明显高质量的作文不要犹豫给出8.0-9.0
        - 轻微瑕疵仅视为改进建议，不要为了指出问题而牵强降低分数
        - 若无实质性缺陷，请避免编造弱点

        要求：所有内容必须用中文书写，返回纯JSON格式。
        """
    
    def _get_cc_prompt(self, content: str, task_type: str) -> str:
        """CC维度评估提示"""
        return f"""
        作为雅思考官，请用中文评估以下{task_type.upper()}作文的连贯与衔接(Coherence and Cohesion)：

        作文内容：
        {content}

        请严格按以下JSON格式用中文返回评估结果，不要包含markdown标记：
        {{
            "score": 分数(1.0-9.0),
            "strengths": ["用中文列出的优点"],
            "weaknesses": ["用中文列出的缺点"],
            "evidence": ["用中文描述的从原文中的证据"],
            "suggestions": ["用中文写的改进建议"],
            "detailed_analysis": "用中文写的详细分析文本"
        }}

        评估标准：
        - 文章整体结构是否清晰
        - 段落间逻辑关系是否合理
        - 连接词使用是否恰当
        - 信息流是否顺畅
        - 高质量文章应当获得8分或以上，请保持宽松但专业的判断

        评分哲学：
        - 作为generous的雅思考官，面对结构明晰、衔接自然的文章要毫不犹豫给出8-9分
        - 仅在存在显著连贯问题时降低分数，轻微重复或衔接小疏漏不应压到7分以下
        - 没有实质性弱点时，不要为了给建议而夸大问题

        要求：所有内容必须用中文书写，返回纯JSON格式。
        """
    
    def _get_lr_prompt(self, content: str, task_type: str) -> str:
        """LR维度评估提示"""
        return f"""
        作为雅思考官，请用中文评估以下{task_type.upper()}作文的词汇资源(Lexical Resource)：

        作文内容：
        {content}

        请严格按以下JSON格式用中文返回评估结果，不要包含markdown标记：
        {{
            "score": 分数(1.0-9.0),
            "strengths": ["用中文列出的优点"],
            "weaknesses": ["用中文列出的缺点"],
            "evidence": ["用中文描述的从原文中的证据"],
            "suggestions": ["用中文写的改进建议"],
            "vocabulary_analysis": {{
                "range": "用中文写的词汇广度评价",
                "accuracy": "用中文写的词汇准确性评价",
                "collocations": "用中文写的搭配使用评价",
                "repetition": "用中文写的重复使用分析"
            }}
        }}

        评估标准：
        - 词汇使用的广度和多样性
        - 词汇使用的准确性
        - 搭配的自然性
        - 学术词汇的使用
        - 在符合高分描述时，慷慨地给出8-9分

        评分哲学：
        - 你是一位Generous的雅思考官，面对词汇丰富、准确且自然的文章要给到高分
        - 对偶尔的轻微拼写或搭配小问题保持包容，不要过度扣分
        - 如未发现实质性词汇弱点，请避免硬找缺陷

        要求：所有内容必须用中文书写，返回纯JSON格式。
        """
    
    def _get_gra_prompt(self, content: str, task_type: str) -> str:
        """GRA维度评估提示"""
        return f"""
        作为雅思考官，请用中文评估以下{task_type.upper()}作文的语法广度与准确性(Grammatical Range and Accuracy)：

        作文内容：
        {content}

        请严格按以下JSON格式用中文返回评估结果，不要包含markdown标记：
        {{
            "score": 分数(1.0-9.0),
            "strengths": ["用中文列出的优点"],
            "weaknesses": ["用中文列出的缺点"],
            "evidence": ["用中文描述的从原文中的证据"],
            "suggestions": ["用中文写的改进建议"],
            "grammar_analysis": {{
                "range": "用中文写的语法结构多样性评价",
                "accuracy": "用中文写的语法准确性评价",
                "complexity": "用中文写的复杂结构使用评价",
                "errors": ["用中文列出的主要错误类型"]
            }}
        }}

        评估标准：
        - 语法结构的多样性
        - 语法使用的准确性
        - 复杂句型的使用
        - 错误的频率和严重性
        - 对整体语法表现优秀的作文要慷慨给出8-9分

        评分哲学：
        - 你是一位Generous的雅思考官，对于错误极少且结构多样的文章要直接给出高分
        - 轻微或非系统性的小错误只能作为建议，不能压低到7分以下
        - 如未发现明确的频繁错误，请避免编造弱点

        要求：所有内容必须用中文书写，返回纯JSON格式。
        """

    async def generate_overall_comment(
        self,
        essay_content: str,
        essay_title: str,
        dimension_results: Dict[str, Any],
        overall_score: float
    ) -> Dict[str, Any]:
        """生成综合评语"""
        prompt = f"""
        作为雅思考官，请基于四个维度的详细分析，为以下作文生成综合评语。请用中文回复。

        题目：{essay_title}
        作文内容：{essay_content}

        四维度分析结果：
        {dimension_results}

        总分：{overall_score}

        请严格按以下JSON格式用中文返回，不要包含任何markdown标记：
        {{
            "overall_comment": "用中文写的综合评语（200-300字）",
            "key_strengths": ["用中文列出的主要优点1", "用中文列出的主要优点2", "用中文列出的主要优点3"],
            "key_weaknesses": ["用中文列出的主要不足1", "用中文列出的主要不足2", "用中文列出的主要不足3"],
            "priority_improvements": ["用中文写的优先改进建议1", "用中文写的优先改进建议2", "用中文写的优先改进建议3"],
            "score_justification": "用中文写的分数说明"
        }}

        重要要求：
        - 所有内容必须用中文书写
        - 评语要专业、具体、有建设性
        - 突出最重要的优缺点
        - 提供明确的改进方向
        - 返回纯JSON格式，不要包含```json```标记
        """

        result = await self.generate_text(prompt)

        # 如果API调用失败，提供默认的综合评语
        if not result.get("success", False) or not result.get("text"):
            logger.warning("AI overall comment generation failed, using fallback")
            fallback_comment = self._get_fallback_overall_comment(overall_score)
            return {
                "text": fallback_comment,
                "model_used": "fallback_system",
                "success": True
            }

        return result

    async def analyze_prompt_with_standards(self, essay_title: str, task_type: str, scoring_criteria: Dict) -> Dict[str, Any]:
        """使用官方标准分析作文题目"""
        prompt = f"""
        作为雅思写作专家，请基于官方IELTS评分标准用中文分析以下{task_type.upper()}题目：

        题目：{essay_title}

        官方评分标准参考：
        {json.dumps(scoring_criteria.get(task_type, {}), ensure_ascii=False, indent=2)}

        请严格按以下JSON格式用中文返回分析结果，不要包含markdown标记：
        {{
            "essay_type": "题型分类（如agree_disagree, discuss_both等）",
            "key_instructions": ["用中文列出的关键指令词"],
            "question_points": ["用中文列出必须回应的问题点"],
            "required_elements": ["用中文列出必需包含的要素"],
            "task_requirements": {{
                "minimum_words": 数字,
                "structure_suggestion": "用中文写的建议结构",
                "key_focus": "用中文写的重点关注内容"
            }},
            "scoring_focus": {{
                "TR_key_points": ["TR维度的关键评分点"],
                "CC_key_points": ["CC维度的关键评分点"],
                "LR_key_points": ["LR维度的关键评分点"],
                "GRA_key_points": ["GRA维度的关键评分点"]
            }}
        }}

        要求：
        - 所有内容必须用中文书写
        - 分析要准确且符合雅思官方标准
        - 特别关注各维度的评分要点
        - 返回纯JSON格式
        """

        result = await self.generate_text(prompt)

        # 如果API调用失败，提供默认的题目分析
        if not result.get("success", False) or not result.get("text"):
            logger.warning(f"AI prompt analysis with standards failed, using fallback for {task_type}")
            fallback_analysis = self._get_fallback_prompt_analysis(essay_title, task_type)
            return {
                "text": fallback_analysis,
                "model_used": "fallback_system",
                "success": True
            }

        return result

    async def evaluate_dimension_with_standards(
        self,
        essay_content: str,
        essay_title: str,
        dimension: str,
        task_type: str,
        prompt_analysis: Dict[str, Any],
        scoring_criteria: Dict
    ) -> Dict[str, Any]:
        """使用官方标准评估单个维度"""

        dimension_prompts = {
            "TR": self._get_tr_prompt_with_standards(essay_content, essay_title, task_type, prompt_analysis, scoring_criteria),
            "CC": self._get_cc_prompt_with_standards(essay_content, task_type, scoring_criteria),
            "LR": self._get_lr_prompt_with_standards(essay_content, task_type, scoring_criteria),
            "GRA": self._get_gra_prompt_with_standards(essay_content, task_type, scoring_criteria)
        }

        prompt = dimension_prompts.get(dimension)
        if not prompt:
            raise ValueError(f"Unknown dimension: {dimension}")

        result = await self.generate_text(prompt)

        # 如果API调用失败，提供默认的维度评估
        if not result.get("success", False) or not result.get("text"):
            logger.warning(f"AI dimension evaluation with standards failed for {dimension}, using fallback")
            fallback_evaluation = self._get_fallback_dimension_evaluation(dimension)
            return {
                "text": fallback_evaluation,
                "model_used": "fallback_system",
                "success": True
            }

        # 后处理：校正可能被低估的高质量作文分数
        if result.get("success") and result.get("text"):
            try:
                parsed_result = json.loads(result["text"])
                corrected_result = self._correct_underestimated_scores(
                    parsed_result, essay_content, dimension, task_type
                )
                if corrected_result != parsed_result:
                    result["text"] = json.dumps(corrected_result, ensure_ascii=False)
                    result["score_corrected"] = True
                    logger.info(f"Score corrected for {dimension}: {parsed_result.get('score')} -> {corrected_result.get('score')}")
            except Exception as e:
                logger.warning(f"Score correction failed for {dimension}: {e}")

        return result

    def _correct_underestimated_scores(self, parsed_result: Dict, essay_content: str,
                                     dimension: str, task_type: str) -> Dict:
        """校正可能被低估的高质量作文分数"""
        try:
            current_score = parsed_result.get("score", 0)
            high_band_features = parsed_result.get("high_band_features", [])
            confidence = parsed_result.get("confidence", 0)
            strengths = parsed_result.get("strengths") or []
            weaknesses = parsed_result.get("weaknesses") or []
            detailed_analysis = parsed_result.get("detailed_analysis", "") or ""

            # 若高分特征缺失，尝试从优点评语中推断
            if not high_band_features:
                inferred_features = self._infer_high_band_features(strengths, detailed_analysis)
                if inferred_features:
                    # 使用有序字典去重，保持原有顺序
                    merged = list(dict.fromkeys(high_band_features + inferred_features))
                    high_band_features = merged
                    parsed_result["high_band_features"] = high_band_features

            # 如果已经是高分，不需要校正
            if current_score >= 8.5:
                return parsed_result

            # 检查是否有明显的高分段特征但分数偏低
            correction_needed = False
            target_score = current_score

            # 基于优缺点数量和表述推断目标分数
            if len(weaknesses) <= 1 and strengths and confidence >= 0.7:
                target_score = max(target_score, 8.0)
            if len(strengths) >= 3 and confidence >= 0.75:
                target_score = max(target_score, 8.5)
            if len(strengths) >= 4 and confidence >= 0.8:
                target_score = max(target_score, 9.0)

            high_quality_phrases = [
                "几乎没有明显问题", "逻辑非常清晰", "整体表现出色", "论证充分", "衔接自然流畅",
                "语言高度准确", "错误极少", "表现非常接近满分", "达到高分段标准",
                "达到9分水平", "堪比官方范文", "基本无可挑剔", "极具说服力"
            ]
            if confidence >= 0.7 and any(phrase in detailed_analysis for phrase in high_quality_phrases):
                target_score = max(target_score, 9.0)

            # 基于高分段特征数量判断
            if len(high_band_features) >= 3 and current_score < 8.5:
                correction_needed = True

            # 基于置信度和特征判断
            if confidence >= 0.85 and len(high_band_features) >= 2 and current_score < 8.0:
                correction_needed = True

            # 基于作文质量指标判断
            quality_indicators = self._assess_essay_quality(essay_content, dimension)
            if quality_indicators >= 6:
                target_score = max(target_score, 9.0)
                correction_needed = True
            elif quality_indicators >= 5 and current_score < 8.5:
                correction_needed = True
            elif quality_indicators >= 4 and current_score < 8.0:
                correction_needed = True

            # 特殊情况：如果是明显的高质量作文但分数过低
            if (len(high_band_features) >= 2 and quality_indicators >= 4 and
                confidence >= 0.85 and current_score < 8.0):
                correction_needed = True

            # 如果目标分数显著高于当前分数，也需要校正
            if target_score - current_score >= 0.5:
                correction_needed = True

            if correction_needed:
                # 计算校正后的分数
                feature_bonus = min(len(high_band_features) * 0.3, 1.2)  # 增加特征奖励
                quality_bonus = min(quality_indicators * 0.2, 1.0)  # 增加质量奖励
                confidence_bonus = min((confidence - 0.8) * 3, 0.5) if confidence > 0.8 else 0  # 增加置信度奖励

                # 对于明显的高质量作文，给予额外奖励
                if (len(high_band_features) >= 3 and quality_indicators >= 5 and confidence >= 0.85):
                    excellence_bonus = 0.5
                else:
                    excellence_bonus = 0
                inferred_bonus = 0.5 if (len(weaknesses) == 0 and strengths and current_score <= 7.5 and confidence >= 0.75) else 0
                generosity_bonus = 0.5 if (target_score >= 8.5 and confidence >= 0.75) else 0

                corrected_score = current_score + feature_bonus + quality_bonus + confidence_bonus + excellence_bonus + inferred_bonus + generosity_bonus
                corrected_score = max(corrected_score, target_score)
                corrected_score = min(corrected_score, 9.0)
                corrected_score = round(corrected_score * 2) / 2  # 四舍五入到0.5

                if corrected_score > current_score:
                    parsed_result["score"] = corrected_score
                    parsed_result["band_level"] = f"Band {corrected_score}"
                    parsed_result["score_correction_applied"] = True
                    parsed_result["original_score"] = current_score

                    # 更新详细分析
                    original_analysis = parsed_result.get("detailed_analysis", "")
                    parsed_result["detailed_analysis"] = f"{original_analysis}\n\n[分数校正说明：基于识别到的{len(high_band_features)}个高分段特征和{quality_indicators}个质量指标，将分数从{current_score}调整为{corrected_score}]"

            return parsed_result

        except Exception as e:
            logger.warning(f"Score correction failed: {e}")
            return parsed_result

    def _assess_essay_quality(self, essay_content: str, dimension: str) -> int:
        """评估作文质量指标数量"""
        quality_count = 0
        content_lower = essay_content.lower()
        tokens = re.findall(r"[a-zA-Z']+", content_lower)
        sentences = [s.strip() for s in re.split(r'[.!?]+', essay_content) if s.strip()]

        # 通用质量指标
        if len(essay_content.split()) >= 250:  # 字数充足
            quality_count += 1
        if len(essay_content.split('\n\n')) >= 4:  # 段落结构完整
            quality_count += 1
        if any(word in content_lower for word in ['for example', 'for instance', 'such as']):  # 有例子
            quality_count += 1
        if any(word in content_lower for word in ['however', 'furthermore', 'moreover', 'nevertheless']):  # 有连接词
            quality_count += 1
        if any(word in content_lower for word in ['in conclusion', 'to conclude', 'in summary']):  # 有结论
            quality_count += 1
        if tokens:
            unique_ratio = len(set(tokens)) / len(tokens)
            if unique_ratio >= 0.4:  # 词汇多样性较高
                quality_count += 1
        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            if avg_sentence_length >= 13:  # 句子长度适中且信息密度高
                quality_count += 1
            complex_sentence_ratio = sum(1 for s in sentences if len(s.split()) >= 18) / len(sentences)
            if complex_sentence_ratio >= 0.35:
                quality_count += 1
        cohesive_phrases = [
            'on the one hand', 'on the other hand', 'in addition', 'in contrast',
            'as a result', 'as a consequence', 'in other words'
        ]
        if sum(content_lower.count(phrase) for phrase in cohesive_phrases) >= 2:
            quality_count += 1
        if any(phrase in content_lower for phrase in ['overall', 'to sum up', 'all things considered']):
            quality_count += 1
        if content_lower.count('because') + content_lower.count('since') + content_lower.count('therefore') >= 3:
            quality_count += 1

        # 维度特定指标
        if dimension == "LR":
            # 词汇多样性指标
            if any(word in content_lower for word in ['substantial', 'significant', 'considerable', 'detrimental']):
                quality_count += 1
            advanced_vocabulary = [
                'mitigate', 'alleviate', 'incentivize', 'paradigm', 'ubiquitous',
                'sustainable', 'viable', 'robust', 'comprehensive', 'detrimental',
                'indispensable', 'prevalent', 'ameliorate', 'consequently'
            ]
            if sum(1 for word in advanced_vocabulary if word in content_lower) >= 3:
                quality_count += 1
            collocation_signals = [
                'play a crucial role', 'a significant number', 'it is widely believed',
                'have a profound impact', 'pose a threat', 'give rise to', 'shed light on'
            ]
            if sum(1 for phrase in collocation_signals if phrase in content_lower) >= 1:
                quality_count += 1
            if any(phrase in content_lower for phrase in ['from my perspective', 'it is undeniable that', 'there is no doubt that']):
                quality_count += 1
        elif dimension == "GRA":
            # 语法复杂性指标
            if 'which' in content_lower or 'that' in content_lower:  # 定语从句
                quality_count += 1
            complex_markers = [
                'although', 'whereas', 'while', 'not only', 'provided that',
                'as long as', 'even though', 'in which', 'had ', 'should '
            ]
            if sum(1 for marker in complex_markers if marker in content_lower) >= 2:
                quality_count += 1
            if ';' in essay_content or ':' in essay_content:  # 高级标点使用
                quality_count += 1
            if any(phrase in content_lower for phrase in ['would have', 'could have', 'should have', 'had it not']):
                quality_count += 1
        elif dimension == "CC":
            # 连贯性指标
            if content_lower.count('firstly') + content_lower.count('secondly') >= 2:
                quality_count += 1
            if 'on the one hand' in content_lower and 'on the other hand' in content_lower:
                quality_count += 1
            if content_lower.count('furthermore') + content_lower.count('moreover') >= 2:
                quality_count += 1
            if any(phrase in content_lower for phrase in ['in contrast', 'by comparison', 'equally important']):
                quality_count += 1
        elif dimension == "TR":
            if 'on the one hand' in content_lower and 'on the other hand' in content_lower:
                quality_count += 1
            if any(phrase in content_lower for phrase in ['i believe', 'i agree', 'in my opinion', 'personally, i']):
                quality_count += 1
            if any(phrase in content_lower for phrase in ['supporters of', 'opponents of', 'some people believe']):
                quality_count += 1
            if any(phrase in content_lower for phrase in ['for example', 'for instance', 'to illustrate']):
                quality_count += 1

        return quality_count

    def _get_generous_fallback_prompt(
        self,
        content: str,
        title: str,
        dimension: str,
        task_type: str,
        analysis: Dict[str, Any]
    ) -> str:
        """构建慷慨评分的备用提示，确保AI仍然给出高分评估"""
        dimension_mapping = {
            "TR": {
                "name": "任务回应（Task Response/Achievement）",
                "focus": "关注是否全面回应题目、观点是否清晰、论证是否充分。"
            },
            "CC": {
                "name": "连贯与衔接（Coherence and Cohesion）",
                "focus": "关注段落结构、逻辑流畅度、衔接手段使用。"
            },
            "LR": {
                "name": "词汇资源（Lexical Resource）",
                "focus": "关注词汇多样性、准确性、搭配自然度以及高级词汇使用。"
            },
            "GRA": {
                "name": "语法范围与准确性（Grammatical Range and Accuracy）",
                "focus": "关注句式多样性、语法准确性、复杂结构与标点使用。"
            }
        }

        meta = dimension_mapping.get(dimension, dimension_mapping["TR"])
        analysis_snippet = analysis if isinstance(analysis, dict) else {}

        return f"""
        你是一位经验丰富且慷慨的雅思考官。请基于官方评分标准，对以下{task_type.upper()}作文的{meta['name']}进行评分。务必保持宽松但专业的判断，只在存在明显且严重的问题时才降低分数。

        题目：{title}
        题目分析：{analysis_snippet}

        作文内容：
        {content}

        请牢记：这篇作文整体质量较高，请按照Band 8-9的标准慷慨评分。轻微问题仅作为改进建议，不要压低分数。

        输出严格遵循以下JSON结构（不要包含markdown）：
        {{
            "score": 分数(1.0-9.0),
            "band_level": "Band 8 或 Band 9优先",
            "strengths": ["优点1", "优点2"],
            "weaknesses": ["不足1"（如无必要可写轻微建议）],
            "evidence": ["引用原文的证据说明"],
            "suggestions": ["改进建议，若仅有轻微问题可聚焦打磨"],
            "detailed_analysis": "详细中文分析，强调其高分特征。",
            "high_band_features": ["高分段特征1", "高分段特征2"],
            "confidence": 置信度(0.8-1.0)
        }}

        评分重点：{meta['focus']} 即使出现小的瑕疵，也要在分析中说明其仍然符合买家所期望的高分特征。
        """

    def _infer_high_band_features(self, strengths: List[str], detailed_analysis: str) -> List[str]:
        """根据优点评语与分析内容推断高分特征"""
        texts: List[str] = []
        for item in strengths:
            if isinstance(item, str):
                texts.append(item)
        if isinstance(detailed_analysis, str) and detailed_analysis:
            texts.append(detailed_analysis)

        if not texts:
            return []

        combined_text = " ".join(texts)

        feature_patterns = [
            (["完全回应", "充分回应", "紧扣题意", "全面回应"], "完全回应题目要求"),
            (["论证充分", "分析深入", "论据有力", "观点展开充分"], "论证深入且有力"),
            (["结构清晰", "结构严谨", "段落清楚", "逻辑严密"], "结构严密且逻辑清晰"),
            (["衔接自然", "连贯流畅", "过渡自然", "顺畅衔接"], "连贯性与衔接优秀"),
            (["词汇丰富", "词汇多样", "词汇精准", "词汇使用灵活"], "词汇资源丰富准确"),
            (["语法准确", "语法多样", "句式多样", "语法控制力强"], "语法多样且精准"),
            (["错误极少", "几乎无错误", "错误很少", "失误极少"], "错误极少，对交流无影响"),
            (["高级词汇", "地道表达", "词汇自然"], "高级词汇与自然表达"),
            (["观点清晰", "观点一致", "立场明确"], "观点清晰一致"),
            (["例证充分", "例子具体", "举例恰当"], "例证具体且有力"),
            (["逻辑严密", "结构严谨", "分析深刻"], "逻辑严密分析深入"),
            (["衔接顺畅", "阅读流畅", "段落自然"], "阅读体验极佳")
        ]

        inferred_features: List[str] = []
        for keywords, feature in feature_patterns:
            if any(keyword in combined_text for keyword in keywords):
                inferred_features.append(feature)

        # 去重保持顺序
        return list(dict.fromkeys(inferred_features))

    def _get_tr_prompt_with_standards(self, content: str, title: str, task_type: str,
                                    analysis: Dict, scoring_criteria: Dict) -> str:
        """基于官方标准的TR/TA维度评估提示 - 增强高分段识别能力"""
        tr_criteria = scoring_criteria.get(task_type, {}).get("TR", {})

        # 提取各分数段的标准描述
        band_descriptions = []
        for band in ["band9", "band8", "band7", "band6", "band5"]:
            if band in tr_criteria:
                band_descriptions.append(f"{band.upper()}: {'; '.join(tr_criteria[band])}")

        criteria_text = "\n".join(band_descriptions) if band_descriptions else "标准加载失败"

        return f"""
        你是一位经验丰富的雅思考官，具有识别高质量作文的专业能力。请基于官方IELTS评分标准用中文评估以下{task_type.upper()}作文的任务回应(Task Response/Achievement)。

        题目：{title}
        题目分析：{analysis}

        作文内容：
        {content}

        官方TR评分标准：
        {criteria_text}

        高分段识别要点（Band 8-9特征）：

        **Band 9 关键特征：**
        - 恰当地回应并深入讨论了问题（不仅回应，还要深入讨论）
        - 以清晰且充分展开的观点直接回答问题（观点必须清晰且充分展开）
        - 论点相关、充分扩展且有很好的论据支持（论据支持质量高）
        - 内容或论据支撑上的错误极少（几乎无错误）

        **Band 8 关键特征：**
        - 恰当且充分地回应了问题（充分回应）
        - 以清晰且充分展开的观点回应问题（观点展开充分）
        - 论点相关，适当进行了扩展和论据支持（有扩展和支持）
        - 偶尔会出现内容上的遗漏或错误（仅偶尔有小错误）

        **评分指导原则：**
        1. 如果作文完全回应题目所有部分，观点清晰且论证充分，论据相关且有说服力，应考虑8-9分
        2. 不要因为作文"看起来不错"就给7分，要仔细检查是否达到8-9分标准
        3. 重点关注论证的深度、论据的质量和观点的展开程度
        4. 高质量作文通常有具体例子、深入分析和逻辑清晰的论证结构

        **慷慨评分原则（Generous Scoring）：**
        - 你是一位专业但宽松的雅思考官，对满足Band 8-9描述的作文要慷慨给分
        - 轻微或措辞层面的细微瑕疵应作为改进建议，而非压分理由
        - 未发现实质性缺陷时请避免生造问题，保持对优秀作品的高评分

        **特别注意：**
        - 如果作文结构完整、论证充分、例子具体、语言流畅，很可能是8-9分作文
        - 不要过于保守，高质量作文应该得到相应的高分
        - 重点看作文是否"深入讨论"问题，而不仅仅是"回应"问题

        **Band 9检测清单：**
        ✓ 完全回应题目所有部分
        ✓ 观点清晰且深入展开
        ✓ 论证充分且有说服力
        ✓ 使用具体相关的例子
        ✓ 论据支持质量高
        ✓ 内容几乎无错误

        如果以上6项中有5项或以上符合，应给予8.5-9.0分

        请严格按以下JSON格式用中文返回评估结果，不要包含markdown标记：
        {{
            "score": 分数(1.0-9.0),
            "band_level": "对应的分数段(如Band 8或Band 9)",
            "strengths": ["用中文列出的优点"],
            "weaknesses": ["用中文列出的缺点"],
            "evidence": ["用中文描述的从原文中的证据"],
            "suggestions": ["用中文写的改进建议"],
            "detailed_analysis": "用中文写的详细分析文本",
            "high_band_features": ["识别出的高分段特征"],
            "official_criteria_match": "与官方标准的匹配度分析",
            "confidence": 置信度(0.0-1.0)
        }}

        评估重点：
        - 是否完全且深入地回应了题目要求
        - 观点是否清晰一致且充分展开
        - 论证是否充分、深入且有说服力
        - 论据是否相关、具体且有力
        - 是否展现了深度思考和分析能力

        重要提醒：不要低估高质量作文的分数。如果作文确实表现出色，应该给予相应的高分（8-9分）。
        """

    def _get_cc_prompt_with_standards(self, content: str, task_type: str, scoring_criteria: Dict) -> str:
        """基于官方标准的CC维度评估提示 - 增强高分段识别能力"""
        cc_criteria = scoring_criteria.get(task_type, {}).get("CC", {})

        # 提取各分数段的标准描述
        band_descriptions = []
        for band in ["band9", "band8", "band7", "band6", "band5"]:
            if band in cc_criteria:
                band_descriptions.append(f"{band.upper()}: {'; '.join(cc_criteria[band])}")

        criteria_text = "\n".join(band_descriptions) if band_descriptions else "标准加载失败"

        return f"""
        你是一位经验丰富的雅思考官，具有识别高质量作文连贯性的专业能力。请基于官方IELTS评分标准用中文评估以下{task_type.upper()}作文的连贯与衔接(Coherence and Cohesion)。

        作文内容：
        {content}

        官方CC评分标准：
        {criteria_text}

        高分段识别要点（Band 8-9特征）：

        **Band 9 关键特征：**
        - 可以毫不费力地理解其信息（读者理解毫无障碍）
        - 衔接手段运用自如，行文连贯（衔接自然流畅）
        - 连贯或衔接方面的错误极少（几乎无错误）
        - 熟练地运用分段（段落划分完美）

        **Band 8 关键特征：**
        - 可以轻松地理解其信息（读者理解容易）
        - 符合逻辑地组织信息及论点，衔接处理得当（逻辑清晰，衔接恰当）
        - 偶尔会出现连贯或衔接上的错误（仅偶尔有小错误）
        - 充分且合理地分段（分段合理有效）

        **高质量作文的连贯性特征：**
        1. 段落结构清晰：引言-主体段-结论，每段有明确主题
        2. 逻辑流畅：观点之间有清晰的逻辑关系和发展脉络
        3. 衔接自然：使用多样化的连接词和衔接手段，不显突兀
        4. 指代准确：代词和替换使用准确，避免重复
        5. 信息组织：信息按逻辑顺序组织，易于理解

        **评分指导原则：**
        1. 如果文章结构清晰、逻辑流畅、衔接自然，应考虑8-9分
        2. 重点关注读者理解的难易程度
        3. 评估衔接手段的多样性和自然性
        4. 检查段落划分是否合理有效

        **慷慨评分原则（Generous Scoring）：**
        - 对于阅读毫不费力、衔接自然的文章，要自信地给出8-9分
        - 细小的衔接重复或偶发失误只作为建议，不应压分
        - 如整体逻辑顺畅、未发现实质问题，请不要刻意寻找弱点

        请严格按以下JSON格式用中文返回评估结果，不要包含markdown标记：
        {{
            "score": 分数(1.0-9.0),
            "band_level": "对应的分数段(如Band 8或Band 9)",
            "strengths": ["用中文列出的优点"],
            "weaknesses": ["用中文列出的缺点"],
            "evidence": ["用中文描述的从原文中的证据"],
            "suggestions": ["用中文写的改进建议"],
            "detailed_analysis": "用中文写的详细分析文本",
            "cohesion_analysis": {{
                "paragraph_structure": "段落结构分析",
                "linking_devices": "连接词使用分析",
                "logical_flow": "逻辑流畅性分析",
                "referencing": "指代和替换分析"
            }},
            "high_band_features": ["识别出的高分段特征"],
            "official_criteria_match": "与官方标准的匹配度分析",
            "confidence": 置信度(0.0-1.0)
        }}

        评估重点：
        - 读者理解的难易程度（毫不费力vs轻松vs需要努力）
        - 衔接手段的自然性和多样性
        - 逻辑发展的清晰度和连贯性
        - 段落划分的合理性和有效性
        - 信息组织的逻辑性

        重要提醒：不要低估高质量作文的分数。如果作文连贯性确实出色，应该给予相应的高分（8-9分）。
        """

    def _get_lr_prompt_with_standards(self, content: str, task_type: str, scoring_criteria: Dict) -> str:
        """基于官方标准的LR维度评估提示 - 增强高分段识别能力"""
        lr_criteria = scoring_criteria.get(task_type, {}).get("LR", {})

        # 提取各分数段的标准描述
        band_descriptions = []
        for band in ["band9", "band8", "band7", "band6", "band5"]:
            if band in lr_criteria:
                band_descriptions.append(f"{band.upper()}: {'; '.join(lr_criteria[band])}")

        criteria_text = "\n".join(band_descriptions) if band_descriptions else "标准加载失败"

        return f"""
        你是一位经验丰富的雅思考官，具有识别高质量词汇使用的专业能力。请基于官方IELTS评分标准用中文评估以下{task_type.upper()}作文的词汇资源(Lexical Resource)。

        作文内容：
        {content}

        官方LR评分标准：
        {criteria_text}

        高分段识别要点（Band 8-9特征）：

        **Band 9 关键特征：**
        - 词汇使用体现了充分的灵活性及准确性（灵活且准确）
        - 拼写和构词方面的轻微错误极少，对于交流影响极小（几乎无错误）
        - 能准确和恰当地使用丰富的词汇，能自然使用并掌握复杂的词汇特征（词汇丰富且自然）

        **Band 8 关键特征：**
        - 流畅和灵活地使用丰富的词汇，达意准确（流畅灵活，意思准确）
        - 熟练地在适当时候使用不常见的词汇或习语（恰当使用高级词汇）
        - 拼写和构词方面偶尔出现错误，但对交流影响极小（仅偶尔有小错误）

        **高质量作文的词汇特征：**
        1. 词汇多样性：避免重复，使用同义词替换
        2. 精确性：词汇选择准确，表达意思精确
        3. 自然性：词汇搭配自然，符合英语习惯
        4. 学术性：适当使用学术词汇和正式表达
        5. 复杂性：使用复杂词汇特征（如词根变化、习语等）

        **高分段词汇示例：**
        - 高级词汇：detrimental, substantial, comprehensive, facilitate, mitigate
        - 精确表达：rather than, in particular, furthermore, consequently, nevertheless
        - 学术搭配：pose a threat, play a crucial role, have detrimental effects
        - 复杂结构：not only...but also, the extent to which, it is widely acknowledged

        **评分指导原则：**
        1. 如果词汇丰富、准确、自然，且有高级词汇和复杂特征，应考虑8-9分
        2. 重点关注词汇的精确性和自然性，而不仅仅是复杂性
        3. 评估词汇搭配的地道性
        4. 检查是否有效避免了重复

        **慷慨评分原则（Generous Scoring）：**
        - 对词汇范围广、搭配自然的文章要毫不犹豫给出8-9分
        - 对偶发的轻微拼写或搭配小问题保持宽容，不要因此压分
        - 若优势明显且弱点轻微，请避免为了指出问题而降低分数

        请严格按以下JSON格式用中文返回评估结果，不要包含markdown标记：
        {{
            "score": 分数(1.0-9.0),
            "band_level": "对应的分数段(如Band 8或Band 9)",
            "strengths": ["用中文列出的优点"],
            "weaknesses": ["用中文列出的缺点"],
            "evidence": ["用中文描述的从原文中的证据"],
            "suggestions": ["用中文写的改进建议"],
            "detailed_analysis": "用中文写的详细分析文本",
            "vocabulary_analysis": {{
                "range": "用中文写的词汇广度评价",
                "accuracy": "用中文写的词汇准确性评价",
                "flexibility": "用中文写的词汇灵活性评价",
                "collocations": "用中文写的搭配使用评价",
                "academic_vocabulary": "用中文写的学术词汇使用评价",
                "repetition": "用中文写的重复使用分析"
            }},
            "high_band_features": ["识别出的高分段词汇特征"],
            "advanced_vocabulary_examples": ["文中使用的高级词汇示例"],
            "official_criteria_match": "与官方标准的匹配度分析",
            "confidence": 置信度(0.0-1.0)
        }}

        评估重点：
        - 词汇的丰富性和多样性（避免重复）
        - 词汇使用的准确性和精确性
        - 词汇搭配的自然性和地道性
        - 高级词汇和学术词汇的恰当使用
        - 复杂词汇特征的掌握程度
        - 拼写和构词的准确性

        重要提醒：不要低估高质量作文的分数。如果词汇使用确实丰富、准确、自然，应该给予相应的高分（8-9分）。
        """

    def _get_gra_prompt_with_standards(self, content: str, task_type: str, scoring_criteria: Dict) -> str:
        """基于官方标准的GRA维度评估提示 - 增强高分段识别能力"""
        gra_criteria = scoring_criteria.get(task_type, {}).get("GRA", {})

        # 提取各分数段的标准描述
        band_descriptions = []
        for band in ["band9", "band8", "band7", "band6", "band5"]:
            if band in gra_criteria:
                band_descriptions.append(f"{band.upper()}: {'; '.join(gra_criteria[band])}")

        criteria_text = "\n".join(band_descriptions) if band_descriptions else "标准加载失败"

        return f"""
        你是一位经验丰富的雅思考官，具有识别高质量语法使用的专业能力。请基于官方IELTS评分标准用中文评估以下{task_type.upper()}作文的语法广度与准确性(Grammatical Range and Accuracy)。

        作文内容：
        {content}

        官方GRA评分标准：
        {criteria_text}

        高分段识别要点（Band 8-9特征）：

        **Band 9 关键特征：**
        - 使用丰富多样的句子结构，具有完全的灵活性和掌控能力（句式多样且掌控完全）
        - 微小错误极少，对交流影响极小（几乎无错误）
        - 全文的标点符号和语法运用得当（标点和语法完美）

        **Band 8 关键特征：**
        - 灵活而准确地使用丰富多样的句子结构（灵活准确，句式丰富）
        - 大多数句子准确无误，标点符号使用得当（大部分句子正确）
        - 偶尔会出现非系统性的错误和不恰当之处，但对交流影响极小（仅偶尔有小错误）

        **高质量作文的语法特征：**
        1. 句式多样性：简单句、复合句、复杂句的有效结合
        2. 复杂结构：定语从句、状语从句、名词性从句的熟练使用
        3. 语法准确性：时态、语态、主谓一致等基本语法正确
        4. 标点符号：逗号、分号、冒号等标点符号使用恰当
        5. 语法灵活性：能够灵活运用各种语法结构表达复杂意思

        **高分段语法结构示例：**
        - 复杂句式：While it is true that..., it is also important to consider...
        - 非限制性定语从句：...which has led to significant changes...
        - 分词结构：Having considered all factors, it can be concluded that...
        - 倒装结构：Not only does this approach..., but it also...
        - 虚拟语气：If governments were to implement such policies...

        **评分指导原则：**
        1. 如果句式多样、语法准确、复杂结构使用恰当，应考虑8-9分
        2. 重点关注语法错误的频率和对理解的影响
        3. 评估复杂句式的掌控能力
        4. 检查标点符号使用的准确性

        **慷慨评分原则（Generous Scoring）：**
        - 对语法掌控力强且错误极少的文章要慷慨给出8-9分
        - 偶发的小错误只作为改进建议，不应压低总分
        - 如整体语法表现稳定，请不要刻意寻找弱点

        请严格按以下JSON格式用中文返回评估结果，不要包含markdown标记：
        {{
            "score": 分数(1.0-9.0),
            "band_level": "对应的分数段(如Band 8或Band 9)",
            "strengths": ["用中文列出的优点"],
            "weaknesses": ["用中文列出的缺点"],
            "evidence": ["用中文描述的从原文中的证据"],
            "suggestions": ["用中文写的改进建议"],
            "detailed_analysis": "用中文写的详细分析文本",
            "grammar_analysis": {{
                "range": "用中文写的语法结构多样性评价",
                "accuracy": "用中文写的语法准确性评价",
                "complexity": "用中文写的复杂结构使用评价",
                "sentence_variety": "用中文写的句式变化评价",
                "punctuation": "用中文写的标点符号使用评价",
                "errors": ["用中文列出的主要错误类型和频率"]
            }},
            "high_band_features": ["识别出的高分段语法特征"],
            "complex_structures_examples": ["文中使用的复杂语法结构示例"],
            "official_criteria_match": "与官方标准的匹配度分析",
            "confidence": 置信度(0.0-1.0)
        }}

        评估重点：
        - 句子结构的多样性和复杂性
        - 语法使用的准确性和灵活性
        - 复杂句式的掌控能力和自然性
        - 标点符号的正确和恰当使用
        - 语法错误的频率、类型和对理解的影响

        重要提醒：不要低估高质量作文的分数。如果语法使用确实多样、准确、灵活，应该给予相应的高分（8-9分）。
        """

    async def generate_comprehensive_comment_with_standards(
        self,
        essay_content: str,
        essay_title: str,
        dimension_results: Dict[str, Any],
        overall_score: float,
        scoring_criteria: Dict,
        prompt_analysis: Dict
    ) -> Dict[str, Any]:
        """基于官方标准生成综合评语"""
        prompt = f"""
        作为雅思考官，请基于官方IELTS评分标准和四个维度的详细分析，为以下作文生成专业的综合评语。请用中文回复。

        题目：{essay_title}
        题目分析：{prompt_analysis}

        作文内容：{essay_content}

        四维度分析结果：
        {json.dumps(dimension_results, ensure_ascii=False, indent=2)}

        总分：{overall_score}

        官方评分标准参考：
        {json.dumps(scoring_criteria, ensure_ascii=False, indent=2)}

        请严格按以下JSON格式用中文返回，不要包含任何markdown标记：
        {{
            "overall_comment": "用中文写的综合评语（300-400字，专业详细）",
            "score_breakdown": {{
                "TR_analysis": "TR维度的具体分析和分数说明",
                "CC_analysis": "CC维度的具体分析和分数说明",
                "LR_analysis": "LR维度的具体分析和分数说明",
                "GRA_analysis": "GRA维度的具体分析和分数说明"
            }},
            "key_strengths": ["用中文列出的主要优点1", "用中文列出的主要优点2", "用中文列出的主要优点3"],
            "key_weaknesses": ["用中文列出的主要不足1", "用中文列出的主要不足2", "用中文列出的主要不足3"],
            "priority_improvements": ["用中文写的优先改进建议1", "用中文写的优先改进建议2", "用中文写的优先改进建议3"],
            "score_justification": "用中文写的总分说明，解释为什么是这个分数",
            "band_level_description": "对应分数段的整体表现描述",
            "next_level_requirements": "达到下一个分数段需要改进的具体方面",
            "official_standards_alignment": "与官方标准的对应关系说明"
        }}

        评语要求：
        - 基于官方IELTS评分标准进行专业评价
        - 评语要具体、准确、有建设性
        - 突出最重要的优缺点和改进方向
        - 提供明确的提升路径
        - 体现雅思考官的专业水准
        - 所有内容必须用中文书写
        - 返回纯JSON格式，不要包含```json```标记

        特别注意：
        - 评语应该反映作文在各个维度的真实表现
        - 分数说明要与官方标准描述符对应
        - 改进建议要具体可操作
        - 体现对IELTS写作评分体系的深度理解
        """

        result = await self.generate_text(prompt)

        # 如果API调用失败，提供默认的综合评语
        if not result.get("success", False) or not result.get("text"):
            logger.warning("AI comprehensive comment with standards generation failed, using fallback")
            fallback_comment = self._get_enhanced_fallback_comment(overall_score, dimension_results)
            return {
                "text": fallback_comment,
                "model_used": "enhanced_fallback_system",
                "success": True
            }

        return result

    def _get_enhanced_fallback_comment(self, overall_score: float, dimension_results: Dict) -> str:
        """增强的备用评语生成"""
        # 基于分数生成基础评语
        if overall_score >= 8.0:
            base_comment = "这是一篇优秀的作文，在IELTS写作的四个评分维度都表现出色。"
        elif overall_score >= 7.0:
            base_comment = "这是一篇良好的作文，整体达到了较高的IELTS写作标准。"
        elif overall_score >= 6.0:
            base_comment = "这是一篇中等水平的作文，基本满足IELTS写作要求。"
        elif overall_score >= 5.0:
            base_comment = "这篇作文达到了IELTS写作的基本要求。"
        else:
            base_comment = "这篇作文需要在多个方面进行改进以达到IELTS写作标准。"

        # 添加维度分析
        dimension_comments = []
        for dimension, result in dimension_results.items():
            score = result.get("score", 5.0)
            if score >= 7.0:
                dimension_comments.append(f"{dimension}维度表现良好（{score}分）")
            elif score >= 6.0:
                dimension_comments.append(f"{dimension}维度基本达标（{score}分）")
            else:
                dimension_comments.append(f"{dimension}维度需要改进（{score}分）")

        if dimension_comments:
            base_comment += " 具体来说，" + "，".join(dimension_comments) + "。"

        # 添加改进建议
        base_comment += " 建议重点关注评分较低的维度，通过针对性练习提升整体写作水平。"

        return json.dumps({
            "overall_comment": base_comment,
            "key_strengths": ["基本完成写作任务"],
            "key_weaknesses": ["需要全面提升"],
            "priority_improvements": ["加强练习", "寻求专业指导", "多读范文"],
            "score_justification": f"总分{overall_score}分反映了当前的写作水平"
        }, ensure_ascii=False)

    def _get_fallback_prompt_analysis(self, essay_title: str, task_type: str) -> str:
        """当AI分析失败时的备用题目分析"""
        import json

        # 基于题目关键词的简单分析
        title_lower = essay_title.lower()

        # 判断题型
        essay_type = "discuss_both"  # 默认
        if any(word in title_lower for word in ["agree", "disagree", "opinion", "think"]):
            essay_type = "agree_disagree"
        elif any(word in title_lower for word in ["advantage", "disadvantage", "benefit", "drawback"]):
            essay_type = "advantages_disadvantages"
        elif any(word in title_lower for word in ["problem", "solution", "solve", "issue"]):
            essay_type = "problem_solution"
        elif "?" in essay_title and essay_title.count("?") >= 2:
            essay_type = "two_part_question"

        fallback_data = {
            "essay_type": essay_type,
            "key_instructions": ["分析题目要求", "明确回应所有问题点", "保持逻辑清晰"],
            "question_points": ["根据题目内容回应相关问题点"],
            "required_elements": ["引言段", "主体段落", "结论段"],
            "task_requirements": {
                "minimum_words": 150 if task_type == "task1" else 250,
                "structure_suggestion": "引言-主体-结论的标准结构",
                "key_focus": "确保完整回应题目要求"
            }
        }

        return json.dumps(fallback_data, ensure_ascii=False)

    def _get_fallback_dimension_evaluation(self, dimension: str) -> str:
        """当AI评估失败时的备用维度评估"""
        import json

        fallback_evaluations = {
            "TR": {
                "score": 5.0,
                "strengths": ["基本回应了题目要求"],
                "weaknesses": ["需要更深入的分析和论证"],
                "evidence": ["文章结构基本完整"],
                "suggestions": ["增加具体例子和深入分析", "确保完全回应所有题目要求"]
            },
            "CC": {
                "score": 5.0,
                "strengths": ["文章有基本的段落结构"],
                "weaknesses": ["段落间连接需要改善"],
                "evidence": ["使用了一些基本的连接词"],
                "suggestions": ["增加更多连接词和过渡句", "改善段落间的逻辑流畅性"]
            },
            "LR": {
                "score": 5.0,
                "strengths": ["使用了适当的基础词汇"],
                "weaknesses": ["词汇多样性有待提高"],
                "evidence": ["词汇使用基本准确"],
                "suggestions": ["增加学术词汇的使用", "提高词汇的精确性和多样性"]
            },
            "GRA": {
                "score": 5.0,
                "strengths": ["基本语法结构正确"],
                "weaknesses": ["复杂句型使用不足"],
                "evidence": ["简单句使用较为准确"],
                "suggestions": ["增加复杂句型的使用", "注意语法的准确性"]
            }
        }

        return json.dumps(fallback_evaluations.get(dimension, fallback_evaluations["TR"]), ensure_ascii=False)

    def _get_fallback_overall_comment(self, overall_score: float) -> str:
        """当AI生成综合评语失败时的备用评语"""
        import json

        if overall_score >= 7.0:
            comment_data = {
                "overall_comment": "本文在雅思写作评估中表现良好，基本达到了题目要求。文章结构清晰，论证较为充分，语言使用恰当。建议继续保持优势，并在细节方面进一步完善。",
                "key_strengths": ["文章结构组织良好", "基本回应了题目要求", "语言表达较为流畅"],
                "key_weaknesses": ["部分论证可以更加深入", "词汇使用可以更加多样化", "语法复杂性有提升空间"],
                "priority_improvements": ["增加更多具体例子支撑论点", "使用更丰富的学术词汇", "尝试使用更复杂的句型结构"],
                "score_justification": f"总分{overall_score}分反映了文章在各维度的均衡表现，具备进一步提升的潜力。"
            }
        elif overall_score >= 6.0:
            comment_data = {
                "overall_comment": "本文基本完成了写作任务，具备雅思写作的基本要素。文章有清晰的结构，观点表达基本明确，但在论证深度和语言精确性方面还有改进空间。",
                "key_strengths": ["文章结构基本完整", "观点表达相对清晰", "基本回应了题目要求"],
                "key_weaknesses": ["论证深度不够充分", "词汇和语法的准确性需要提高", "段落间连接可以更加流畅"],
                "priority_improvements": ["深化论证过程，增加具体例子", "提高词汇和语法的准确性", "改善段落间的逻辑连接"],
                "score_justification": f"总分{overall_score}分表明文章达到了基本要求，通过针对性改进可以获得更高分数。"
            }
        else:
            comment_data = {
                "overall_comment": "本文在完成写作任务方面还有较大改进空间。建议重点关注题目要求的完整回应、文章结构的组织以及语言表达的准确性。",
                "key_strengths": ["尝试回应了题目", "有基本的段落划分", "表达了一定的观点"],
                "key_weaknesses": ["题目回应不够完整", "文章结构需要改善", "语言表达的准确性有待提高"],
                "priority_improvements": ["确保完整回应所有题目要求", "改善文章的整体结构和逻辑", "提高语言表达的准确性和流畅性"],
                "score_justification": f"总分{overall_score}分反映了文章在多个维度需要显著改进，建议系统性地提升写作技能。"
            }

        return json.dumps(comment_data, ensure_ascii=False)

    async def analyze_topic_with_comprehensive_data(
        self,
        essay_title: str,
        essay_content: str = ""
    ) -> Dict[str, Any]:
        """基于综合数据进行题型分析"""

        # 获取相关数据
        topic_data = self.data_loader.get_topic_analysis_data()

        # 构建包含丰富数据的提示
        prompt = f"""
        作为雅思写作专家，请基于以下丰富的数据资源对题目进行深度分析。

        题目：{essay_title}
        作文内容：{essay_content}

        参考数据资源：

        1. 题型知识库：
        {json.dumps(topic_data.get('task2_basic_knowledge', {}), ensure_ascii=False, indent=2)}

        2. 指令类型数据：
        {json.dumps(topic_data.get('instruction_types', {}), ensure_ascii=False, indent=2)}

        3. 写作技巧知识：
        {json.dumps(topic_data.get('writing_techniques', {}), ensure_ascii=False, indent=2)}

        请提供详细的题型分析，包括：
        1. 题型识别（参考指令类型数据）
        2. 审题要点（基于题型知识库）
        3. 结构建议（参考写作技巧）
        4. 论证策略（基于知识库中的论证方法）
        5. 常见陷阱和注意事项
        6. 具体的写作指导

        要求：
        - 分析要详细具体，有实际指导价值
        - 参考提供的数据资源中的具体内容
        - 提供可操作的建议
        - 用中文回复，返回JSON格式

        返回格式：
        {{
            "topic_type": "识别的题型",
            "confidence": "识别置信度(0-1)",
            "analysis_details": {{
                "instruction_analysis": "指令分析",
                "key_requirements": ["要求1", "要求2"],
                "structure_recommendation": "结构建议",
                "argument_strategy": "论证策略",
                "common_pitfalls": ["陷阱1", "陷阱2"],
                "writing_guidance": ["指导1", "指导2"]
            }},
            "specific_advice": {{
                "brainstorming_questions": ["问题1", "问题2"],
                "outline_template": {{"段落1": "内容", "段落2": "内容"}},
                "useful_expressions": ["表达1", "表达2"],
                "time_management": "时间分配建议"
            }}
        }}
        """

        result = await self.generate_text(prompt)
        return result

    async def generate_comprehensive_comment_with_data(
        self,
        essay_content: str,
        essay_title: str,
        dimension_results: Dict[str, Any],
        overall_score: float
    ) -> Dict[str, Any]:
        """基于综合数据生成详细评语"""

        # 获取相关数据
        scoring_data = self.data_loader.get_scoring_reference_data()
        vocabulary_data = self.data_loader.get_vocabulary_analysis_data()

        # 查找相关范文
        relevant_essays = self.data_loader.find_relevant_sample_essays(
            topic=essay_title,
            essay_type="task2",
            target_band=overall_score
        )

        prompt = f"""
        作为资深雅思考官，请基于官方评分标准和丰富的参考数据，为以下作文生成专业详细的综合评语。

        题目：{essay_title}
        作文内容：{essay_content}

        评分结果：
        {json.dumps(dimension_results, ensure_ascii=False, indent=2)}
        总分：{overall_score}

        参考数据资源：

        1. 官方评分标准：
        {json.dumps(scoring_data.get('scoring_criteria', {}), ensure_ascii=False, indent=2)}

        2. 相关范文示例：
        {json.dumps(relevant_essays[:2], ensure_ascii=False, indent=2)}

        3. 词汇升级建议：
        {json.dumps(vocabulary_data.get('upgrade_suggestions', {}), ensure_ascii=False, indent=2)}

        请生成包含以下内容的详细评语：
        1. 总体表现评估（对比官方标准）
        2. 各维度详细分析（参考评分标准）
        3. 与范文的对比分析
        4. 具体优势和亮点
        5. 明确的弱点和问题
        6. 详细的改进建议（参考升级建议）
        7. 下一阶段的学习重点
        8. 具体的练习建议

        要求：
        - 评语要专业、详细、有建设性
        - 充分利用提供的参考数据
        - 给出具体可操作的建议
        - 用中文回复，返回JSON格式

        返回格式：
        {{
            "overall_assessment": {{
                "performance_level": "表现水平",
                "band_characteristics": ["特征1", "特征2"],
                "achievement_summary": "成就总结"
            }},
            "dimension_analysis": {{
                "TR": {{"analysis": "分析", "suggestions": ["建议1", "建议2"]}},
                "CC": {{"analysis": "分析", "suggestions": ["建议1", "建议2"]}},
                "LR": {{"analysis": "分析", "suggestions": ["建议1", "建议2"]}},
                "GRA": {{"analysis": "分析", "suggestions": ["建议1", "建议2"]}}
            }},
            "sample_comparison": {{
                "similarities": ["相似点1", "相似点2"],
                "differences": ["差异点1", "差异点2"],
                "learning_points": ["学习点1", "学习点2"]
            }},
            "strengths": ["优势1", "优势2", "优势3"],
            "weaknesses": ["弱点1", "弱点2", "弱点3"],
            "improvement_roadmap": {{
                "immediate_actions": ["行动1", "行动2"],
                "short_term_goals": ["目标1", "目标2"],
                "long_term_objectives": ["目标1", "目标2"]
            }},
            "specific_recommendations": {{
                "vocabulary_improvements": ["建议1", "建议2"],
                "grammar_corrections": ["建议1", "建议2"],
                "structure_enhancements": ["建议1", "建议2"],
                "content_development": ["建议1", "建议2"]
            }},
            "practice_suggestions": {{
                "daily_exercises": ["练习1", "练习2"],
                "weekly_focus": ["重点1", "重点2"],
                "resource_recommendations": ["资源1", "资源2"]
            }}
        }}
        """

        result = await self.generate_text(prompt)
        return result

    async def generate_ultra_detailed_improvements(
        self,
        essay_content: str,
        essay_title: str,
        dimension_scores: Dict[str, float],
        overall_score: float
    ) -> Dict[str, Any]:
        """生成极致详细的改进建议 - 完全覆盖批改文章的所有需要改进的部分"""

        # 1. 执行全面的改进分析
        comprehensive_analysis = comprehensive_improvement_analyzer.analyze_comprehensive_improvements(
            essay_content, essay_title, dimension_scores, overall_score
        )

        # 2. 分句处理
        sentences = comprehensive_improvement_analyzer._split_into_sentences(essay_content)

        # 3. 详细错误检测
        detailed_errors = detailed_error_detector.detect_all_errors(essay_content, sentences)

        # 4. 逐句改进建议
        sentence_improvements = sentence_improvement_generator.generate_sentence_improvements(
            sentences, dimension_scores, overall_score
        )

        # 5. 加载所有数据资源
        all_data_resources = self._load_all_data_resources()
        improvement_templates = self._load_improvement_templates()
        error_patterns = self._load_error_patterns()

        # 6. 构建包含所有数据的超详细提示
        prompt = f"""
        作为世界顶级的雅思写作专家和语言学家，请基于以下极其丰富的分析数据，为这篇作文生成最详细、最全面、最具体的改进建议。

        【作文信息】
        题目：{essay_title}
        作文内容：{essay_content}

        【评分结果】
        各维度分数：{json.dumps(dimension_scores, ensure_ascii=False, indent=2)}
        总分：{overall_score}

        【全面分析结果】
        {json.dumps(comprehensive_analysis, ensure_ascii=False, indent=2)}

        【详细错误检测】
        {json.dumps(detailed_errors, ensure_ascii=False, indent=2)}

        【逐句改进建议】
        {json.dumps([improvement.__dict__ for improvement in sentence_improvements], ensure_ascii=False, indent=2)}

        【改进模板库】
        {json.dumps(improvement_templates, ensure_ascii=False, indent=2)}

        【错误模式数据库】
        {json.dumps(error_patterns, ensure_ascii=False, indent=2)}

        请生成包含以下所有内容的极致详细改进建议：

        1. 【整体改进概览】
        - 文章整体质量评估和改进潜力
        - 主要问题识别和优先级排序
        - 改进路线图和时间规划

        2. 【逐句详细分析和改进】
        - 对每个句子进行详细分析
        - 识别具体错误和问题
        - 提供多个改进版本
        - 解释改进原因和技巧

        3. 【语法错误全面修正】
        - 精确定位所有语法错误
        - 提供具体修正方案
        - 解释语法规则和原理
        - 给出相关练习建议

        4. 【词汇使用深度优化】
        - 识别所有可升级词汇
        - 提供语境适当的替换选项
        - 分析词汇使用的准确性和多样性
        - 推荐学术词汇和高级表达

        5. 【句式结构全面提升】
        - 分析句式复杂度和多样性
        - 提供结构改进建议
        - 示范高级语法结构的使用
        - 优化句子间的逻辑关系

        6. 【段落结构和连贯性优化】
        - 分析段落组织和逻辑流程
        - 改进段落间的过渡和连接
        - 优化论证结构和支撑细节
        - 提升整体连贯性和统一性

        7. 【内容深度和论证强化】
        - 评估论证的完整性和说服力
        - 建议增加或改进的论点和证据
        - 优化例子的相关性和有效性
        - 提升内容的深度和广度

        8. 【学术写作规范完善】
        - 检查和改进学术语调
        - 优化正式性和客观性
        - 规范引用和表述方式
        - 提升整体的专业水准

        9. 【具体修改示例】
        - 提供原句和改进句的对比
        - 详细解释每个修改的原因
        - 展示不同层次的改进选项
        - 给出具体的写作技巧

        10. 【个性化学习计划】
        - 基于具体问题制定学习重点
        - 推荐针对性的练习和资源
        - 设定阶段性的改进目标
        - 提供长期的能力提升建议

        要求：
        - 建议必须极其详细和具体，每个问题都要有明确的解决方案
        - 充分利用提供的所有分析数据和模板资源
        - 给出可直接应用的修改建议和示例
        - 按重要性和影响程度排序所有建议
        - 提供清晰的改进步骤和时间安排
        - 用中文回复，返回JSON格式

        返回格式：
        {{
            "overall_improvement_overview": {{
                "quality_assessment": "整体质量评估",
                "main_issues": ["主要问题1", "主要问题2"],
                "improvement_potential": "改进潜力评估",
                "priority_ranking": ["优先级1", "优先级2"],
                "improvement_roadmap": {{
                    "immediate_actions": ["立即行动1", "立即行动2"],
                    "short_term_goals": ["短期目标1", "短期目标2"],
                    "long_term_objectives": ["长期目标1", "长期目标2"]
                }}
            }},
            "sentence_by_sentence_analysis": [
                {{
                    "sentence_index": 0,
                    "original_sentence": "原句",
                    "identified_issues": ["问题1", "问题2"],
                    "improved_versions": [
                        {{"version": "改进版本1", "explanation": "改进说明1"}},
                        {{"version": "改进版本2", "explanation": "改进说明2"}}
                    ],
                    "specific_techniques": ["技巧1", "技巧2"],
                    "learning_points": ["学习要点1", "学习要点2"]
                }}
            ],
            "grammar_corrections": {{
                "total_errors": 0,
                "error_categories": {{
                    "subject_verb_agreement": [
                        {{
                            "location": "位置",
                            "error": "错误内容",
                            "correction": "修正内容",
                            "explanation": "解释",
                            "rule": "语法规则"
                        }}
                    ]
                }},
                "correction_priorities": ["优先级1", "优先级2"],
                "practice_recommendations": ["练习建议1", "练习建议2"]
            }},
            "vocabulary_optimization": {{
                "upgrade_opportunities": [
                    {{
                        "original_word": "原词",
                        "suggested_replacements": [
                            {{"word": "替换词", "context": "语境", "example": "例句"}}
                        ],
                        "improvement_reason": "改进原因"
                    }}
                ],
                "academic_vocabulary_suggestions": ["学术词汇1", "学术词汇2"],
                "precision_improvements": ["精确性改进1", "精确性改进2"],
                "formality_enhancements": ["正式性提升1", "正式性提升2"]
            }},
            "structure_enhancements": {{
                "sentence_complexity": {{
                    "current_level": "当前水平",
                    "target_level": "目标水平",
                    "improvement_strategies": ["策略1", "策略2"],
                    "example_transformations": [
                        {{"simple": "简单句", "complex": "复杂句", "technique": "技巧"}}
                    ]
                }},
                "paragraph_organization": {{
                    "current_structure": "当前结构",
                    "recommended_structure": "推荐结构",
                    "transition_improvements": ["过渡改进1", "过渡改进2"]
                }}
            }},
            "content_development": {{
                "argument_strength": "论证强度评估",
                "evidence_quality": "证据质量评估",
                "development_suggestions": ["发展建议1", "发展建议2"],
                "example_improvements": ["例子改进1", "例子改进2"]
            }},
            "academic_writing_standards": {{
                "formality_assessment": "正式性评估",
                "objectivity_level": "客观性水平",
                "tone_adjustments": ["语调调整1", "语调调整2"],
                "style_improvements": ["风格改进1", "风格改进2"]
            }},
            "specific_modification_examples": [
                {{
                    "category": "修改类别",
                    "original_text": "原文",
                    "modified_text": "修改文",
                    "explanation": "修改说明",
                    "techniques_used": ["技巧1", "技巧2"]
                }}
            ],
            "personalized_learning_plan": {{
                "immediate_focus": ["立即重点1", "立即重点2"],
                "weekly_goals": [
                    {{"week": 1, "focus": "重点", "exercises": ["练习1", "练习2"]}}
                ],
                "monthly_objectives": ["月目标1", "月目标2"],
                "resource_recommendations": ["资源1", "资源2"],
                "progress_milestones": ["里程碑1", "里程碑2"]
            }}
        }}
        """

        result = await self.generate_text(prompt)
        return result

    def _load_improvement_templates(self) -> Dict[str, Any]:
        """加载改进模板"""
        try:
            with open('data/enhanced_improvement_templates.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load improvement templates: {e}")
            return {}

    def _load_error_patterns(self) -> Dict[str, Any]:
        """加载错误模式"""
        try:
            with open('data/detailed_error_patterns.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load error patterns: {e}")
            return {}

    def _load_all_data_resources(self) -> Dict[str, Any]:
        """加载所有数据资源用于改进建议生成"""
        from .comprehensive_data_loader import comprehensive_data_loader

        try:
            # 获取所有数据资源
            all_data = {
                # 评分标准和范文
                'scoring_data': comprehensive_data_loader.get_scoring_reference_data(),

                # 词汇资源
                'vocabulary_data': comprehensive_data_loader.get_vocabulary_analysis_data(),

                # 语法资源
                'grammar_data': comprehensive_data_loader.get_grammar_analysis_data(),

                # 连贯性资源
                'coherence_data': comprehensive_data_loader.get_coherence_analysis_data(),

                # 改进建议模板
                'improvement_data': comprehensive_data_loader.get_improvement_suggestions_data(),

                # 讲义知识点
                'knowledge_data': {
                    'task2_basic': comprehensive_data_loader.get_data('task2_basic_knowledge'),
                    'writing_techniques': comprehensive_data_loader.get_data('writing_techniques_knowledge'),
                    'argument_construction': comprehensive_data_loader.get_data('argument_construction_knowledge'),
                    'essay_structure': comprehensive_data_loader.get_data('essay_structure_knowledge')
                }
            }

            return all_data

        except Exception as e:
            logger.warning(f"Failed to load comprehensive data resources: {e}")
            return {}

    async def generate_comprehensive_detailed_improvements(
        self,
        essay_content: str,
        essay_title: str,
        dimension_scores: Dict[str, float],
        overall_score: float
    ) -> Dict[str, Any]:
        """生成最全面、最详细的改进建议 - 基于所有数据资源的深度分析"""

        # 1. 加载所有数据资源
        all_data = self._load_all_data_resources()

        # 2. 执行全面分析
        comprehensive_analysis = comprehensive_improvement_analyzer.analyze_comprehensive_improvements(
            essay_content, essay_title, dimension_scores, overall_score
        )

        # 3. 分句处理和详细分析
        sentences = comprehensive_improvement_analyzer._split_into_sentences(essay_content)
        detailed_errors = detailed_error_detector.detect_all_errors(essay_content, sentences)
        sentence_improvements = sentence_improvement_generator.generate_sentence_improvements(
            sentences, dimension_scores, overall_score
        )

        # 4. 查找相关范文
        relevant_samples = comprehensive_data_loader.find_relevant_sample_essays(
            essay_title, "task2", overall_score + 1.0  # 查找更高分数的范文
        )

        # 5. 获取分数段特征
        band_characteristics = comprehensive_data_loader.get_band_specific_examples(overall_score + 1.0)

        # 6. 构建超详细的改进建议提示
        prompt = f"""
        作为世界顶级的雅思写作专家、语言学家和教育学者，请基于以下极其丰富的数据资源和分析结果，为这篇作文生成最详细、最全面、最具体的改进建议。你的建议应该完全覆盖文章的所有需要改进的部分，并且要非常具体、细致，针对文章对每一个可以改进的单词、句子、段落结构、逻辑结构、语法、任务回应给出改进后的结果。

        【作文基本信息】
        题目：{essay_title}
        作文内容：{essay_content}

        【评分结果】
        各维度分数：{json.dumps(dimension_scores, ensure_ascii=False, indent=2)}
        总分：{overall_score}

        【完整数据资源库】
        {json.dumps(all_data, ensure_ascii=False, indent=2)}

        【全面分析结果】
        {json.dumps(comprehensive_analysis, ensure_ascii=False, indent=2)}

        【详细错误检测】
        {json.dumps(detailed_errors, ensure_ascii=False, indent=2)}

        【逐句改进建议】
        {json.dumps([improvement.__dict__ for improvement in sentence_improvements], ensure_ascii=False, indent=2)}

        【相关高分范文】
        {json.dumps(relevant_samples[:3], ensure_ascii=False, indent=2)}

        【目标分数段特征】
        {json.dumps(band_characteristics, ensure_ascii=False, indent=2)}

        请生成包含以下所有内容的极致详细改进建议：

        ## 1. 【整体改进战略】
        - 文章整体质量深度评估
        - 与目标分数段的具体差距分析
        - 改进优先级矩阵（高影响/低难度优先）
        - 详细的改进路线图和时间规划
        - 预期改进效果和分数提升潜力

        ## 2. 【逐句精细分析与改进】
        对每个句子进行显微镜级别的分析：
        - 句子结构分析（简单句/复合句/复杂句）
        - 语法错误精确定位和修正
        - 词汇选择优化（基础词→高级词）
        - 句式复杂度提升建议
        - 逻辑连接和流畅度改进
        - 提供3-5个不同层次的改进版本
        - 详细解释每个修改的原因和技巧

        ## 3. 【语法错误全面诊断与治疗】
        - 系统性语法错误分类和统计
        - 每个错误的精确位置标注
        - 具体修正方案和正确形式
        - 相关语法规则详细解释
        - 类似错误的预防策略
        - 针对性语法练习推荐

        ## 4. 【词汇使用深度优化】
        - 基础词汇升级清单（word by word）
        - 学术词汇和高级表达替换
        - 词汇多样性和准确性分析
        - 主题相关词汇补充建议
        - 搭配和习语使用优化
        - 词汇使用的语境适当性检查

        ## 5. 【句式结构全面升级】
        - 句式复杂度和多样性评估
        - 简单句→复合句→复杂句的升级路径
        - 高级语法结构的具体应用示例
        - 句子间逻辑关系的优化
        - 并列、从属、嵌套结构的平衡使用
        - 句式变化技巧和模板

        ## 6. 【段落结构和连贯性重构】
        - 段落内部逻辑结构分析
        - 主题句、支撑句、结论句的优化
        - 段落间过渡和连接的改进
        - 连贯性设备的恰当使用
        - 整体论证结构的重新组织
        - 信息流和逻辑流的优化

        ## 7. 【内容深度和论证强化】
        - 论点的完整性和说服力评估
        - 论据和例证的相关性和有效性
        - 论证逻辑链条的完善
        - 反驳和让步的适当使用
        - 内容深度和广度的扩展建议
        - 批判性思维的体现方式

        ## 8. 【任务回应完整性检查】
        - 题目要求的逐项对照检查
        - 遗漏要点的识别和补充
        - 观点表达的清晰度和一致性
        - 论证的平衡性和全面性
        - 字数要求和结构要求的满足
        - 题型特定要求的针对性改进

        ## 9. 【学术写作规范完善】
        - 学术语调和正式性检查
        - 客观性和中立性的维持
        - 避免口语化和非正式表达
        - 引用和表述方式的规范化
        - 逻辑标记词的恰当使用
        - 整体专业水准的提升

        ## 10. 【具体修改示例展示】
        提供大量的before/after对比：
        - 原句 → 改进句（多个版本）
        - 详细解释每个修改的原因
        - 展示不同难度层次的改进选项
        - 具体的写作技巧和策略
        - 可直接应用的模板和句型

        ## 11. 【与高分范文对比学习】
        - 与相关高分范文的详细对比
        - 学习高分范文的优秀特征
        - 具体的模仿和借鉴建议
        - 高分表达和结构的移植方法
        - 避免抄袭的创新性改写技巧

        ## 12. 【个性化学习计划】
        - 基于具体问题的学习重点排序
        - 每日、每周、每月的具体练习计划
        - 推荐的学习资源和材料
        - 阶段性目标和检验标准
        - 长期能力提升的系统性建议
        - 自我评估和进步跟踪方法

        要求：
        - 建议必须极其详细和具体，每个问题都要有明确的解决方案
        - 充分利用提供的所有数据资源和分析结果
        - 给出可直接应用的修改建议和具体示例
        - 按重要性和影响程度排序所有建议
        - 提供清晰的改进步骤和实施方法
        - 确保建议的可操作性和实用性
        - 用中文回复，返回JSON格式，不要包含```json```标记

        返回格式必须包含以上所有12个部分的详细内容。
        """

        result = await self.generate_text(prompt)
        return result

    async def generate_sentence_level_detailed_analysis(
        self,
        essay_content: str,
        essay_title: str,
        dimension_scores: Dict[str, float],
        overall_score: float
    ) -> Dict[str, Any]:
        """生成逐句详细分析 - 对每个句子进行深度分析和改进"""

        # 1. 分句处理
        sentences = comprehensive_improvement_analyzer._split_into_sentences(essay_content)

        # 2. 加载相关数据资源
        vocabulary_data = comprehensive_data_loader.get_vocabulary_analysis_data()
        grammar_data = comprehensive_data_loader.get_grammar_analysis_data()

        # 3. 构建逐句分析提示
        prompt = f"""
        作为雅思写作专家，请对以下作文进行逐句详细分析。对每个句子都要提供极其详细的分析和多个改进版本。

        【作文信息】
        题目：{essay_title}
        作文内容：{essay_content}
        当前分数：{overall_score}
        各维度分数：{json.dumps(dimension_scores, ensure_ascii=False)}

        【句子列表】
        {json.dumps([{"index": i, "text": sent["text"]} for i, sent in enumerate(sentences)], ensure_ascii=False, indent=2)}

        【词汇资源】
        {json.dumps(vocabulary_data, ensure_ascii=False, indent=2)}

        【语法资源】
        {json.dumps(grammar_data, ensure_ascii=False, indent=2)}

        请对每个句子进行以下详细分析：

        1. **语法结构分析**
           - 句子类型（简单句/复合句/复杂句）
           - 主谓宾结构分析
           - 从句类型和使用
           - 语法错误识别和修正

        2. **词汇使用分析**
           - 词汇水平评估（基础/中级/高级）
           - 可升级词汇识别
           - 搭配和习语使用
           - 词汇准确性检查

        3. **句式复杂度评估**
           - 当前复杂度评分（1-10）
           - 复杂度提升建议
           - 高级结构使用机会

        4. **清晰度和流畅度**
           - 句子清晰度评估
           - 逻辑连接检查
           - 信息密度分析

        5. **改进版本生成**
           - 基础改进版本（修正错误）
           - 中级改进版本（提升词汇和结构）
           - 高级改进版本（使用复杂结构和高级词汇）
           - 专家级改进版本（接近9分水平）

        6. **具体改进技巧**
           - 使用的具体技巧说明
           - 为什么这样改进
           - 对分数的预期影响

        要求：
        - 对每个句子都要提供完整的分析
        - 改进建议要具体可操作
        - 提供多个不同层次的改进版本
        - 解释每个改进的原因和技巧
        - 用中文回复，返回JSON格式

        返回格式：
        {{
            "sentence_analysis": [
                {{
                    "sentence_index": 0,
                    "original_sentence": "原句",
                    "grammar_analysis": {{
                        "sentence_type": "句子类型",
                        "structure_analysis": "结构分析",
                        "grammar_errors": [
                            {{
                                "error_type": "错误类型",
                                "error_location": "错误位置",
                                "correction": "修正方案",
                                "explanation": "解释"
                            }}
                        ],
                        "grammar_score": "语法评分(1-10)"
                    }},
                    "vocabulary_analysis": {{
                        "vocabulary_level": "词汇水平",
                        "upgradeable_words": [
                            {{
                                "original_word": "原词",
                                "suggested_replacements": ["替换词1", "替换词2"],
                                "reason": "替换原因"
                            }}
                        ],
                        "collocation_issues": ["搭配问题"],
                        "vocabulary_score": "词汇评分(1-10)"
                    }},
                    "complexity_analysis": {{
                        "current_complexity": "当前复杂度(1-10)",
                        "complexity_opportunities": ["复杂度提升机会"],
                        "advanced_structures": ["可使用的高级结构"]
                    }},
                    "clarity_analysis": {{
                        "clarity_score": "清晰度评分(1-10)",
                        "clarity_issues": ["清晰度问题"],
                        "flow_assessment": "流畅度评估"
                    }},
                    "improvement_versions": {{
                        "basic_improvement": {{
                            "text": "基础改进版本",
                            "changes_made": ["改进1", "改进2"],
                            "techniques_used": ["技巧1", "技巧2"]
                        }},
                        "intermediate_improvement": {{
                            "text": "中级改进版本",
                            "changes_made": ["改进1", "改进2"],
                            "techniques_used": ["技巧1", "技巧2"]
                        }},
                        "advanced_improvement": {{
                            "text": "高级改进版本",
                            "changes_made": ["改进1", "改进2"],
                            "techniques_used": ["技巧1", "技巧2"]
                        }},
                        "expert_improvement": {{
                            "text": "专家级改进版本",
                            "changes_made": ["改进1", "改进2"],
                            "techniques_used": ["技巧1", "技巧2"]
                        }}
                    }},
                    "improvement_impact": {{
                        "expected_score_improvement": "预期分数提升",
                        "dimension_impact": {{
                            "TR": "对TR的影响",
                            "CC": "对CC的影响",
                            "LR": "对LR的影响",
                            "GRA": "对GRA的影响"
                        }}
                    }},
                    "learning_points": ["学习要点1", "学习要点2"],
                    "practice_suggestions": ["练习建议1", "练习建议2"]
                }}
            ],
            "overall_sentence_analysis": {{
                "total_sentences": "句子总数",
                "average_complexity": "平均复杂度",
                "main_issues": ["主要问题"],
                "improvement_priorities": ["改进优先级"],
                "expected_overall_improvement": "整体预期改进"
            }}
        }}
        """

        result = await self.generate_text(prompt)
        return result

    async def generate_comprehensive_error_analysis(
        self,
        essay_content: str,
        essay_title: str,
        dimension_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """生成全面的错误分析和修正建议"""

        # 1. 分句处理
        sentences = comprehensive_improvement_analyzer._split_into_sentences(essay_content)

        # 2. 加载错误检测数据
        grammar_data = comprehensive_data_loader.get_grammar_analysis_data()
        vocabulary_data = comprehensive_data_loader.get_vocabulary_analysis_data()

        # 3. 执行详细错误检测
        detailed_errors = detailed_error_detector.detect_all_errors(essay_content, sentences)

        prompt = f"""
        作为雅思写作专家和语言学家，请对以下作文进行全面的错误分析。识别所有类型的错误，并提供详细的修正方案和解释。

        【作文信息】
        题目：{essay_title}
        作文内容：{essay_content}
        各维度分数：{json.dumps(dimension_scores, ensure_ascii=False)}

        【语法数据库】
        {json.dumps(grammar_data, ensure_ascii=False, indent=2)}

        【词汇数据库】
        {json.dumps(vocabulary_data, ensure_ascii=False, indent=2)}

        【检测到的错误】
        {json.dumps(detailed_errors, ensure_ascii=False, indent=2)}

        请进行以下全面的错误分析：

        ## 1. 语法错误分析
        - 主谓一致错误
        - 时态使用错误
        - 语态使用错误
        - 冠词使用错误
        - 介词使用错误
        - 从句结构错误
        - 并列结构错误
        - 修饰语位置错误

        ## 2. 词汇错误分析
        - 词汇选择错误
        - 搭配使用错误
        - 词性使用错误
        - 拼写错误
        - 词汇重复过度
        - 非正式用词
        - 中式英语表达

        ## 3. 句式结构错误
        - 句子不完整
        - 句子过长难懂
        - 逻辑关系不清
        - 句式单调
        - 结构不平衡

        ## 4. 标点符号错误
        - 逗号使用错误
        - 句号使用错误
        - 分号和冒号错误
        - 引号使用错误

        ## 5. 学术写作规范错误
        - 语调不够正式
        - 主观色彩过强
        - 逻辑标记词误用
        - 论证结构不规范

        对每个错误，请提供：
        - 错误的精确位置
        - 错误类型和严重程度
        - 具体的修正方案
        - 详细的解释和规则说明
        - 类似错误的预防方法
        - 相关的练习建议

        要求：
        - 识别所有可能的错误
        - 按严重程度排序
        - 提供多种修正选项
        - 解释每个修正的原因
        - 给出预防策略
        - 用中文回复，返回JSON格式

        返回格式：
        {{
            "error_summary": {{
                "total_errors": "错误总数",
                "error_distribution": {{
                    "grammar_errors": "语法错误数",
                    "vocabulary_errors": "词汇错误数",
                    "structure_errors": "结构错误数",
                    "punctuation_errors": "标点错误数",
                    "academic_writing_errors": "学术写作错误数"
                }},
                "severity_distribution": {{
                    "critical": "严重错误数",
                    "major": "重要错误数",
                    "minor": "轻微错误数"
                }}
            }},
            "detailed_errors": [
                {{
                    "error_id": "错误编号",
                    "error_category": "错误类别",
                    "error_type": "具体错误类型",
                    "severity": "严重程度(critical/major/minor)",
                    "location": {{
                        "sentence_index": "句子索引",
                        "character_start": "字符开始位置",
                        "character_end": "字符结束位置"
                    }},
                    "original_text": "原始错误文本",
                    "error_description": "错误描述",
                    "corrections": [
                        {{
                            "corrected_text": "修正文本",
                            "correction_type": "修正类型",
                            "explanation": "修正解释",
                            "confidence": "修正置信度(1-10)"
                        }}
                    ],
                    "grammar_rule": "相关语法规则",
                    "examples": {{
                        "correct_examples": ["正确示例1", "正确示例2"],
                        "incorrect_examples": ["错误示例1", "错误示例2"]
                    }},
                    "prevention_tips": ["预防建议1", "预防建议2"],
                    "practice_exercises": ["练习建议1", "练习建议2"],
                    "impact_on_score": {{
                        "dimension_affected": "影响的维度",
                        "score_impact": "分数影响程度"
                    }}
                }}
            ],
            "correction_priorities": [
                {{
                    "priority_level": "优先级等级",
                    "error_types": ["错误类型1", "错误类型2"],
                    "reason": "优先原因",
                    "expected_improvement": "预期改进效果"
                }}
            ],
            "systematic_issues": {{
                "recurring_patterns": ["重复出现的错误模式"],
                "root_causes": ["根本原因分析"],
                "systematic_solutions": ["系统性解决方案"]
            }},
            "learning_plan": {{
                "immediate_focus": ["立即关注的错误类型"],
                "weekly_goals": [
                    {{
                        "week": 1,
                        "focus_errors": ["重点错误类型"],
                        "practice_activities": ["练习活动"],
                        "success_metrics": ["成功指标"]
                    }}
                ],
                "long_term_objectives": ["长期目标"],
                "resource_recommendations": ["推荐资源"]
            }}
        }}
        """

        result = await self.generate_text(prompt)
        return result

    async def generate_personalized_learning_plan(
        self,
        essay_content: str,
        essay_title: str,
        dimension_scores: Dict[str, float],
        overall_score: float,
        target_score: float = None
    ) -> Dict[str, Any]:
        """生成个性化学习计划"""

        if target_score is None:
            target_score = min(9.0, overall_score + 1.0)

        # 1. 加载学习资源数据
        all_data = self._load_all_data_resources()

        # 2. 分析当前水平和目标差距
        score_gap = target_score - overall_score

        prompt = f"""
        作为雅思写作教学专家和学习规划师，请基于学生的具体表现和问题，制定一个详细的个性化学习计划。

        【学生当前状况】
        作文题目：{essay_title}
        作文内容：{essay_content}
        当前分数：{overall_score}
        目标分数：{target_score}
        分数差距：{score_gap}
        各维度分数：{json.dumps(dimension_scores, ensure_ascii=False)}

        【完整学习资源】
        {json.dumps(all_data, ensure_ascii=False, indent=2)}

        请制定包含以下内容的详细学习计划：

        ## 1. 学习现状分析
        - 当前写作水平详细评估
        - 各维度优势和劣势分析
        - 与目标分数的具体差距
        - 学习难点和重点识别

        ## 2. 学习目标设定
        - 总体目标和阶段性目标
        - 各维度具体提升目标
        - 时间节点和里程碑
        - 可衡量的成功指标

        ## 3. 详细学习计划
        ### 第1-2周：基础巩固期
        - 每日学习任务（具体到小时）
        - 重点语法规则学习
        - 基础词汇积累
        - 句式结构练习

        ### 第3-4周：技能提升期
        - 写作技巧训练
        - 论证结构优化
        - 高级词汇学习
        - 复杂句式练习

        ### 第5-6周：综合应用期
        - 完整作文练习
        - 时间管理训练
        - 自我评估能力
        - 错误分析总结

        ### 第7-8周：冲刺提高期
        - 模拟考试练习
        - 弱项针对性训练
        - 高分技巧掌握
        - 心理状态调整

        ## 4. 具体练习活动
        - 每日必做练习
        - 每周重点训练
        - 月度综合测试
        - 阶段性评估

        ## 5. 学习资源推荐
        - 教材和参考书
        - 在线学习平台
        - 练习题库
        - 范文分析材料

        ## 6. 进度跟踪方法
        - 学习日志记录
        - 定期自测评估
        - 错误统计分析
        - 进步情况监控

        ## 7. 问题解决策略
        - 常见问题预防
        - 学习困难应对
        - 动机维持方法
        - 效率提升技巧

        要求：
        - 计划要具体可操作
        - 时间安排要合理
        - 难度递进要科学
        - 评估标准要明确
        - 用中文回复，返回JSON格式

        返回格式：
        {{
            "current_analysis": {{
                "writing_level": "当前写作水平",
                "strengths": ["优势1", "优势2"],
                "weaknesses": ["劣势1", "劣势2"],
                "score_gaps": {{
                    "TR": "TR差距分析",
                    "CC": "CC差距分析",
                    "LR": "LR差距分析",
                    "GRA": "GRA差距分析"
                }},
                "learning_priorities": ["学习重点1", "学习重点2"]
            }},
            "learning_objectives": {{
                "overall_goal": "总体目标",
                "dimension_goals": {{
                    "TR": "TR目标",
                    "CC": "CC目标",
                    "LR": "LR目标",
                    "GRA": "GRA目标"
                }},
                "timeline": "学习时间线",
                "milestones": [
                    {{
                        "week": 2,
                        "target": "阶段目标",
                        "success_criteria": ["成功标准1", "成功标准2"]
                    }}
                ]
            }},
            "detailed_plan": {{
                "phase1_foundation": {{
                    "duration": "第1-2周",
                    "focus": "基础巩固",
                    "daily_tasks": [
                        {{
                            "task": "任务描述",
                            "time_required": "所需时间",
                            "materials": ["材料1", "材料2"],
                            "success_metrics": ["成功指标1", "成功指标2"]
                        }}
                    ],
                    "weekly_goals": ["周目标1", "周目标2"],
                    "assessment": "评估方法"
                }},
                "phase2_improvement": {{
                    "duration": "第3-4周",
                    "focus": "技能提升",
                    "daily_tasks": [],
                    "weekly_goals": [],
                    "assessment": "评估方法"
                }},
                "phase3_application": {{
                    "duration": "第5-6周",
                    "focus": "综合应用",
                    "daily_tasks": [],
                    "weekly_goals": [],
                    "assessment": "评估方法"
                }},
                "phase4_mastery": {{
                    "duration": "第7-8周",
                    "focus": "冲刺提高",
                    "daily_tasks": [],
                    "weekly_goals": [],
                    "assessment": "评估方法"
                }}
            }},
            "practice_activities": {{
                "daily_essentials": ["每日必做1", "每日必做2"],
                "weekly_focus": [
                    {{
                        "week": 1,
                        "focus_area": "重点领域",
                        "activities": ["活动1", "活动2"],
                        "time_allocation": "时间分配"
                    }}
                ],
                "monthly_assessments": ["月度评估1", "月度评估2"]
            }},
            "resource_recommendations": {{
                "textbooks": ["教材1", "教材2"],
                "online_platforms": ["平台1", "平台2"],
                "practice_materials": ["材料1", "材料2"],
                "sample_essays": ["范文类型1", "范文类型2"]
            }},
            "progress_tracking": {{
                "daily_logging": ["记录内容1", "记录内容2"],
                "weekly_reviews": ["回顾要点1", "回顾要点2"],
                "monthly_evaluations": ["评估标准1", "评估标准2"],
                "adjustment_triggers": ["调整触发条件1", "调整触发条件2"]
            }},
            "problem_solving": {{
                "common_challenges": [
                    {{
                        "challenge": "常见挑战",
                        "solutions": ["解决方案1", "解决方案2"],
                        "prevention": ["预防措施1", "预防措施2"]
                    }}
                ],
                "motivation_strategies": ["动机策略1", "动机策略2"],
                "efficiency_tips": ["效率技巧1", "效率技巧2"]
            }}
        }}
        """

        result = await self.generate_text(prompt)
        return result

    async def generate_sample_essay_comparison(
        self,
        essay_content: str,
        essay_title: str,
        dimension_scores: Dict[str, float],
        overall_score: float
    ) -> Dict[str, Any]:
        """生成与高分范文的详细对比分析"""

        # 1. 查找相关的高分范文
        relevant_samples = comprehensive_data_loader.find_relevant_sample_essays(
            essay_title, "task2", overall_score + 1.5  # 查找更高分数的范文
        )

        # 2. 获取评分标准
        scoring_data = comprehensive_data_loader.get_scoring_reference_data()

        prompt = f"""
        作为雅思写作专家，请将学生作文与高分范文进行详细对比分析，帮助学生学习高分作文的优秀特征。

        【学生作文】
        题目：{essay_title}
        内容：{essay_content}
        分数：{overall_score}
        各维度：{json.dumps(dimension_scores, ensure_ascii=False)}

        【高分范文】
        {json.dumps(relevant_samples[:2], ensure_ascii=False, indent=2)}

        【评分标准】
        {json.dumps(scoring_data, ensure_ascii=False, indent=2)}

        请进行以下详细对比分析：

        ## 1. 整体结构对比
        - 文章组织结构差异
        - 段落安排和逻辑流程
        - 开头和结尾的处理方式
        - 论证结构的完整性

        ## 2. 任务回应对比
        - 题目理解和回应程度
        - 观点表达的清晰度
        - 论证的全面性和深度
        - 例证的相关性和有效性

        ## 3. 连贯性和衔接对比
        - 段落间的逻辑连接
        - 句子间的衔接处理
        - 连接词的使用技巧
        - 信息的组织和呈现

        ## 4. 词汇使用对比
        - 词汇的丰富性和准确性
        - 学术词汇的使用
        - 词汇搭配的地道性
        - 词汇重复的处理

        ## 5. 语法结构对比
        - 句式的复杂度和多样性
        - 语法的准确性
        - 高级结构的使用
        - 语法错误的对比

        ## 6. 具体学习建议
        - 可以直接借鉴的表达
        - 需要模仿的写作技巧
        - 可以改进的具体方面
        - 避免抄袭的创新方法

        要求：
        - 对比要具体详细
        - 突出高分范文的优势
        - 提供可操作的学习建议
        - 给出具体的改进示例
        - 用中文回复，返回JSON格式

        返回格式：
        {{
            "comparison_overview": {{
                "student_essay_summary": "学生作文总结",
                "sample_essay_summary": "范文总结",
                "main_differences": ["主要差异1", "主要差异2"],
                "learning_opportunities": ["学习机会1", "学习机会2"]
            }},
            "structural_comparison": {{
                "student_structure": {{
                    "organization": "学生作文结构",
                    "paragraph_arrangement": "段落安排",
                    "logical_flow": "逻辑流程"
                }},
                "sample_structure": {{
                    "organization": "范文结构",
                    "paragraph_arrangement": "段落安排",
                    "logical_flow": "逻辑流程"
                }},
                "improvement_suggestions": ["结构改进建议1", "结构改进建议2"]
            }},
            "task_response_comparison": {{
                "student_response": {{
                    "task_understanding": "任务理解程度",
                    "position_clarity": "立场清晰度",
                    "argument_development": "论证发展",
                    "evidence_quality": "证据质量"
                }},
                "sample_response": {{
                    "task_understanding": "任务理解程度",
                    "position_clarity": "立场清晰度",
                    "argument_development": "论证发展",
                    "evidence_quality": "证据质量"
                }},
                "learning_points": ["学习要点1", "学习要点2"]
            }},
            "coherence_comparison": {{
                "student_coherence": {{
                    "paragraph_linking": "段落连接",
                    "sentence_flow": "句子流畅度",
                    "cohesive_devices": "衔接手段"
                }},
                "sample_coherence": {{
                    "paragraph_linking": "段落连接",
                    "sentence_flow": "句子流畅度",
                    "cohesive_devices": "衔接手段"
                }},
                "techniques_to_learn": ["可学习技巧1", "可学习技巧2"]
            }},
            "vocabulary_comparison": {{
                "student_vocabulary": {{
                    "range": "词汇范围",
                    "accuracy": "词汇准确性",
                    "sophistication": "词汇复杂度"
                }},
                "sample_vocabulary": {{
                    "range": "词汇范围",
                    "accuracy": "词汇准确性",
                    "sophistication": "词汇复杂度"
                }},
                "vocabulary_to_learn": [
                    {{
                        "sample_expression": "范文表达",
                        "student_equivalent": "学生对应表达",
                        "improvement_reason": "改进原因",
                        "usage_context": "使用语境"
                    }}
                ]
            }},
            "grammar_comparison": {{
                "student_grammar": {{
                    "complexity": "语法复杂度",
                    "accuracy": "语法准确性",
                    "variety": "句式多样性"
                }},
                "sample_grammar": {{
                    "complexity": "语法复杂度",
                    "accuracy": "语法准确性",
                    "variety": "句式多样性"
                }},
                "structures_to_practice": [
                    {{
                        "structure_type": "结构类型",
                        "sample_example": "范文例子",
                        "practice_suggestion": "练习建议"
                    }}
                ]
            }},
            "specific_learning_actions": {{
                "immediate_improvements": [
                    {{
                        "area": "改进领域",
                        "specific_action": "具体行动",
                        "sample_reference": "范文参考",
                        "practice_method": "练习方法"
                    }}
                ],
                "expressions_to_memorize": ["值得记忆的表达1", "值得记忆的表达2"],
                "techniques_to_practice": ["需要练习的技巧1", "需要练习的技巧2"],
                "patterns_to_follow": ["可遵循的模式1", "可遵循的模式2"]
            }},
            "rewriting_suggestions": {{
                "paragraph_rewrites": [
                    {{
                        "original_paragraph": "原段落",
                        "improved_version": "改进版本",
                        "techniques_used": ["使用技巧1", "使用技巧2"],
                        "sample_inspiration": "范文启发"
                    }}
                ],
                "sentence_improvements": [
                    {{
                        "original_sentence": "原句",
                        "improved_sentence": "改进句",
                        "sample_model": "范文模板",
                        "improvement_explanation": "改进说明"
                    }}
                ]
            }}
        }}
        """

        result = await self.generate_text(prompt)
        return result

    async def generate_complete_improvement_package(
        self,
        essay_content: str,
        essay_title: str,
        dimension_scores: Dict[str, float],
        overall_score: float,
        target_score: float = None
    ) -> Dict[str, Any]:
        """生成完整的改进建议包 - 整合所有详细分析方法"""

        if target_score is None:
            target_score = min(9.0, overall_score + 1.0)

        logger.info(f"Generating complete improvement package for essay: {essay_title}")

        try:
            # 并行执行所有分析方法
            import asyncio

            # 创建所有分析任务
            tasks = [
                self.generate_comprehensive_detailed_improvements(
                    essay_content, essay_title, dimension_scores, overall_score
                ),
                self.generate_sentence_level_detailed_analysis(
                    essay_content, essay_title, dimension_scores, overall_score
                ),
                self.generate_comprehensive_error_analysis(
                    essay_content, essay_title, dimension_scores
                ),
                self.generate_sample_essay_comparison(
                    essay_content, essay_title, dimension_scores, overall_score
                ),
                self.generate_personalized_learning_plan(
                    essay_content, essay_title, dimension_scores, overall_score, target_score
                )
            ]

            # 并行执行所有任务
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果
            comprehensive_improvements = results[0] if not isinstance(results[0], Exception) else {"error": str(results[0])}
            sentence_analysis = results[1] if not isinstance(results[1], Exception) else {"error": str(results[1])}
            error_analysis = results[2] if not isinstance(results[2], Exception) else {"error": str(results[2])}
            sample_comparison = results[3] if not isinstance(results[3], Exception) else {"error": str(results[3])}
            learning_plan = results[4] if not isinstance(results[4], Exception) else {"error": str(results[4])}

            # 整合所有结果
            complete_package = {
                "essay_info": {
                    "title": essay_title,
                    "content": essay_content,
                    "current_score": overall_score,
                    "target_score": target_score,
                    "dimension_scores": dimension_scores,
                    "analysis_timestamp": str(datetime.now())
                },
                "comprehensive_improvements": comprehensive_improvements,
                "sentence_level_analysis": sentence_analysis,
                "error_analysis": error_analysis,
                "sample_comparison": sample_comparison,
                "learning_plan": learning_plan,
                "package_summary": {
                    "total_components": 5,
                    "successful_analyses": sum(1 for r in results if not isinstance(r, Exception)),
                    "failed_analyses": sum(1 for r in results if isinstance(r, Exception)),
                    "completeness_score": (sum(1 for r in results if not isinstance(r, Exception)) / len(results)) * 100
                }
            }

            logger.info(f"Complete improvement package generated successfully. Completeness: {complete_package['package_summary']['completeness_score']:.1f}%")

            return complete_package

        except Exception as e:
            logger.error(f"Error generating complete improvement package: {str(e)}")
            return {
                "error": f"Failed to generate complete improvement package: {str(e)}",
                "essay_info": {
                    "title": essay_title,
                    "current_score": overall_score,
                    "target_score": target_score
                }
            }

# 全局AI客户端实例
ai_client = AIClient()
