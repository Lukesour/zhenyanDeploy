"""
训练数据分析器 - 基于大量训练数据的评分模式学习
"""

import pandas as pd
import numpy as np
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict, Counter
import pickle

logger = logging.getLogger(__name__)

class TrainingDataAnalyzer:
    """训练数据分析器 - 从大量评分数据中学习评分模式"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent.parent / "data"
        self.cache_dir = self.data_dir / "derived"
        self.cache_dir.mkdir(exist_ok=True)
        
        # 评分模式缓存
        self.score_patterns = {}
        self.vocabulary_patterns = {}
        self.structure_patterns = {}
        self.feedback_patterns = {}
        
        # 加载或分析数据
        self._load_or_analyze_data()
    
    def _load_or_analyze_data(self):
        """加载缓存数据或重新分析"""
        cache_file = self.cache_dir / "training_patterns_cache.pkl"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                    self.score_patterns = cached_data.get("score_patterns", {})
                    self.vocabulary_patterns = cached_data.get("vocabulary_patterns", {})
                    self.structure_patterns = cached_data.get("structure_patterns", {})
                    self.feedback_patterns = cached_data.get("feedback_patterns", {})
                logger.info("Loaded training patterns from cache")
                return
            except Exception as e:
                logger.warning(f"Failed to load cache: {str(e)}")
        
        # 重新分析数据
        self._analyze_training_data()
        self._save_cache()
    
    def _analyze_training_data(self):
        """分析训练数据"""
        try:
            train_file = self.data_dir / "2. 高质量范文与样本数据" / "task2" / "train.csv"
            
            if not train_file.exists():
                logger.error("Training data file not found")
                return
            
            logger.info("Starting training data analysis...")
            
            # 分批读取数据以避免内存问题
            chunk_size = 5000
            total_processed = 0
            
            for chunk in pd.read_csv(train_file, chunksize=chunk_size):
                self._process_chunk(chunk)
                total_processed += len(chunk)
                
                if total_processed >= 50000:  # 限制处理数量
                    break
                    
                if total_processed % 10000 == 0:
                    logger.info(f"Processed {total_processed} samples")
            
            logger.info(f"Training data analysis completed. Processed {total_processed} samples")
            
        except Exception as e:
            logger.error(f"Error analyzing training data: {str(e)}")
    
    def _process_chunk(self, chunk: pd.DataFrame):
        """处理数据块"""
        for _, row in chunk.iterrows():
            try:
                essay_text = str(row.get('essay', ''))
                evaluation = str(row.get('evaluation', ''))
                band_score_raw = row.get('band', 0)

                # 确保band_score是数值类型
                try:
                    band_score = float(band_score_raw) if band_score_raw else 0
                except (ValueError, TypeError):
                    band_score = 0

                if not essay_text or not evaluation or band_score == 0:
                    continue
                
                # 分析评分模式
                self._analyze_score_patterns(essay_text, evaluation, band_score)
                
                # 分析词汇模式
                self._analyze_vocabulary_patterns(essay_text, band_score)
                
                # 分析结构模式
                self._analyze_structure_patterns(essay_text, band_score)
                
                # 分析反馈模式
                self._analyze_feedback_patterns(evaluation, band_score)
                
            except Exception as e:
                logger.warning(f"Error processing row: {str(e)}")
                continue
    
    def _analyze_score_patterns(self, essay_text: str, evaluation: str, band_score: float):
        """分析评分模式"""
        try:
            word_count = len(essay_text.split())
            paragraph_count = len([p for p in essay_text.split('\n\n') if p.strip()])
            
            score_range = self._get_score_range(band_score)
            
            if score_range not in self.score_patterns:
                self.score_patterns[score_range] = {
                    "word_counts": [],
                    "paragraph_counts": [],
                    "avg_sentence_length": [],
                    "sample_count": 0
                }
            
            self.score_patterns[score_range]["word_counts"].append(word_count)
            self.score_patterns[score_range]["paragraph_counts"].append(paragraph_count)
            
            # 计算平均句长
            sentences = re.split(r'[.!?]+', essay_text)
            valid_sentences = [s.strip() for s in sentences if s.strip()]
            if valid_sentences:
                avg_sentence_length = sum(len(s.split()) for s in valid_sentences) / len(valid_sentences)
                self.score_patterns[score_range]["avg_sentence_length"].append(avg_sentence_length)
            
            self.score_patterns[score_range]["sample_count"] += 1
            
        except Exception as e:
            logger.warning(f"Error analyzing score patterns: {str(e)}")
    
    def _analyze_vocabulary_patterns(self, essay_text: str, band_score: float):
        """分析词汇模式"""
        try:
            score_range = self._get_score_range(band_score)
            
            if score_range not in self.vocabulary_patterns:
                self.vocabulary_patterns[score_range] = {
                    "common_words": Counter(),
                    "unique_words": set(),
                    "word_lengths": [],
                    "academic_indicators": []
                }
            
            words = re.findall(r'\b[a-zA-Z]+\b', essay_text.lower())
            
            # 统计常用词
            self.vocabulary_patterns[score_range]["common_words"].update(words)
            
            # 统计独特词汇
            self.vocabulary_patterns[score_range]["unique_words"].update(words)
            
            # 统计词长
            word_lengths = [len(word) for word in words]
            self.vocabulary_patterns[score_range]["word_lengths"].extend(word_lengths)
            
            # 检测学术词汇指标
            academic_words = [word for word in words if len(word) > 6]
            self.vocabulary_patterns[score_range]["academic_indicators"].extend(academic_words)
            
        except Exception as e:
            logger.warning(f"Error analyzing vocabulary patterns: {str(e)}")
    
    def _analyze_structure_patterns(self, essay_text: str, band_score: float):
        """分析结构模式"""
        try:
            score_range = self._get_score_range(band_score)
            
            if score_range not in self.structure_patterns:
                self.structure_patterns[score_range] = {
                    "transition_words": Counter(),
                    "paragraph_starters": Counter(),
                    "conclusion_patterns": Counter()
                }
            
            # 检测过渡词
            transition_words = [
                "however", "furthermore", "moreover", "therefore", "consequently",
                "in addition", "on the other hand", "in contrast", "similarly",
                "firstly", "secondly", "finally", "in conclusion"
            ]
            
            text_lower = essay_text.lower()
            for word in transition_words:
                if word in text_lower:
                    self.structure_patterns[score_range]["transition_words"][word] += 1
            
            # 分析段落开头
            paragraphs = [p.strip() for p in essay_text.split('\n\n') if p.strip()]
            for para in paragraphs:
                first_words = ' '.join(para.split()[:3]).lower()
                self.structure_patterns[score_range]["paragraph_starters"][first_words] += 1
            
            # 分析结论模式
            if paragraphs:
                last_para = paragraphs[-1].lower()
                conclusion_starters = ["in conclusion", "to conclude", "in summary", "overall"]
                for starter in conclusion_starters:
                    if starter in last_para:
                        self.structure_patterns[score_range]["conclusion_patterns"][starter] += 1
                        
        except Exception as e:
            logger.warning(f"Error analyzing structure patterns: {str(e)}")
    
    def _analyze_feedback_patterns(self, evaluation: str, band_score: float):
        """分析反馈模式"""
        try:
            score_range = self._get_score_range(band_score)
            
            if score_range not in self.feedback_patterns:
                self.feedback_patterns[score_range] = {
                    "positive_keywords": Counter(),
                    "negative_keywords": Counter(),
                    "improvement_suggestions": Counter()
                }
            
            eval_lower = evaluation.lower()
            
            # 正面关键词
            positive_keywords = [
                "excellent", "outstanding", "sophisticated", "comprehensive",
                "coherent", "cohesive", "accurate", "appropriate", "effective",
                "clear", "logical", "well-organized", "relevant", "convincing"
            ]
            
            # 负面关键词
            negative_keywords = [
                "limited", "inadequate", "unclear", "inaccurate", "inappropriate",
                "repetitive", "basic", "simple", "errors", "mistakes", "lacks"
            ]
            
            for keyword in positive_keywords:
                if keyword in eval_lower:
                    self.feedback_patterns[score_range]["positive_keywords"][keyword] += 1
            
            for keyword in negative_keywords:
                if keyword in eval_lower:
                    self.feedback_patterns[score_range]["negative_keywords"][keyword] += 1
            
            # 提取改进建议
            suggestion_patterns = re.findall(r'suggest[^.]*\.', eval_lower)
            for suggestion in suggestion_patterns:
                self.feedback_patterns[score_range]["improvement_suggestions"][suggestion] += 1
                
        except Exception as e:
            logger.warning(f"Error analyzing feedback patterns: {str(e)}")
    
    def _get_score_range(self, band_score: float) -> str:
        """获取分数范围"""
        if band_score >= 8.0:
            return "high"
        elif band_score >= 6.0:
            return "mid"
        else:
            return "low"
    
    def _save_cache(self):
        """保存缓存"""
        try:
            cache_data = {
                "score_patterns": self.score_patterns,
                "vocabulary_patterns": self.vocabulary_patterns,
                "structure_patterns": self.structure_patterns,
                "feedback_patterns": self.feedback_patterns
            }
            
            cache_file = self.cache_dir / "training_patterns_cache.pkl"
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            logger.info("Training patterns cached successfully")
            
        except Exception as e:
            logger.error(f"Error saving cache: {str(e)}")
    
    def predict_score_from_patterns(self, essay_text: str) -> Dict[str, Any]:
        """基于学习的模式预测分数"""
        try:
            word_count = len(essay_text.split())
            paragraph_count = len([p for p in essay_text.split('\n\n') if p.strip()])
            
            # 计算与各分数段的相似度
            similarities = {}
            
            for score_range, patterns in self.score_patterns.items():
                if not patterns["word_counts"]:
                    continue
                
                # 词数相似度
                avg_word_count = np.mean(patterns["word_counts"])
                word_similarity = 1 - abs(word_count - avg_word_count) / avg_word_count
                
                # 段落数相似度
                avg_paragraph_count = np.mean(patterns["paragraph_counts"])
                para_similarity = 1 - abs(paragraph_count - avg_paragraph_count) / avg_paragraph_count
                
                # 综合相似度
                similarities[score_range] = (word_similarity + para_similarity) / 2
            
            # 找到最相似的分数段
            if similarities:
                best_match = max(similarities, key=similarities.get)
                confidence = similarities[best_match]
                
                score_mapping = {"high": 8.0, "mid": 6.5, "low": 5.0}
                predicted_score = score_mapping.get(best_match, 6.0)
                
                return {
                    "predicted_score": predicted_score,
                    "confidence": confidence,
                    "best_match": best_match,
                    "similarities": similarities
                }
            
            return {"predicted_score": 6.0, "confidence": 0.5, "best_match": "mid"}
            
        except Exception as e:
            logger.error(f"Error predicting score from patterns: {str(e)}")
            return {"predicted_score": 6.0, "confidence": 0.5, "error": str(e)}
    
    def get_improvement_suggestions_from_patterns(self, essay_text: str, target_score: float) -> List[str]:
        """基于模式提供改进建议"""
        try:
            suggestions = []
            
            word_count = len(essay_text.split())
            paragraph_count = len([p for p in essay_text.split('\n\n') if p.strip()])
            
            target_range = self._get_score_range(target_score)
            
            if target_range in self.score_patterns:
                target_patterns = self.score_patterns[target_range]
                
                # 词数建议
                if target_patterns["word_counts"]:
                    avg_target_words = np.mean(target_patterns["word_counts"])
                    if word_count < avg_target_words * 0.8:
                        suggestions.append(f"建议增加文章长度至{int(avg_target_words)}词左右")
                
                # 段落建议
                if target_patterns["paragraph_counts"]:
                    avg_target_paras = np.mean(target_patterns["paragraph_counts"])
                    if paragraph_count < avg_target_paras:
                        suggestions.append(f"建议使用{int(avg_target_paras)}段结构")
            
            # 基于词汇模式的建议
            if target_range in self.vocabulary_patterns:
                vocab_patterns = self.vocabulary_patterns[target_range]
                
                # 检查学术词汇使用
                text_words = set(re.findall(r'\b[a-zA-Z]+\b', essay_text.lower()))
                common_academic = vocab_patterns["common_words"].most_common(20)
                
                missing_academic = [word for word, _ in common_academic 
                                  if word not in text_words and len(word) > 6]
                
                if missing_academic:
                    suggestions.append(f"建议使用更多学术词汇，如: {', '.join(missing_academic[:5])}")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting improvement suggestions: {str(e)}")
            return []
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """获取模式统计信息"""
        try:
            stats = {
                "score_patterns": {},
                "vocabulary_diversity": {},
                "structure_complexity": {}
            }
            
            for score_range, patterns in self.score_patterns.items():
                if patterns["word_counts"]:
                    stats["score_patterns"][score_range] = {
                        "avg_word_count": np.mean(patterns["word_counts"]),
                        "avg_paragraph_count": np.mean(patterns["paragraph_counts"]),
                        "sample_count": patterns["sample_count"]
                    }
            
            for score_range, vocab in self.vocabulary_patterns.items():
                stats["vocabulary_diversity"][score_range] = {
                    "unique_words": len(vocab["unique_words"]),
                    "avg_word_length": np.mean(vocab["word_lengths"]) if vocab["word_lengths"] else 0
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting pattern statistics: {str(e)}")
            return {}
