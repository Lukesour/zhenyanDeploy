"""
评分标准增强器 - 利用高质量数据提升评分准确性
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
import pandas as pd
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)

class ScoringCriteriaEnhancer:
    """评分标准增强器 - 基于大量高质量样本数据"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent.parent / "data"
        self.scoring_criteria = {}
        self.high_band_samples = []
        self.mid_band_samples = []
        self.low_band_samples = []
        self.training_data = None
        self.score_patterns = {}
        
        self._load_all_data()
        self._analyze_score_patterns()
    
    def _load_all_data(self):
        """加载所有评分相关数据"""
        try:
            # 1. 加载核心评分标准
            criteria_file = self.data_dir / "1. 核心评分标准数据" / "cleaned_ielts_scoring_criteria.json"
            with open(criteria_file, 'r', encoding='utf-8') as f:
                self.scoring_criteria = json.load(f)
            
            # 2. 加载高质量范文样本
            high_band_file = self.data_dir / "2. 高质量范文与样本数据" / "task2" / "cleaned_task2_high_band.json"
            with open(high_band_file, 'r', encoding='utf-8') as f:
                self.high_band_samples = json.load(f)
            
            mid_band_file = self.data_dir / "2. 高质量范文与样本数据" / "task2" / "cleaned_task2_mid_band.json"
            with open(mid_band_file, 'r', encoding='utf-8') as f:
                self.mid_band_samples = json.load(f)
            
            low_band_file = self.data_dir / "2. 高质量范文与样本数据" / "task2" / "cleaned_task2_low_band.json"
            with open(low_band_file, 'r', encoding='utf-8') as f:
                self.low_band_samples = json.load(f)
            
            # 3. 加载训练数据（采样以避免内存问题）
            train_file = self.data_dir / "2. 高质量范文与样本数据" / "task2" / "train.csv"
            if train_file.exists():
                # 只加载前10000条数据进行分析
                self.training_data = pd.read_csv(train_file, nrows=10000)
            
            logger.info("Successfully loaded all scoring data")
            
        except Exception as e:
            logger.error(f"Error loading scoring data: {str(e)}")
    
    def _analyze_score_patterns(self):
        """分析评分模式，提取关键特征"""
        try:
            # 分析高分样本的特征
            self.score_patterns = {
                "high_band": self._extract_features(self.high_band_samples, "high"),
                "mid_band": self._extract_features(self.mid_band_samples, "mid"),
                "low_band": self._extract_features(self.low_band_samples, "low")
            }
            
            # 从训练数据中提取分数分布
            if self.training_data is not None:
                self._analyze_training_patterns()
                
        except Exception as e:
            logger.error(f"Error analyzing score patterns: {str(e)}")
    
    def _extract_features(self, samples: List[Dict], band_level: str) -> Dict[str, Any]:
        """从样本中提取关键特征"""
        features = {
            "word_count_range": [],
            "paragraph_count": [],
            "common_phrases": [],
            "score_distribution": defaultdict(list),
            "feedback_keywords": []
        }
        
        for sample in samples[:100]:  # 限制分析数量
            try:
                essay = sample.get("essay", {})
                scores = sample.get("scores", {})
                feedback = sample.get("detailed_feedback", {})
                
                # 词数统计
                word_count = essay.get("word_count", 0)
                if word_count > 0:
                    features["word_count_range"].append(word_count)
                
                # 段落数统计
                text = essay.get("text", "")
                if text:
                    paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
                    features["paragraph_count"].append(paragraph_count)
                
                # 分数分布
                overall_score = scores.get("overall", 0)
                if overall_score > 0:
                    features["score_distribution"]["overall"].append(overall_score)
                
                # 提取反馈关键词
                if isinstance(feedback, dict):
                    feedback_text = feedback.get("overall_feedback", "")
                    if feedback_text:
                        features["feedback_keywords"].extend(
                            self._extract_keywords_from_feedback(feedback_text)
                        )
                        
            except Exception as e:
                logger.warning(f"Error processing sample: {str(e)}")
                continue
        
        # 计算统计信息
        if features["word_count_range"]:
            features["avg_word_count"] = np.mean(features["word_count_range"])
            features["word_count_std"] = np.std(features["word_count_range"])
        
        if features["paragraph_count"]:
            features["avg_paragraph_count"] = np.mean(features["paragraph_count"])
        
        return features
    
    def _extract_keywords_from_feedback(self, feedback_text: str) -> List[str]:
        """从反馈中提取关键词"""
        keywords = []
        
        # 常见的评分关键词
        positive_indicators = [
            "excellent", "outstanding", "sophisticated", "comprehensive",
            "coherent", "cohesive", "accurate", "appropriate", "effective",
            "clear", "logical", "well-organized", "relevant", "convincing"
        ]
        
        negative_indicators = [
            "limited", "inadequate", "unclear", "inaccurate", "inappropriate",
            "repetitive", "basic", "simple", "errors", "mistakes", "lacks"
        ]
        
        feedback_lower = feedback_text.lower()
        
        for keyword in positive_indicators + negative_indicators:
            if keyword in feedback_lower:
                keywords.append(keyword)
        
        return keywords
    
    def _analyze_training_patterns(self):
        """分析训练数据中的评分模式"""
        try:
            if 'band' in self.training_data.columns:
                # 确保band列是数值类型
                self.training_data['band'] = pd.to_numeric(self.training_data['band'], errors='coerce')

                # 移除无效的分数值
                valid_data = self.training_data.dropna(subset=['band'])

                if not valid_data.empty:
                    # 分析分数分布
                    score_dist = valid_data['band'].value_counts().sort_index()
                    self.score_patterns["training_distribution"] = score_dist.to_dict()

                    # 分析高分样本特征
                    high_score_samples = valid_data[valid_data['band'] >= 7]
                    if not high_score_samples.empty:
                        self.score_patterns["high_score_characteristics"] = {
                            "count": len(high_score_samples),
                            "percentage": len(high_score_samples) / len(valid_data) * 100
                        }

        except Exception as e:
            logger.warning(f"Error analyzing training patterns: {str(e)}")
    
    def get_enhanced_criteria(self, dimension: str, task_type: str, score_range: Tuple[float, float] = None) -> Dict[str, Any]:
        """获取增强的评分标准"""
        try:
            # 基础标准
            base_criteria = self.scoring_criteria.get(task_type, {}).get(dimension, {})
            
            # 增强信息
            enhanced_criteria = {
                "base_criteria": base_criteria,
                "score_patterns": self.score_patterns,
                "dimension_specific": self._get_dimension_specific_guidance(dimension),
                "sample_references": self._get_relevant_samples(dimension, score_range)
            }
            
            return enhanced_criteria
            
        except Exception as e:
            logger.error(f"Error getting enhanced criteria: {str(e)}")
            return {"base_criteria": {}}
    
    def _get_dimension_specific_guidance(self, dimension: str) -> Dict[str, Any]:
        """获取维度特定的指导"""
        guidance = {
            "TR": {
                "key_indicators": ["task_response", "position_clarity", "argument_development"],
                "common_issues": ["off_topic", "insufficient_development", "unclear_position"]
            },
            "CC": {
                "key_indicators": ["paragraph_structure", "linking_devices", "logical_flow"],
                "common_issues": ["poor_paragraphing", "overuse_connectors", "unclear_progression"]
            },
            "LR": {
                "key_indicators": ["vocabulary_range", "accuracy", "appropriateness"],
                "common_issues": ["repetition", "inappropriate_register", "spelling_errors"]
            },
            "GRA": {
                "key_indicators": ["sentence_variety", "accuracy", "punctuation"],
                "common_issues": ["simple_sentences", "grammar_errors", "punctuation_mistakes"]
            }
        }
        
        return guidance.get(dimension, {})
    
    def _get_relevant_samples(self, dimension: str, score_range: Tuple[float, float] = None) -> List[Dict]:
        """获取相关的样本参考"""
        relevant_samples = []
        
        # 根据分数范围选择样本
        if score_range:
            min_score, max_score = score_range
            
            if max_score >= 8:
                relevant_samples.extend(self.high_band_samples[:3])
            elif max_score >= 6:
                relevant_samples.extend(self.mid_band_samples[:3])
            else:
                relevant_samples.extend(self.low_band_samples[:3])
        else:
            # 提供各个分数段的代表性样本
            relevant_samples.extend(self.high_band_samples[:2])
            relevant_samples.extend(self.mid_band_samples[:2])
            relevant_samples.extend(self.low_band_samples[:2])
        
        return relevant_samples
    
    def predict_score_range(self, essay_features: Dict[str, Any]) -> Tuple[float, float]:
        """基于特征预测分数范围 - 改进版本，减少对7分的偏向"""
        try:
            word_count = essay_features.get("word_count", 0)
            paragraph_count = essay_features.get("paragraph_count", 0)
            response_completeness = essay_features.get("response_completeness", 0.5)
            argument_depth = essay_features.get("argument_depth", 0.5)

            # 计算综合质量分数
            quality_score = self._calculate_quality_score(
                word_count, paragraph_count, response_completeness, argument_depth
            )

            # 基于质量分数预测范围，避免过度集中在7分
            if quality_score >= 0.85:
                return (8.0, 9.0)  # 高质量作文
            elif quality_score >= 0.75:
                return (7.5, 8.5)  # 较高质量
            elif quality_score >= 0.65:
                return (6.5, 7.5)  # 中上质量
            elif quality_score >= 0.55:
                return (6.0, 7.0)  # 中等质量
            elif quality_score >= 0.45:
                return (5.0, 6.5)  # 中下质量
            elif quality_score >= 0.35:
                return (4.0, 5.5)  # 较低质量
            else:
                return (3.0, 4.5)  # 低质量

        except Exception as e:
            logger.error(f"Error predicting score range: {str(e)}")
            return (5.0, 6.0)

    def _calculate_quality_score(self, word_count: int, paragraph_count: int,
                               response_completeness: float, argument_depth: float) -> float:
        """计算综合质量分数"""
        try:
            # 词数评分 (0-1)
            if word_count >= 350:
                word_score = 1.0
            elif word_count >= 300:
                word_score = 0.9
            elif word_count >= 250:
                word_score = 0.7
            elif word_count >= 200:
                word_score = 0.5
            elif word_count >= 150:
                word_score = 0.3
            else:
                word_score = 0.1

            # 段落结构评分 (0-1)
            if paragraph_count >= 5:
                structure_score = 1.0
            elif paragraph_count == 4:
                structure_score = 0.9
            elif paragraph_count == 3:
                structure_score = 0.6
            elif paragraph_count == 2:
                structure_score = 0.3
            else:
                structure_score = 0.1

            # 综合评分，权重分配
            quality_score = (
                word_score * 0.25 +           # 词数权重25%
                structure_score * 0.25 +      # 结构权重25%
                response_completeness * 0.25 + # 任务完成度权重25%
                argument_depth * 0.25          # 论证深度权重25%
            )

            return max(0.0, min(1.0, quality_score))

        except Exception as e:
            logger.error(f"Error calculating quality score: {str(e)}")
            return 0.5
    
    def get_score_improvement_suggestions(self, current_score: float, target_score: float) -> List[str]:
        """获取分数提升建议"""
        suggestions = []
        
        if target_score > current_score:
            gap = target_score - current_score
            
            if gap >= 2.0:
                suggestions.extend([
                    "需要全面提升写作质量，建议系统性学习",
                    "重点关注任务回应和论证发展",
                    "加强词汇和语法的准确性"
                ])
            elif gap >= 1.0:
                suggestions.extend([
                    "需要在特定维度上重点改进",
                    "提升论证的深度和说服力",
                    "改善文章的连贯性和衔接"
                ])
            else:
                suggestions.extend([
                    "接近目标分数，需要细节优化",
                    "减少语法和词汇错误",
                    "提升表达的准确性和地道性"
                ])
        
        return suggestions
