"""
分步骤改进建议服务 - 解决token限制问题
"""

import logging
import json
from typing import Dict, Any, List, Optional
from .ai_client import ai_client
from .comprehensive_data_loader import comprehensive_data_loader

logger = logging.getLogger(__name__)

class StepByStepImprovementService:
    """分步骤改进建议服务"""
    
    def __init__(self):
        self.ai_client = ai_client
        self.data_loader = comprehensive_data_loader
        self.max_tokens_per_call = 10000  # 安全的token限制
    
    def estimate_tokens(self, text: str) -> int:
        """估算文本的token数量"""
        # 简单估算：1 token ≈ 0.75 个英文单词 ≈ 1.5 个中文字符
        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        english_words = len(text.split()) - chinese_chars // 2
        return int(chinese_chars / 1.5 + english_words / 0.75)
    
    async def generate_comprehensive_analysis(
        self,
        essay_content: str,
        essay_title: str,
        dimension_scores: Dict[str, float],
        overall_score: float
    ) -> Dict[str, Any]:
        """生成综合详细改进建议 - 控制token数量"""
        
        # 获取基础评分标准（精简版）
        scoring_data = self.data_loader.get_scoring_reference_data()
        basic_scoring = {
            "TR": scoring_data.get("task_response", {}).get("band_descriptors", {}).get(str(int(dimension_scores.get("TR", 5))), ""),
            "CC": scoring_data.get("coherence_cohesion", {}).get("band_descriptors", {}).get(str(int(dimension_scores.get("CC", 5))), ""),
            "LR": scoring_data.get("lexical_resource", {}).get("band_descriptors", {}).get(str(int(dimension_scores.get("LR", 5))), ""),
            "GRA": scoring_data.get("grammatical_range", {}).get("band_descriptors", {}).get(str(int(dimension_scores.get("GRA", 5))), "")
        }
        
        prompt = f"""
        作为雅思写作专家，请为这篇作文生成详细的综合改进建议。

        【作文信息】
        题目：{essay_title}
        作文内容：{essay_content}
        
        【评分结果】
        TR (任务回应): {dimension_scores.get('TR', 0)}分
        CC (连贯衔接): {dimension_scores.get('CC', 0)}分  
        LR (词汇资源): {dimension_scores.get('LR', 0)}分
        GRA (语法准确): {dimension_scores.get('GRA', 0)}分
        总分: {overall_score}分

        【评分标准参考】
        {json.dumps(basic_scoring, ensure_ascii=False, indent=2)}

        请生成包含以下内容的详细改进建议：

        ## 📋 总体评价
        - 文章整体质量评估
        - 各维度表现分析
        - 主要优点和不足

        ## 🎯 分项详细分析

        ### 1. 任务回应 (Task Response)
        - 当前表现分析
        - 具体问题识别
        - 改进建议和示例

        ### 2. 连贯与衔接 (Coherence and Cohesion)
        - 结构组织评估
        - 逻辑连接分析
        - 具体改进方案

        ### 3. 词汇丰富度 (Lexical Resource)
        - 词汇使用评估
        - 常见错误分析
        - 词汇升级建议

        ### 4. 语法多样性及准确性 (Grammatical Range and Accuracy)
        - 语法错误识别
        - 句式多样性分析
        - 具体修改建议

        ## 📈 优先改进建议
        - 最重要的3-5个改进点
        - 具体实施步骤
        - 预期效果

        请用中文回复，内容要详细具体，针对这篇作文的实际问题。
        """
        
        # 检查token数量
        estimated_tokens = self.estimate_tokens(prompt)
        logger.info(f"Comprehensive analysis prompt tokens: {estimated_tokens}")
        
        if estimated_tokens > self.max_tokens_per_call:
            logger.warning(f"Prompt too long ({estimated_tokens} tokens), truncating essay content")
            # 如果太长，截断作文内容
            max_essay_length = len(essay_content) // 2
            essay_content = essay_content[:max_essay_length] + "..."
            return await self.generate_comprehensive_analysis(essay_content, essay_title, dimension_scores, overall_score)
        
        try:
            result = await self.ai_client.generate_text(prompt)
            return {
                "success": True,
                "text": result.get("text", ""),
                "type": "comprehensive",
                "tokens_used": estimated_tokens
            }
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "type": "comprehensive"
            }
    
    async def generate_sentence_analysis(
        self,
        essay_content: str,
        essay_title: str,
        dimension_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """生成逐句详细分析"""
        
        # 分句处理
        sentences = essay_content.split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 如果句子太多，分批处理
        if len(sentences) > 10:
            sentences = sentences[:10]  # 只分析前10句
        
        prompt = f"""
        作为雅思写作专家，请对以下作文进行逐句详细分析。

        【作文题目】{essay_title}
        
        【句子列表】
        {chr(10).join([f"{i+1}. {sentence}." for i, sentence in enumerate(sentences)])}

        请对每个句子进行以下分析：

        ## 逐句分析

        ### 句子1: "{sentences[0] if sentences else ''}"
        - **语法分析**: 句子结构、时态、主谓一致等
        - **词汇分析**: 用词准确性、词汇层次、搭配等
        - **改进建议**: 具体的修改建议
        - **改进版本**: 提供2-3个改进后的版本

        (请按此格式分析所有句子)

        ## 整体句式建议
        - 句式多样性评估
        - 连接词使用建议
        - 学术写作规范建议

        请用中文回复，分析要具体详细。
        """
        
        estimated_tokens = self.estimate_tokens(prompt)
        logger.info(f"Sentence analysis prompt tokens: {estimated_tokens}")
        
        try:
            result = await self.ai_client.generate_text(prompt)
            return {
                "success": True,
                "text": result.get("text", ""),
                "type": "sentence",
                "sentences_analyzed": len(sentences),
                "tokens_used": estimated_tokens
            }
        except Exception as e:
            logger.error(f"Error in sentence analysis: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "type": "sentence"
            }
    
    async def generate_error_analysis(
        self,
        essay_content: str,
        dimension_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """生成全面错误分析"""
        
        prompt = f"""
        作为雅思写作专家，请对以下作文进行全面的错误分析。

        【作文内容】
        {essay_content}

        【当前分数】
        语法准确性: {dimension_scores.get('GRA', 0)}分
        词汇资源: {dimension_scores.get('LR', 0)}分

        请进行以下错误分析：

        ## 🔍 错误统计概览
        - 语法错误总数
        - 词汇错误总数
        - 结构错误总数
        - 标点错误总数

        ## 📝 详细错误分析

        ### 1. 语法错误
        - 主谓一致错误
        - 动词时态错误
        - 介词使用错误
        - 冠词使用错误
        (每类错误请列出具体例子和修正方案)

        ### 2. 词汇错误
        - 拼写错误
        - 用词不当
        - 搭配错误
        - 词汇重复
        (每类错误请列出具体例子和改进建议)

        ### 3. 句子结构错误
        - 句子片段
        - 流水句
        - 结构混乱
        (请提供具体修改示例)

        ## 🎯 改进优先级
        1. 高优先级错误（影响理解）
        2. 中优先级错误（影响流畅性）
        3. 低优先级错误（影响准确性）

        ## 📚 学习建议
        - 针对性练习建议
        - 学习资源推荐
        - 避免错误的方法

        请用中文回复，要具体指出每个错误的位置和修改方案。
        """
        
        estimated_tokens = self.estimate_tokens(prompt)
        logger.info(f"Error analysis prompt tokens: {estimated_tokens}")
        
        try:
            result = await self.ai_client.generate_text(prompt)
            return {
                "success": True,
                "text": result.get("text", ""),
                "type": "error",
                "tokens_used": estimated_tokens
            }
        except Exception as e:
            logger.error(f"Error in error analysis: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "type": "error"
            }
    
    async def generate_comparison_analysis(
        self,
        essay_content: str,
        essay_title: str,
        overall_score: float
    ) -> Dict[str, Any]:
        """生成范文对比分析"""
        
        # 获取一篇相关范文（简化版）
        sample_essays = self.data_loader.find_relevant_sample_essays(essay_title, "task2", overall_score + 1.5)
        sample_essay = sample_essays[0] if sample_essays else None
        
        if not sample_essay:
            return {
                "success": False,
                "error": "No relevant sample essay found",
                "type": "comparison"
            }
        
        # 只使用范文的部分内容以控制token
        sample_content = sample_essay.get("content", "")[:500] + "..."
        
        prompt = f"""
        作为雅思写作专家，请将学生作文与高分范文进行对比分析。

        【学生作文】
        题目：{essay_title}
        内容：{essay_content}
        分数：{overall_score}

        【高分范文（部分）】
        分数：{sample_essay.get('score', 'N/A')}
        内容：{sample_content}

        请进行以下对比分析：

        ## 📊 整体结构对比
        - 文章组织结构差异
        - 段落安排对比
        - 开头结尾处理方式

        ## 🎯 内容质量对比
        - 论点表达清晰度
        - 论证深度和广度
        - 例证使用效果

        ## 🔗 语言表达对比
        - 词汇使用水平差异
        - 句式复杂度对比
        - 语法准确性对比

        ## 📈 具体学习建议
        - 可以借鉴的表达方式
        - 需要改进的具体方面
        - 提升到高分的关键点

        ## ✍️ 重写建议
        - 针对学生作文的具体重写建议
        - 提供1-2个段落的重写示例

        请用中文回复，对比要具体，建议要可操作。
        """
        
        estimated_tokens = self.estimate_tokens(prompt)
        logger.info(f"Comparison analysis prompt tokens: {estimated_tokens}")
        
        try:
            result = await self.ai_client.generate_text(prompt)
            return {
                "success": True,
                "text": result.get("text", ""),
                "type": "comparison",
                "sample_score": sample_essay.get('score', 'N/A'),
                "tokens_used": estimated_tokens
            }
        except Exception as e:
            logger.error(f"Error in comparison analysis: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "type": "comparison"
            }

    async def generate_learning_plan(
        self,
        essay_title: str,
        dimension_scores: Dict[str, float],
        overall_score: float,
        target_score: float = 7.0
    ) -> Dict[str, Any]:
        """生成个性化学习计划"""

        # 识别最弱的维度
        weakest_dimensions = sorted(dimension_scores.items(), key=lambda x: x[1])[:2]

        prompt = f"""
        作为雅思写作专家，请为学生制定个性化的学习计划。

        【学生现状】
        当前总分：{overall_score}
        目标分数：{target_score}
        各维度分数：
        - TR (任务回应): {dimension_scores.get('TR', 0)}分
        - CC (连贯衔接): {dimension_scores.get('CC', 0)}分
        - LR (词汇资源): {dimension_scores.get('LR', 0)}分
        - GRA (语法准确): {dimension_scores.get('GRA', 0)}分

        【最需要改进的维度】
        {', '.join([f"{dim}: {score}分" for dim, score in weakest_dimensions])}

        请制定以下学习计划：

        ## 🎯 学习目标设定
        - 8周内的具体目标
        - 各维度的提升目标
        - 可达成的分数预期

        ## 📅 8周详细学习计划

        ### 第1-2周：基础强化
        - 每日学习任务
        - 重点练习内容
        - 学习资源推荐

        ### 第3-4周：技能提升
        - 进阶练习内容
        - 写作技巧训练
        - 模拟练习安排

        ### 第5-6周：综合应用
        - 完整作文练习
        - 弱项专项训练
        - 自我评估方法

        ### 第7-8周：考前冲刺
        - 模考安排
        - 查漏补缺
        - 心理准备

        ## 📚 学习资源推荐
        - 推荐书籍和材料
        - 在线资源和工具
        - 练习网站推荐

        ## 📊 进度跟踪方法
        - 每周自测方式
        - 进步评估标准
        - 调整计划的时机

        ## 🔧 常见问题解决
        - 学习中可能遇到的困难
        - 解决方案和应对策略
        - 保持动力的方法

        请用中文回复，计划要具体可执行。
        """

        estimated_tokens = self.estimate_tokens(prompt)
        logger.info(f"Learning plan prompt tokens: {estimated_tokens}")

        try:
            result = await self.ai_client.generate_text(prompt)
            return {
                "success": True,
                "text": result.get("text", ""),
                "type": "learning",
                "current_score": overall_score,
                "target_score": target_score,
                "weakest_dimensions": weakest_dimensions,
                "tokens_used": estimated_tokens
            }
        except Exception as e:
            logger.error(f"Error in learning plan generation: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "type": "learning"
            }

    async def generate_step_by_step_improvements(
        self,
        essay_content: str,
        essay_title: str,
        dimension_scores: Dict[str, float],
        overall_score: float,
        target_score: float = 7.0,
        analysis_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """分步骤生成所有类型的改进建议"""

        if analysis_types is None:
            analysis_types = ["comprehensive", "sentence", "error", "comparison", "learning"]

        results = {
            "essay_info": {
                "title": essay_title,
                "current_score": overall_score,
                "target_score": target_score,
                "dimension_scores": dimension_scores
            },
            "analysis_results": {},
            "generation_summary": {
                "total_steps": len(analysis_types),
                "completed_steps": 0,
                "failed_steps": 0,
                "total_tokens_used": 0
            }
        }

        logger.info(f"Starting step-by-step improvement generation for {len(analysis_types)} types")

        # 按步骤生成不同类型的分析
        for i, analysis_type in enumerate(analysis_types):
            logger.info(f"Step {i+1}/{len(analysis_types)}: Generating {analysis_type} analysis")

            try:
                if analysis_type == "comprehensive":
                    result = await self.generate_comprehensive_analysis(
                        essay_content, essay_title, dimension_scores, overall_score
                    )
                elif analysis_type == "sentence":
                    result = await self.generate_sentence_analysis(
                        essay_content, essay_title, dimension_scores
                    )
                elif analysis_type == "error":
                    result = await self.generate_error_analysis(
                        essay_content, dimension_scores
                    )
                elif analysis_type == "comparison":
                    result = await self.generate_comparison_analysis(
                        essay_content, essay_title, overall_score
                    )
                elif analysis_type == "learning":
                    result = await self.generate_learning_plan(
                        essay_title, dimension_scores, overall_score, target_score
                    )
                else:
                    result = {
                        "success": False,
                        "error": f"Unknown analysis type: {analysis_type}",
                        "type": analysis_type
                    }

                results["analysis_results"][analysis_type] = result

                if result.get("success", False):
                    results["generation_summary"]["completed_steps"] += 1
                    results["generation_summary"]["total_tokens_used"] += result.get("tokens_used", 0)
                    logger.info(f"Step {i+1} ({analysis_type}) completed successfully")
                else:
                    results["generation_summary"]["failed_steps"] += 1
                    logger.warning(f"Step {i+1} ({analysis_type}) failed: {result.get('error', 'Unknown error')}")

            except Exception as e:
                logger.error(f"Error in step {i+1} ({analysis_type}): {str(e)}")
                results["analysis_results"][analysis_type] = {
                    "success": False,
                    "error": str(e),
                    "type": analysis_type
                }
                results["generation_summary"]["failed_steps"] += 1

        # 计算成功率
        total_steps = results["generation_summary"]["total_steps"]
        completed_steps = results["generation_summary"]["completed_steps"]
        results["generation_summary"]["success_rate"] = completed_steps / total_steps if total_steps > 0 else 0

        logger.info(f"Step-by-step generation completed: {completed_steps}/{total_steps} successful")

        return {
            "success": completed_steps > 0,  # 至少有一个步骤成功
            "data": results,
            "message": f"Generated {completed_steps} out of {total_steps} analysis types"
        }

# 创建全局服务实例
step_by_step_improvement_service = StepByStepImprovementService()
