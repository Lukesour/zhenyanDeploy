"""
逐句改进建议生成系统 - 对每个句子提供具体的改进建议
包括语法修正、词汇升级、表达优化等
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from .comprehensive_data_loader import comprehensive_data_loader
from .detailed_error_detector import detailed_error_detector

logger = logging.getLogger(__name__)

@dataclass
class SentenceImprovement:
    """句子改进建议"""
    sentence_index: int
    original_sentence: str
    improved_versions: List[str]
    improvement_type: str  # grammar, vocabulary, structure, clarity, style
    improvement_explanation: str
    specific_changes: List[Dict[str, str]]
    difficulty_level: str  # basic, intermediate, advanced
    impact_on_score: str
    learning_focus: List[str]

class SentenceImprovementGenerator:
    """逐句改进建议生成器"""
    
    def __init__(self):
        self.data_loader = comprehensive_data_loader
        self.error_detector = detailed_error_detector
        
        # 加载改进相关数据
        self.vocabulary_upgrades = self._load_vocabulary_upgrades()
        self.grammar_structures = self._load_grammar_structures()
        self.sentence_patterns = self._load_sentence_patterns()
        self.academic_expressions = self._load_academic_expressions()
        
        # 初始化改进生成器
        self._initialize_generators()
    
    def _load_vocabulary_upgrades(self) -> Dict[str, Any]:
        """加载词汇升级数据"""
        vocab_data = self.data_loader.get_vocabulary_analysis_data()
        return vocab_data.get('upgrade_suggestions', {})
    
    def _load_grammar_structures(self) -> Dict[str, Any]:
        """加载语法结构数据"""
        grammar_data = self.data_loader.get_grammar_analysis_data()
        return grammar_data.get('complex_structures_library', {})
    
    def _load_sentence_patterns(self) -> Dict[str, Any]:
        """加载句型模式"""
        # 从讲义知识点加载
        knowledge_data = self.data_loader.get_topic_analysis_data()
        return knowledge_data.get('writing_techniques', {})
    
    def _load_academic_expressions(self) -> Dict[str, Any]:
        """加载学术表达"""
        vocab_data = self.data_loader.get_vocabulary_analysis_data()
        return vocab_data.get('academic_word_list', {})
    
    def _initialize_generators(self):
        """初始化各种生成器"""
        self.improvement_templates = self._create_improvement_templates()
        self.sentence_enhancers = self._create_sentence_enhancers()
        self.style_improvers = self._create_style_improvers()
    
    def generate_sentence_improvements(
        self,
        sentences: List[Dict[str, Any]],
        dimension_scores: Dict[str, float],
        overall_score: float
    ) -> List[SentenceImprovement]:
        """为每个句子生成改进建议"""
        
        improvements = []
        
        for sentence_info in sentences:
            sentence_text = sentence_info['text']
            sentence_index = sentence_info['index']
            
            # 生成多种类型的改进建议
            sentence_improvements = []
            
            # 1. 语法改进
            grammar_improvements = self._generate_grammar_improvements(sentence_text, sentence_index)
            sentence_improvements.extend(grammar_improvements)
            
            # 2. 词汇改进
            vocabulary_improvements = self._generate_vocabulary_improvements(sentence_text, sentence_index)
            sentence_improvements.extend(vocabulary_improvements)
            
            # 3. 结构改进
            structure_improvements = self._generate_structure_improvements(sentence_text, sentence_index)
            sentence_improvements.extend(structure_improvements)
            
            # 4. 清晰度改进
            clarity_improvements = self._generate_clarity_improvements(sentence_text, sentence_index)
            sentence_improvements.extend(clarity_improvements)
            
            # 5. 风格改进
            style_improvements = self._generate_style_improvements(sentence_text, sentence_index, overall_score)
            sentence_improvements.extend(style_improvements)
            
            # 合并和优化改进建议
            if sentence_improvements:
                best_improvement = self._select_best_improvement(sentence_improvements, dimension_scores)
                improvements.append(best_improvement)
        
        return improvements
    
    def _generate_grammar_improvements(self, sentence: str, sentence_index: int) -> List[SentenceImprovement]:
        """生成语法改进建议"""
        improvements = []
        
        # 检测语法错误并生成改进建议
        errors = self.error_detector._detect_grammar_errors([{'text': sentence, 'index': sentence_index}])
        
        if errors:
            # 基于错误生成改进版本
            improved_sentence = sentence
            specific_changes = []
            
            for error in errors:
                if hasattr(error, 'correction_suggestion'):
                    improved_sentence = improved_sentence.replace(
                        error.original_text, 
                        error.correction_suggestion
                    )
                    specific_changes.append({
                        'type': 'grammar_correction',
                        'original': error.original_text,
                        'improved': error.correction_suggestion,
                        'reason': error.explanation
                    })
            
            if improved_sentence != sentence:
                improvements.append(SentenceImprovement(
                    sentence_index=sentence_index,
                    original_sentence=sentence,
                    improved_versions=[improved_sentence],
                    improvement_type="grammar",
                    improvement_explanation="修正语法错误，提高准确性",
                    specific_changes=specific_changes,
                    difficulty_level="basic",
                    impact_on_score="可能提升GRA分数0.25-0.5分",
                    learning_focus=["语法准确性", "错误识别", "基础语法规则"]
                ))
        
        return improvements
    
    def _generate_vocabulary_improvements(self, sentence: str, sentence_index: int) -> List[SentenceImprovement]:
        """生成词汇改进建议"""
        improvements = []
        
        # 查找可以升级的词汇
        improved_sentence = sentence
        specific_changes = []
        
        for basic_word, upgrade_info in self.vocabulary_upgrades.items():
            if basic_word.lower() in sentence.lower():
                suggestions = upgrade_info.get('suggestions', [])
                if suggestions:
                    best_replacement = suggestions[0]  # 选择第一个建议
                    
                    # 替换词汇
                    pattern = rf'\b{re.escape(basic_word)}\b'
                    if re.search(pattern, improved_sentence, re.IGNORECASE):
                        improved_sentence = re.sub(
                            pattern, 
                            best_replacement['word'], 
                            improved_sentence, 
                            count=1, 
                            flags=re.IGNORECASE
                        )
                        
                        specific_changes.append({
                            'type': 'vocabulary_upgrade',
                            'original': basic_word,
                            'improved': best_replacement['word'],
                            'reason': f"{best_replacement['meaning']} - {upgrade_info.get('comment', '')}"
                        })
        
        if improved_sentence != sentence and specific_changes:
            improvements.append(SentenceImprovement(
                sentence_index=sentence_index,
                original_sentence=sentence,
                improved_versions=[improved_sentence],
                improvement_type="vocabulary",
                improvement_explanation="升级词汇选择，提高表达精确性和学术性",
                specific_changes=specific_changes,
                difficulty_level="intermediate",
                impact_on_score="可能提升LR分数0.25-0.5分",
                learning_focus=["词汇升级", "学术词汇", "精确表达"]
            ))
        
        return improvements
    
    def _generate_structure_improvements(self, sentence: str, sentence_index: int) -> List[SentenceImprovement]:
        """生成结构改进建议"""
        improvements = []
        
        # 分析句子复杂度
        complexity_score = self._calculate_sentence_complexity(sentence)
        
        if complexity_score < 3:  # 句子过于简单
            # 生成更复杂的版本
            enhanced_versions = self._enhance_sentence_structure(sentence)
            
            if enhanced_versions:
                improvements.append(SentenceImprovement(
                    sentence_index=sentence_index,
                    original_sentence=sentence,
                    improved_versions=enhanced_versions,
                    improvement_type="structure",
                    improvement_explanation="增加句子复杂度，使用更高级的语法结构",
                    specific_changes=[{
                        'type': 'structure_enhancement',
                        'original': '简单句结构',
                        'improved': '复合句/复杂句结构',
                        'reason': '提高语法复杂度和表达层次'
                    }],
                    difficulty_level="advanced",
                    impact_on_score="可能提升GRA分数0.5-1分",
                    learning_focus=["复杂句型", "从句使用", "句式变化"]
                ))
        
        return improvements
    
    def _generate_clarity_improvements(self, sentence: str, sentence_index: int) -> List[SentenceImprovement]:
        """生成清晰度改进建议"""
        improvements = []
        
        # 检查句子长度和清晰度
        word_count = len(sentence.split())
        
        if word_count > 30:  # 句子过长
            # 建议分割句子
            split_versions = self._split_long_sentence(sentence)
            
            if split_versions:
                improvements.append(SentenceImprovement(
                    sentence_index=sentence_index,
                    original_sentence=sentence,
                    improved_versions=split_versions,
                    improvement_type="clarity",
                    improvement_explanation="分割过长句子，提高可读性和清晰度",
                    specific_changes=[{
                        'type': 'sentence_splitting',
                        'original': '一个长句',
                        'improved': '两个或多个清晰的短句',
                        'reason': '提高句子清晰度和可读性'
                    }],
                    difficulty_level="intermediate",
                    impact_on_score="可能提升CC分数0.25分",
                    learning_focus=["句子清晰度", "逻辑表达", "可读性"]
                ))
        
        # 检查模糊表达
        vague_expressions = ['things', 'stuff', 'something', 'it', 'this', 'that']
        for vague_word in vague_expressions:
            if vague_word.lower() in sentence.lower():
                clarified_version = self._clarify_vague_expressions(sentence, vague_word)
                if clarified_version != sentence:
                    improvements.append(SentenceImprovement(
                        sentence_index=sentence_index,
                        original_sentence=sentence,
                        improved_versions=[clarified_version],
                        improvement_type="clarity",
                        improvement_explanation="替换模糊表达，提高表达精确性",
                        specific_changes=[{
                            'type': 'clarity_enhancement',
                            'original': vague_word,
                            'improved': '更具体的表达',
                            'reason': '避免模糊表达，提高精确性'
                        }],
                        difficulty_level="basic",
                        impact_on_score="可能提升LR分数0.25分",
                        learning_focus=["精确表达", "避免模糊词汇", "具体化描述"]
                    ))
                    break  # 只处理第一个模糊表达
        
        return improvements
    
    def _generate_style_improvements(self, sentence: str, sentence_index: int, overall_score: float) -> List[SentenceImprovement]:
        """生成风格改进建议"""
        improvements = []
        
        # 检查学术语调
        informal_markers = ['I think', 'I believe', 'you know', 'kind of', 'sort of']
        
        for marker in informal_markers:
            if marker.lower() in sentence.lower():
                formal_version = self._formalize_expression(sentence, marker)
                if formal_version != sentence:
                    improvements.append(SentenceImprovement(
                        sentence_index=sentence_index,
                        original_sentence=sentence,
                        improved_versions=[formal_version],
                        improvement_type="style",
                        improvement_explanation="提高表达的正式性和学术性",
                        specific_changes=[{
                            'type': 'formality_enhancement',
                            'original': marker,
                            'improved': '更正式的表达',
                            'reason': '学术写作要求正式语调'
                        }],
                        difficulty_level="intermediate",
                        impact_on_score="可能提升整体分数0.25分",
                        learning_focus=["学术语调", "正式表达", "客观性"]
                    ))
                    break
        
        return improvements
    
    def _calculate_sentence_complexity(self, sentence: str) -> int:
        """计算句子复杂度"""
        complexity_score = 0
        
        # 检查从句
        subordinating_conjunctions = ['because', 'although', 'while', 'since', 'if', 'when', 'where', 'unless']
        for conj in subordinating_conjunctions:
            if conj in sentence.lower():
                complexity_score += 1
        
        # 检查关系从句
        relative_pronouns = ['which', 'that', 'who', 'whom', 'whose', 'where']
        for pronoun in relative_pronouns:
            if pronoun in sentence.lower():
                complexity_score += 1
        
        # 检查并列结构
        if ',' in sentence:
            complexity_score += sentence.count(',') * 0.5
        
        return int(complexity_score)

    def _select_best_improvement(self, improvements: List[SentenceImprovement], dimension_scores: Dict[str, float]) -> SentenceImprovement:
        """选择最佳改进建议"""
        if not improvements:
            return None

        # 根据维度分数确定优先级
        priority_map = {
            'grammar': dimension_scores.get('GRA', 5.0),
            'vocabulary': dimension_scores.get('LR', 5.0),
            'structure': dimension_scores.get('GRA', 5.0),
            'clarity': dimension_scores.get('CC', 5.0),
            'style': (dimension_scores.get('TR', 5.0) + dimension_scores.get('CC', 5.0)) / 2
        }

        # 选择最需要改进的类型
        best_improvement = improvements[0]
        best_priority = priority_map.get(best_improvement.improvement_type, 5.0)

        for improvement in improvements[1:]:
            current_priority = priority_map.get(improvement.improvement_type, 5.0)
            if current_priority < best_priority:  # 分数越低，越需要改进
                best_improvement = improvement
                best_priority = current_priority

        return best_improvement

    def _enhance_sentence_structure(self, sentence: str) -> List[str]:
        """增强句子结构"""
        enhanced_versions = []

        # 简单的结构增强示例
        if ' and ' in sentence:
            # 将并列句改为复合句
            parts = sentence.split(' and ', 1)
            if len(parts) == 2:
                enhanced = f"While {parts[0].lower()}, {parts[1]}"
                enhanced_versions.append(enhanced)

        if not any(conj in sentence.lower() for conj in ['because', 'although', 'while', 'since']):
            # 添加从属连词
            enhanced = f"Although {sentence.lower()}, this demonstrates the complexity of the issue."
            enhanced_versions.append(enhanced)

        return enhanced_versions[:2]  # 返回最多2个版本

    def _split_long_sentence(self, sentence: str) -> List[str]:
        """分割长句"""
        split_versions = []

        # 在连词处分割
        conjunctions = [', and ', ', but ', ', or ', ', so ']

        for conj in conjunctions:
            if conj in sentence:
                parts = sentence.split(conj, 1)
                if len(parts) == 2:
                    # 创建两个独立的句子
                    first_part = parts[0].strip() + '.'
                    second_part = parts[1].strip()
                    if not second_part.endswith('.'):
                        second_part += '.'

                    # 确保第二部分以大写字母开头
                    if second_part and second_part[0].islower():
                        second_part = second_part[0].upper() + second_part[1:]

                    split_version = f"{first_part} {second_part}"
                    split_versions.append(split_version)
                    break

        return split_versions

    def _clarify_vague_expressions(self, sentence: str, vague_word: str) -> str:
        """澄清模糊表达"""
        clarification_map = {
            'things': 'factors',
            'stuff': 'materials',
            'something': 'a particular issue',
            'it': 'this approach',
            'this': 'this method',
            'that': 'that approach'
        }

        replacement = clarification_map.get(vague_word.lower(), 'the specific element')

        # 简单的替换
        pattern = rf'\b{re.escape(vague_word)}\b'
        clarified = re.sub(pattern, replacement, sentence, count=1, flags=re.IGNORECASE)

        return clarified

    def _formalize_expression(self, sentence: str, informal_marker: str) -> str:
        """正式化表达"""
        formalization_map = {
            'I think': 'It can be argued that',
            'I believe': 'Evidence suggests that',
            'you know': '',
            'kind of': 'somewhat',
            'sort of': 'rather'
        }

        formal_replacement = formalization_map.get(informal_marker, '')

        if formal_replacement:
            pattern = rf'\b{re.escape(informal_marker)}\b'
            formalized = re.sub(pattern, formal_replacement, sentence, count=1, flags=re.IGNORECASE)

            # 清理多余的空格
            formalized = re.sub(r'\s+', ' ', formalized).strip()

            return formalized

        return sentence

    def _create_improvement_templates(self) -> Dict[str, Any]:
        """创建改进模板"""
        return {
            'grammar_templates': {
                'subject_verb_agreement': 'Ensure the verb agrees with the subject',
                'article_usage': 'Check if articles (a, an, the) are needed',
                'preposition_errors': 'Verify correct preposition usage'
            },
            'vocabulary_templates': {
                'word_choice': 'Consider more precise vocabulary',
                'academic_register': 'Use more formal academic language',
                'collocation': 'Check word combinations'
            },
            'structure_templates': {
                'sentence_variety': 'Vary sentence structures',
                'complexity': 'Add subordinate clauses',
                'transitions': 'Improve sentence connections'
            }
        }

    def _create_sentence_enhancers(self) -> Dict[str, Any]:
        """创建句子增强器"""
        return {
            'complexity_enhancers': [
                'Add relative clauses',
                'Use participial phrases',
                'Include conditional statements'
            ],
            'clarity_enhancers': [
                'Remove redundant words',
                'Clarify pronoun references',
                'Simplify complex structures'
            ],
            'style_enhancers': [
                'Use active voice',
                'Vary sentence beginnings',
                'Employ parallel structure'
            ]
        }

    def _create_style_improvers(self) -> Dict[str, Any]:
        """创建风格改进器"""
        return {
            'formality_improvers': {
                'contractions': 'Expand contractions (don\'t → do not)',
                'informal_words': 'Replace informal vocabulary',
                'personal_pronouns': 'Reduce use of I, you, we'
            },
            'academic_improvers': {
                'objectivity': 'Use objective language',
                'precision': 'Choose precise terminology',
                'hedging': 'Use appropriate hedging language'
            }
        }

# 创建全局实例
sentence_improvement_generator = SentenceImprovementGenerator()
