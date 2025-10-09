"""
全面的改进建议分析器 - 提供极致详细的文章改进建议
覆盖批改文章的所有需要改进的部分，包括逐句分析、具体错误定位、替换建议等
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from .comprehensive_data_loader import comprehensive_data_loader

logger = logging.getLogger(__name__)

@dataclass
class ErrorLocation:
    """错误位置信息"""
    sentence_index: int
    start_pos: int
    end_pos: int
    error_text: str

@dataclass
class ImprovementSuggestion:
    """改进建议"""
    location: ErrorLocation
    error_type: str
    severity: str  # high, medium, low
    original_text: str
    suggested_text: str
    explanation: str
    examples: List[str]
    impact_on_score: str

class ComprehensiveImprovementAnalyzer:
    """全面的改进建议分析器"""
    
    def __init__(self):
        self.data_loader = comprehensive_data_loader
        
        # 加载所有相关数据
        self.scoring_criteria = self.data_loader.get_scoring_reference_data()
        self.vocabulary_data = self.data_loader.get_vocabulary_analysis_data()
        self.grammar_data = self.data_loader.get_grammar_analysis_data()
        self.coherence_data = self.data_loader.get_coherence_analysis_data()
        self.improvement_data = self.data_loader.get_improvement_suggestions_data()
        
        # 初始化分析器组件
        self._initialize_analyzers()
    
    def _initialize_analyzers(self):
        """初始化各种分析器"""
        self.error_patterns = self._load_error_patterns()
        self.vocabulary_upgrades = self._load_vocabulary_upgrades()
        self.grammar_rules = self._load_grammar_rules()
        self.structure_templates = self._load_structure_templates()
        self.academic_standards = self._load_academic_standards()
    
    def analyze_comprehensive_improvements(
        self,
        essay_content: str,
        essay_title: str,
        dimension_scores: Dict[str, float],
        overall_score: float
    ) -> Dict[str, Any]:
        """生成全面的改进建议分析"""
        
        # 分句处理
        sentences = self._split_into_sentences(essay_content)
        
        # 执行多层次分析
        analysis_result = {
            # 1. 整体文章分析
            'overall_analysis': self._analyze_overall_quality(essay_content, essay_title, overall_score),
            
            # 2. 逐句详细分析
            'sentence_by_sentence_analysis': self._analyze_sentences_detailed(sentences),
            
            # 3. 段落结构分析
            'paragraph_structure_analysis': self._analyze_paragraph_structure(essay_content),
            
            # 4. 语法错误详细检测
            'grammar_error_detection': self._detect_grammar_errors_detailed(sentences),
            
            # 5. 词汇使用深度分析
            'vocabulary_analysis_detailed': self._analyze_vocabulary_detailed(essay_content, sentences),
            
            # 6. 连贯性和衔接分析
            'coherence_cohesion_analysis': self._analyze_coherence_detailed(sentences),
            
            # 7. 论证质量分析
            'argumentation_analysis': self._analyze_argumentation_quality(essay_content, essay_title),
            
            # 8. 学术写作规范检查
            'academic_writing_standards': self._check_academic_standards(essay_content, sentences),
            
            # 9. 具体改进建议生成
            'specific_improvement_suggestions': self._generate_specific_suggestions(sentences, dimension_scores),
            
            # 10. 优先级排序和改进路径
            'improvement_roadmap': self._create_improvement_roadmap(dimension_scores, overall_score),
            
            # 11. 范文对比和学习建议
            'sample_comparison_learning': self._compare_with_samples(essay_content, essay_title, overall_score),
            
            # 12. 个性化练习建议
            'personalized_practice_plan': self._create_practice_plan(dimension_scores, overall_score)
        }
        
        return analysis_result
    
    def _split_into_sentences(self, text: str) -> List[Dict[str, Any]]:
        """将文本分割成句子并添加位置信息"""
        sentences = []
        
        # 使用正则表达式分句
        sentence_pattern = r'[.!?]+\s*'
        parts = re.split(sentence_pattern, text)
        
        current_pos = 0
        for i, sentence in enumerate(parts):
            if sentence.strip():
                sentences.append({
                    'index': i,
                    'text': sentence.strip(),
                    'start_pos': current_pos,
                    'end_pos': current_pos + len(sentence),
                    'word_count': len(sentence.split()),
                    'char_count': len(sentence)
                })
                current_pos += len(sentence) + 1  # +1 for punctuation
        
        return sentences
    
    def _analyze_overall_quality(self, essay_content: str, essay_title: str, overall_score: float) -> Dict[str, Any]:
        """分析整体文章质量"""
        
        word_count = len(essay_content.split())
        char_count = len(essay_content)
        paragraph_count = len([p for p in essay_content.split('\n\n') if p.strip()])
        
        return {
            'basic_statistics': {
                'word_count': word_count,
                'character_count': char_count,
                'paragraph_count': paragraph_count,
                'average_sentence_length': word_count / max(len(self._split_into_sentences(essay_content)), 1),
                'word_count_assessment': self._assess_word_count(word_count),
                'structure_assessment': self._assess_structure(paragraph_count)
            },
            'content_coverage': self._analyze_content_coverage(essay_content, essay_title),
            'writing_style_analysis': self._analyze_writing_style(essay_content),
            'overall_coherence': self._assess_overall_coherence(essay_content),
            'academic_tone': self._assess_academic_tone(essay_content),
            'improvement_potential': self._calculate_improvement_potential(overall_score)
        }
    
    def _analyze_sentences_detailed(self, sentences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """逐句详细分析"""
        detailed_analysis = []
        
        for sentence_info in sentences:
            sentence_text = sentence_info['text']
            
            analysis = {
                'sentence_info': sentence_info,
                'grammar_check': self._check_sentence_grammar(sentence_text),
                'vocabulary_analysis': self._analyze_sentence_vocabulary(sentence_text),
                'structure_analysis': self._analyze_sentence_structure(sentence_text),
                'clarity_assessment': self._assess_sentence_clarity(sentence_text),
                'improvement_suggestions': self._suggest_sentence_improvements(sentence_text),
                'rewritten_versions': self._generate_improved_versions(sentence_text),
                'complexity_score': self._calculate_sentence_complexity(sentence_text),
                'academic_appropriateness': self._assess_academic_appropriateness(sentence_text)
            }
            
            detailed_analysis.append(analysis)
        
        return detailed_analysis
    
    def _analyze_paragraph_structure(self, essay_content: str) -> Dict[str, Any]:
        """分析段落结构"""
        paragraphs = [p.strip() for p in essay_content.split('\n\n') if p.strip()]
        
        paragraph_analysis = []
        for i, paragraph in enumerate(paragraphs):
            analysis = {
                'paragraph_index': i,
                'paragraph_text': paragraph,
                'word_count': len(paragraph.split()),
                'sentence_count': len(self._split_into_sentences(paragraph)),
                'function_analysis': self._identify_paragraph_function(paragraph, i, len(paragraphs)),
                'topic_sentence_analysis': self._analyze_topic_sentence(paragraph),
                'supporting_details': self._analyze_supporting_details(paragraph),
                'transitions': self._analyze_paragraph_transitions(paragraph),
                'coherence_within_paragraph': self._assess_paragraph_coherence(paragraph),
                'improvement_suggestions': self._suggest_paragraph_improvements(paragraph, i)
            }
            paragraph_analysis.append(analysis)
        
        return {
            'paragraph_count': len(paragraphs),
            'paragraph_analysis': paragraph_analysis,
            'overall_structure_assessment': self._assess_overall_structure(paragraphs),
            'transition_effectiveness': self._assess_transition_effectiveness(paragraphs),
            'balance_assessment': self._assess_paragraph_balance(paragraphs)
        }
    
    def _detect_grammar_errors_detailed(self, sentences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """详细的语法错误检测"""
        all_errors = []
        error_categories = {
            'subject_verb_agreement': [],
            'article_errors': [],
            'preposition_errors': [],
            'tense_errors': [],
            'sentence_fragments': [],
            'run_on_sentences': [],
            'punctuation_errors': [],
            'word_order_errors': [],
            'pronoun_errors': [],
            'modifier_errors': []
        }
        
        for sentence_info in sentences:
            sentence_text = sentence_info['text']
            sentence_errors = self._detect_sentence_errors(sentence_text, sentence_info['index'])
            
            for error in sentence_errors:
                all_errors.append(error)
                error_type = error.get('error_type', 'other')
                if error_type in error_categories:
                    error_categories[error_type].append(error)
        
        return {
            'total_errors': len(all_errors),
            'all_errors': all_errors,
            'error_categories': error_categories,
            'error_density': len(all_errors) / max(len(sentences), 1),
            'severity_distribution': self._calculate_severity_distribution(all_errors),
            'most_common_errors': self._identify_most_common_errors(all_errors),
            'correction_priorities': self._prioritize_corrections(all_errors)
        }
    
    def _analyze_vocabulary_detailed(self, essay_content: str, sentences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """详细的词汇分析"""
        words = essay_content.lower().split()
        unique_words = set(words)
        
        return {
            'basic_statistics': {
                'total_words': len(words),
                'unique_words': len(unique_words),
                'vocabulary_diversity': len(unique_words) / len(words) if words else 0,
                'average_word_length': sum(len(word) for word in words) / len(words) if words else 0
            },
            'word_level_analysis': self._analyze_word_levels(words),
            'academic_vocabulary': self._analyze_academic_vocabulary(words),
            'topic_specific_vocabulary': self._analyze_topic_vocabulary(essay_content),
            'collocation_analysis': self._analyze_collocations(essay_content),
            'word_choice_precision': self._analyze_word_precision(sentences),
            'vocabulary_upgrades': self._identify_vocabulary_upgrades(essay_content),
            'overused_words': self._identify_overused_words(words),
            'missing_vocabulary': self._identify_missing_vocabulary(essay_content),
            'formality_assessment': self._assess_vocabulary_formality(words)
        }
    
    def _load_error_patterns(self) -> Dict[str, Any]:
        """加载错误模式"""
        return self.grammar_data.get('common_errors', {})
    
    def _load_vocabulary_upgrades(self) -> Dict[str, Any]:
        """加载词汇升级建议"""
        return self.improvement_data.get('upgrade_suggestions', {})
    
    def _load_grammar_rules(self) -> Dict[str, Any]:
        """加载语法规则"""
        return self.grammar_data.get('complex_structures_library', {})
    
    def _load_structure_templates(self) -> Dict[str, Any]:
        """加载结构模板"""
        return self.coherence_data.get('essay_structures', {})
    
    def _load_academic_standards(self) -> Dict[str, Any]:
        """加载学术写作标准"""
        return self.scoring_criteria.get('scoring_criteria', {})

    def _assess_word_count(self, word_count: int) -> str:
        """评估字数"""
        if word_count < 250:
            return "字数不足，需要增加内容深度和细节"
        elif word_count > 350:
            return "字数过多，建议精简表达，提高简洁性"
        else:
            return "字数适中，符合要求"

    def _assess_structure(self, paragraph_count: int) -> str:
        """评估结构"""
        if paragraph_count < 4:
            return "段落数量不足，建议采用4-5段式结构"
        elif paragraph_count > 6:
            return "段落过多，建议合并相关内容"
        else:
            return "段落结构合理"

    def _analyze_content_coverage(self, essay_content: str, essay_title: str) -> Dict[str, Any]:
        """分析内容覆盖度"""
        # 简化版本的内容覆盖分析
        return {
            'task_response_completeness': "需要更详细的题目分析来评估",
            'argument_development': "需要检查论证的完整性和深度",
            'example_usage': "需要评估例子的相关性和有效性",
            'position_clarity': "需要检查立场的清晰度"
        }

    def _analyze_writing_style(self, essay_content: str) -> Dict[str, Any]:
        """分析写作风格"""
        sentences = self._split_into_sentences(essay_content)
        avg_sentence_length = sum(s['word_count'] for s in sentences) / len(sentences) if sentences else 0

        return {
            'sentence_variety': self._assess_sentence_variety(sentences),
            'average_sentence_length': avg_sentence_length,
            'complexity_level': "中等" if 15 <= avg_sentence_length <= 25 else "需要调整",
            'tone_consistency': "需要检查语调的一致性",
            'formality_level': "需要评估正式程度"
        }

    def _assess_overall_coherence(self, essay_content: str) -> Dict[str, Any]:
        """评估整体连贯性"""
        return {
            'logical_flow': "需要检查逻辑流程",
            'idea_connection': "需要评估观点之间的联系",
            'paragraph_transitions': "需要检查段落间的过渡",
            'overall_unity': "需要评估整体统一性"
        }

    def _assess_academic_tone(self, essay_content: str) -> Dict[str, Any]:
        """评估学术语调"""
        informal_markers = ['I think', 'I believe', 'you know', 'kind of', 'sort of']
        informal_count = sum(1 for marker in informal_markers if marker.lower() in essay_content.lower())

        return {
            'formality_score': max(0, 10 - informal_count * 2),
            'informal_expressions_found': informal_count,
            'objectivity_level': "需要评估客观性程度",
            'academic_vocabulary_usage': "需要评估学术词汇使用"
        }

    def _calculate_improvement_potential(self, overall_score: float) -> Dict[str, Any]:
        """计算改进潜力"""
        if overall_score < 5.0:
            potential = "很高"
            timeline = "2-3个月"
            focus = "基础技能建设"
        elif overall_score < 6.0:
            potential = "高"
            timeline = "3-4个月"
            focus = "技能强化和应用"
        elif overall_score < 7.0:
            potential = "中等"
            timeline = "4-6个月"
            focus = "精细化提升"
        else:
            potential = "适中"
            timeline = "6-8个月"
            focus = "高级技巧掌握"

        return {
            'potential_level': potential,
            'estimated_timeline': timeline,
            'focus_area': focus,
            'next_target_score': min(9.0, overall_score + 0.5)
        }

    def _check_sentence_grammar(self, sentence: str) -> Dict[str, Any]:
        """检查句子语法"""
        errors = []

        # 基础语法检查
        if not sentence.strip().endswith(('.', '!', '?')):
            errors.append({
                'type': 'punctuation',
                'description': '句子缺少结束标点',
                'severity': 'medium'
            })

        # 主谓一致检查（简化版）
        if ' are ' in sentence and any(singular in sentence for singular in ['one of', 'each of', 'every']):
            errors.append({
                'type': 'subject_verb_agreement',
                'description': '可能存在主谓不一致',
                'severity': 'high'
            })

        return {
            'errors_found': len(errors),
            'error_details': errors,
            'grammar_score': max(0, 10 - len(errors) * 2)
        }

    def _analyze_sentence_vocabulary(self, sentence: str) -> Dict[str, Any]:
        """分析句子词汇"""
        words = sentence.lower().split()

        # 检查基础词汇
        basic_words = ['good', 'bad', 'very', 'really', 'a lot of']
        basic_count = sum(1 for word in basic_words if word in sentence.lower())

        return {
            'word_count': len(words),
            'basic_words_count': basic_count,
            'vocabulary_level': 'basic' if basic_count > 2 else 'intermediate',
            'upgrade_opportunities': basic_count
        }

    def _analyze_sentence_structure(self, sentence: str) -> Dict[str, Any]:
        """分析句子结构"""
        # 简化的结构分析
        has_subordinate = any(conj in sentence.lower() for conj in ['because', 'although', 'while', 'since', 'if'])
        has_relative_clause = any(rel in sentence.lower() for rel in ['which', 'that', 'who', 'where'])

        complexity_score = 0
        if has_subordinate:
            complexity_score += 2
        if has_relative_clause:
            complexity_score += 2
        if len(sentence.split(',')) > 2:
            complexity_score += 1

        return {
            'complexity_score': complexity_score,
            'structure_type': 'complex' if complexity_score >= 3 else 'simple',
            'has_subordinate_clause': has_subordinate,
            'has_relative_clause': has_relative_clause,
            'improvement_potential': max(0, 5 - complexity_score)
        }

    def _assess_sentence_clarity(self, sentence: str) -> Dict[str, Any]:
        """评估句子清晰度"""
        word_count = len(sentence.split())

        clarity_issues = []
        if word_count > 30:
            clarity_issues.append("句子过长")

        vague_words = ['things', 'stuff', 'it', 'this', 'that']
        for word in vague_words:
            if f' {word} ' in sentence.lower():
                clarity_issues.append(f"包含模糊词汇: {word}")

        return {
            'clarity_score': max(0, 10 - len(clarity_issues) * 2),
            'clarity_issues': clarity_issues,
            'word_count': word_count,
            'readability': 'good' if len(clarity_issues) == 0 else 'needs improvement'
        }

    def _suggest_sentence_improvements(self, sentence: str) -> List[Dict[str, str]]:
        """建议句子改进"""
        improvements = []

        # 检查基础词汇
        basic_words = ['good', 'bad', 'very', 'really']
        for word in basic_words:
            if word in sentence.lower():
                improvements.append({
                    'type': 'vocabulary_upgrade',
                    'suggestion': f"将'{word}'替换为更学术的词汇",
                    'example': f"例如：{word} → beneficial/effective/significant"
                })

        # 检查句子长度
        if len(sentence.split()) > 25:
            improvements.append({
                'type': 'sentence_length',
                'suggestion': "考虑分割长句以提高可读性",
                'example': "将一个长句分为两个清晰的短句"
            })

        return improvements

    def _generate_improved_versions(self, sentence: str) -> List[str]:
        """生成改进版本"""
        improved_versions = []

        # 简单的改进示例
        if 'good' in sentence.lower():
            improved = sentence.replace('good', 'beneficial').replace('Good', 'Beneficial')
            improved_versions.append(improved)

        if 'bad' in sentence.lower():
            improved = sentence.replace('bad', 'detrimental').replace('Bad', 'Detrimental')
            improved_versions.append(improved)

        if 'very' in sentence.lower():
            improved = sentence.replace('very', 'extremely').replace('Very', 'Extremely')
            improved_versions.append(improved)

        return improved_versions[:3]  # 返回最多3个版本

    def _assess_academic_appropriateness(self, sentence: str) -> Dict[str, Any]:
        """评估学术适当性"""
        informal_markers = ['I think', 'I believe', 'you know', 'kind of']
        informal_count = sum(1 for marker in informal_markers if marker.lower() in sentence.lower())

        return {
            'academic_score': max(0, 10 - informal_count * 3),
            'informal_expressions': informal_count,
            'formality_level': 'high' if informal_count == 0 else 'needs improvement',
            'suggestions': ['使用更正式的表达方式'] if informal_count > 0 else []
        }

    def _identify_paragraph_function(self, paragraph: str, index: int, total_paragraphs: int) -> str:
        """识别段落功能"""
        if index == 0:
            return "introduction"
        elif index == total_paragraphs - 1:
            return "conclusion"
        else:
            return "body_paragraph"

    def _analyze_topic_sentence(self, paragraph: str) -> Dict[str, Any]:
        """分析主题句"""
        sentences = paragraph.split('.')
        first_sentence = sentences[0].strip() if sentences else ""

        return {
            'has_clear_topic_sentence': len(first_sentence) > 10,
            'topic_sentence': first_sentence,
            'clarity': 'clear' if len(first_sentence) > 15 else 'unclear'
        }

    def _analyze_supporting_details(self, paragraph: str) -> Dict[str, Any]:
        """分析支撑细节"""
        sentences = paragraph.split('.')
        detail_count = len([s for s in sentences if len(s.strip()) > 10])

        return {
            'detail_count': detail_count,
            'development_level': 'well_developed' if detail_count >= 3 else 'needs_development',
            'has_examples': 'for example' in paragraph.lower() or 'such as' in paragraph.lower()
        }

    def _analyze_paragraph_transitions(self, paragraph: str) -> List[str]:
        """分析段落过渡"""
        transition_words = ['however', 'furthermore', 'moreover', 'therefore', 'in addition']
        found_transitions = [word for word in transition_words if word in paragraph.lower()]
        return found_transitions

    def _assess_paragraph_coherence(self, paragraph: str) -> Dict[str, Any]:
        """评估段落连贯性"""
        sentences = paragraph.split('.')
        sentence_count = len([s for s in sentences if len(s.strip()) > 5])

        return {
            'coherence_score': min(10, sentence_count * 2),
            'sentence_count': sentence_count,
            'unity': 'good' if sentence_count >= 3 else 'needs_improvement'
        }

    def _suggest_paragraph_improvements(self, paragraph: str, index: int) -> List[str]:
        """建议段落改进"""
        suggestions = []

        if len(paragraph.split('.')) < 3:
            suggestions.append("增加更多支撑句来发展段落")

        if 'for example' not in paragraph.lower() and 'such as' not in paragraph.lower():
            suggestions.append("添加具体例子来支持论点")

        transition_words = ['however', 'furthermore', 'moreover']
        if not any(word in paragraph.lower() for word in transition_words):
            suggestions.append("使用过渡词来改善连贯性")

        return suggestions

    def _assess_overall_structure(self, paragraphs: List[str]) -> Dict[str, Any]:
        """评估整体结构"""
        return {
            'paragraph_count': len(paragraphs),
            'structure_type': 'standard' if len(paragraphs) >= 4 else 'needs_development',
            'balance': 'balanced' if all(len(p.split()) > 50 for p in paragraphs) else 'unbalanced'
        }

    def _assess_transition_effectiveness(self, paragraphs: List[str]) -> Dict[str, Any]:
        """评估过渡有效性"""
        transition_count = 0
        for paragraph in paragraphs[1:]:  # 跳过第一段
            if any(word in paragraph[:50].lower() for word in ['however', 'furthermore', 'moreover']):
                transition_count += 1

        return {
            'transition_score': (transition_count / max(1, len(paragraphs) - 1)) * 10,
            'transitions_found': transition_count,
            'effectiveness': 'good' if transition_count >= len(paragraphs) // 2 else 'needs_improvement'
        }

    def _assess_paragraph_balance(self, paragraphs: List[str]) -> Dict[str, Any]:
        """评估段落平衡"""
        word_counts = [len(p.split()) for p in paragraphs]
        avg_length = sum(word_counts) / len(word_counts) if word_counts else 0

        return {
            'average_length': avg_length,
            'word_counts': word_counts,
            'balance_score': 10 if all(50 <= count <= 150 for count in word_counts) else 5
        }

    def _detect_sentence_errors(self, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """检测句子错误"""
        errors = []

        # 基础语法检查
        if not sentence.strip().endswith(('.', '!', '?')):
            errors.append({
                'type': 'punctuation',
                'description': '句子缺少结束标点',
                'severity': 'medium',
                'suggestion': '添加适当的结束标点'
            })

        # 主谓一致检查
        if 'one of' in sentence.lower() and ' are ' in sentence.lower():
            errors.append({
                'type': 'subject_verb_agreement',
                'description': 'one of结构应该使用单数动词',
                'severity': 'high',
                'suggestion': '将are改为is'
            })

        return errors

    def _calculate_severity_distribution(self, errors: List[Dict[str, Any]]) -> Dict[str, int]:
        """计算错误严重程度分布"""
        distribution = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}

        for error in errors:
            severity = error.get('severity', 'low')
            if severity in distribution:
                distribution[severity] += 1

        return distribution

    def _identify_most_common_errors(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """识别最常见的错误"""
        error_types = {}

        for error in errors:
            error_type = error.get('type', 'unknown')
            if error_type not in error_types:
                error_types[error_type] = {'count': 0, 'examples': []}
            error_types[error_type]['count'] += 1
            error_types[error_type]['examples'].append(error)

        # 按频率排序
        sorted_errors = sorted(error_types.items(), key=lambda x: x[1]['count'], reverse=True)

        return [{'type': error_type, 'count': data['count'], 'examples': data['examples'][:3]}
                for error_type, data in sorted_errors[:5]]

    def _prioritize_corrections(self, errors: List[Dict[str, Any]]) -> List[str]:
        """优先级排序修正建议"""
        priority_map = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}

        # 按严重程度排序
        sorted_errors = sorted(errors, key=lambda x: priority_map.get(x.get('severity', 'low'), 1), reverse=True)

        priorities = []
        for error in sorted_errors[:10]:  # 取前10个最重要的错误
            priorities.append(f"{error.get('type', 'unknown')}: {error.get('description', 'No description')}")

        return priorities

    def _analyze_word_levels(self, words: List[str]) -> Dict[str, Any]:
        """分析词汇水平"""
        basic_words = ['good', 'bad', 'very', 'really', 'big', 'small']
        intermediate_words = ['important', 'significant', 'effective', 'beneficial']
        advanced_words = ['substantial', 'considerable', 'paramount', 'detrimental']

        basic_count = sum(1 for word in words if word.lower() in basic_words)
        intermediate_count = sum(1 for word in words if word.lower() in intermediate_words)
        advanced_count = sum(1 for word in words if word.lower() in advanced_words)

        return {
            'basic_words': basic_count,
            'intermediate_words': intermediate_count,
            'advanced_words': advanced_count,
            'level_distribution': {
                'basic': basic_count,
                'intermediate': intermediate_count,
                'advanced': advanced_count
            }
        }

    def _analyze_academic_vocabulary(self, words: List[str]) -> Dict[str, Any]:
        """分析学术词汇"""
        # 简化的学术词汇列表
        academic_words = ['analyze', 'evaluate', 'demonstrate', 'establish', 'indicate',
                         'significant', 'substantial', 'considerable', 'furthermore', 'moreover']

        academic_count = sum(1 for word in words if word.lower() in academic_words)
        academic_percentage = (academic_count / len(words)) * 100 if words else 0

        return {
            'academic_word_count': academic_count,
            'academic_percentage': academic_percentage,
            'level': 'high' if academic_percentage > 10 else 'medium' if academic_percentage > 5 else 'low'
        }

    def _analyze_topic_vocabulary(self, essay_content: str) -> Dict[str, Any]:
        """分析主题词汇"""
        # 简化的主题词汇分析
        education_words = ['education', 'learning', 'student', 'teacher', 'school', 'university']
        technology_words = ['technology', 'computer', 'internet', 'digital', 'online', 'software']
        environment_words = ['environment', 'pollution', 'climate', 'sustainable', 'green', 'ecology']

        content_lower = essay_content.lower()

        education_count = sum(1 for word in education_words if word in content_lower)
        technology_count = sum(1 for word in technology_words if word in content_lower)
        environment_count = sum(1 for word in environment_words if word in content_lower)

        topic_scores = {
            'education': education_count,
            'technology': technology_count,
            'environment': environment_count
        }

        likely_topic = max(topic_scores, key=topic_scores.get) if max(topic_scores.values()) > 0 else 'general'

        return {
            'likely_topic': likely_topic,
            'topic_scores': topic_scores,
            'topic_vocabulary_density': max(topic_scores.values()) / len(essay_content.split()) * 100
        }

    def _analyze_collocations(self, essay_content: str) -> Dict[str, Any]:
        """分析搭配使用"""
        # 常见错误搭配
        wrong_collocations = ['make research', 'do a decision', 'make a travel']
        correct_collocations = ['conduct research', 'make a decision', 'take a trip']

        collocation_errors = []
        for wrong in wrong_collocations:
            if wrong in essay_content.lower():
                collocation_errors.append(wrong)

        return {
            'collocation_errors': collocation_errors,
            'error_count': len(collocation_errors),
            'suggestions': ['使用正确的动词搭配', '查阅搭配词典', '多读范文学习地道表达']
        }

    def _analyze_word_precision(self, sentences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析词汇精确性"""
        vague_words = ['things', 'stuff', 'something', 'people', 'good', 'bad']
        precision_issues = []

        for sentence_info in sentences:
            sentence_text = sentence_info['text']
            for vague_word in vague_words:
                if vague_word in sentence_text.lower():
                    precision_issues.append({
                        'sentence_index': sentence_info['index'],
                        'vague_word': vague_word,
                        'suggestion': f"将'{vague_word}'替换为更精确的词汇"
                    })

        return {
            'precision_issues': precision_issues,
            'issue_count': len(precision_issues),
            'precision_score': max(0, 10 - len(precision_issues))
        }

    def _identify_vocabulary_upgrades(self, essay_content: str) -> List[Dict[str, Any]]:
        """识别词汇升级机会"""
        upgrade_opportunities = []

        basic_upgrades = {
            'good': ['beneficial', 'effective', 'positive'],
            'bad': ['detrimental', 'harmful', 'negative'],
            'very': ['extremely', 'significantly', 'considerably'],
            'big': ['substantial', 'considerable', 'significant'],
            'small': ['minimal', 'negligible', 'limited']
        }

        for basic_word, alternatives in basic_upgrades.items():
            if basic_word in essay_content.lower():
                upgrade_opportunities.append({
                    'basic_word': basic_word,
                    'alternatives': alternatives,
                    'priority': 'high' if basic_word in ['good', 'bad', 'very'] else 'medium'
                })

        return upgrade_opportunities

    def _identify_overused_words(self, words: List[str]) -> List[Dict[str, Any]]:
        """识别过度使用的词汇"""
        word_counts = {}
        for word in words:
            word_lower = word.lower()
            if len(word_lower) > 3:  # 只统计长度大于3的词
                word_counts[word_lower] = word_counts.get(word_lower, 0) + 1

        # 找出使用频率过高的词汇
        overused = []
        total_words = len(words)

        for word, count in word_counts.items():
            frequency = count / total_words
            if frequency > 0.02 and count > 3:  # 频率超过2%且出现超过3次
                overused.append({
                    'word': word,
                    'count': count,
                    'frequency': frequency,
                    'suggestion': f"考虑使用同义词替换部分'{word}'"
                })

        return sorted(overused, key=lambda x: x['frequency'], reverse=True)[:5]

    def _identify_missing_vocabulary(self, essay_content: str) -> List[str]:
        """识别缺失的词汇"""
        # 根据内容推荐可能有用的词汇
        recommendations = []

        if 'education' in essay_content.lower():
            education_vocab = ['curriculum', 'pedagogy', 'academic', 'scholarly', 'intellectual']
            recommendations.extend(education_vocab)

        if 'technology' in essay_content.lower():
            tech_vocab = ['innovation', 'digital', 'automated', 'sophisticated', 'revolutionary']
            recommendations.extend(tech_vocab)

        return recommendations[:10]  # 返回最多10个建议

    def _assess_vocabulary_formality(self, words: List[str]) -> Dict[str, Any]:
        """评估词汇正式程度"""
        informal_words = ['gonna', 'wanna', 'kinda', 'sorta', 'yeah', 'ok', 'lots of']
        formal_words = ['therefore', 'furthermore', 'consequently', 'nevertheless', 'substantial']

        informal_count = sum(1 for word in words if word.lower() in informal_words)
        formal_count = sum(1 for word in words if word.lower() in formal_words)

        formality_score = max(0, 10 - informal_count * 2 + formal_count)

        return {
            'formality_score': formality_score,
            'informal_words_found': informal_count,
            'formal_words_found': formal_count,
            'level': 'high' if formality_score >= 8 else 'medium' if formality_score >= 5 else 'low'
        }

# 创建全局实例
comprehensive_improvement_analyzer = ComprehensiveImprovementAnalyzer()
