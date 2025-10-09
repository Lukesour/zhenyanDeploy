"""
增强的题型分析器 - 基于讲义知识点和题型数据的详细题型分析
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from .comprehensive_data_loader import comprehensive_data_loader

logger = logging.getLogger(__name__)

class EnhancedTopicAnalyzer:
    """增强的题型分析器"""
    
    def __init__(self):
        self.data_loader = comprehensive_data_loader
        
        # 加载题型分析相关数据
        self.topic_data = self.data_loader.get_topic_analysis_data()
        
        # 题型识别模式
        self.instruction_patterns = self._build_instruction_patterns()
        
        # 关键词模式
        self.keyword_patterns = self._build_keyword_patterns()
    
    def _build_instruction_patterns(self) -> Dict[str, List[str]]:
        """构建指令识别模式"""
        instruction_types = self.topic_data.get('instruction_types', {})
        patterns = {}
        
        if 'types' in instruction_types:
            for type_info in instruction_types['types']:
                type_name = type_info.get('type', '')
                anchors = type_info.get('anchors', [])
                patterns[type_name] = [anchor.lower() for anchor in anchors]
        
        # 从基础知识中补充模式
        basic_knowledge = self.topic_data.get('task2_basic_knowledge', {})
        question_types = basic_knowledge.get('question_types', {})
        
        for type_name, type_info in question_types.items():
            instructions = type_info.get('instructions', [])
            key = type_name.split('(')[0].strip().lower().replace(' ', '_')
            if key not in patterns:
                patterns[key] = []
            patterns[key].extend([inst.lower() for inst in instructions])
        
        return patterns
    
    def _build_keyword_patterns(self) -> Dict[str, List[str]]:
        """构建关键词模式"""
        prompt_lexicon = self.topic_data.get('prompt_lexicon', {})
        return {
            'absolute_terms': prompt_lexicon.get('absolute_terms', []),
            'limiters': prompt_lexicon.get('limiters', []),
            'comparative': prompt_lexicon.get('comparative', []),
            'causal': prompt_lexicon.get('causal', []),
            'concession': prompt_lexicon.get('concession', []),
            'condition': prompt_lexicon.get('condition', []),
            'suggestion': prompt_lexicon.get('suggestion', [])
        }
    
    def analyze_comprehensive_topic(self, essay_title: str, essay_content: str = "") -> Dict[str, Any]:
        """综合题型分析"""
        analysis = {
            'topic_identification': self._identify_topic_type(essay_title),
            'instruction_analysis': self._analyze_instructions(essay_title),
            'key_elements_analysis': self._analyze_key_elements(essay_title),
            'structure_recommendations': self._get_structure_recommendations(essay_title),
            'argument_strategies': self._get_argument_strategies(essay_title),
            'writing_approach': self._get_writing_approach(essay_title),
            'common_pitfalls': self._get_common_pitfalls(essay_title),
            'success_criteria': self._get_success_criteria(essay_title),
            'detailed_guidance': self._get_detailed_guidance(essay_title)
        }
        
        return analysis
    
    def _identify_topic_type(self, essay_title: str) -> Dict[str, Any]:
        """识别题型"""
        title_lower = essay_title.lower()
        
        # 计算每种题型的匹配分数
        type_scores = {}
        
        for type_name, patterns in self.instruction_patterns.items():
            score = 0
            matched_patterns = []
            
            for pattern in patterns:
                if pattern in title_lower:
                    score += len(pattern.split())  # 长模式权重更高
                    matched_patterns.append(pattern)
            
            if score > 0:
                type_scores[type_name] = {
                    'score': score,
                    'matched_patterns': matched_patterns
                }
        
        # 确定最佳匹配
        if type_scores:
            best_type = max(type_scores.keys(), key=lambda x: type_scores[x]['score'])
            confidence = min(type_scores[best_type]['score'] / 10.0, 1.0)
        else:
            best_type = 'unknown'
            confidence = 0.0
        
        # 获取题型详细信息
        basic_knowledge = self.topic_data.get('task2_basic_knowledge', {})
        question_types = basic_knowledge.get('question_types', {})
        
        type_info = {}
        for type_name, info in question_types.items():
            if best_type in type_name.lower() or any(best_type in inst.lower() for inst in info.get('instructions', [])):
                type_info = info
                break
        
        return {
            'identified_type': best_type,
            'confidence': confidence,
            'matched_patterns': type_scores.get(best_type, {}).get('matched_patterns', []),
            'type_characteristics': type_info.get('characteristics', ''),
            'writing_style': type_info.get('writing_style', ''),
            'structure': type_info.get('structure', ''),
            'argument_patterns': type_info.get('argument_patterns', [])
        }
    
    def _analyze_instructions(self, essay_title: str) -> Dict[str, Any]:
        """分析指令要求"""
        title_lower = essay_title.lower()
        
        # 检测关键指令词
        instruction_analysis = {
            'primary_instruction': '',
            'secondary_instructions': [],
            'required_elements': [],
            'writing_requirements': []
        }
        
        # 主要指令识别
        main_instructions = [
            ('agree or disagree', 'express clear position'),
            ('discuss both views', 'discuss both perspectives equally'),
            ('advantages and disadvantages', 'analyze pros and cons'),
            ('problems and solutions', 'identify problems and propose solutions'),
            ('to what extent', 'evaluate degree of agreement'),
            ('what is your opinion', 'provide personal viewpoint')
        ]
        
        for pattern, requirement in main_instructions:
            if pattern in title_lower:
                instruction_analysis['primary_instruction'] = pattern
                instruction_analysis['writing_requirements'].append(requirement)
                break
        
        # 检测特殊关键词
        for category, keywords in self.keyword_patterns.items():
            found_keywords = [kw for kw in keywords if kw.lower() in title_lower]
            if found_keywords:
                instruction_analysis['secondary_instructions'].append({
                    'category': category,
                    'keywords': found_keywords,
                    'implication': self._get_keyword_implication(category)
                })
        
        return instruction_analysis
    
    def _get_keyword_implication(self, category: str) -> str:
        """获取关键词类别的含义"""
        implications = {
            'absolute_terms': '题目包含绝对化表述，需要谨慎处理，可能需要反驳或限定',
            'limiters': '题目包含限定词，注意不要过度概括',
            'comparative': '题目涉及比较，需要进行对比分析',
            'causal': '题目涉及因果关系，需要分析原因和结果',
            'concession': '题目可能需要让步论证',
            'condition': '题目包含条件性表述，需要分情况讨论',
            'suggestion': '题目可能需要提出建议或解决方案'
        }
        return implications.get(category, '需要特别注意这类词汇的使用')
    
    def _analyze_key_elements(self, essay_title: str) -> Dict[str, Any]:
        """分析题目关键要素"""
        # 提取主题词
        topic_words = self._extract_topic_words(essay_title)
        
        # 分析逻辑关系
        logical_relationships = self._identify_logical_relationships(essay_title)
        
        # 识别讨论范围
        discussion_scope = self._identify_discussion_scope(essay_title)
        
        return {
            'topic_words': topic_words,
            'logical_relationships': logical_relationships,
            'discussion_scope': discussion_scope,
            'key_concepts': self._extract_key_concepts(essay_title)
        }
    
    def _extract_topic_words(self, essay_title: str) -> List[str]:
        """提取主题词"""
        # 简单的主题词提取（可以进一步优化）
        words = re.findall(r'\b[a-zA-Z]{4,}\b', essay_title)
        
        # 过滤常见功能词
        function_words = {'some', 'people', 'think', 'that', 'this', 'they', 'have', 'been', 
                         'will', 'would', 'could', 'should', 'must', 'many', 'most', 'more',
                         'what', 'when', 'where', 'which', 'while', 'with', 'from', 'about'}
        
        topic_words = [word.lower() for word in words if word.lower() not in function_words]
        return list(set(topic_words))  # 去重
    
    def _identify_logical_relationships(self, essay_title: str) -> List[str]:
        """识别逻辑关系"""
        title_lower = essay_title.lower()
        relationships = []
        
        relationship_patterns = {
            'contrast': ['however', 'but', 'while', 'whereas', 'although', 'though'],
            'cause_effect': ['because', 'since', 'as a result', 'therefore', 'thus', 'so'],
            'comparison': ['more than', 'less than', 'compared to', 'rather than'],
            'condition': ['if', 'unless', 'provided that', 'as long as'],
            'addition': ['and', 'also', 'furthermore', 'moreover', 'in addition']
        }
        
        for rel_type, patterns in relationship_patterns.items():
            if any(pattern in title_lower for pattern in patterns):
                relationships.append(rel_type)
        
        return relationships
    
    def _identify_discussion_scope(self, essay_title: str) -> Dict[str, Any]:
        """识别讨论范围"""
        title_lower = essay_title.lower()
        
        scope_indicators = {
            'global': ['world', 'global', 'international', 'worldwide', 'all countries'],
            'national': ['country', 'nation', 'government', 'society'],
            'local': ['community', 'local', 'neighborhood', 'city'],
            'individual': ['people', 'person', 'individual', 'personal'],
            'temporal': ['today', 'nowadays', 'modern', 'future', 'past', 'recent']
        }
        
        identified_scopes = []
        for scope, indicators in scope_indicators.items():
            if any(indicator in title_lower for indicator in indicators):
                identified_scopes.append(scope)
        
        return {
            'scopes': identified_scopes,
            'breadth': 'broad' if len(identified_scopes) > 2 else 'narrow',
            'complexity': 'high' if 'global' in identified_scopes and 'individual' in identified_scopes else 'medium'
        }
    
    def _extract_key_concepts(self, essay_title: str) -> List[Dict[str, str]]:
        """提取关键概念"""
        # 这里可以结合词汇数据库来识别重要概念
        topic_vocabulary = self.data_loader.get_data('topic_vocabulary')
        
        key_concepts = []
        title_lower = essay_title.lower()
        
        for topic, vocab_data in topic_vocabulary.items():
            if isinstance(vocab_data, dict) and 'keywords' in vocab_data:
                for keyword in vocab_data['keywords']:
                    if keyword.lower() in title_lower:
                        key_concepts.append({
                            'concept': keyword,
                            'topic_area': topic,
                            'importance': 'high'
                        })
        
        return key_concepts[:5]  # 返回最多5个关键概念
    
    def _get_structure_recommendations(self, essay_title: str) -> Dict[str, Any]:
        """获取结构建议"""
        topic_type = self._identify_topic_type(essay_title)
        structure_knowledge = self.topic_data.get('essay_structure_knowledge', {})
        
        # 根据题型推荐结构
        type_name = topic_type['identified_type']
        
        recommendations = {
            'recommended_structure': '1+2+1模式（开头段+2个展开段+结尾段）',
            'paragraph_organization': [],
            'introduction_elements': [],
            'body_paragraph_elements': [],
            'conclusion_elements': []
        }
        
        # 从知识库获取具体建议
        basic_knowledge = self.topic_data.get('task2_basic_knowledge', {})
        question_types = basic_knowledge.get('question_types', {})
        
        for type_name_full, type_info in question_types.items():
            if type_name in type_name_full.lower():
                recommendations.update({
                    'paragraph_organization': type_info.get('paragraph_organization', {}),
                    'introduction_elements': type_info.get('introduction_elements', []),
                    'body_paragraph_elements': type_info.get('body_elements', []),
                    'conclusion_elements': type_info.get('conclusion_elements', [])
                })
                break
        
        return recommendations
    
    def _get_argument_strategies(self, essay_title: str) -> Dict[str, Any]:
        """获取论证策略"""
        argument_construction = self.topic_data.get('argument_construction', {})
        
        strategies = {
            'primary_strategies': [],
            'supporting_techniques': [],
            'evidence_types': [],
            'logical_development': []
        }
        
        # 从论证构建知识中获取策略
        if 'argument_development_methods' in argument_construction:
            methods = argument_construction['argument_development_methods']
            strategies['primary_strategies'] = list(methods.keys())[:3]
        
        # 添加写作技巧
        writing_techniques = self.topic_data.get('writing_techniques', {})
        if 'argument_chain_extension' in writing_techniques:
            chain_extension = writing_techniques['argument_chain_extension']
            strategies['supporting_techniques'] = chain_extension.get('enhancement_logic', [])
        
        return strategies
    
    def _get_writing_approach(self, essay_title: str) -> Dict[str, Any]:
        """获取写作方法"""
        writing_techniques = self.topic_data.get('writing_techniques', {})
        
        approach = {
            'recommended_method': '5步写作法',
            'steps': [],
            'time_allocation': {},
            'key_considerations': []
        }
        
        if 'five_step_method' in writing_techniques:
            five_step = writing_techniques['five_step_method']
            approach['steps'] = five_step.get('steps', [])
        
        return approach
    
    def _get_common_pitfalls(self, essay_title: str) -> List[Dict[str, str]]:
        """获取常见陷阱"""
        topic_type = self._identify_topic_type(essay_title)['identified_type']
        
        # 根据题型返回常见错误
        common_pitfalls = {
            'agree_disagree': [
                {'pitfall': '立场不明确', 'solution': '在开头段明确表达同意或不同意的立场'},
                {'pitfall': '论证不充分', 'solution': '每个分论点都要有详细的解释和例子支持'},
                {'pitfall': '忽视反方观点', 'solution': '可以适当承认反方观点的合理性，然后反驳'}
            ],
            'discuss_both': [
                {'pitfall': '偏向一方', 'solution': '确保两个观点都有充分的讨论篇幅'},
                {'pitfall': '缺少个人观点', 'solution': '在结尾段明确表达个人立场'},
                {'pitfall': '观点混淆', 'solution': '清楚区分两个不同的观点，避免混合论述'}
            ]
        }
        
        return common_pitfalls.get(topic_type, [
            {'pitfall': '偏离主题', 'solution': '始终围绕题目要求进行论述'},
            {'pitfall': '结构混乱', 'solution': '使用清晰的段落结构和连接词'},
            {'pitfall': '例子不当', 'solution': '使用具体、相关的例子支持论点'}
        ])
    
    def _get_success_criteria(self, essay_title: str) -> Dict[str, List[str]]:
        """获取成功标准"""
        return {
            'task_response': [
                '完全回应题目所有要求',
                '观点清晰一致',
                '论证充分展开',
                '达到最低字数要求（250词）'
            ],
            'coherence_cohesion': [
                '逻辑清晰，段落组织合理',
                '有效使用连接词和指代',
                '段落内部和段落之间连贯性强'
            ],
            'lexical_resource': [
                '词汇丰富多样',
                '用词准确恰当',
                '有效使用学术词汇',
                '拼写基本正确'
            ],
            'grammatical_range': [
                '语法结构多样',
                '复杂句式使用恰当',
                '语法错误较少',
                '标点符号使用正确'
            ]
        }
    
    def _get_detailed_guidance(self, essay_title: str) -> Dict[str, Any]:
        """获取详细指导"""
        topic_type = self._identify_topic_type(essay_title)
        
        return {
            'brainstorming_questions': self._generate_brainstorming_questions(essay_title, topic_type),
            'outline_template': self._generate_outline_template(topic_type),
            'useful_expressions': self._get_useful_expressions(topic_type),
            'sample_sentences': self._get_sample_sentences(topic_type)
        }
    
    def _generate_brainstorming_questions(self, essay_title: str, topic_type: Dict) -> List[str]:
        """生成头脑风暴问题"""
        type_name = topic_type['identified_type']
        
        questions_map = {
            'agree_disagree': [
                '你同意还是不同意这个观点？为什么？',
                '支持这个观点的主要理由是什么？',
                '反对这个观点的理由有哪些？',
                '你能想到哪些具体的例子来支持你的立场？'
            ],
            'discuss_both': [
                '第一个观点的主要优点是什么？',
                '第二个观点的主要优点是什么？',
                '这两个观点各自的局限性在哪里？',
                '你个人更倾向于哪个观点？为什么？'
            ]
        }
        
        return questions_map.get(type_name, [
            '这个话题的核心问题是什么？',
            '有哪些不同的角度可以分析这个问题？',
            '你能想到哪些相关的例子或经验？',
            '这个问题对不同群体有什么影响？'
        ])
    
    def _generate_outline_template(self, topic_type: Dict) -> Dict[str, List[str]]:
        """生成大纲模板"""
        type_name = topic_type['identified_type']
        
        templates = {
            'agree_disagree': {
                '开头段': ['背景介绍', '明确立场'],
                '主体段1': ['第一个支持理由', '详细解释', '具体例子'],
                '主体段2': ['第二个支持理由', '详细解释', '具体例子'],
                '结尾段': ['重申立场', '总结要点']
            },
            'discuss_both': {
                '开头段': ['背景介绍', '概述两个观点'],
                '主体段1': ['第一个观点的优点', '详细分析', '例子支持'],
                '主体段2': ['第二个观点的优点', '详细分析', '例子支持'],
                '结尾段': ['个人观点', '平衡总结']
            }
        }
        
        return templates.get(type_name, {
            '开头段': ['背景介绍', '提出观点'],
            '主体段': ['主要论点', '支持论据', '具体例子'],
            '结尾段': ['总结观点', '呼应开头']
        })
    
    def _get_useful_expressions(self, topic_type: Dict) -> Dict[str, List[str]]:
        """获取有用表达"""
        return {
            '表达观点': [
                'In my opinion/view...',
                'I believe/think that...',
                'From my perspective...',
                'It seems to me that...'
            ],
            '举例说明': [
                'For example/instance...',
                'To illustrate this point...',
                'A case in point is...',
                'This can be seen in...'
            ],
            '对比转折': [
                'However/Nevertheless...',
                'On the other hand...',
                'In contrast...',
                'Despite this...'
            ],
            '总结结论': [
                'In conclusion...',
                'To sum up...',
                'Overall...',
                'Taking everything into account...'
            ]
        }
    
    def _get_sample_sentences(self, topic_type: Dict) -> List[str]:
        """获取示例句子"""
        return [
            'This issue has become increasingly important in recent years.',
            'There are compelling arguments on both sides of this debate.',
            'The evidence suggests that this approach has several advantages.',
            'However, it is important to consider the potential drawbacks.',
            'In conclusion, while there are valid concerns, the benefits outweigh the risks.'
        ]

# 创建全局实例
enhanced_topic_analyzer = EnhancedTopicAnalyzer()
