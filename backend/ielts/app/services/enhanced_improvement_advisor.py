"""
增强的改进建议系统 - 基于词汇升级建议、语法错误数据库、写作技巧知识生成具体可操作的改进建议
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from .comprehensive_data_loader import comprehensive_data_loader

logger = logging.getLogger(__name__)

class EnhancedImprovementAdvisor:
    """增强的改进建议系统"""
    
    def __init__(self):
        self.data_loader = comprehensive_data_loader
        
        # 加载改进建议相关数据
        self.improvement_data = self.data_loader.get_improvement_suggestions_data()
        self.vocabulary_data = self.data_loader.get_vocabulary_analysis_data()
        self.grammar_data = self.data_loader.get_grammar_analysis_data()
        self.coherence_data = self.data_loader.get_coherence_analysis_data()
    
    def generate_comprehensive_improvements(
        self,
        essay_content: str,
        essay_title: str,
        dimension_scores: Dict[str, float],
        overall_score: float
    ) -> Dict[str, Any]:
        """生成综合改进建议"""
        
        improvements = {
            'vocabulary_improvements': self._generate_vocabulary_improvements(essay_content, dimension_scores.get('LR', 5.0)),
            'grammar_improvements': self._generate_grammar_improvements(essay_content, dimension_scores.get('GRA', 5.0)),
            'structure_improvements': self._generate_structure_improvements(essay_content, dimension_scores.get('CC', 5.0)),
            'content_improvements': self._generate_content_improvements(essay_content, essay_title, dimension_scores.get('TR', 5.0)),
            'specific_replacements': self._suggest_specific_replacements(essay_content),
            'sentence_improvements': self._suggest_sentence_improvements(essay_content),
            'coherence_enhancements': self._suggest_coherence_enhancements(essay_content),
            'advanced_techniques': self._suggest_advanced_techniques(overall_score),
            'practice_exercises': self._generate_targeted_exercises(dimension_scores),
            'priority_ranking': self._rank_improvement_priorities(dimension_scores)
        }
        
        return improvements
    
    def _generate_vocabulary_improvements(self, essay_content: str, lr_score: float) -> Dict[str, Any]:
        """生成词汇改进建议"""
        improvements = {
            'current_level_analysis': self._analyze_vocabulary_level(essay_content, lr_score),
            'upgrade_suggestions': self._find_vocabulary_upgrades(essay_content),
            'topic_vocabulary_gaps': self._identify_topic_vocabulary_gaps(essay_content),
            'academic_word_opportunities': self._find_academic_word_opportunities(essay_content),
            'collocation_improvements': self._suggest_collocation_improvements(essay_content),
            'precision_enhancements': self._suggest_precision_enhancements(essay_content)
        }
        
        return improvements
    
    def _generate_grammar_improvements(self, essay_content: str, gra_score: float) -> Dict[str, Any]:
        """生成语法改进建议"""
        improvements = {
            'error_analysis': self._analyze_grammar_errors(essay_content),
            'complexity_suggestions': self._suggest_complexity_improvements(essay_content, gra_score),
            'sentence_variety': self._analyze_sentence_variety(essay_content),
            'punctuation_improvements': self._suggest_punctuation_improvements(essay_content),
            'tense_consistency': self._check_tense_consistency(essay_content),
            'advanced_structures': self._suggest_advanced_structures(gra_score)
        }
        
        return improvements
    
    def _generate_structure_improvements(self, essay_content: str, cc_score: float) -> Dict[str, Any]:
        """生成结构改进建议"""
        improvements = {
            'paragraph_organization': self._analyze_paragraph_organization(essay_content),
            'linking_improvements': self._suggest_linking_improvements(essay_content),
            'coherence_analysis': self._analyze_coherence_issues(essay_content),
            'flow_enhancements': self._suggest_flow_enhancements(essay_content),
            'transition_improvements': self._suggest_transition_improvements(essay_content),
            'reference_improvements': self._suggest_reference_improvements(essay_content)
        }
        
        return improvements
    
    def _generate_content_improvements(self, essay_content: str, essay_title: str, tr_score: float) -> Dict[str, Any]:
        """生成内容改进建议"""
        improvements = {
            'task_response_analysis': self._analyze_task_response(essay_content, essay_title),
            'argument_strengthening': self._suggest_argument_improvements(essay_content),
            'evidence_enhancements': self._suggest_evidence_improvements(essay_content),
            'depth_improvements': self._suggest_depth_improvements(essay_content, tr_score),
            'relevance_check': self._check_content_relevance(essay_content, essay_title),
            'development_suggestions': self._suggest_development_improvements(essay_content)
        }
        
        return improvements
    
    def _suggest_specific_replacements(self, essay_content: str) -> List[Dict[str, Any]]:
        """建议具体替换"""
        replacements = []
        upgrade_suggestions = self.improvement_data.get('upgrade_suggestions', {})
        
        # 查找常见的简单词汇并建议替换
        common_words = ['good', 'bad', 'big', 'small', 'important', 'very', 'really', 'a lot of']
        
        for word in common_words:
            if word.lower() in essay_content.lower():
                word_suggestions = upgrade_suggestions.get(word, {})
                if 'suggestions' in word_suggestions:
                    for suggestion in word_suggestions['suggestions'][:3]:  # 取前3个建议
                        replacements.append({
                            'original': word,
                            'replacement': suggestion.get('word', ''),
                            'meaning': suggestion.get('meaning', ''),
                            'example': suggestion.get('example', ''),
                            'improvement_type': 'vocabulary_upgrade',
                            'priority': 'high' if word in ['good', 'bad', 'very'] else 'medium'
                        })
        
        return replacements[:10]  # 返回最多10个替换建议
    
    def _suggest_sentence_improvements(self, essay_content: str) -> List[Dict[str, Any]]:
        """建议句子改进"""
        improvements = []
        
        sentences = re.split(r'[.!?]+', essay_content)
        
        for i, sentence in enumerate(sentences[:5]):  # 分析前5个句子
            sentence = sentence.strip()
            if len(sentence) < 10:  # 跳过太短的句子
                continue
            
            # 分析句子长度
            word_count = len(sentence.split())
            if word_count < 8:
                improvements.append({
                    'sentence_number': i + 1,
                    'original': sentence,
                    'issue': '句子过短，缺乏复杂性',
                    'suggestion': '考虑添加从句、修饰语或连接相关观点',
                    'improvement_type': 'sentence_complexity',
                    'priority': 'medium'
                })
            elif word_count > 30:
                improvements.append({
                    'sentence_number': i + 1,
                    'original': sentence,
                    'issue': '句子过长，可能影响清晰度',
                    'suggestion': '考虑分解为两个相关的句子',
                    'improvement_type': 'sentence_clarity',
                    'priority': 'high'
                })
            
            # 检查句子开头的多样性
            first_word = sentence.split()[0].lower() if sentence.split() else ''
            if first_word in ['the', 'this', 'it', 'there']:
                improvements.append({
                    'sentence_number': i + 1,
                    'original': sentence,
                    'issue': '句子开头缺乏变化',
                    'suggestion': '尝试使用不同的句子开头，如副词、介词短语或从句',
                    'improvement_type': 'sentence_variety',
                    'priority': 'low'
                })
        
        return improvements
    
    def _suggest_coherence_enhancements(self, essay_content: str) -> List[Dict[str, Any]]:
        """建议连贯性增强"""
        enhancements = []
        
        # 分析连接词使用
        linking_categories = self.coherence_data.get('cc_linking_categories', {})
        used_links = []
        
        for category, links in linking_categories.items():
            for link in links:
                if link.lower() in essay_content.lower():
                    used_links.append((category, link))
        
        # 建议缺失的连接词类型
        all_categories = set(linking_categories.keys())
        used_categories = set(cat for cat, _ in used_links)
        missing_categories = all_categories - used_categories
        
        for category in missing_categories:
            if category == 'contrast':
                enhancements.append({
                    'type': 'linking_words',
                    'category': category,
                    'suggestion': '考虑添加对比连接词，如 "however", "in contrast", "on the other hand"',
                    'examples': linking_categories[category][:3],
                    'priority': 'high'
                })
            elif category == 'cause_effect':
                enhancements.append({
                    'type': 'linking_words',
                    'category': category,
                    'suggestion': '考虑添加因果关系连接词，如 "therefore", "as a result", "consequently"',
                    'examples': linking_categories[category][:3],
                    'priority': 'medium'
                })
        
        return enhancements
    
    def _suggest_advanced_techniques(self, overall_score: float) -> List[Dict[str, Any]]:
        """建议高级技巧"""
        techniques = []
        
        writing_techniques = self.improvement_data.get('writing_techniques', {})
        
        if overall_score < 6.5:
            # 基础技巧
            techniques.extend([
                {
                    'technique': '5步写作法',
                    'description': '审题 → 立意 → 构思 → 写作 → 检查',
                    'application': '确保每篇作文都按照这个流程进行',
                    'level': 'foundation',
                    'priority': 'high'
                },
                {
                    'technique': '段落结构PEEL',
                    'description': 'Point(观点) → Evidence(证据) → Explanation(解释) → Link(连接)',
                    'application': '每个主体段落都使用这个结构',
                    'level': 'foundation',
                    'priority': 'high'
                }
            ])
        
        elif overall_score < 7.5:
            # 中级技巧
            techniques.extend([
                {
                    'technique': '论证链条延长',
                    'description': '通过因果链条、对比分析、深层原因探讨来丰富论证',
                    'application': '在每个论点后面问"为什么"和"会导致什么"',
                    'level': 'intermediate',
                    'priority': 'high'
                },
                {
                    'technique': '让步反驳',
                    'description': '承认对方观点的合理性，然后提出更强的反驳',
                    'application': '使用"Although...","While it is true that..."等句式',
                    'level': 'intermediate',
                    'priority': 'medium'
                }
            ])
        
        else:
            # 高级技巧
            techniques.extend([
                {
                    'technique': '多角度分析',
                    'description': '从不同利益相关者的角度分析问题',
                    'application': '考虑个人、社会、经济、环境等多个维度',
                    'level': 'advanced',
                    'priority': 'medium'
                },
                {
                    'technique': '修辞手法运用',
                    'description': '适当使用比喻、排比、反问等修辞手法',
                    'application': '在关键论点处使用，增强表达力',
                    'level': 'advanced',
                    'priority': 'low'
                }
            ])
        
        return techniques
    
    def _generate_targeted_exercises(self, dimension_scores: Dict[str, float]) -> Dict[str, List[Dict[str, Any]]]:
        """生成针对性练习"""
        exercises = {
            'daily_practice': [],
            'weekly_focus': [],
            'monthly_goals': []
        }
        
        # 找出最弱的维度
        weakest_dimension = min(dimension_scores.items(), key=lambda x: x[1])
        dimension_name, score = weakest_dimension
        
        if dimension_name == 'TR':
            exercises['daily_practice'].extend([
                {
                    'exercise': '审题练习',
                    'description': '每天分析一个雅思题目，识别题型和关键要求',
                    'time': '15分钟',
                    'frequency': '每日'
                },
                {
                    'exercise': '观点构建',
                    'description': '针对不同话题快速构建2-3个支持观点',
                    'time': '10分钟',
                    'frequency': '每日'
                }
            ])
            
            exercises['weekly_focus'].append({
                'focus': '完整作文练习',
                'description': '每周写2-3篇完整作文，重点关注题目回应',
                'evaluation': '检查是否完全回应了题目要求'
            })
        
        elif dimension_name == 'CC':
            exercises['daily_practice'].extend([
                {
                    'exercise': '连接词练习',
                    'description': '学习并练习使用不同类型的连接词',
                    'time': '10分钟',
                    'frequency': '每日'
                },
                {
                    'exercise': '段落重组',
                    'description': '将打乱的段落重新组织成逻辑清晰的文章',
                    'time': '15分钟',
                    'frequency': '每日'
                }
            ])
        
        elif dimension_name == 'LR':
            exercises['daily_practice'].extend([
                {
                    'exercise': '词汇替换',
                    'description': '每天学习10个新词汇，并练习在句子中使用',
                    'time': '20分钟',
                    'frequency': '每日'
                },
                {
                    'exercise': '搭配练习',
                    'description': '学习常用词汇的搭配用法',
                    'time': '15分钟',
                    'frequency': '每日'
                }
            ])
        
        elif dimension_name == 'GRA':
            exercises['daily_practice'].extend([
                {
                    'exercise': '句型转换',
                    'description': '将简单句改写为复杂句',
                    'time': '15分钟',
                    'frequency': '每日'
                },
                {
                    'exercise': '语法改错',
                    'description': '找出并修正句子中的语法错误',
                    'time': '10分钟',
                    'frequency': '每日'
                }
            ])
        
        return exercises
    
    def _rank_improvement_priorities(self, dimension_scores: Dict[str, float]) -> List[Dict[str, Any]]:
        """排序改进优先级"""
        priorities = []
        
        # 按分数排序维度
        sorted_dimensions = sorted(dimension_scores.items(), key=lambda x: x[1])
        
        for i, (dimension, score) in enumerate(sorted_dimensions):
            priority_level = 'high' if i == 0 else 'medium' if i == 1 else 'low'
            
            priorities.append({
                'dimension': dimension,
                'current_score': score,
                'priority_level': priority_level,
                'improvement_potential': self._calculate_improvement_potential(score),
                'recommended_focus': self._get_dimension_focus(dimension, score),
                'expected_timeline': self._estimate_improvement_time(score)
            })
        
        return priorities

    # 辅助方法实现
    def _analyze_vocabulary_level(self, essay_content: str, lr_score: float) -> Dict[str, Any]:
        """分析词汇水平"""
        words = re.findall(r'\b[a-zA-Z]+\b', essay_content.lower())
        unique_words = set(words)

        # 计算词汇多样性
        vocabulary_diversity = len(unique_words) / len(words) if words else 0

        # 检查学术词汇使用
        academic_words = self.vocabulary_data.get('academic_word_list', {})
        academic_count = 0

        for sublist_key, word_list in academic_words.items():
            if isinstance(word_list, list):
                for word in word_list:
                    if word.lower() in words:
                        academic_count += 1

        return {
            'total_words': len(words),
            'unique_words': len(unique_words),
            'vocabulary_diversity': vocabulary_diversity,
            'academic_words_used': academic_count,
            'level_assessment': self._assess_vocabulary_level(lr_score, vocabulary_diversity, academic_count)
        }

    def _assess_vocabulary_level(self, lr_score: float, diversity: float, academic_count: int) -> str:
        """评估词汇水平"""
        if lr_score >= 7.0 and diversity > 0.6 and academic_count > 10:
            return "词汇水平较高，使用丰富多样"
        elif lr_score >= 6.0 and diversity > 0.5 and academic_count > 5:
            return "词汇水平中等，有一定多样性"
        else:
            return "词汇水平需要提升，建议扩大词汇量"

    def _find_vocabulary_upgrades(self, essay_content: str) -> List[Dict[str, Any]]:
        """查找词汇升级机会"""
        upgrades = []
        upgrade_suggestions = self.improvement_data.get('upgrade_suggestions', {})

        # 查找可以升级的词汇
        for basic_word, upgrade_info in upgrade_suggestions.items():
            if basic_word.lower() in essay_content.lower():
                suggestions = upgrade_info.get('suggestions', [])
                if suggestions:
                    upgrades.append({
                        'basic_word': basic_word,
                        'upgrade_options': suggestions[:3],  # 取前3个选项
                        'comment': upgrade_info.get('comment', ''),
                        'priority': 'high' if basic_word in ['good', 'bad', 'very'] else 'medium'
                    })

        return upgrades[:8]  # 返回最多8个升级建议

    def _identify_topic_vocabulary_gaps(self, essay_content: str) -> List[Dict[str, Any]]:
        """识别主题词汇缺口"""
        gaps = []
        topic_vocabulary = self.vocabulary_data.get('topic_vocabulary', {})

        # 简单的主题识别（基于关键词）
        content_lower = essay_content.lower()

        for topic, vocab_data in topic_vocabulary.items():
            if isinstance(vocab_data, dict) and 'keywords' in vocab_data:
                topic_relevance = 0
                missing_keywords = []

                for keyword in vocab_data['keywords'][:10]:  # 检查前10个关键词
                    if keyword.lower() in content_lower:
                        topic_relevance += 1
                    else:
                        missing_keywords.append(keyword)

                if topic_relevance > 0 and missing_keywords:  # 如果话题相关但缺少关键词
                    gaps.append({
                        'topic': topic,
                        'relevance_score': topic_relevance,
                        'missing_keywords': missing_keywords[:5],  # 最多5个缺失词汇
                        'suggestion': f"考虑在{topic}相关内容中使用这些词汇"
                    })

        return sorted(gaps, key=lambda x: x['relevance_score'], reverse=True)[:3]

    def _find_academic_word_opportunities(self, essay_content: str) -> List[str]:
        """查找学术词汇使用机会"""
        opportunities = []
        academic_words = self.vocabulary_data.get('academic_word_list', {})
        content_lower = essay_content.lower()

        # 检查高频学术词汇的使用
        if 'sublist_1' in academic_words:
            high_frequency_words = academic_words['sublist_1'][:20]  # 前20个高频词

            for word in high_frequency_words:
                if word not in content_lower:
                    opportunities.append(word)

        return opportunities[:10]  # 返回最多10个机会

    def _suggest_collocation_improvements(self, essay_content: str) -> List[Dict[str, Any]]:
        """建议搭配改进"""
        improvements = []
        collocations = self.vocabulary_data.get('collocations_database', {})

        # 这里可以实现更复杂的搭配分析
        # 简化版本：提供一些常见的搭配建议
        common_collocations = [
            {'phrase': 'make a decision', 'instead_of': 'do a decision'},
            {'phrase': 'take responsibility', 'instead_of': 'make responsibility'},
            {'phrase': 'conduct research', 'instead_of': 'make research'},
            {'phrase': 'raise awareness', 'instead_of': 'make awareness'}
        ]

        for collocation in common_collocations:
            improvements.append({
                'correct_collocation': collocation['phrase'],
                'common_mistake': collocation['instead_of'],
                'suggestion': f"使用 '{collocation['phrase']}' 而不是 '{collocation['instead_of']}'"
            })

        return improvements[:5]

    def _suggest_precision_enhancements(self, essay_content: str) -> List[Dict[str, Any]]:
        """建议精确性增强"""
        enhancements = []

        # 查找模糊表达
        vague_expressions = ['things', 'stuff', 'something', 'someone', 'somewhere']

        for expression in vague_expressions:
            if expression in essay_content.lower():
                enhancements.append({
                    'vague_expression': expression,
                    'suggestion': f"将 '{expression}' 替换为更具体的词汇",
                    'examples': self._get_specific_alternatives(expression)
                })

        return enhancements

    def _get_specific_alternatives(self, vague_word: str) -> List[str]:
        """获取具体替代词"""
        alternatives = {
            'things': ['factors', 'elements', 'aspects', 'issues', 'matters'],
            'stuff': ['materials', 'items', 'content', 'information'],
            'something': ['a particular issue', 'a specific matter', 'an important factor'],
            'someone': ['individuals', 'people', 'experts', 'researchers'],
            'somewhere': ['in certain places', 'in specific locations', 'in particular areas']
        }
        return alternatives.get(vague_word, [])

    def _calculate_improvement_potential(self, score: float) -> str:
        """计算改进潜力"""
        if score < 5.0:
            return "很高 - 通过系统学习可以快速提升"
        elif score < 6.0:
            return "高 - 有明显的提升空间"
        elif score < 7.0:
            return "中等 - 需要针对性练习"
        else:
            return "适中 - 需要精细化提升"

    def _get_dimension_focus(self, dimension: str, score: float) -> str:
        """获取维度重点"""
        focus_map = {
            'TR': "加强题目分析和论证展开",
            'CC': "提高文章结构和连贯性",
            'LR': "扩大词汇量和提高用词准确性",
            'GRA': "增强语法复杂性和准确性"
        }
        return focus_map.get(dimension, "全面提升")

    def _estimate_improvement_time(self, score: float) -> str:
        """估算改进时间"""
        if score < 5.0:
            return "2-3个月"
        elif score < 6.0:
            return "3-4个月"
        elif score < 7.0:
            return "4-6个月"
        else:
            return "6-8个月"

# 创建全局实例
enhanced_improvement_advisor = EnhancedImprovementAdvisor()
