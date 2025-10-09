"""
范文参考服务 - 基于高质量范文的评分参考系统
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import re
from collections import defaultdict

logger = logging.getLogger(__name__)

class SampleReferenceService:
    """范文参考服务 - 提供分数段对应的范文参考"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent.parent / "data"
        self.sample_library = {
            "high_band": [],  # 8-9分范文
            "mid_band": [],   # 6-7分范文
            "low_band": []    # 3-5分范文
        }
        self.topic_samples = defaultdict(list)  # 按话题分类的样本
        self.question_type_samples = defaultdict(list)  # 按题型分类的样本
        
        self._load_sample_library()
        self._categorize_samples()
    
    def _load_sample_library(self):
        """加载范文库"""
        try:
            # 加载高分范文
            high_band_file = self.data_dir / "2. 高质量范文与样本数据" / "task2" / "cleaned_task2_high_band.json"
            with open(high_band_file, 'r', encoding='utf-8') as f:
                self.sample_library["high_band"] = json.load(f)
            
            # 加载中等分数范文
            mid_band_file = self.data_dir / "2. 高质量范文与样本数据" / "task2" / "cleaned_task2_mid_band.json"
            with open(mid_band_file, 'r', encoding='utf-8') as f:
                self.sample_library["mid_band"] = json.load(f)
            
            # 加载低分范文
            low_band_file = self.data_dir / "2. 高质量范文与样本数据" / "task2" / "cleaned_task2_low_band.json"
            with open(low_band_file, 'r', encoding='utf-8') as f:
                self.sample_library["low_band"] = json.load(f)
            
            logger.info(f"Loaded sample library: {len(self.sample_library['high_band'])} high, "
                       f"{len(self.sample_library['mid_band'])} mid, "
                       f"{len(self.sample_library['low_band'])} low band samples")
                       
        except Exception as e:
            logger.error(f"Error loading sample library: {str(e)}")
    
    def _categorize_samples(self):
        """按话题和题型对样本进行分类"""
        try:
            for band_level, samples in self.sample_library.items():
                for sample in samples:
                    prompt = sample.get("prompt", {})
                    prompt_text = prompt.get("text", "")
                    question_type = prompt.get("type", "")
                    
                    # 提取话题
                    topic = self._extract_topic(prompt_text)
                    if topic:
                        self.topic_samples[topic].append({
                            "sample": sample,
                            "band_level": band_level
                        })
                    
                    # 按题型分类
                    if question_type:
                        self.question_type_samples[question_type].append({
                            "sample": sample,
                            "band_level": band_level
                        })
                        
        except Exception as e:
            logger.error(f"Error categorizing samples: {str(e)}")
    
    def _extract_topic(self, prompt_text: str) -> Optional[str]:
        """从题目中提取话题"""
        topic_keywords = {
            "environment": ["environment", "pollution", "climate", "green", "sustainable"],
            "technology": ["technology", "internet", "computer", "digital", "AI"],
            "education": ["education", "school", "university", "student", "learning"],
            "health": ["health", "medical", "hospital", "disease", "fitness"],
            "work": ["work", "job", "employment", "career", "workplace"],
            "society": ["society", "social", "community", "culture", "tradition"],
            "government": ["government", "law", "policy", "authority", "regulation"],
            "media": ["media", "television", "newspaper", "advertising", "news"]
        }
        
        prompt_lower = prompt_text.lower()
        for topic, keywords in topic_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                return topic
        
        return "general"
    
    def get_reference_samples(self, target_score: float, question_type: str = None, 
                            topic: str = None, limit: int = 3) -> List[Dict[str, Any]]:
        """获取参考范文"""
        try:
            # 确定分数段
            if target_score >= 8.0:
                band_level = "high_band"
            elif target_score >= 6.0:
                band_level = "mid_band"
            else:
                band_level = "low_band"
            
            # 获取候选样本
            candidates = []
            
            # 优先按题型和话题匹配
            if question_type and question_type in self.question_type_samples:
                type_samples = [s for s in self.question_type_samples[question_type] 
                              if s["band_level"] == band_level]
                candidates.extend(type_samples)
            
            if topic and topic in self.topic_samples:
                topic_samples = [s for s in self.topic_samples[topic] 
                               if s["band_level"] == band_level]
                candidates.extend(topic_samples)
            
            # 如果候选样本不足，从对应分数段补充
            if len(candidates) < limit:
                band_samples = [{"sample": s, "band_level": band_level} 
                              for s in self.sample_library[band_level]]
                candidates.extend(band_samples)
            
            # 去重并限制数量
            seen_texts = set()
            unique_candidates = []
            for candidate in candidates:
                sample_text = candidate["sample"].get("essay", {}).get("text", "")
                if sample_text and sample_text not in seen_texts:
                    seen_texts.add(sample_text)
                    unique_candidates.append(candidate)
                    if len(unique_candidates) >= limit:
                        break
            
            return unique_candidates[:limit]
            
        except Exception as e:
            logger.error(f"Error getting reference samples: {str(e)}")
            return []
    
    def compare_with_reference(self, essay_text: str, reference_samples: List[Dict]) -> Dict[str, Any]:
        """与参考范文进行对比分析"""
        try:
            comparison_result = {
                "word_count_comparison": {},
                "structure_comparison": {},
                "content_quality": {},
                "specific_suggestions": []
            }
            
            essay_word_count = len(essay_text.split())
            essay_paragraphs = len([p for p in essay_text.split('\n\n') if p.strip()])
            
            for ref_data in reference_samples:
                ref_sample = ref_data["sample"]
                ref_essay = ref_sample.get("essay", {})
                ref_text = ref_essay.get("text", "")
                ref_word_count = ref_essay.get("word_count", len(ref_text.split()))
                ref_paragraphs = len([p for p in ref_text.split('\n\n') if p.strip()])
                
                # 词数对比
                word_count_diff = essay_word_count - ref_word_count
                comparison_result["word_count_comparison"][ref_data["band_level"]] = {
                    "reference_count": ref_word_count,
                    "essay_count": essay_word_count,
                    "difference": word_count_diff
                }
                
                # 结构对比
                comparison_result["structure_comparison"][ref_data["band_level"]] = {
                    "reference_paragraphs": ref_paragraphs,
                    "essay_paragraphs": essay_paragraphs,
                    "structure_match": abs(essay_paragraphs - ref_paragraphs) <= 1
                }
                
                # 生成具体建议
                if word_count_diff < -50:
                    comparison_result["specific_suggestions"].append(
                        f"相比{ref_data['band_level']}范文，您的文章字数偏少，建议增加{abs(word_count_diff)}词左右"
                    )
                elif word_count_diff > 100:
                    comparison_result["specific_suggestions"].append(
                        f"文章字数充足，超过{ref_data['band_level']}范文{word_count_diff}词"
                    )
                
                if essay_paragraphs < ref_paragraphs:
                    comparison_result["specific_suggestions"].append(
                        f"建议增加段落数量，参考{ref_data['band_level']}范文的{ref_paragraphs}段结构"
                    )
            
            return comparison_result
            
        except Exception as e:
            logger.error(f"Error comparing with reference: {str(e)}")
            return {}
    
    def get_score_calibration(self, essay_features: Dict[str, Any]) -> Dict[str, Any]:
        """基于范文库进行分数校准"""
        try:
            word_count = essay_features.get("word_count", 0)
            paragraph_count = essay_features.get("paragraph_count", 0)
            
            calibration_result = {
                "suggested_score_range": (5.0, 6.0),
                "confidence": 0.5,
                "reasoning": []
            }
            
            # 基于词数和段落数进行初步判断
            high_band_avg_words = self._get_average_word_count("high_band")
            mid_band_avg_words = self._get_average_word_count("mid_band")
            low_band_avg_words = self._get_average_word_count("low_band")
            
            if word_count >= high_band_avg_words * 0.9:
                calibration_result["suggested_score_range"] = (7.5, 9.0)
                calibration_result["confidence"] = 0.8
                calibration_result["reasoning"].append(f"词数({word_count})接近高分范文平均水平({high_band_avg_words})")
            elif word_count >= mid_band_avg_words * 0.9:
                calibration_result["suggested_score_range"] = (6.0, 7.5)
                calibration_result["confidence"] = 0.7
                calibration_result["reasoning"].append(f"词数({word_count})接近中等分数范文平均水平({mid_band_avg_words})")
            else:
                calibration_result["suggested_score_range"] = (4.0, 6.0)
                calibration_result["confidence"] = 0.6
                calibration_result["reasoning"].append(f"词数({word_count})低于中等分数范文平均水平")
            
            return calibration_result
            
        except Exception as e:
            logger.error(f"Error in score calibration: {str(e)}")
            return {"suggested_score_range": (5.0, 6.0), "confidence": 0.5, "reasoning": []}
    
    def _get_average_word_count(self, band_level: str) -> int:
        """获取特定分数段的平均词数"""
        try:
            samples = self.sample_library.get(band_level, [])
            if not samples:
                return 250  # 默认值
            
            word_counts = []
            for sample in samples:
                essay = sample.get("essay", {})
                word_count = essay.get("word_count")
                if word_count:
                    word_counts.append(word_count)
                else:
                    text = essay.get("text", "")
                    if text:
                        word_counts.append(len(text.split()))
            
            return int(sum(word_counts) / len(word_counts)) if word_counts else 250
            
        except Exception as e:
            logger.error(f"Error calculating average word count: {str(e)}")
            return 250
    
    def get_sample_statistics(self) -> Dict[str, Any]:
        """获取样本库统计信息"""
        try:
            stats = {
                "total_samples": sum(len(samples) for samples in self.sample_library.values()),
                "band_distribution": {band: len(samples) for band, samples in self.sample_library.items()},
                "topic_distribution": {topic: len(samples) for topic, samples in self.topic_samples.items()},
                "question_type_distribution": {qtype: len(samples) for qtype, samples in self.question_type_samples.items()},
                "average_word_counts": {
                    band: self._get_average_word_count(band) 
                    for band in self.sample_library.keys()
                }
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting sample statistics: {str(e)}")
            return {}
