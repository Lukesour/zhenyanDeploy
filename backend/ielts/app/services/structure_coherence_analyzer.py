"""
结构连贯性分析器 - 基于结构数据的CC维度评分增强
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple, Set
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

class StructureCoherenceAnalyzer:
    """结构连贯性分析器 - 提升CC维度评分准确性"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent.parent / "data"
        
        # 结构资源
        self.essay_structures = {}
        self.cohesive_devices = {}
        self.transition_patterns = []
        self.paragraph_patterns = {}
        
        self._load_structure_resources()
    
    def _load_structure_resources(self):
        """加载结构分析资源"""
        try:
            # 作文结构模板
            structures_file = self.data_dir / "3. 结构与逻辑分析资源" / "essay_structures.json"
            with open(structures_file, 'r', encoding='utf-8') as f:
                self.essay_structures = json.load(f)
            
            # 连接词设备
            cohesive_file = self.data_dir / "3. 结构与逻辑分析资源" / "cohesive_devices.json"
            with open(cohesive_file, 'r', encoding='utf-8') as f:
                self.cohesive_devices = json.load(f)
            
            # 过渡模式
            transitions_file = self.data_dir / "3. 结构与逻辑分析资源" / "transition_patterns.json"
            if transitions_file.exists():
                with open(transitions_file, 'r', encoding='utf-8') as f:
                    self.transition_patterns = json.load(f)
            
            # 段落模式
            paragraphs_file = self.data_dir / "3. 结构与逻辑分析资源" / "paragraph_patterns.json"
            if paragraphs_file.exists():
                with open(paragraphs_file, 'r', encoding='utf-8') as f:
                    self.paragraph_patterns = json.load(f)
            
            logger.info("Structure and coherence resources loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading structure resources: {str(e)}")
    
    def analyze_coherence_cohesion(self, essay_text: str, task_type: str = "task2") -> Dict[str, Any]:
        """分析连贯性和衔接性 (CC维度)"""
        try:
            analysis = {
                "structure_score": 0,
                "cohesion_score": 0,
                "coherence_score": 0,
                "structure_analysis": {},
                "cohesive_devices_analysis": {},
                "logical_flow_analysis": {},
                "score_indicators": [],
                "evidence": [],
                "suggestions": []
            }
            
            # 1. 结构分析
            structure_result = self._analyze_essay_structure(essay_text, task_type)
            analysis["structure_analysis"] = structure_result
            analysis["structure_score"] = structure_result.get("score", 6.0)
            
            # 2. 连接词分析
            cohesion_result = self._analyze_cohesive_devices(essay_text)
            analysis["cohesive_devices_analysis"] = cohesion_result
            analysis["cohesion_score"] = cohesion_result.get("score", 6.0)
            
            # 3. 逻辑流程分析
            coherence_result = self._analyze_logical_coherence(essay_text)
            analysis["logical_flow_analysis"] = coherence_result
            analysis["coherence_score"] = coherence_result.get("score", 6.0)
            
            # 综合评分
            base_score = (analysis["structure_score"] + analysis["cohesion_score"] + analysis["coherence_score"]) / 3

            # 高质量文章的额外加分
            quality_bonus = 0

            # 检查是否有清晰的引言、主体、结论结构
            paragraphs = [p.strip() for p in essay_text.split('\n\n') if p.strip()]
            if len(paragraphs) >= 4:
                quality_bonus += 0.5

            # 检查高质量的连接和过渡
            high_quality_transitions = [
                "firstly", "secondly", "another reason", "in my view", "for example",
                "in conclusion", "furthermore", "moreover", "however", "therefore"
            ]
            transition_count = sum(1 for trans in high_quality_transitions if trans in essay_text.lower())
            if transition_count >= 5:
                quality_bonus += 0.5
            elif transition_count >= 3:
                quality_bonus += 0.3

            # 检查段落发展质量
            if len(paragraphs) >= 4 and all(len(p.split()) > 30 for p in paragraphs[1:-1]):
                quality_bonus += 0.4

            final_score = base_score + quality_bonus
            analysis["final_score"] = round(max(3.0, min(9.0, final_score)) * 2) / 2
            
            # 合并证据和建议
            analysis["evidence"].extend(structure_result.get("evidence", []))
            analysis["evidence"].extend(cohesion_result.get("evidence", []))
            analysis["evidence"].extend(coherence_result.get("evidence", []))
            
            analysis["suggestions"].extend(structure_result.get("suggestions", []))
            analysis["suggestions"].extend(cohesion_result.get("suggestions", []))
            analysis["suggestions"].extend(coherence_result.get("suggestions", []))
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing coherence and cohesion: {str(e)}")
            return {"error": str(e), "final_score": 6.0}
    
    def _analyze_essay_structure(self, essay_text: str, task_type: str) -> Dict[str, Any]:
        """分析作文结构"""
        try:
            result = {
                "score": 6.0,
                "evidence": [],
                "suggestions": [],
                "structure_type": "unknown",
                "paragraph_analysis": {}
            }
            
            paragraphs = [p.strip() for p in essay_text.split('\n\n') if p.strip()]
            paragraph_count = len(paragraphs)
            
            # 获取理想结构模板
            ideal_structures = self.essay_structures.get(task_type, {}).get("structures", [])
            
            # 分析段落数量
            if paragraph_count >= 4:
                result["evidence"].append(f"文章结构清晰，共{paragraph_count}段")
                result["score"] += 0.5
            elif paragraph_count == 3:
                result["evidence"].append(f"文章采用三段式结构")
                result["score"] += 0.2
            else:
                result["suggestions"].append(f"建议增加段落数量（当前{paragraph_count}段，建议4-5段）")
                result["score"] -= 0.5
            
            # 分析段落功能
            if paragraphs:
                # 开头段分析
                intro_analysis = self._analyze_introduction(paragraphs[0])
                if intro_analysis["has_hook"]:
                    result["evidence"].append("开头段包含引入句")
                    result["score"] += 0.3
                if intro_analysis["has_thesis"]:
                    result["evidence"].append("开头段包含明确论点")
                    result["score"] += 0.3
                
                # 结尾段分析
                if len(paragraphs) > 1:
                    conclusion_analysis = self._analyze_conclusion(paragraphs[-1])
                    if conclusion_analysis["has_summary"]:
                        result["evidence"].append("结尾段有效总结论点")
                        result["score"] += 0.3
                    if conclusion_analysis["has_final_thought"]:
                        result["evidence"].append("结尾段提供最终思考")
                        result["score"] += 0.2
                
                # 主体段分析
                if len(paragraphs) > 2:
                    body_analysis = self._analyze_body_paragraphs(paragraphs[1:-1])
                    if body_analysis["avg_length"] > 50:
                        result["evidence"].append("主体段内容充实")
                        result["score"] += 0.3
                    if body_analysis["has_topic_sentences"]:
                        result["evidence"].append("主体段包含主题句")
                        result["score"] += 0.4
            
            # 匹配结构模板
            best_match = self._match_structure_template(paragraphs, ideal_structures)
            if best_match:
                result["structure_type"] = best_match["name"]
                result["evidence"].append(f"文章结构符合{best_match['name']}模式")
                result["score"] += 0.5
            
            result["score"] = max(3.0, min(9.0, result["score"]))
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing essay structure: {str(e)}")
            return {"score": 6.0, "evidence": [], "suggestions": []}
    
    def _analyze_cohesive_devices(self, essay_text: str) -> Dict[str, Any]:
        """分析连接词使用"""
        try:
            result = {
                "score": 6.0,
                "evidence": [],
                "suggestions": [],
                "devices_found": [],
                "device_types": {},
                "variety_score": 0
            }
            
            essay_lower = essay_text.lower()
            
            # 获取连接词类别
            device_categories = self.cohesive_devices.get("categories", {})
            
            total_devices = 0
            used_categories = set()
            
            for category, devices in device_categories.items():
                category_count = 0
                category_devices = []
                
                for device in devices.get("devices", []):
                    device_text = device.get("text", "").lower()
                    if device_text and device_text in essay_lower:
                        category_count += essay_lower.count(device_text)
                        category_devices.append(device_text)
                        total_devices += essay_lower.count(device_text)
                
                if category_count > 0:
                    used_categories.add(category)
                    result["device_types"][category] = {
                        "count": category_count,
                        "devices": category_devices
                    }
            
            # 评分逻辑
            if total_devices >= 8:
                result["evidence"].append(f"连接词使用丰富（共{total_devices}个）")
                result["score"] += 1.0
            elif total_devices >= 5:
                result["evidence"].append(f"连接词使用适当（共{total_devices}个）")
                result["score"] += 0.5
            elif total_devices >= 3:
                result["evidence"].append(f"连接词使用基本（共{total_devices}个）")
            else:
                result["suggestions"].append("建议增加连接词使用，提高文章连贯性")
                result["score"] -= 0.5
            
            # 多样性评分
            category_variety = len(used_categories)
            if category_variety >= 4:
                result["evidence"].append(f"连接词类型多样（使用了{category_variety}种类型）")
                result["score"] += 0.8
            elif category_variety >= 3:
                result["evidence"].append(f"连接词类型较多样（使用了{category_variety}种类型）")
                result["score"] += 0.5
            elif category_variety >= 2:
                result["evidence"].append(f"连接词类型一般（使用了{category_variety}种类型）")
            else:
                result["suggestions"].append("建议使用更多样的连接词类型")
                result["score"] -= 0.3
            
            result["variety_score"] = category_variety
            result["score"] = max(3.0, min(9.0, result["score"]))
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing cohesive devices: {str(e)}")
            return {"score": 6.0, "evidence": [], "suggestions": []}
    
    def _analyze_logical_coherence(self, essay_text: str) -> Dict[str, Any]:
        """分析逻辑连贯性"""
        try:
            result = {
                "score": 6.0,
                "evidence": [],
                "suggestions": [],
                "flow_score": 0,
                "progression_analysis": {}
            }
            
            paragraphs = [p.strip() for p in essay_text.split('\n\n') if p.strip()]
            
            if len(paragraphs) < 2:
                result["suggestions"].append("文章段落过少，难以评估逻辑连贯性")
                result["score"] = 4.0
                return result
            
            # 分析段落间的逻辑关系
            logical_connections = 0
            
            for i in range(len(paragraphs) - 1):
                current_para = paragraphs[i].lower()
                next_para = paragraphs[i + 1].lower()
                
                # 检查逻辑连接词
                logical_indicators = [
                    "however", "furthermore", "moreover", "therefore", "consequently",
                    "in addition", "on the other hand", "in contrast", "similarly",
                    "firstly", "secondly", "finally", "in conclusion"
                ]
                
                connection_found = False
                for indicator in logical_indicators:
                    if indicator in next_para[:100]:  # 检查段落开头
                        logical_connections += 1
                        connection_found = True
                        break
                
                # 检查主题连续性
                if not connection_found:
                    # 简单的主题词重复检查
                    current_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', current_para))
                    next_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', next_para[:200]))
                    
                    overlap = len(current_words & next_words)
                    if overlap >= 3:
                        logical_connections += 0.5
            
            # 评分
            connection_ratio = logical_connections / (len(paragraphs) - 1) if len(paragraphs) > 1 else 0
            
            if connection_ratio >= 0.8:
                result["evidence"].append("段落间逻辑连接清晰")
                result["score"] += 1.0
            elif connection_ratio >= 0.6:
                result["evidence"].append("段落间逻辑连接较好")
                result["score"] += 0.5
            elif connection_ratio >= 0.4:
                result["evidence"].append("段落间逻辑连接一般")
            else:
                result["suggestions"].append("建议加强段落间的逻辑连接")
                result["score"] -= 0.5
            
            # 分析论证发展
            argument_progression = self._analyze_argument_progression(paragraphs)
            if argument_progression["has_clear_progression"]:
                result["evidence"].append("论证发展清晰")
                result["score"] += 0.5
            
            result["flow_score"] = connection_ratio
            result["progression_analysis"] = argument_progression
            result["score"] = max(3.0, min(9.0, result["score"]))
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing logical coherence: {str(e)}")
            return {"score": 6.0, "evidence": [], "suggestions": []}
    
    def _analyze_introduction(self, intro_paragraph: str) -> Dict[str, bool]:
        """分析开头段"""
        intro_lower = intro_paragraph.lower()
        
        # 检查引入句
        hook_indicators = ["nowadays", "in recent years", "it is widely believed", "many people think"]
        has_hook = any(indicator in intro_lower for indicator in hook_indicators)
        
        # 检查论点句
        thesis_indicators = ["i believe", "in my opinion", "this essay will", "i agree", "i disagree"]
        has_thesis = any(indicator in intro_lower for indicator in thesis_indicators)
        
        return {"has_hook": has_hook, "has_thesis": has_thesis}
    
    def _analyze_conclusion(self, conclusion_paragraph: str) -> Dict[str, bool]:
        """分析结尾段"""
        conclusion_lower = conclusion_paragraph.lower()
        
        # 检查总结
        summary_indicators = ["in conclusion", "to conclude", "in summary", "overall"]
        has_summary = any(indicator in conclusion_lower for indicator in summary_indicators)
        
        # 检查最终思考
        final_thought_indicators = ["therefore", "thus", "hence", "as a result"]
        has_final_thought = any(indicator in conclusion_lower for indicator in final_thought_indicators)
        
        return {"has_summary": has_summary, "has_final_thought": has_final_thought}
    
    def _analyze_body_paragraphs(self, body_paragraphs: List[str]) -> Dict[str, Any]:
        """分析主体段"""
        if not body_paragraphs:
            return {"avg_length": 0, "has_topic_sentences": False}
        
        total_words = sum(len(para.split()) for para in body_paragraphs)
        avg_length = total_words / len(body_paragraphs)
        
        # 检查主题句
        topic_sentence_indicators = ["firstly", "secondly", "another", "furthermore", "moreover"]
        has_topic_sentences = any(
            any(indicator in para.lower()[:50] for indicator in topic_sentence_indicators)
            for para in body_paragraphs
        )
        
        return {"avg_length": avg_length, "has_topic_sentences": has_topic_sentences}
    
    def _match_structure_template(self, paragraphs: List[str], templates: List[Dict]) -> Dict[str, Any]:
        """匹配结构模板"""
        if not templates:
            return None
        
        best_match = None
        best_score = 0
        
        for template in templates:
            score = 0
            expected_paras = template.get("paragraph_count", 4)
            
            # 段落数量匹配
            if len(paragraphs) == expected_paras:
                score += 2
            elif abs(len(paragraphs) - expected_paras) == 1:
                score += 1
            
            # 结构特征匹配
            features = template.get("features", [])
            for feature in features:
                if self._check_structure_feature(paragraphs, feature):
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = template
        
        return best_match if best_score > 2 else None
    
    def _check_structure_feature(self, paragraphs: List[str], feature: str) -> bool:
        """检查结构特征"""
        if feature == "clear_introduction" and paragraphs:
            intro_analysis = self._analyze_introduction(paragraphs[0])
            return intro_analysis["has_thesis"]
        elif feature == "clear_conclusion" and len(paragraphs) > 1:
            conclusion_analysis = self._analyze_conclusion(paragraphs[-1])
            return conclusion_analysis["has_summary"]
        elif feature == "body_paragraphs" and len(paragraphs) > 2:
            body_analysis = self._analyze_body_paragraphs(paragraphs[1:-1])
            return body_analysis["avg_length"] > 30
        
        return False
    
    def _analyze_argument_progression(self, paragraphs: List[str]) -> Dict[str, Any]:
        """分析论证发展"""
        if len(paragraphs) < 3:
            return {"has_clear_progression": False}
        
        # 简单检查：每个主体段是否有不同的论点
        body_paragraphs = paragraphs[1:-1] if len(paragraphs) > 2 else paragraphs[1:]
        
        # 检查关键词多样性
        paragraph_keywords = []
        for para in body_paragraphs:
            words = set(re.findall(r'\b[a-zA-Z]{5,}\b', para.lower()))
            paragraph_keywords.append(words)
        
        # 计算段落间的词汇重叠度
        if len(paragraph_keywords) >= 2:
            overlaps = []
            for i in range(len(paragraph_keywords) - 1):
                overlap = len(paragraph_keywords[i] & paragraph_keywords[i + 1])
                total = len(paragraph_keywords[i] | paragraph_keywords[i + 1])
                overlap_ratio = overlap / total if total > 0 else 0
                overlaps.append(overlap_ratio)
            
            # 如果重叠度适中（不太高也不太低），说明有清晰的论证发展
            avg_overlap = sum(overlaps) / len(overlaps)
            has_clear_progression = 0.2 <= avg_overlap <= 0.6
        else:
            has_clear_progression = False
        
        return {"has_clear_progression": has_clear_progression}
