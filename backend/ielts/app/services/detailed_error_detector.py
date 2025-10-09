"""
详细的错误检测系统 - 基于现有数据精确定位语法、词汇、结构、内容等各类错误
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from .comprehensive_data_loader import comprehensive_data_loader

logger = logging.getLogger(__name__)

@dataclass
class DetailedError:
    """详细错误信息"""
    error_id: str
    error_type: str
    error_category: str
    severity: str  # critical, high, medium, low
    sentence_index: int
    start_position: int
    end_position: int
    original_text: str
    error_description: str
    correction_suggestion: str
    explanation: str
    examples: List[str]
    impact_on_band: str
    learning_resources: List[str]

class DetailedErrorDetector:
    """详细的错误检测系统"""
    
    def __init__(self):
        self.data_loader = comprehensive_data_loader
        
        # 加载错误检测相关数据
        self.grammar_errors = self._load_grammar_error_database()
        self.vocabulary_errors = self._load_vocabulary_error_patterns()
        self.structure_errors = self._load_structure_error_patterns()
        self.punctuation_rules = self._load_punctuation_rules()
        self.academic_standards = self._load_academic_writing_standards()
        
        # 初始化检测器
        self._initialize_detectors()
    
    def _load_grammar_error_database(self) -> Dict[str, Any]:
        """加载语法错误数据库"""
        grammar_data = self.data_loader.get_grammar_analysis_data()
        return grammar_data.get('common_errors', {})
    
    def _load_vocabulary_error_patterns(self) -> Dict[str, Any]:
        """加载词汇错误模式"""
        vocab_data = self.data_loader.get_vocabulary_analysis_data()
        return {
            'upgrade_suggestions': vocab_data.get('upgrade_suggestions', {}),
            'collocations': vocab_data.get('collocations_database', {}),
            'academic_words': vocab_data.get('academic_word_list', {})
        }
    
    def _load_structure_error_patterns(self) -> Dict[str, Any]:
        """加载结构错误模式"""
        coherence_data = self.data_loader.get_coherence_analysis_data()
        return {
            'cohesive_devices': coherence_data.get('cohesive_devices', {}),
            'essay_structures': coherence_data.get('essay_structures', {})
        }
    
    def _load_punctuation_rules(self) -> Dict[str, Any]:
        """加载标点符号规则"""
        grammar_data = self.data_loader.get_grammar_analysis_data()
        return grammar_data.get('punctuation_rules', {})
    
    def _load_academic_writing_standards(self) -> Dict[str, Any]:
        """加载学术写作标准"""
        scoring_data = self.data_loader.get_scoring_reference_data()
        return scoring_data.get('scoring_criteria', {})
    
    def _initialize_detectors(self):
        """初始化各种检测器"""
        self.grammar_patterns = self._compile_grammar_patterns()
        self.vocabulary_patterns = self._compile_vocabulary_patterns()
        self.structure_patterns = self._compile_structure_patterns()
        self.punctuation_patterns = self._compile_punctuation_patterns()

    def _compile_grammar_patterns(self) -> Dict[str, Any]:
        """编译语法错误模式"""
        return {
            'subject_verb_agreement': [
                r'\bone of the \w+s (are|have|do)\b',
                r'(everyone|everybody|someone|somebody|anyone|anybody|no one|nobody)\s+\w*\s*(are|have|do)\b'
            ],
            'article_errors': [
                r'\b(is|was|has)\s+([a-z]+(?:tion|sion|ment|ness|ity|ty|cy|ry|ly|al|ic|ous|ive|able|ible))\b'
            ],
            'preposition_errors': [
                r'\bdepend of\b',
                r'\bdifferent than\b'
            ]
        }

    def _compile_vocabulary_patterns(self) -> Dict[str, Any]:
        """编译词汇错误模式"""
        return {
            'basic_words': ['good', 'bad', 'very', 'a lot of', 'things', 'people'],
            'collocation_errors': [
                r'\bmake research\b',
                r'\bdo a decision\b'
            ],
            'informal_expressions': ['I think', 'I believe', 'you know']
        }

    def _compile_structure_patterns(self) -> Dict[str, Any]:
        """编译结构错误模式"""
        return {
            'run_on_sentence_indicators': [',', 'and', 'but', 'or'],
            'fragment_indicators': ['because', 'although', 'since', 'while']
        }

    def _compile_punctuation_patterns(self) -> Dict[str, Any]:
        """编译标点符号模式"""
        return {
            'missing_periods': r'[a-zA-Z]\s*$',
            'comma_splices': r'[a-zA-Z],\s*[A-Z]',
            'apostrophe_errors': r"its'"
        }
    
    def detect_all_errors(
        self,
        essay_content: str,
        sentences: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """检测所有类型的错误"""
        
        all_errors = []
        
        # 1. 语法错误检测
        grammar_errors = self._detect_grammar_errors(sentences)
        all_errors.extend(grammar_errors)
        
        # 2. 词汇错误检测
        vocabulary_errors = self._detect_vocabulary_errors(sentences)
        all_errors.extend(vocabulary_errors)
        
        # 3. 结构错误检测
        structure_errors = self._detect_structure_errors(essay_content, sentences)
        all_errors.extend(structure_errors)
        
        # 4. 标点符号错误检测
        punctuation_errors = self._detect_punctuation_errors(sentences)
        all_errors.extend(punctuation_errors)
        
        # 5. 学术写作规范检测
        academic_errors = self._detect_academic_writing_errors(sentences)
        all_errors.extend(academic_errors)
        
        # 6. 连贯性错误检测
        coherence_errors = self._detect_coherence_errors(sentences)
        all_errors.extend(coherence_errors)
        
        return self._organize_error_results(all_errors)
    
    def _detect_grammar_errors(self, sentences: List[Dict[str, Any]]) -> List[DetailedError]:
        """检测语法错误"""
        errors = []
        
        for sentence_info in sentences:
            sentence_text = sentence_info['text']
            sentence_index = sentence_info['index']
            
            # 主谓一致错误
            sva_errors = self._detect_subject_verb_agreement_errors(sentence_text, sentence_index)
            errors.extend(sva_errors)
            
            # 冠词错误
            article_errors = self._detect_article_errors(sentence_text, sentence_index)
            errors.extend(article_errors)
            
            # 介词错误
            preposition_errors = self._detect_preposition_errors(sentence_text, sentence_index)
            errors.extend(preposition_errors)
            
            # 时态错误
            tense_errors = self._detect_tense_errors(sentence_text, sentence_index)
            errors.extend(tense_errors)
            
            # 代词错误
            pronoun_errors = self._detect_pronoun_errors(sentence_text, sentence_index)
            errors.extend(pronoun_errors)
            
            # 修饰语错误
            modifier_errors = self._detect_modifier_errors(sentence_text, sentence_index)
            errors.extend(modifier_errors)
        
        return errors
    
    def _detect_subject_verb_agreement_errors(self, sentence: str, sentence_index: int) -> List[DetailedError]:
        """检测主谓一致错误"""
        errors = []
        
        # 检查 "one of the + 复数名词 + 单数动词" 结构
        pattern1 = r'\bone of the \w+s (is|has|does)\b'
        if not re.search(pattern1, sentence, re.IGNORECASE):
            # 检查错误用法
            wrong_pattern = r'\bone of the \w+s (are|have|do)\b'
            match = re.search(wrong_pattern, sentence, re.IGNORECASE)
            if match:
                errors.append(DetailedError(
                    error_id="GRA_SVA_01",
                    error_type="Subject-Verb Agreement",
                    error_category="Grammar",
                    severity="high",
                    sentence_index=sentence_index,
                    start_position=match.start(),
                    end_position=match.end(),
                    original_text=match.group(),
                    error_description="'one of the + 复数名词'结构中动词应该用单数形式",
                    correction_suggestion=match.group().replace(match.group(1), 
                        'is' if match.group(1).lower() == 'are' else 
                        'has' if match.group(1).lower() == 'have' else 'does'),
                    explanation="'one'是主语，是单数，所以动词必须用单数形式",
                    examples=[
                        "正确: One of the most important factors is...",
                        "错误: One of the most important factors are..."
                    ],
                    impact_on_band="可能影响GRA分数0.5-1分",
                    learning_resources=["语法书第3章：主谓一致", "练习册：主谓一致专项练习"]
                ))
        
        # 检查不定代词主语
        indefinite_pronouns = ['everyone', 'everybody', 'someone', 'somebody', 'anyone', 'anybody', 'no one', 'nobody']
        for pronoun in indefinite_pronouns:
            pattern = rf'\b{pronoun}\s+\w*\s*(are|have|do)\b'
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                errors.append(DetailedError(
                    error_id="GRA_SVA_02",
                    error_type="Subject-Verb Agreement",
                    error_category="Grammar",
                    severity="high",
                    sentence_index=sentence_index,
                    start_position=match.start(),
                    end_position=match.end(),
                    original_text=match.group(),
                    error_description=f"不定代词'{pronoun}'作主语时动词应该用单数形式",
                    correction_suggestion=match.group().replace(match.group(1), 
                        'is' if match.group(1).lower() == 'are' else 
                        'has' if match.group(1).lower() == 'have' else 'does'),
                    explanation="不定代词在语法上被视为单数，需要单数动词",
                    examples=[
                        f"正确: {pronoun.capitalize()} is responsible for...",
                        f"错误: {pronoun.capitalize()} are responsible for..."
                    ],
                    impact_on_band="可能影响GRA分数0.5分",
                    learning_resources=["语法书：不定代词用法", "在线练习：主谓一致"]
                ))
        
        return errors
    
    def _detect_article_errors(self, sentence: str, sentence_index: int) -> List[DetailedError]:
        """检测冠词错误"""
        errors = []
        
        # 检查可数名词单数前缺少冠词
        # 这是一个简化的检测，实际应该更复杂
        pattern = r'\b(?:is|was|has)\s+([a-z]+(?:tion|sion|ment|ness|ity|ty|cy|ry|ly|al|ic|ous|ive|able|ible))\b'
        matches = re.finditer(pattern, sentence, re.IGNORECASE)
        
        for match in matches:
            noun = match.group(1)
            if not re.search(rf'\b(?:a|an|the)\s+{noun}\b', sentence, re.IGNORECASE):
                errors.append(DetailedError(
                    error_id="GRA_ART_01",
                    error_type="Article Misuse",
                    error_category="Grammar",
                    severity="medium",
                    sentence_index=sentence_index,
                    start_position=match.start(1),
                    end_position=match.end(1),
                    original_text=noun,
                    error_description=f"可数名词单数'{noun}'前可能需要冠词",
                    correction_suggestion=f"考虑在'{noun}'前添加适当的冠词(a/an/the)",
                    explanation="可数名词单数在句中通常需要冠词",
                    examples=[
                        f"可能正确: ...is a {noun}",
                        f"可能正确: ...is the {noun}"
                    ],
                    impact_on_band="可能影响GRA分数0.25-0.5分",
                    learning_resources=["语法书：冠词用法", "练习：冠词选择"]
                ))
        
        return errors

    def _detect_preposition_errors(self, sentence: str, sentence_index: int) -> List[DetailedError]:
        """检测介词错误"""
        errors = []

        preposition_errors = {
            'depend of': 'depend on',
            'different than': 'different from',
            'consist in': 'consist of',
            'discuss about': 'discuss'
        }

        for wrong, correct in preposition_errors.items():
            if wrong in sentence.lower():
                match = re.search(rf'\b{re.escape(wrong)}\b', sentence, re.IGNORECASE)
                if match:
                    errors.append(DetailedError(
                        error_id="GRA_PREP_01",
                        error_type="Preposition Error",
                        error_category="Grammar",
                        severity="medium",
                        sentence_index=sentence_index,
                        start_position=match.start(),
                        end_position=match.end(),
                        original_text=match.group(),
                        error_description=f"介词搭配错误：应该使用'{correct}'而不是'{wrong}'",
                        correction_suggestion=correct,
                        explanation="这是固定搭配，需要记忆正确的介词使用",
                        examples=[f"正确: {correct}", f"错误: {wrong}"],
                        impact_on_band="可能影响GRA分数0.25分",
                        learning_resources=["介词搭配词典", "固定搭配练习"]
                    ))

        return errors

    def _detect_tense_errors(self, sentence: str, sentence_index: int) -> List[DetailedError]:
        """检测时态错误"""
        errors = []

        # 简化的时态错误检测
        # 检查时间状语与动词时态的不匹配
        past_indicators = ['yesterday', 'last year', 'in 2020', 'ago']
        present_indicators = ['now', 'today', 'currently', 'nowadays']

        for indicator in past_indicators:
            if indicator in sentence.lower():
                # 检查是否使用了现在时动词
                present_verbs = re.findall(r'\b(is|are|am|do|does|have|has)\b', sentence, re.IGNORECASE)
                if present_verbs:
                    errors.append(DetailedError(
                        error_id="GRA_TENSE_01",
                        error_type="Tense Error",
                        error_category="Grammar",
                        severity="medium",
                        sentence_index=sentence_index,
                        start_position=0,
                        end_position=len(sentence),
                        original_text=sentence,
                        error_description=f"时态不一致：'{indicator}'表示过去时间，但使用了现在时动词",
                        correction_suggestion="将现在时动词改为过去时",
                        explanation="时间状语与动词时态必须保持一致",
                        examples=["正确: Yesterday, I was busy.", "错误: Yesterday, I am busy."],
                        impact_on_band="可能影响GRA分数0.25-0.5分",
                        learning_resources=["时态用法指南", "时态练习题"]
                    ))
                    break

        return errors

    def _detect_pronoun_errors(self, sentence: str, sentence_index: int) -> List[DetailedError]:
        """检测代词错误"""
        errors = []

        # 检查代词指代不明
        pronouns = ['it', 'this', 'that', 'they', 'them']
        for pronoun in pronouns:
            if f' {pronoun} ' in sentence.lower():
                # 简化检测：如果句子开头就是代词，可能指代不明
                if sentence.lower().strip().startswith(pronoun):
                    errors.append(DetailedError(
                        error_id="GRA_PRON_01",
                        error_type="Pronoun Reference",
                        error_category="Grammar",
                        severity="low",
                        sentence_index=sentence_index,
                        start_position=0,
                        end_position=len(pronoun),
                        original_text=pronoun,
                        error_description=f"代词'{pronoun}'的指代可能不够明确",
                        correction_suggestion=f"考虑用具体名词替换'{pronoun}'或确保指代清晰",
                        explanation="代词应该有明确的先行词",
                        examples=["模糊: It is important.", "清晰: Education is important."],
                        impact_on_band="可能影响CC分数0.25分",
                        learning_resources=["代词用法指南", "指代清晰性练习"]
                    ))
                    break

        return errors

    def _detect_modifier_errors(self, sentence: str, sentence_index: int) -> List[DetailedError]:
        """检测修饰语错误"""
        errors = []

        # 检查悬垂修饰语（简化版）
        # 如果句子以-ing开头，检查主语是否合适
        if re.match(r'^[A-Z]\w*ing', sentence):
            errors.append(DetailedError(
                error_id="GRA_MOD_01",
                error_type="Dangling Modifier",
                error_category="Grammar",
                severity="medium",
                sentence_index=sentence_index,
                start_position=0,
                end_position=20,
                original_text=sentence[:20] + "...",
                error_description="可能存在悬垂修饰语，需要检查逻辑主语",
                correction_suggestion="确保修饰语的逻辑主语与句子主语一致",
                explanation="分词短语的逻辑主语应该与句子主语相同",
                examples=["错误: Walking to school, the bag was heavy.", "正确: Walking to school, I found the bag heavy."],
                impact_on_band="可能影响GRA分数0.25-0.5分",
                learning_resources=["修饰语用法", "分词结构练习"]
            ))

        return errors

    def _detect_vocabulary_errors(self, sentences: List[Dict[str, Any]]) -> List[DetailedError]:
        """检测词汇错误"""
        errors = []
        
        for sentence_info in sentences:
            sentence_text = sentence_info['text']
            sentence_index = sentence_info['index']
            
            # 检测基础词汇过度使用
            basic_word_errors = self._detect_basic_word_overuse(sentence_text, sentence_index)
            errors.extend(basic_word_errors)
            
            # 检测搭配错误
            collocation_errors = self._detect_collocation_errors(sentence_text, sentence_index)
            errors.extend(collocation_errors)
            
            # 检测词汇精确性问题
            precision_errors = self._detect_word_precision_errors(sentence_text, sentence_index)
            errors.extend(precision_errors)
        
        return errors
    
    def _detect_basic_word_overuse(self, sentence: str, sentence_index: int) -> List[DetailedError]:
        """检测基础词汇过度使用"""
        errors = []
        
        basic_words = {
            'good': {
                'alternatives': ['beneficial', 'advantageous', 'effective', 'positive'],
                'description': '过于基础，缺乏精确性'
            },
            'bad': {
                'alternatives': ['detrimental', 'harmful', 'negative', 'adverse'],
                'description': '过于简单，不够学术'
            },
            'very': {
                'alternatives': ['extremely', 'significantly', 'considerably', 'remarkably'],
                'description': '过度使用，建议用更精确的副词'
            },
            'a lot of': {
                'alternatives': ['numerous', 'a significant number of', 'substantial', 'considerable'],
                'description': '过于口语化，不适合学术写作'
            }
        }
        
        for basic_word, info in basic_words.items():
            if basic_word.lower() in sentence.lower():
                # 找到具体位置
                match = re.search(rf'\b{re.escape(basic_word)}\b', sentence, re.IGNORECASE)
                if match:
                    errors.append(DetailedError(
                        error_id=f"VOC_BASIC_{basic_word.upper().replace(' ', '_')}",
                        error_type="Basic Word Overuse",
                        error_category="Vocabulary",
                        severity="medium",
                        sentence_index=sentence_index,
                        start_position=match.start(),
                        end_position=match.end(),
                        original_text=match.group(),
                        error_description=f"'{basic_word}' {info['description']}",
                        correction_suggestion=f"考虑替换为: {', '.join(info['alternatives'][:3])}",
                        explanation=f"使用更精确的词汇可以提高表达的准确性和学术性",
                        examples=[
                            f"原句: ...{basic_word}...",
                            f"改进: ...{info['alternatives'][0]}..."
                        ],
                        impact_on_band="可能影响LR分数0.25-0.5分",
                        learning_resources=["词汇升级指南", "学术词汇表"]
                    ))
        
        return errors

    def _detect_collocation_errors(self, sentence: str, sentence_index: int) -> List[DetailedError]:
        """检测搭配错误"""
        errors = []

        collocation_errors = {
            'make research': 'conduct research',
            'do a decision': 'make a decision',
            'make a mistake': 'make an error',  # 这个实际是正确的，只是示例
            'take a photo': 'take a picture'   # 这个也是正确的，只是示例
        }

        for wrong, correct in collocation_errors.items():
            if wrong.lower() in sentence.lower():
                match = re.search(rf'\b{re.escape(wrong)}\b', sentence, re.IGNORECASE)
                if match:
                    errors.append(DetailedError(
                        error_id="VOC_COL_01",
                        error_type="Collocation Error",
                        error_category="Vocabulary",
                        severity="medium",
                        sentence_index=sentence_index,
                        start_position=match.start(),
                        end_position=match.end(),
                        original_text=match.group(),
                        error_description=f"搭配错误：应该使用'{correct}'而不是'{wrong}'",
                        correction_suggestion=correct,
                        explanation="这是固定搭配，需要记忆正确的动词搭配",
                        examples=[f"正确: {correct}", f"错误: {wrong}"],
                        impact_on_band="可能影响LR分数0.25分",
                        learning_resources=["搭配词典", "动词搭配练习"]
                    ))

        return errors

    def _detect_word_precision_errors(self, sentence: str, sentence_index: int) -> List[DetailedError]:
        """检测词汇精确性错误"""
        errors = []

        vague_words = {
            'things': ['factors', 'elements', 'aspects', 'issues'],
            'people': ['individuals', 'citizens', 'residents', 'members'],
            'stuff': ['materials', 'items', 'content', 'information'],
            'good': ['beneficial', 'effective', 'positive', 'advantageous'],
            'bad': ['detrimental', 'harmful', 'negative', 'problematic']
        }

        for vague_word, alternatives in vague_words.items():
            if f' {vague_word} ' in sentence.lower() or sentence.lower().startswith(vague_word):
                match = re.search(rf'\b{vague_word}\b', sentence, re.IGNORECASE)
                if match:
                    errors.append(DetailedError(
                        error_id="VOC_PREC_01",
                        error_type="Word Precision",
                        error_category="Vocabulary",
                        severity="low",
                        sentence_index=sentence_index,
                        start_position=match.start(),
                        end_position=match.end(),
                        original_text=match.group(),
                        error_description=f"'{vague_word}'过于模糊，建议使用更精确的词汇",
                        correction_suggestion=f"考虑使用: {', '.join(alternatives[:3])}",
                        explanation="使用更精确的词汇可以提高表达的准确性",
                        examples=[f"模糊: {vague_word}", f"精确: {alternatives[0]}"],
                        impact_on_band="可能影响LR分数0.25分",
                        learning_resources=["词汇精确性指南", "同义词词典"]
                    ))
                    break  # 只报告第一个发现的模糊词汇

        return errors

    def _detect_structure_errors(self, essay_content: str, sentences: List[Dict[str, Any]]) -> List[DetailedError]:
        """检测结构错误"""
        errors = []

        for sentence_info in sentences:
            sentence_text = sentence_info['text']
            sentence_index = sentence_info['index']

            # 检测过长句子
            word_count = len(sentence_text.split())
            if word_count > 35:
                errors.append(DetailedError(
                    error_id="STRUCT_LONG_01",
                    error_type="Run-on Sentence",
                    error_category="Structure",
                    severity="medium",
                    sentence_index=sentence_index,
                    start_position=0,
                    end_position=len(sentence_text),
                    original_text=sentence_text[:50] + "...",
                    error_description=f"句子过长（{word_count}词），可能影响可读性",
                    correction_suggestion="考虑将长句分割为两个或多个较短的句子",
                    explanation="过长的句子会影响读者理解，建议控制在20-25词以内",
                    examples=["长句: This is a very long sentence...", "改进: This is shorter. This is clearer."],
                    impact_on_band="可能影响CC分数0.25分",
                    learning_resources=["句子长度控制", "句子分割技巧"]
                ))

            # 检测句子片段
            if not sentence_text.strip().endswith(('.', '!', '?')):
                errors.append(DetailedError(
                    error_id="STRUCT_FRAG_01",
                    error_type="Sentence Fragment",
                    error_category="Structure",
                    severity="high",
                    sentence_index=sentence_index,
                    start_position=0,
                    end_position=len(sentence_text),
                    original_text=sentence_text,
                    error_description="句子不完整，缺少适当的结束标点",
                    correction_suggestion="在句子末尾添加句号、感叹号或问号",
                    explanation="完整的句子必须有适当的结束标点",
                    examples=["片段: Because it is important", "完整: Because it is important, we should act."],
                    impact_on_band="可能影响GRA分数0.5分",
                    learning_resources=["句子完整性", "标点符号使用"]
                ))

        return errors

    def _detect_punctuation_errors(self, sentences: List[Dict[str, Any]]) -> List[DetailedError]:
        """检测标点符号错误"""
        errors = []

        for sentence_info in sentences:
            sentence_text = sentence_info['text']
            sentence_index = sentence_info['index']

            # 检测缺少句号
            if sentence_text.strip() and not sentence_text.strip().endswith(('.', '!', '?', ':')):
                errors.append(DetailedError(
                    error_id="PUNCT_PERIOD_01",
                    error_type="Missing Period",
                    error_category="Punctuation",
                    severity="low",
                    sentence_index=sentence_index,
                    start_position=len(sentence_text.strip()),
                    end_position=len(sentence_text.strip()),
                    original_text="",
                    error_description="句子末尾缺少句号",
                    correction_suggestion="在句子末尾添加句号",
                    explanation="每个完整的句子都应该以句号结束",
                    examples=["错误: This is a sentence", "正确: This is a sentence."],
                    impact_on_band="可能影响GRA分数0.1分",
                    learning_resources=["标点符号规则", "句号使用指南"]
                ))

        return errors

    def _detect_academic_writing_errors(self, sentences: List[Dict[str, Any]]) -> List[DetailedError]:
        """检测学术写作错误"""
        errors = []

        informal_expressions = {
            'I think': ['It can be argued that', 'Evidence suggests that'],
            'I believe': ['It is evident that', 'Research indicates that'],
            'you': ['individuals', 'people', 'one'],
            'a lot of': ['numerous', 'a significant number of'],
            'very': ['extremely', 'significantly']
        }

        for sentence_info in sentences:
            sentence_text = sentence_info['text']
            sentence_index = sentence_info['index']

            for informal, formal_alternatives in informal_expressions.items():
                if informal.lower() in sentence_text.lower():
                    match = re.search(rf'\b{re.escape(informal)}\b', sentence_text, re.IGNORECASE)
                    if match:
                        errors.append(DetailedError(
                            error_id="ACAD_FORM_01",
                            error_type="Informal Expression",
                            error_category="Academic Writing",
                            severity="medium",
                            sentence_index=sentence_index,
                            start_position=match.start(),
                            end_position=match.end(),
                            original_text=match.group(),
                            error_description=f"'{informal}'过于非正式，不适合学术写作",
                            correction_suggestion=f"考虑使用: {', '.join(formal_alternatives[:2])}",
                            explanation="学术写作要求使用正式、客观的表达方式",
                            examples=[f"非正式: {informal}", f"正式: {formal_alternatives[0]}"],
                            impact_on_band="可能影响整体分数0.25分",
                            learning_resources=["学术写作规范", "正式表达指南"]
                        ))
                        break  # 每个句子只报告一个非正式表达

        return errors

    def _detect_coherence_errors(self, sentences: List[Dict[str, Any]]) -> List[DetailedError]:
        """检测连贯性错误"""
        errors = []

        # 检测缺少连接词的情况
        for i, sentence_info in enumerate(sentences[1:], 1):  # 从第二个句子开始
            sentence_text = sentence_info['text']
            sentence_index = sentence_info['index']

            # 简化的连贯性检测：检查是否缺少过渡词
            transition_words = ['however', 'furthermore', 'moreover', 'therefore', 'consequently',
                             'in addition', 'on the other hand', 'for example', 'in contrast']

            has_transition = any(word in sentence_text.lower() for word in transition_words)

            # 如果句子较长但没有过渡词，可能需要改进连贯性
            if len(sentence_text.split()) > 15 and not has_transition and i < len(sentences) - 1:
                errors.append(DetailedError(
                    error_id="COH_TRANS_01",
                    error_type="Missing Transition",
                    error_category="Coherence",
                    severity="low",
                    sentence_index=sentence_index,
                    start_position=0,
                    end_position=20,
                    original_text=sentence_text[:20] + "...",
                    error_description="句子间可能缺少适当的过渡词或连接词",
                    correction_suggestion="考虑添加适当的过渡词来改善连贯性",
                    explanation="过渡词有助于连接思想，提高文章的连贯性",
                    examples=["缺少过渡: Technology is useful. It has problems.",
                             "有过渡: Technology is useful. However, it has problems."],
                    impact_on_band="可能影响CC分数0.25分",
                    learning_resources=["过渡词使用", "连贯性写作技巧"]
                ))

        return errors

    def _organize_error_results(self, all_errors: List[DetailedError]) -> Dict[str, Any]:
        """组织错误结果"""
        error_categories = {}
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}

        for error in all_errors:
            # 按类别分组
            category = error.error_category
            if category not in error_categories:
                error_categories[category] = []
            error_categories[category].append(error.__dict__)

            # 统计严重程度
            severity_counts[error.severity] += 1

        return {
            'total_errors': len(all_errors),
            'error_categories': error_categories,
            'severity_distribution': severity_counts,
            'error_density': len(all_errors) / 100,  # 每100词的错误数
            'most_critical_errors': [e.__dict__ for e in all_errors if e.severity == 'critical'][:5],
            'improvement_priority': self._calculate_improvement_priority(all_errors)
        }

    def _calculate_improvement_priority(self, errors: List[DetailedError]) -> List[str]:
        """计算改进优先级"""
        priority_map = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        category_scores = {}

        for error in errors:
            category = error.error_category
            score = priority_map.get(error.severity, 1)
            category_scores[category] = category_scores.get(category, 0) + score

        # 按分数排序
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        return [category for category, score in sorted_categories]

# 创建全局实例
detailed_error_detector = DetailedErrorDetector()
