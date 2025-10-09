"""
讲义知识点增强器
基于九分学长讲义知识点提升评分准确性和建议质量
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple

class TeachingMaterialEnhancer:
    """讲义知识点增强器"""
    
    def __init__(self):
        self.knowledge_dir = Path("data/6. 讲义知识点")
        self.knowledge_cache = {}
        self._load_knowledge()
    
    def _load_knowledge(self):
        """加载所有讲义知识点"""
        knowledge_files = {
            "basic": "task2_basic_knowledge.json",
            "structure": "essay_structure_knowledge.json", 
            "argument": "argument_construction_knowledge.json",
            "scoring": "scoring_criteria_knowledge.json",
            "techniques": "writing_techniques_knowledge.json"
        }
        
        for key, filename in knowledge_files.items():
            file_path = self.knowledge_dir / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.knowledge_cache[key] = json.load(f)
    
    def enhance_question_type_identification(self, prompt: str) -> Dict[str, Any]:
        """增强题型识别"""
        if "basic" not in self.knowledge_cache:
            return {"type": "Unknown", "confidence": 0.0}
        
        question_types = self.knowledge_cache["basic"]["question_types"]
        
        # 检查指令词匹配
        best_match = None
        highest_confidence = 0.0

        for type_name, type_info in question_types.items():
            for instruction in type_info["instructions"]:
                if instruction.lower() in prompt.lower():
                    confidence = len(instruction) / len(prompt)  # 简单的置信度计算
                    if confidence > highest_confidence:
                        highest_confidence = confidence
                        best_match = {
                            "type": type_name,
                            "english_type": type_name.split(" (")[1].rstrip(")") if " (" in type_name else type_name,
                            "characteristics": type_info["characteristics"],
                            "writing_style": type_info["writing_style"],
                            "structure": type_info["structure"],
                            "confidence": min(confidence * 10, 1.0)  # 调整置信度范围
                        }

        # 特殊检查：双问题类型
        if "?" in prompt and prompt.count("?") >= 2:
            return {
                "type": "报告型 (Report)",
                "english_type": "Two-part Question",
                "characteristics": "分析原因和提出解决方案",
                "writing_style": "客观风格",
                "structure": "开头段 + 原因段 + 解决方案段 + 结尾段",
                "confidence": 0.9
            }

        return best_match or {"type": "Unknown", "confidence": 0.0}
    
    def enhance_topic_analysis(self, prompt: str) -> Dict[str, Any]:
        """增强审题分析"""
        if "basic" not in self.knowledge_cache:
            return {}
        
        analysis_knowledge = self.knowledge_cache["basic"]["topic_analysis"]
        
        # 识别关键词类型
        key_elements = {
            "topic_keywords": [],
            "limiting_words": [],
            "instruction_words": [],
            "logical_connectors": []
        }
        
        # 检查逻辑关系词
        attention_points = analysis_knowledge["attention_points"]
        logical_relationships = []
        
        for relationship, keywords in attention_points.items():
            for keyword in keywords:
                if keyword.lower() in prompt.lower():
                    logical_relationships.append({
                        "type": relationship,
                        "keyword": keyword,
                        "position": prompt.lower().find(keyword.lower())
                    })
        
        # 提取指令词
        instruction_patterns = [
            r"to what extent do you agree or disagree",
            r"do you think this is a positive or negative development",
            r"discuss both views and give your opinion",
            r"do you think the advantages outweigh the disadvantages",
            r"why has this happened.*what can be done",
            r"what causes.*is it.*development"
        ]
        
        instruction_words = []
        for pattern in instruction_patterns:
            matches = re.finditer(pattern, prompt.lower())
            for match in matches:
                instruction_words.append({
                    "text": match.group(),
                    "start": match.start(),
                    "end": match.end()
                })
        
        return {
            "key_elements": key_elements,
            "logical_relationships": logical_relationships,
            "instruction_words": instruction_words,
            "analysis_suggestions": self._generate_analysis_suggestions(logical_relationships)
        }
    
    def _generate_analysis_suggestions(self, logical_relationships: List[Dict]) -> List[str]:
        """生成审题建议"""
        suggestions = []
        
        for rel in logical_relationships:
            rel_type = rel["type"]
            if rel_type == "并列关系":
                suggestions.append("注意题目中的并列要素，需要同时论述所有并列的内容")
            elif rel_type == "比较关系":
                suggestions.append("注意题目中的比较关系，重点论述比较中的主要部分")
            elif rel_type == "因果关系":
                suggestions.append("注意题目中的因果关系，可以质疑因果关系的合理性")
            elif rel_type == "程度关键词":
                suggestions.append("注意题目中的程度词，可以从程度的合理性角度论证")
        
        return suggestions
    
    def enhance_argument_construction(self, question_type: str, prompt: str) -> Dict[str, Any]:
        """增强分论点构建"""
        if "argument" not in self.knowledge_cache:
            return {}
        
        argument_knowledge = self.knowledge_cache["argument"]
        
        # 根据题型提供构建建议
        construction_advice = {}
        
        if "观点型" in question_type or "Opinion" in question_type:
            construction_advice = argument_knowledge["argument_construction_by_type"]["观点型/好坏型"]
        elif "讨论型" in question_type or "Discussion" in question_type:
            construction_advice = argument_knowledge["argument_construction_by_type"]["讨论型"]
        elif "比较型" in question_type or "Comparison" in question_type:
            construction_advice = argument_knowledge["argument_construction_by_type"]["比较型"]
        elif "报告型" in question_type or "Report" in question_type:
            construction_advice = argument_knowledge["argument_construction_by_type"]["报告型"]
        
        # 3C分解法建议
        three_c_method = argument_knowledge["3c_method"]
        
        # 特殊关键词处理建议
        special_keywords = self._identify_special_keywords(prompt)
        
        return {
            "construction_advice": construction_advice,
            "three_c_method": three_c_method,
            "special_keywords": special_keywords,
            "argument_suggestions": self._generate_argument_suggestions(question_type, special_keywords)
        }
    
    def _identify_special_keywords(self, prompt: str) -> List[Dict]:
        """识别特殊关键词"""
        if "argument" not in self.knowledge_cache:
            return []
        
        special_handling = self.knowledge_cache["argument"]["special_keywords_handling"]
        identified_keywords = []
        
        for category, info in special_handling.items():
            for keyword in info["关键词"]:
                if keyword.lower() in prompt.lower():
                    identified_keywords.append({
                        "category": category,
                        "keyword": keyword,
                        "handling_method": info["处理方法"]
                    })
        
        return identified_keywords
    
    def _generate_argument_suggestions(self, question_type: str, special_keywords: List[Dict]) -> List[str]:
        """生成分论点构建建议"""
        suggestions = []
        
        # 基于题型的建议
        if "观点型" in question_type or "Opinion" in question_type:
            suggestions.append("使用3C分解法：从原因(Cause)、结果(Consequence)、对比(Comparison)角度构建分论点")
            suggestions.append("确保所有分论点都支持你的总观点")
        elif "讨论型" in question_type or "Discussion" in question_type:
            suggestions.append("客观论述两个预设观点，每个观点找1-2个支持论据")
            suggestions.append("在结尾或单独段落表达个人观点")
        elif "比较型" in question_type or "Comparison" in question_type:
            suggestions.append("分别论述优势和劣势，根据总观点确定重点")
            suggestions.append("确保两方面都有涉及，保持平衡性")
        
        # 基于特殊关键词的建议
        for keyword_info in special_keywords:
            suggestions.append(f"注意{keyword_info['category']}关键词'{keyword_info['keyword']}'：{keyword_info['handling_method']}")
        
        return suggestions
    
    def enhance_structure_analysis(self, essay_text: str, question_type: str) -> Dict[str, Any]:
        """增强结构分析"""
        if "structure" not in self.knowledge_cache:
            return {}
        
        structure_knowledge = self.knowledge_cache["structure"]
        
        # 分析段落结构
        paragraphs = [p.strip() for p in essay_text.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)
        
        # 判断使用的模式
        if paragraph_count == 4:
            pattern = "1+2+1模式"
        elif paragraph_count == 5:
            pattern = "1+3+1模式"
        else:
            pattern = "非标准模式"
        
        # 分析开头段
        intro_analysis = self._analyze_introduction(paragraphs[0] if paragraphs else "", question_type)
        
        # 分析结尾段
        conclusion_analysis = self._analyze_conclusion(paragraphs[-1] if paragraphs else "")
        
        # 分析展开段
        body_analysis = self._analyze_body_paragraphs(paragraphs[1:-1] if len(paragraphs) > 2 else [])
        
        return {
            "paragraph_pattern": pattern,
            "pattern_info": structure_knowledge["paragraph_patterns"].get(pattern, {}),
            "introduction_analysis": intro_analysis,
            "conclusion_analysis": conclusion_analysis,
            "body_analysis": body_analysis,
            "structure_suggestions": self._generate_structure_suggestions(pattern, intro_analysis, conclusion_analysis, body_analysis)
        }
    
    def _analyze_introduction(self, intro_text: str, question_type: str) -> Dict[str, Any]:
        """分析开头段"""
        if "structure" not in self.knowledge_cache:
            return {}
        
        intro_knowledge = self.knowledge_cache["structure"]["introduction_writing"]
        
        # 判断类型
        if "报告型" in question_type or "Report" in question_type:
            required_elements = intro_knowledge["Report类型"]["必备内容"]
        else:
            required_elements = intro_knowledge["Argument类型"]["必备内容"]
        
        # 检查是否包含必备要素
        has_background = len(intro_text) > 50  # 简单判断是否有背景介绍
        has_position = any(word in intro_text.lower() for word in ["believe", "think", "agree", "disagree", "opinion"])
        
        return {
            "required_elements": required_elements,
            "has_background": has_background,
            "has_position": has_position,
            "word_count": len(intro_text.split()),
            "quality_score": (int(has_background) + int(has_position)) / 2
        }
    
    def _analyze_conclusion(self, conclusion_text: str) -> Dict[str, Any]:
        """分析结尾段"""
        if "structure" not in self.knowledge_cache:
            return {}
        
        conclusion_knowledge = self.knowledge_cache["structure"]["conclusion_writing"]
        
        # 检查是否重申观点
        has_restatement = any(word in conclusion_text.lower() for word in ["conclude", "summary", "overall", "therefore"])
        
        # 检查是否结合分论点
        has_reasoning = "since" in conclusion_text.lower() or "because" in conclusion_text.lower()
        
        return {
            "required_content": conclusion_knowledge["必备内容"],
            "has_restatement": has_restatement,
            "has_reasoning": has_reasoning,
            "word_count": len(conclusion_text.split()),
            "quality_score": (int(has_restatement) + int(has_reasoning)) / 2
        }
    
    def _analyze_body_paragraphs(self, body_paragraphs: List[str]) -> Dict[str, Any]:
        """分析展开段"""
        if "structure" not in self.knowledge_cache:
            return {}
        
        elements_knowledge = self.knowledge_cache["structure"]["body_paragraph_elements"]
        
        analysis_results = []
        
        for i, paragraph in enumerate(body_paragraphs):
            # 检查写作元素
            has_reasoning = len(paragraph) > 100  # 简单判断是否有充分论述
            has_example = any(word in paragraph.lower() for word in ["example", "instance", "such as", "like"])
            has_details = len(paragraph.split('.')) > 3  # 简单判断是否有细节
            
            analysis_results.append({
                "paragraph_index": i + 1,
                "word_count": len(paragraph.split()),
                "sentence_count": len(paragraph.split('.')),
                "has_reasoning": has_reasoning,
                "has_example": has_example,
                "has_details": has_details,
                "quality_score": (int(has_reasoning) + int(has_example) + int(has_details)) / 3
            })
        
        return {
            "paragraph_count": len(body_paragraphs),
            "elements_knowledge": elements_knowledge,
            "paragraph_analysis": analysis_results,
            "average_quality": sum(p["quality_score"] for p in analysis_results) / len(analysis_results) if analysis_results else 0
        }
    
    def _generate_structure_suggestions(self, pattern: str, intro_analysis: Dict, conclusion_analysis: Dict, body_analysis: Dict) -> List[str]:
        """生成结构建议"""
        suggestions = []
        
        # 段落模式建议
        if pattern == "非标准模式":
            suggestions.append("建议使用标准的1+2+1或1+3+1模式组织文章")
        
        # 开头段建议
        if intro_analysis.get("quality_score", 0) < 0.8:
            suggestions.append("开头段需要包含背景介绍和明确的观点表达")
        
        # 结尾段建议
        if conclusion_analysis.get("quality_score", 0) < 0.8:
            suggestions.append("结尾段应该重申观点并结合分论点进行总结")
        
        # 展开段建议
        if body_analysis.get("average_quality", 0) < 0.7:
            suggestions.append("展开段需要包含论述、例子和细节三个要素")
        
        return suggestions
