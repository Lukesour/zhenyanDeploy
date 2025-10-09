"""
增强的总体评语生成器 - 基于范文数据和评分标准生成详细专业的总体评语
"""

import json
import logging
from typing import Dict, Any, List, Optional
from .comprehensive_data_loader import comprehensive_data_loader

logger = logging.getLogger(__name__)

class EnhancedCommentGenerator:
    """增强的总体评语生成器"""
    
    def __init__(self):
        self.data_loader = comprehensive_data_loader
        
        # 加载评分参考数据
        self.scoring_data = self.data_loader.get_scoring_reference_data()
        self.vocabulary_data = self.data_loader.get_vocabulary_analysis_data()
        self.grammar_data = self.data_loader.get_grammar_analysis_data()
        self.coherence_data = self.data_loader.get_coherence_analysis_data()
    
    def generate_comprehensive_comment(
        self,
        essay_content: str,
        essay_title: str,
        dimension_scores: Dict[str, float],
        overall_score: float,
        essay_type: str = "task2"
    ) -> Dict[str, Any]:
        """生成综合评语"""
        
        comment_data = {
            'overall_assessment': self._generate_overall_assessment(overall_score, dimension_scores),
            'band_comparison': self._generate_band_comparison(overall_score, dimension_scores),
            'dimension_analysis': self._generate_dimension_analysis(dimension_scores, essay_content),
            'strengths_analysis': self._analyze_strengths(essay_content, dimension_scores),
            'weaknesses_analysis': self._analyze_weaknesses(essay_content, dimension_scores),
            'improvement_roadmap': self._generate_improvement_roadmap(dimension_scores, overall_score),
            'sample_comparisons': self._find_sample_comparisons(essay_content, essay_title, overall_score),
            'next_level_requirements': self._get_next_level_requirements(overall_score, dimension_scores),
            'specific_recommendations': self._generate_specific_recommendations(essay_content, dimension_scores),
            'practice_suggestions': self._generate_practice_suggestions(dimension_scores, essay_type)
        }
        
        # 生成最终的综合评语文本
        comment_data['formatted_comment'] = self._format_comprehensive_comment(comment_data)
        
        return comment_data
    
    def _generate_overall_assessment(self, overall_score: float, dimension_scores: Dict[str, float]) -> Dict[str, Any]:
        """生成总体评估"""
        band_level = int(overall_score)
        
        # 获取对应分数段的特征描述
        band_characteristics = self._get_band_characteristics(band_level)
        
        # 分析分数分布
        score_distribution = self._analyze_score_distribution(dimension_scores)
        
        # 确定整体表现水平
        performance_level = self._determine_performance_level(overall_score)
        
        return {
            'overall_score': overall_score,
            'band_level': band_level,
            'performance_level': performance_level,
            'band_characteristics': band_characteristics,
            'score_distribution': score_distribution,
            'consistency_analysis': self._analyze_score_consistency(dimension_scores),
            'achievement_summary': self._generate_achievement_summary(overall_score, dimension_scores)
        }
    
    def _generate_band_comparison(self, overall_score: float, dimension_scores: Dict[str, float]) -> Dict[str, Any]:
        """生成分数段对比"""
        current_band = int(overall_score)
        
        comparison = {
            'current_band_features': self._get_band_features(current_band),
            'higher_band_features': self._get_band_features(current_band + 1) if current_band < 9 else None,
            'lower_band_features': self._get_band_features(current_band - 1) if current_band > 1 else None,
            'gap_analysis': self._analyze_band_gaps(overall_score, dimension_scores),
            'progression_indicators': self._get_progression_indicators(overall_score, dimension_scores)
        }
        
        return comparison
    
    def _generate_dimension_analysis(self, dimension_scores: Dict[str, float], essay_content: str) -> Dict[str, Any]:
        """生成维度分析"""
        analysis = {}
        
        for dimension, score in dimension_scores.items():
            analysis[dimension] = {
                'score': score,
                'band_level': int(score),
                'performance_description': self._get_dimension_performance_description(dimension, score),
                'specific_observations': self._get_dimension_observations(dimension, essay_content, score),
                'improvement_potential': self._assess_improvement_potential(dimension, score),
                'key_requirements': self._get_dimension_requirements(dimension, int(score) + 1)
            }
        
        return analysis
    
    def _analyze_strengths(self, essay_content: str, dimension_scores: Dict[str, float]) -> List[Dict[str, Any]]:
        """分析优势"""
        strengths = []
        
        # 找出表现最好的维度
        best_dimensions = sorted(dimension_scores.items(), key=lambda x: x[1], reverse=True)[:2]
        
        for dimension, score in best_dimensions:
            if score >= 6.0:  # 只分析表现较好的维度
                strength_analysis = {
                    'dimension': dimension,
                    'score': score,
                    'strength_description': self._get_strength_description(dimension, score),
                    'evidence_examples': self._find_strength_evidence(dimension, essay_content),
                    'maintenance_advice': self._get_maintenance_advice(dimension, score)
                }
                strengths.append(strength_analysis)
        
        # 添加整体优势
        overall_strengths = self._identify_overall_strengths(essay_content, dimension_scores)
        strengths.extend(overall_strengths)
        
        return strengths
    
    def _analyze_weaknesses(self, essay_content: str, dimension_scores: Dict[str, float]) -> List[Dict[str, Any]]:
        """分析弱点"""
        weaknesses = []
        
        # 找出表现最差的维度
        weak_dimensions = sorted(dimension_scores.items(), key=lambda x: x[1])[:2]
        
        for dimension, score in weak_dimensions:
            if score < 7.0:  # 分析需要改进的维度
                weakness_analysis = {
                    'dimension': dimension,
                    'score': score,
                    'weakness_description': self._get_weakness_description(dimension, score),
                    'specific_issues': self._identify_specific_issues(dimension, essay_content, score),
                    'impact_analysis': self._analyze_weakness_impact(dimension, score),
                    'priority_level': self._assess_improvement_priority(dimension, score)
                }
                weaknesses.append(weakness_analysis)
        
        return weaknesses
    
    def _generate_improvement_roadmap(self, dimension_scores: Dict[str, float], overall_score: float) -> Dict[str, Any]:
        """生成改进路线图"""
        current_band = int(overall_score)
        target_band = min(current_band + 1, 9)
        
        roadmap = {
            'current_level': current_band,
            'target_level': target_band,
            'priority_dimensions': self._identify_priority_dimensions(dimension_scores),
            'short_term_goals': self._generate_short_term_goals(dimension_scores),
            'medium_term_goals': self._generate_medium_term_goals(dimension_scores, target_band),
            'long_term_goals': self._generate_long_term_goals(target_band),
            'milestone_indicators': self._get_milestone_indicators(dimension_scores, target_band),
            'estimated_timeline': self._estimate_improvement_timeline(dimension_scores, target_band)
        }
        
        return roadmap
    
    def _find_sample_comparisons(self, essay_content: str, essay_title: str, overall_score: float) -> List[Dict[str, Any]]:
        """查找范文对比"""
        # 查找相关范文
        relevant_essays = self.data_loader.find_relevant_sample_essays(
            topic=essay_title,
            essay_type="task2",
            target_band=overall_score
        )
        
        comparisons = []
        for essay in relevant_essays[:3]:  # 最多3篇范文
            comparison = {
                'sample_title': essay.get('title', ''),
                'sample_band': essay.get('band_score', essay.get('score', 0)),
                'comparison_points': self._compare_with_sample(essay_content, essay),
                'learning_points': self._extract_learning_points(essay),
                'applicable_techniques': self._identify_applicable_techniques(essay)
            }
            comparisons.append(comparison)
        
        return comparisons
    
    def _get_next_level_requirements(self, overall_score: float, dimension_scores: Dict[str, float]) -> Dict[str, Any]:
        """获取下一级别要求"""
        next_band = min(int(overall_score) + 1, 9)
        
        requirements = {
            'target_band': next_band,
            'overall_requirements': self._get_band_features(next_band),
            'dimension_requirements': {},
            'key_improvements_needed': [],
            'specific_targets': {}
        }
        
        # 为每个维度设定具体目标
        for dimension, current_score in dimension_scores.items():
            target_score = min(current_score + 0.5, 9.0)
            requirements['dimension_requirements'][dimension] = {
                'current_score': current_score,
                'target_score': target_score,
                'requirements': self._get_dimension_requirements(dimension, int(target_score)),
                'improvement_focus': self._get_improvement_focus(dimension, current_score, target_score)
            }
        
        return requirements
    
    def _generate_specific_recommendations(self, essay_content: str, dimension_scores: Dict[str, float]) -> Dict[str, List[str]]:
        """生成具体建议"""
        recommendations = {
            'immediate_actions': [],
            'study_focus_areas': [],
            'practice_exercises': [],
            'resource_suggestions': []
        }
        
        # 基于最弱的维度生成建议
        weakest_dimension = min(dimension_scores.items(), key=lambda x: x[1])
        dimension_name, score = weakest_dimension
        
        if dimension_name == 'TR':
            recommendations['immediate_actions'].extend([
                '仔细分析题目要求，确保完全理解所有指令',
                '在写作前列出详细大纲，确保涵盖所有要点',
                '每个段落都要有明确的主题句'
            ])
            recommendations['study_focus_areas'].extend([
                '题型识别和审题技巧',
                '论证结构和逻辑展开',
                '观点表达的清晰度'
            ])
        
        elif dimension_name == 'CC':
            recommendations['immediate_actions'].extend([
                '学习和练习使用多样化的连接词',
                '注意段落之间的逻辑关系',
                '使用指代词避免重复'
            ])
            recommendations['study_focus_areas'].extend([
                '连贯性和衔接手段',
                '段落结构组织',
                '逻辑关系表达'
            ])
        
        elif dimension_name == 'LR':
            recommendations['immediate_actions'].extend([
                '扩大学术词汇量，特别是话题相关词汇',
                '学习词汇的准确搭配和用法',
                '避免重复使用相同词汇'
            ])
            recommendations['study_focus_areas'].extend([
                '学术词汇积累',
                '词汇搭配和用法',
                '同义词替换技巧'
            ])
        
        elif dimension_name == 'GRA':
            recommendations['immediate_actions'].extend([
                '练习复杂句式的构造',
                '注意语法准确性，减少基础错误',
                '学习使用多样化的句型结构'
            ])
            recommendations['study_focus_areas'].extend([
                '复杂语法结构',
                '句式多样性',
                '语法准确性'
            ])
        
        return recommendations
    
    def _generate_practice_suggestions(self, dimension_scores: Dict[str, float], essay_type: str) -> List[Dict[str, Any]]:
        """生成练习建议"""
        suggestions = []
        
        # 基于分数生成不同的练习建议
        avg_score = sum(dimension_scores.values()) / len(dimension_scores)
        
        if avg_score < 6.0:
            suggestions.extend([
                {
                    'type': 'foundation_building',
                    'activity': '基础语法和词汇练习',
                    'frequency': '每日30分钟',
                    'focus': '建立扎实的语言基础'
                },
                {
                    'type': 'structure_practice',
                    'activity': '段落结构练习',
                    'frequency': '每周3次',
                    'focus': '掌握基本的文章结构'
                }
            ])
        
        elif avg_score < 7.0:
            suggestions.extend([
                {
                    'type': 'topic_practice',
                    'activity': '分话题写作练习',
                    'frequency': '每周2-3篇',
                    'focus': '提高论证质量和词汇使用'
                },
                {
                    'type': 'model_analysis',
                    'activity': '范文分析和模仿',
                    'frequency': '每周1-2篇',
                    'focus': '学习高分作文的写作技巧'
                }
            ])
        
        else:
            suggestions.extend([
                {
                    'type': 'advanced_practice',
                    'activity': '复杂话题深度分析',
                    'frequency': '每周1-2篇',
                    'focus': '提升论证深度和语言精确性'
                },
                {
                    'type': 'refinement',
                    'activity': '作文修改和完善',
                    'frequency': '每篇作文',
                    'focus': '追求语言的准确性和优雅性'
                }
            ])
        
        return suggestions
    
    def _format_comprehensive_comment(self, comment_data: Dict[str, Any]) -> str:
        """格式化综合评语"""
        overall = comment_data['overall_assessment']
        
        comment_parts = []
        
        # 总体评估
        comment_parts.append(f"## 总体评估\n")
        comment_parts.append(f"您的作文获得了{overall['overall_score']:.1f}分，达到了雅思{overall['band_level']}分水平。")
        comment_parts.append(f"整体表现为{overall['performance_level']}，{overall['achievement_summary']}")
        
        # 维度分析
        comment_parts.append(f"\n## 各维度表现\n")
        dimension_analysis = comment_data['dimension_analysis']
        for dimension, analysis in dimension_analysis.items():
            comment_parts.append(f"**{dimension}维度 ({analysis['score']:.1f}分)**: {analysis['performance_description']}")
        
        # 优势分析
        if comment_data['strengths_analysis']:
            comment_parts.append(f"\n## 主要优势\n")
            for strength in comment_data['strengths_analysis'][:3]:
                comment_parts.append(f"• {strength['strength_description']}")
        
        # 改进建议
        if comment_data['weaknesses_analysis']:
            comment_parts.append(f"\n## 改进重点\n")
            for weakness in comment_data['weaknesses_analysis'][:3]:
                comment_parts.append(f"• {weakness['weakness_description']}")
        
        # 下一步建议
        roadmap = comment_data['improvement_roadmap']
        comment_parts.append(f"\n## 提升建议\n")
        comment_parts.append(f"目标：从{roadmap['current_level']}分提升到{roadmap['target_level']}分")
        
        for goal in roadmap['short_term_goals'][:3]:
            comment_parts.append(f"• {goal}")
        
        return "\n".join(comment_parts)
    
    # 辅助方法实现
    def _get_band_characteristics(self, band_level: int) -> List[str]:
        """获取分数段特征"""
        scoring_criteria = self.scoring_data.get('scoring_criteria', {})
        characteristics = []
        
        band_key = f"band{band_level}"
        for task_type in ['task2']:
            task_data = scoring_criteria.get(task_type, {})
            for dimension in ['TR', 'CC', 'LR', 'GRA']:
                dimension_data = task_data.get(dimension, {})
                band_data = dimension_data.get(band_key, [])
                if isinstance(band_data, list) and band_data:
                    characteristics.extend(band_data[:1])  # 取第一个特征
        
        return characteristics[:4]  # 返回最多4个特征
    
    def _analyze_score_distribution(self, dimension_scores: Dict[str, float]) -> Dict[str, Any]:
        """分析分数分布"""
        scores = list(dimension_scores.values())
        return {
            'highest_score': max(scores),
            'lowest_score': min(scores),
            'score_range': max(scores) - min(scores),
            'balance_level': 'balanced' if max(scores) - min(scores) <= 1.0 else 'unbalanced'
        }
    
    def _determine_performance_level(self, overall_score: float) -> str:
        """确定表现水平"""
        if overall_score >= 8.0:
            return "优秀"
        elif overall_score >= 7.0:
            return "良好"
        elif overall_score >= 6.0:
            return "合格"
        elif overall_score >= 5.0:
            return "基础"
        else:
            return "需要提高"
    
    def _analyze_score_consistency(self, dimension_scores: Dict[str, float]) -> str:
        """分析分数一致性"""
        scores = list(dimension_scores.values())
        score_range = max(scores) - min(scores)
        
        if score_range <= 0.5:
            return "各维度表现非常均衡"
        elif score_range <= 1.0:
            return "各维度表现较为均衡"
        elif score_range <= 1.5:
            return "各维度表现存在一定差异"
        else:
            return "各维度表现差异较大，需要重点关注薄弱环节"
    
    def _generate_achievement_summary(self, overall_score: float, dimension_scores: Dict[str, float]) -> str:
        """生成成就总结"""
        band_level = int(overall_score)
        
        if band_level >= 7:
            return "已经具备了较强的英语写作能力，能够有效地完成学术写作任务。"
        elif band_level >= 6:
            return "具备了基本的英语写作能力，能够完成大部分写作任务，但仍有提升空间。"
        elif band_level >= 5:
            return "写作能力处于发展阶段，能够表达基本观点，但需要在多个方面加强练习。"
        else:
            return "写作能力需要系统性提升，建议加强基础训练。"

    def _get_band_features(self, band_level: int) -> List[str]:
        """获取分数段特征"""
        if band_level <= 0 or band_level > 9:
            return []
        return self._get_band_characteristics(band_level)

    def _analyze_band_gaps(self, overall_score: float, dimension_scores: Dict[str, float]) -> Dict[str, Any]:
        """分析分数段差距"""
        current_band = int(overall_score)
        next_band = min(current_band + 1, 9)

        gaps = {}
        for dimension, score in dimension_scores.items():
            gap_to_next = next_band - score
            gaps[dimension] = {
                'current_score': score,
                'target_score': next_band,
                'gap': gap_to_next,
                'difficulty': 'easy' if gap_to_next <= 0.5 else 'moderate' if gap_to_next <= 1.0 else 'challenging'
            }

        return gaps

    def _get_progression_indicators(self, overall_score: float, dimension_scores: Dict[str, float]) -> List[str]:
        """获取进步指标"""
        indicators = []

        # 分析哪些维度最接近下一个分数段
        next_band = min(int(overall_score) + 1, 9)
        close_dimensions = []

        for dimension, score in dimension_scores.items():
            if score >= next_band - 0.5:
                close_dimensions.append(dimension)

        if close_dimensions:
            indicators.append(f"{', '.join(close_dimensions)}维度已接近{next_band}分水平")

        # 分析整体进步潜力
        avg_score = sum(dimension_scores.values()) / len(dimension_scores)
        if avg_score > overall_score:
            indicators.append("各维度平均分高于总分，具有良好的提升潜力")

        return indicators

    def _get_dimension_performance_description(self, dimension: str, score: float) -> str:
        """获取维度表现描述"""
        band_level = int(score)

        descriptions = {
            'TR': {
                9: "完全回应题目要求，观点清晰深刻，论证充分有力",
                8: "充分回应题目要求，观点明确，论证较为充分",
                7: "回应题目要求，观点相对清晰，论证基本充分",
                6: "基本回应题目要求，观点较为明确，论证有待加强",
                5: "部分回应题目要求，观点不够清晰，论证不够充分",
                4: "回应题目要求不够充分，观点模糊，论证薄弱"
            },
            'CC': {
                9: "文章结构清晰，逻辑严密，连贯性和衔接性极佳",
                8: "文章结构合理，逻辑清晰，连贯性和衔接性良好",
                7: "文章结构基本合理，逻辑较为清晰，连贯性较好",
                6: "文章结构基本清晰，但逻辑和连贯性有待提高",
                5: "文章结构不够清晰，逻辑和连贯性存在问题",
                4: "文章结构混乱，逻辑不清，连贯性差"
            },
            'LR': {
                9: "词汇使用丰富准确，表达自然流畅，用词精确恰当",
                8: "词汇使用较为丰富，表达流畅，用词基本准确",
                7: "词汇使用适当，表达较为流畅，偶有用词不当",
                6: "词汇使用基本适当，但丰富度和准确性有待提高",
                5: "词汇使用有限，表达不够流畅，用词错误较多",
                4: "词汇使用贫乏，表达困难，用词错误频繁"
            },
            'GRA': {
                9: "语法结构复杂多样，使用准确，句式变化丰富",
                8: "语法结构较为复杂，使用基本准确，句式有一定变化",
                7: "语法结构适当，使用较为准确，句式变化适中",
                6: "语法结构基本正确，但复杂性和准确性有待提高",
                5: "语法结构简单，错误较多，句式变化有限",
                4: "语法结构简单，错误频繁，句式单调"
            }
        }

        return descriptions.get(dimension, {}).get(band_level, f"{dimension}维度表现为{band_level}分水平")

    def _get_dimension_observations(self, dimension: str, essay_content: str, score: float) -> List[str]:
        """获取维度观察"""
        observations = []

        # 基于分数和维度生成具体观察
        if dimension == 'TR':
            if score >= 7:
                observations.append("能够明确回应题目要求")
                observations.append("观点表达清晰一致")
            else:
                observations.append("题目回应需要更加充分")
                observations.append("观点表达可以更加明确")

        elif dimension == 'CC':
            if score >= 7:
                observations.append("段落组织合理有序")
                observations.append("连接词使用恰当")
            else:
                observations.append("段落组织需要改进")
                observations.append("连接词使用有待加强")

        elif dimension == 'LR':
            if score >= 7:
                observations.append("词汇使用较为丰富")
                observations.append("用词基本准确恰当")
            else:
                observations.append("词汇丰富度需要提升")
                observations.append("用词准确性有待改进")

        elif dimension == 'GRA':
            if score >= 7:
                observations.append("语法结构使用恰当")
                observations.append("句式有一定变化")
            else:
                observations.append("语法准确性需要提高")
                observations.append("句式变化需要增加")

        return observations

    def _assess_improvement_potential(self, dimension: str, score: float) -> str:
        """评估改进潜力"""
        if score < 5.0:
            return "高潜力 - 通过系统练习可以显著提升"
        elif score < 6.5:
            return "中等潜力 - 通过针对性练习可以稳步提升"
        elif score < 7.5:
            return "适中潜力 - 需要精细化练习来提升"
        else:
            return "需要高质量练习 - 追求卓越需要持续努力"

    def _get_dimension_requirements(self, dimension: str, target_band: int) -> List[str]:
        """获取维度要求"""
        requirements_map = {
            'TR': {
                6: ["基本回应题目所有要求", "观点相对清晰", "有一定的论证支持"],
                7: ["充分回应题目要求", "观点清晰一致", "论证较为充分"],
                8: ["完全回应题目要求", "观点明确深入", "论证充分有力"],
                9: ["完美回应题目要求", "观点深刻独到", "论证严密完整"]
            },
            'CC': {
                6: ["段落组织基本合理", "使用基本连接词", "整体连贯性可接受"],
                7: ["段落组织清晰", "连接词使用恰当", "连贯性良好"],
                8: ["段落组织严密", "连接词使用熟练", "连贯性很好"],
                9: ["段落组织完美", "连接词使用精确", "连贯性极佳"]
            },
            'LR': {
                6: ["词汇使用基本适当", "词汇量适中", "用词基本准确"],
                7: ["词汇使用恰当", "词汇较为丰富", "用词准确性较高"],
                8: ["词汇使用熟练", "词汇丰富多样", "用词准确恰当"],
                9: ["词汇使用精确", "词汇极其丰富", "用词完美恰当"]
            },
            'GRA': {
                6: ["语法基本正确", "句式有一定变化", "错误不影响理解"],
                7: ["语法较为准确", "句式变化适当", "错误较少"],
                8: ["语法准确性高", "句式变化丰富", "错误很少"],
                9: ["语法完全准确", "句式变化极其丰富", "几乎无错误"]
            }
        }

        return requirements_map.get(dimension, {}).get(target_band, [f"{dimension}维度{target_band}分要求"])

    def _get_strength_description(self, dimension: str, score: float) -> str:
        """获取优势描述"""
        band_level = int(score)

        strength_descriptions = {
            'TR': f"任务回应能力强，能够{self._get_dimension_performance_description(dimension, score)}",
            'CC': f"文章连贯性好，{self._get_dimension_performance_description(dimension, score)}",
            'LR': f"词汇运用能力较强，{self._get_dimension_performance_description(dimension, score)}",
            'GRA': f"语法掌握较好，{self._get_dimension_performance_description(dimension, score)}"
        }

        return strength_descriptions.get(dimension, f"{dimension}维度表现优秀")

    def _find_strength_evidence(self, dimension: str, essay_content: str) -> List[str]:
        """找到优势证据"""
        # 这里可以实现更复杂的文本分析来找到具体证据
        evidence = []

        if dimension == 'TR':
            evidence.append("观点表达明确清晰")
            evidence.append("论证结构合理")
        elif dimension == 'CC':
            evidence.append("段落组织有序")
            evidence.append("逻辑连接自然")
        elif dimension == 'LR':
            evidence.append("词汇使用恰当")
            evidence.append("表达多样化")
        elif dimension == 'GRA':
            evidence.append("语法结构正确")
            evidence.append("句式有变化")

        return evidence

    def _get_maintenance_advice(self, dimension: str, score: float) -> str:
        """获取维持建议"""
        return f"继续保持{dimension}维度的优势，可以通过更多练习进一步巩固和提升"

    def _identify_overall_strengths(self, essay_content: str, dimension_scores: Dict[str, float]) -> List[Dict[str, Any]]:
        """识别整体优势"""
        overall_strengths = []

        avg_score = sum(dimension_scores.values()) / len(dimension_scores)

        if avg_score >= 6.5:
            overall_strengths.append({
                'dimension': 'overall',
                'score': avg_score,
                'strength_description': '整体写作水平较高，各维度发展相对均衡',
                'evidence_examples': ['文章结构完整', '内容表达清晰'],
                'maintenance_advice': '继续保持良好的写作习惯，追求更高水平'
            })

        return overall_strengths

    def _get_weakness_description(self, dimension: str, score: float) -> str:
        """获取弱点描述"""
        weakness_descriptions = {
            'TR': f"任务回应需要加强，{self._get_dimension_performance_description(dimension, score)}",
            'CC': f"文章连贯性有待提高，{self._get_dimension_performance_description(dimension, score)}",
            'LR': f"词汇运用需要改进，{self._get_dimension_performance_description(dimension, score)}",
            'GRA': f"语法掌握需要加强，{self._get_dimension_performance_description(dimension, score)}"
        }

        return weakness_descriptions.get(dimension, f"{dimension}维度需要改进")

    def _identify_specific_issues(self, dimension: str, essay_content: str, score: float) -> List[str]:
        """识别具体问题"""
        issues = []

        if dimension == 'TR' and score < 6.5:
            issues.extend([
                "题目回应不够充分",
                "观点表达不够明确",
                "论证展开不够深入"
            ])
        elif dimension == 'CC' and score < 6.5:
            issues.extend([
                "段落组织不够清晰",
                "连接词使用不当或缺乏",
                "逻辑关系不够明确"
            ])
        elif dimension == 'LR' and score < 6.5:
            issues.extend([
                "词汇量有限，重复使用",
                "用词不够准确",
                "缺乏高级词汇"
            ])
        elif dimension == 'GRA' and score < 6.5:
            issues.extend([
                "语法错误较多",
                "句式变化不够",
                "复杂结构使用不当"
            ])

        return issues

    def _analyze_weakness_impact(self, dimension: str, score: float) -> str:
        """分析弱点影响"""
        if score < 5.0:
            return "严重影响整体表现，需要优先改进"
        elif score < 6.0:
            return "明显影响整体分数，建议重点关注"
        elif score < 7.0:
            return "对整体表现有一定影响，可以通过练习改善"
        else:
            return "影响相对较小，但仍有提升空间"

    def _assess_improvement_priority(self, dimension: str, score: float) -> str:
        """评估改进优先级"""
        if score < 5.0:
            return "高优先级"
        elif score < 6.0:
            return "中高优先级"
        elif score < 7.0:
            return "中等优先级"
        else:
            return "低优先级"

    def _identify_priority_dimensions(self, dimension_scores: Dict[str, float]) -> List[str]:
        """识别优先维度"""
        # 按分数排序，分数最低的维度优先级最高
        sorted_dimensions = sorted(dimension_scores.items(), key=lambda x: x[1])
        return [dim for dim, score in sorted_dimensions if score < 7.0]

    def _generate_short_term_goals(self, dimension_scores: Dict[str, float]) -> List[str]:
        """生成短期目标"""
        goals = []

        # 找出最需要改进的维度
        weakest_dimension = min(dimension_scores.items(), key=lambda x: x[1])
        dimension_name, score = weakest_dimension

        if dimension_name == 'TR':
            goals.extend([
                "练习审题技巧，确保完全理解题目要求",
                "学习构建清晰的论证结构",
                "练习观点的明确表达"
            ])
        elif dimension_name == 'CC':
            goals.extend([
                "学习使用多样化的连接词",
                "练习段落内部的逻辑组织",
                "提高文章整体连贯性"
            ])
        elif dimension_name == 'LR':
            goals.extend([
                "扩大词汇量，特别是学术词汇",
                "学习词汇的准确用法和搭配",
                "练习同义词替换技巧"
            ])
        elif dimension_name == 'GRA':
            goals.extend([
                "加强基础语法练习",
                "学习使用复杂句式",
                "提高语法准确性"
            ])

        return goals[:3]  # 返回前3个目标

    def _generate_medium_term_goals(self, dimension_scores: Dict[str, float], target_band: int) -> List[str]:
        """生成中期目标"""
        goals = []

        current_avg = sum(dimension_scores.values()) / len(dimension_scores)

        goals.extend([
            f"将整体写作水平提升到{target_band}分",
            "在所有维度达到相对均衡的表现",
            "掌握高分作文的写作技巧和策略"
        ])

        return goals

    def _generate_long_term_goals(self, target_band: int) -> List[str]:
        """生成长期目标"""
        goals = [
            f"稳定达到{target_band}分以上水平",
            "具备流利准确的学术写作能力",
            "能够应对各种复杂的写作任务"
        ]

        if target_band >= 8:
            goals.append("达到接近母语者的写作水平")

        return goals

    def _get_milestone_indicators(self, dimension_scores: Dict[str, float], target_band: int) -> List[str]:
        """获取里程碑指标"""
        indicators = []

        for dimension, current_score in dimension_scores.items():
            if current_score < target_band:
                indicators.append(f"{dimension}维度达到{target_band}分")

        indicators.append(f"整体分数稳定在{target_band}分以上")

        return indicators

    def _estimate_improvement_timeline(self, dimension_scores: Dict[str, float], target_band: int) -> Dict[str, str]:
        """估算改进时间线"""
        current_avg = sum(dimension_scores.values()) / len(dimension_scores)
        gap = target_band - current_avg

        if gap <= 0.5:
            timeline = "1-2个月"
        elif gap <= 1.0:
            timeline = "3-4个月"
        elif gap <= 1.5:
            timeline = "6-8个月"
        else:
            timeline = "8-12个月"

        return {
            'estimated_time': timeline,
            'factors': '具体时间取决于练习频率和学习方法',
            'recommendation': '建议制定详细的学习计划并坚持执行'
        }

# 创建全局实例
enhanced_comment_generator = EnhancedCommentGenerator()
