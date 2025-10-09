"""
数据加载服务 - 用于初始化系统数据
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.ielts.app.core.database import SessionLocal
from backend.ielts.app.models.reference_data import BandDescriptor, SampleEssay, VocabularyResource, GrammarRule

logger = logging.getLogger(__name__)

class EnhancedDataLoader:
    """增强的数据加载器 - 基于 /data 目录中的结构化数据"""

    def __init__(self):
        self.db = SessionLocal()
        # 数据目录路径
        self.data_dir = Path(__file__).parent.parent.parent.parent / "data"

        # 数据文件路径
        self.scoring_criteria_file = self.data_dir / "1. 核心评分标准数据" / "cleaned_ielts_scoring_criteria.json"
        self.essay_structures_file = self.data_dir / "3. 结构与逻辑分析资源" / "essay_structures.json"
        self.cohesive_devices_file = self.data_dir / "3. 结构与逻辑分析资源" / "cohesive_devices.json"
        self.topic_vocabulary_file = self.data_dir / "4. 词汇资源" / "topic_vocabulary.json"
        self.upgrade_suggestions_file = self.data_dir / "4. 词汇资源" / "upgrade_suggestions.json"
        self.academic_word_list_file = self.data_dir / "4. 词汇资源" / "academic_word_list.json"
        self.collocations_file = self.data_dir / "4. 词汇资源" / "collocations_database.json"
        self.common_errors_file = self.data_dir / "5. 语法广度与准确性" / "common_errors_database.json"
        self.complex_structures_file = self.data_dir / "5. 语法广度与准确性" / "complex_structures_library.json"

        # 范文数据目录
        self.task2_dir = self.data_dir / "2. 高质量范文与样本数据" / "task2"

    def load_file_safely(self, file_path: Path) -> Dict[str, Any]:
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
    
    def load_band_descriptors(self):
        """从官方评分标准文件加载评分标准数据"""
        logger.info("Loading band descriptors from official criteria...")

        # 加载官方评分标准
        criteria_data = self.load_file_safely(self.scoring_criteria_file)
        if not criteria_data:
            logger.error("Failed to load scoring criteria data")
            return

        descriptors_loaded = 0

        # 处理 Task 1 和 Task 2 的评分标准
        for task_type, task_data in criteria_data.items():
            for dimension, dimension_data in task_data.items():
                for band_level, criteria_list in dimension_data.items():
                    # 提取分数（如 "band9" -> 9.0）
                    try:
                        band_score = float(band_level.replace("band", ""))
                    except ValueError:
                        continue

                    # 检查是否已存在
                    existing = self.db.query(BandDescriptor).filter(
                        BandDescriptor.dimension == dimension,
                        BandDescriptor.band_score == band_score,
                        BandDescriptor.task_type == task_type
                    ).first()

                    if not existing:
                        # 将标准列表转换为文本
                        criteria_text = "; ".join(criteria_list)

                        descriptor = BandDescriptor(
                            dimension=dimension,
                            band_score=band_score,
                            task_type=task_type,
                            criteria_text=criteria_text,
                            key_features=criteria_list
                        )
                        self.db.add(descriptor)
                        descriptors_loaded += 1

        self.db.commit()
        logger.info(f"Loaded {descriptors_loaded} band descriptors successfully")
    
    def load_sample_essays(self):
        """从范文数据文件加载范文数据"""
        logger.info("Loading sample essays from data files...")

        essays_loaded = 0

        # 加载不同类型的范文文件
        essay_files = [
            "cleaned_task2_high_band.json",
            "cleaned_task2_mid_band.json",
            "cleaned_task2_low_band.json",
            "cleaned_task2_agree_disagree.json",
            "cleaned_task2_discuss_both.json",
            "cleaned_task2_advantages_disadvantages.json",
            "cleaned_task2_problem_solution.json"
        ]

        for file_name in essay_files:
            file_path = self.task2_dir / file_name
            essay_data = self.load_file_safely(file_path)

            if isinstance(essay_data, list):
                for essay_item in essay_data[:10]:  # 限制每个文件加载10篇范文
                    try:
                        # 检查是否已存在
                        prompt_text = essay_item.get("prompt", {}).get("text", "")
                        if not prompt_text:
                            continue

                        existing = self.db.query(SampleEssay).filter(
                            SampleEssay.prompt == prompt_text
                        ).first()

                        if not existing:
                            # 提取题型
                            essay_type = essay_item.get("prompt", {}).get("type", "unknown")

                            # 构建范文数据
                            sample_essay = SampleEssay(
                                task_type="task2",
                                essay_type=essay_type,
                                topic=self._extract_topic_from_prompt(prompt_text),
                                prompt=prompt_text,
                                content=essay_item.get("essay", {}).get("text", ""),
                                word_count=essay_item.get("essay", {}).get("word_count", 0),
                                overall_score=essay_item.get("scores", {}).get("overall", 0.0),
                                tr_score=essay_item.get("scores", {}).get("TR"),
                                cc_score=essay_item.get("scores", {}).get("CC"),
                                lr_score=essay_item.get("scores", {}).get("LR"),
                                gra_score=essay_item.get("scores", {}).get("GRA"),
                                examiner_comment=essay_item.get("detailed_feedback", {}).get("overall_feedback", ""),
                                structure_analysis=essay_item.get("structure_analysis", {}),
                                vocabulary_highlights=essay_item.get("vocabulary_highlights", []),
                                grammar_features=essay_item.get("grammar_features", [])
                            )

                            self.db.add(sample_essay)
                            essays_loaded += 1

                    except Exception as e:
                        logger.error(f"Error processing essay from {file_name}: {str(e)}")
                        continue

        self.db.commit()
        logger.info(f"Loaded {essays_loaded} sample essays successfully")

    def _extract_topic_from_prompt(self, prompt: str) -> str:
        """从题目中提取主题"""
        # 简单的主题提取逻辑，可以后续优化
        keywords = {
            "technology": ["computer", "internet", "digital", "online", "technology"],
            "education": ["education", "school", "university", "learning", "student"],
            "environment": ["environment", "pollution", "climate", "green", "sustainable"],
            "health": ["health", "medical", "hospital", "disease", "fitness"],
            "society": ["society", "social", "community", "culture", "tradition"],
            "work": ["work", "job", "employment", "career", "business"]
        }

        prompt_lower = prompt.lower()
        for topic, words in keywords.items():
            if any(word in prompt_lower for word in words):
                return topic

        return "general"

    def load_vocabulary_resources_enhanced(self):
        """从词汇资源文件加载词汇数据"""
        logger.info("Loading vocabulary resources from data files...")

        vocab_loaded = 0

        # 加载主题词汇
        topic_vocab_data = self.load_file_safely(self.topic_vocabulary_file)
        for topic, data in topic_vocab_data.items():
            if isinstance(data, dict) and "keywords" in data:
                for keyword in data["keywords"]:
                    existing = self.db.query(VocabularyResource).filter(
                        VocabularyResource.word == keyword
                    ).first()

                    if not existing:
                        vocab = VocabularyResource(
                            word=keyword,
                            word_type="noun/adjective/verb",  # 简化处理
                            definition=f"Topic vocabulary for {topic}",
                            category="topic_vocabulary",
                            topic=topic,
                            difficulty_level="intermediate",
                            collocations=[],
                            synonyms=[],
                            example_sentences=[],
                            frequency_score=0.7,
                            importance_score=0.8
                        )
                        self.db.add(vocab)
                        vocab_loaded += 1

        # 加载学术词汇表
        awl_data = self.load_file_safely(self.academic_word_list_file)
        if isinstance(awl_data, dict) and "words" in awl_data:
            for word_data in awl_data["words"][:100]:  # 限制数量
                if isinstance(word_data, dict):
                    word = word_data.get("word", "")
                    if word:
                        existing = self.db.query(VocabularyResource).filter(
                            VocabularyResource.word == word
                        ).first()

                        if not existing:
                            vocab = VocabularyResource(
                                word=word,
                                word_type=word_data.get("part_of_speech", "unknown"),
                                definition=word_data.get("definition", ""),
                                category="AWL",
                                topic="academic",
                                difficulty_level="advanced",
                                collocations=word_data.get("collocations", []),
                                synonyms=word_data.get("synonyms", []),
                                example_sentences=word_data.get("examples", []),
                                frequency_score=word_data.get("frequency", 0.8),
                                importance_score=0.9
                            )
                            self.db.add(vocab)
                            vocab_loaded += 1

        self.db.commit()
        logger.info(f"Loaded {vocab_loaded} vocabulary resources successfully")

    def load_vocabulary_resources(self):
        """加载词汇资源"""
        logger.info("Loading vocabulary resources...")
        
        vocabulary_data = [
            {
                "word": "significant",
                "word_type": "adjective",
                "definition": "sufficiently great or important to be worthy of attention; noteworthy",
                "category": "AWL",
                "topic": "general",
                "difficulty_level": "intermediate",
                "collocations": ["significant impact", "significant difference", "significant improvement"],
                "synonyms": ["important", "considerable", "substantial", "notable"],
                "example_sentences": [
                    "There has been a significant improvement in air quality.",
                    "The research findings are significant for future policy decisions."
                ],
                "frequency_score": 0.85,
                "importance_score": 0.9
            },
            {
                "word": "furthermore",
                "word_type": "adverb",
                "definition": "in addition; besides (used to introduce a fresh consideration in an argument)",
                "category": "linking_word",
                "topic": "general",
                "difficulty_level": "intermediate",
                "collocations": ["furthermore, it should be noted", "furthermore, research shows"],
                "synonyms": ["moreover", "additionally", "in addition", "besides"],
                "example_sentences": [
                    "The policy is expensive. Furthermore, it may not be effective.",
                    "Furthermore, we need to consider the environmental impact."
                ],
                "frequency_score": 0.7,
                "importance_score": 0.8
            }
        ]
        
        for vocab_data in vocabulary_data:
            existing = self.db.query(VocabularyResource).filter(
                VocabularyResource.word == vocab_data["word"]
            ).first()
            
            if not existing:
                vocab = VocabularyResource(**vocab_data)
                self.db.add(vocab)
        
        self.db.commit()
        logger.info("Vocabulary resources loaded successfully")
    
    def load_grammar_rules(self):
        """加载语法规则"""
        logger.info("Loading grammar rules...")
        
        grammar_data = [
            {
                "rule_name": "Subject-Verb Agreement",
                "rule_category": "agreement",
                "description": "The subject and verb must agree in number (singular/plural)",
                "error_patterns": [
                    "The students *is* studying → The students *are* studying",
                    "Each of the books *are* → Each of the books *is*"
                ],
                "correct_examples": [
                    "The student is studying hard.",
                    "The students are studying hard.",
                    "Each of the books is interesting."
                ],
                "incorrect_examples": [
                    "The student are studying hard.",
                    "The students is studying hard.",
                    "Each of the books are interesting."
                ],
                "complexity_level": "basic",
                "importance_score": 0.95
            },
            {
                "rule_name": "Article Usage",
                "rule_category": "article",
                "description": "Proper use of definite (the) and indefinite (a/an) articles",
                "error_patterns": [
                    "I saw *a* movie yesterday → I saw *the* movie yesterday (if specific)",
                    "He is *the* teacher → He is *a* teacher (if one of many)"
                ],
                "correct_examples": [
                    "I need a pen to write.",
                    "The pen you gave me is broken.",
                    "Education is important."
                ],
                "incorrect_examples": [
                    "I need the pen to write. (when any pen will do)",
                    "A pen you gave me is broken.",
                    "The education is important. (in general sense)"
                ],
                "complexity_level": "intermediate",
                "importance_score": 0.8
            }
        ]
        
        for grammar_data in grammar_data:
            existing = self.db.query(GrammarRule).filter(
                GrammarRule.rule_name == grammar_data["rule_name"]
            ).first()
            
            if not existing:
                rule = GrammarRule(**grammar_data)
                self.db.add(rule)
        
        self.db.commit()
        logger.info("Grammar rules loaded successfully")
    
    def load_grammar_rules_enhanced(self):
        """从语法数据文件加载语法规则"""
        logger.info("Loading grammar rules from data files...")

        rules_loaded = 0

        # 加载常见错误数据库
        errors_data = self.load_file_safely(self.common_errors_file)
        if isinstance(errors_data, dict) and "entries" in errors_data:
            for error_entry in errors_data["entries"][:20]:  # 限制数量
                rule_name = error_entry.get("error_type_cn", "未知错误")

                existing = self.db.query(GrammarRule).filter(
                    GrammarRule.rule_name == rule_name
                ).first()

                if not existing:
                    rule = GrammarRule(
                        rule_name=rule_name,
                        rule_category=error_entry.get("error_type", "general"),
                        description=error_entry.get("explanation_cn", ""),
                        error_patterns=[ex.get("incorrect", "") for ex in error_entry.get("examples", [])],
                        correct_examples=[ex.get("correct", "") for ex in error_entry.get("examples", [])],
                        incorrect_examples=[ex.get("incorrect", "") for ex in error_entry.get("examples", [])],
                        complexity_level=error_entry.get("impact_on_score", "medium").lower(),
                        importance_score=0.8 if error_entry.get("impact_on_score") == "High" else 0.6
                    )
                    self.db.add(rule)
                    rules_loaded += 1

        # 加载复杂句型库
        structures_data = self.load_file_safely(self.complex_structures_file)
        if isinstance(structures_data, dict) and "entries" in structures_data:
            for structure_entry in structures_data["entries"][:15]:  # 限制数量
                structure_name = structure_entry.get("structure_name_cn", "复杂句型")

                existing = self.db.query(GrammarRule).filter(
                    GrammarRule.rule_name == structure_name
                ).first()

                if not existing:
                    examples = structure_entry.get("examples", [])
                    correct_examples = [ex.get("sentence", "") for ex in examples if ex.get("sentence")]

                    rule = GrammarRule(
                        rule_name=structure_name,
                        rule_category="complex_structure",
                        description=structure_entry.get("function_cn", ""),
                        error_patterns=[],
                        correct_examples=correct_examples,
                        incorrect_examples=[],
                        complexity_level="advanced",
                        importance_score=0.9
                    )
                    self.db.add(rule)
                    rules_loaded += 1

        self.db.commit()
        logger.info(f"Loaded {rules_loaded} grammar rules successfully")

    def load_all_data(self):
        """加载所有数据"""
        try:
            self.load_band_descriptors()
            self.load_sample_essays()
            self.load_vocabulary_resources_enhanced()
            self.load_grammar_rules_enhanced()
            logger.info("All enhanced data loaded successfully")
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            self.db.rollback()
        finally:
            self.db.close()

# 创建增强数据加载器实例
data_loader = EnhancedDataLoader()

if __name__ == "__main__":
    data_loader.load_all_data()
