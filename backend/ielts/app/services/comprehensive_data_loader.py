"""
综合数据资源加载器 - 整合data目录中的所有结构化数据
用于增强题型分析、总体评语和改进建议功能
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import glob

logger = logging.getLogger(__name__)

class ComprehensiveDataLoader:
    """综合数据资源加载器"""
    
    def __init__(self):
        # 数据目录路径
        self.data_dir = Path(__file__).parent.parent.parent.parent / "data"
        
        # 缓存加载的数据
        self._cache = {}
        
        # 数据文件映射
        self.data_files = {
            # 核心评分标准
            'scoring_criteria': self.data_dir / "1. 核心评分标准数据" / "cleaned_ielts_scoring_criteria.json",
            
            # 结构与逻辑资源
            'essay_structures': self.data_dir / "3. 结构与逻辑分析资源" / "essay_structures.json",
            'cohesive_devices': self.data_dir / "3. 结构与逻辑分析资源" / "cohesive_devices.json",
            
            # 词汇资源
            'topic_vocabulary': self.data_dir / "4. 词汇资源" / "topic_vocabulary.json",
            'academic_word_list': self.data_dir / "4. 词汇资源" / "academic_word_list.json",
            'upgrade_suggestions': self.data_dir / "4. 词汇资源" / "upgrade_suggestions.json",
            'collocations_database': self.data_dir / "4. 词汇资源" / "collocations_database.json",
            'idiomatic_expressions': self.data_dir / "4. 词汇资源" / "idiomatic_expressions.json",
            
            # 语法资源
            'common_errors': self.data_dir / "5. 语法广度与准确性" / "common_errors_database.json",
            'complex_structures': self.data_dir / "5. 语法广度与准确性" / "complex_structures_library.json",
            'punctuation_rules': self.data_dir / "5. 语法广度与准确性" / "punctuation_rules.json",
            
            # 讲义知识点
            'task2_basic_knowledge': self.data_dir / "6. 讲义知识点" / "task2_basic_knowledge.json",
            'essay_structure_knowledge': self.data_dir / "6. 讲义知识点" / "essay_structure_knowledge.json",
            'argument_construction': self.data_dir / "6. 讲义知识点" / "argument_construction_knowledge.json",
            'scoring_criteria_knowledge': self.data_dir / "6. 讲义知识点" / "scoring_criteria_knowledge.json",
            'writing_techniques': self.data_dir / "6. 讲义知识点" / "writing_techniques_knowledge.json",
            
            # 衍生数据
            'instruction_types': self.data_dir / "derived" / "instruction_types.json",
            'cc_linking_categories': self.data_dir / "derived" / "cc_linking_categories.json",
            'prompt_lexicon': self.data_dir / "derived" / "prompt_lexicon.json",
        }
        
        # 范文数据目录
        self.sample_essays_dir = self.data_dir / "2. 高质量范文与样本数据" / "task2"
    
    def load_json_safely(self, file_path: Path) -> Dict[str, Any]:
        """安全加载JSON文件"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"File not found: {file_path}")
                return {}
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {str(e)}")
            return {}
    
    def get_data(self, data_key: str, force_reload: bool = False) -> Dict[str, Any]:
        """获取指定的数据资源"""
        if not force_reload and data_key in self._cache:
            return self._cache[data_key]
        
        if data_key in self.data_files:
            data = self.load_json_safely(self.data_files[data_key])
            self._cache[data_key] = data
            return data
        else:
            logger.warning(f"Unknown data key: {data_key}")
            return {}
    
    def load_sample_essays(self) -> Dict[str, List[Dict]]:
        """加载所有范文数据"""
        if 'sample_essays' in self._cache:
            return self._cache['sample_essays']
        
        sample_essays = {}
        
        # 查找所有范文JSON文件
        essay_files = glob.glob(str(self.sample_essays_dir / "*.json"))
        
        for file_path in essay_files:
            file_name = Path(file_path).stem
            essays_data = self.load_json_safely(Path(file_path))
            
            if essays_data:
                sample_essays[file_name] = essays_data
                logger.info(f"Loaded {len(essays_data)} essays from {file_name}")
        
        self._cache['sample_essays'] = sample_essays
        return sample_essays
    
    def get_topic_analysis_data(self) -> Dict[str, Any]:
        """获取题型分析相关的数据"""
        return {
            'task2_basic_knowledge': self.get_data('task2_basic_knowledge'),
            'instruction_types': self.get_data('instruction_types'),
            'essay_structure_knowledge': self.get_data('essay_structure_knowledge'),
            'argument_construction': self.get_data('argument_construction'),
            'prompt_lexicon': self.get_data('prompt_lexicon'),
            'writing_techniques': self.get_data('writing_techniques')
        }
    
    def get_vocabulary_analysis_data(self) -> Dict[str, Any]:
        """获取词汇分析相关的数据"""
        return {
            'topic_vocabulary': self.get_data('topic_vocabulary'),
            'academic_word_list': self.get_data('academic_word_list'),
            'upgrade_suggestions': self.get_data('upgrade_suggestions'),
            'collocations_database': self.get_data('collocations_database'),
            'idiomatic_expressions': self.get_data('idiomatic_expressions')
        }
    
    def get_grammar_analysis_data(self) -> Dict[str, Any]:
        """获取语法分析相关的数据"""
        return {
            'common_errors': self.get_data('common_errors'),
            'complex_structures': self.get_data('complex_structures'),
            'punctuation_rules': self.get_data('punctuation_rules')
        }
    
    def get_coherence_analysis_data(self) -> Dict[str, Any]:
        """获取连贯性分析相关的数据"""
        return {
            'essay_structures': self.get_data('essay_structures'),
            'cohesive_devices': self.get_data('cohesive_devices'),
            'cc_linking_categories': self.get_data('cc_linking_categories')
        }
    
    def get_scoring_reference_data(self) -> Dict[str, Any]:
        """获取评分参考数据"""
        return {
            'scoring_criteria': self.get_data('scoring_criteria'),
            'scoring_criteria_knowledge': self.get_data('scoring_criteria_knowledge'),
            'sample_essays': self.load_sample_essays()
        }
    
    def get_improvement_suggestions_data(self) -> Dict[str, Any]:
        """获取改进建议相关的数据"""
        return {
            'upgrade_suggestions': self.get_data('upgrade_suggestions'),
            'common_errors': self.get_data('common_errors'),
            'writing_techniques': self.get_data('writing_techniques'),
            'complex_structures': self.get_data('complex_structures'),
            'topic_vocabulary': self.get_data('topic_vocabulary'),
            'academic_word_list': self.get_data('academic_word_list'),
            'idiomatic_expressions': self.get_data('idiomatic_expressions')
        }
    
    def get_comprehensive_data(self) -> Dict[str, Any]:
        """获取所有数据资源"""
        comprehensive_data = {}
        
        # 加载所有基础数据
        for key in self.data_files.keys():
            comprehensive_data[key] = self.get_data(key)
        
        # 加载范文数据
        comprehensive_data['sample_essays'] = self.load_sample_essays()
        
        return comprehensive_data
    
    def find_relevant_sample_essays(self, topic: str, essay_type: str, target_band: float = None) -> List[Dict]:
        """查找相关的范文"""
        sample_essays = self.load_sample_essays()
        relevant_essays = []
        
        # 根据题型查找
        type_mapping = {
            'agree_disagree': ['agree_disagree', 'opinion'],
            'discuss_both': ['discuss_both'],
            'advantages_disadvantages': ['advantages_disadvantages', 'pros_cons'],
            'problem_solution': ['problem_solution', 'causes_solutions'],
            'two_part_question': ['two_part']
        }
        
        target_types = type_mapping.get(essay_type, [essay_type])
        
        for file_name, essays in sample_essays.items():
            # 检查文件名是否匹配题型
            if any(t in file_name.lower() for t in target_types):
                if isinstance(essays, list):
                    for essay in essays:
                        if self._is_essay_relevant(essay, topic, target_band):
                            relevant_essays.append(essay)
                elif isinstance(essays, dict):
                    for essay_key, essay in essays.items():
                        if self._is_essay_relevant(essay, topic, target_band):
                            relevant_essays.append(essay)
        
        return relevant_essays[:5]  # 返回最多5篇相关范文
    
    def _is_essay_relevant(self, essay: Dict, topic: str, target_band: float = None) -> bool:
        """判断范文是否相关"""
        if not isinstance(essay, dict):
            return False
        
        # 检查分数段
        if target_band:
            essay_band = essay.get('band_score', essay.get('score', 0))
            if isinstance(essay_band, (int, float)):
                if abs(essay_band - target_band) > 1.0:  # 分数差距超过1分
                    return False
        
        # 检查主题相关性（简单关键词匹配）
        essay_content = str(essay.get('content', '')) + str(essay.get('title', ''))
        topic_words = topic.lower().split()
        
        relevance_score = 0
        for word in topic_words:
            if len(word) > 3 and word in essay_content.lower():
                relevance_score += 1
        
        return relevance_score > 0
    
    def get_band_specific_examples(self, band_score: float) -> Dict[str, List[str]]:
        """获取特定分数段的示例"""
        scoring_criteria = self.get_data('scoring_criteria')
        examples = {
            'strengths': [],
            'weaknesses': [],
            'characteristics': []
        }
        
        # 从评分标准中提取对应分数段的特征
        band_key = f"band{int(band_score)}"
        
        for task_type in ['task1', 'task2']:
            task_data = scoring_criteria.get(task_type, {})
            for dimension in ['TR', 'CC', 'LR', 'GRA']:
                dimension_data = task_data.get(dimension, {})
                band_data = dimension_data.get(band_key, [])
                
                if isinstance(band_data, list):
                    examples['characteristics'].extend(band_data[:2])  # 取前2个特征
        
        return examples

# 创建全局实例
comprehensive_data_loader = ComprehensiveDataLoader()
