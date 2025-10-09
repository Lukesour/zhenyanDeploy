"""
评语格式化服务 - 将JSON格式的评语转换为用户友好的显示格式
"""

import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class CommentFormatter:
    """评语格式化器"""
    
    def __init__(self):
        pass
    
    def parse_and_format_comment(self, raw_comment: str) -> Dict[str, Any]:
        """
        解析并格式化评语
        
        Args:
            raw_comment: 原始评语文本（可能是JSON格式）
            
        Returns:
            格式化后的评语数据
        """
        try:
            # 尝试解析JSON格式的评语
            parsed_data = self._parse_json_comment(raw_comment)
            
            if parsed_data:
                # 格式化为用户友好的显示格式
                return self._format_comment_data(parsed_data)
            else:
                # 如果不是JSON格式，作为普通文本处理
                return {
                    "formatted_comment": raw_comment,
                    "is_formatted": False,
                    "original_format": "text"
                }
                
        except Exception as e:
            logger.error(f"Error formatting comment: {str(e)}")
            return {
                "formatted_comment": raw_comment,
                "is_formatted": False,
                "error": str(e)
            }
    
    def _parse_json_comment(self, text: str) -> Optional[Dict[str, Any]]:
        """解析JSON格式的评语"""
        if not text:
            return None

        # 首先清理文本
        cleaned_text = text.strip()

        try:
            # 直接尝试解析
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            try:
                # 移除markdown代码块标记
                if cleaned_text.startswith('```json'):
                    cleaned_text = cleaned_text[7:]
                elif cleaned_text.startswith('```'):
                    cleaned_text = cleaned_text[3:]

                if cleaned_text.endswith('```'):
                    cleaned_text = cleaned_text[:-3]

                cleaned_text = cleaned_text.strip()

                return json.loads(cleaned_text)
            except json.JSONDecodeError:
                # 尝试提取JSON部分
                try:
                    # 查找第一个 { 和最后一个 }
                    start = cleaned_text.find('{')
                    end = cleaned_text.rfind('}')
                    if start != -1 and end != -1 and end > start:
                        json_part = cleaned_text[start:end+1]
                        # 再次清理提取的JSON部分
                        json_part = json_part.strip()
                        return json.loads(json_part)
                except json.JSONDecodeError:
                    pass

                # 尝试修复常见的JSON格式问题
                try:
                    # 移除可能的BOM标记
                    if cleaned_text.startswith('\ufeff'):
                        cleaned_text = cleaned_text[1:]

                    # 简单粗暴但有效的方法：直接替换所有中文引号
                    fixed_text = self._fix_chinese_quotes(cleaned_text)

                    return json.loads(fixed_text)
                except json.JSONDecodeError:
                    pass

                # 如果JSON解析失败，尝试直接字符串处理
                logger.info("JSON parsing failed, trying direct string processing...")
                return self._parse_json_directly(cleaned_text)

        logger.warning(f"Failed to parse JSON comment: {cleaned_text[:100]}...")
        return None

    def _fix_chinese_quotes(self, text: str) -> str:
        """修复中文引号问题"""
        # 这是一个简单但有效的方法
        # 我们需要小心处理，只替换字符串值内的中文引号

        # 首先，我们使用一个更智能的方法
        # 找到所有的字符串值（在双引号之间），然后只在这些值内替换中文引号

        import re

        def replace_quotes_in_string(match):
            """替换字符串内的中文引号"""
            full_match = match.group(0)
            key_part = match.group(1)  # 键名部分
            value_part = match.group(2)  # 值部分

            # 只在值部分替换中文引号
            fixed_value = value_part.replace('"', '\\"').replace('"', '\\"')
            fixed_value = fixed_value.replace(''', "\\'").replace(''', "\\'")

            return f'"{key_part}": "{fixed_value}"'

        # 匹配 "key": "value" 模式
        pattern = r'"([^"]+)":\s*"([^"]*)"'
        fixed_text = re.sub(pattern, replace_quotes_in_string, text)

        return fixed_text

    def _parse_json_directly(self, text: str) -> Optional[Dict[str, Any]]:
        """直接从文本中提取JSON数据，不依赖JSON解析"""
        try:
            result = {}

            # 提取总体评语
            if '"overall_comment":' in text:
                start = text.find('"overall_comment":') + len('"overall_comment":')
                end = text.find('", "', start)
                if end == -1:
                    end = text.find('",', start)
                if end != -1:
                    comment_text = text[start:end].strip().strip('"').strip()
                    result['overall_comment'] = comment_text

            # 提取各维度分析
            score_breakdown = {}
            for dimension in ['TR_analysis', 'CC_analysis', 'LR_analysis', 'GRA_analysis']:
                if f'"{dimension}":' in text:
                    start = text.find(f'"{dimension}":') + len(f'"{dimension}":')
                    end = text.find('",', start)
                    if end == -1:
                        end = text.find('"', start + 1)
                    if end != -1:
                        analysis_text = text[start:end].strip().strip('"').strip()
                        score_breakdown[dimension] = analysis_text

            if score_breakdown:
                result['score_breakdown'] = score_breakdown

            # 提取数组类型的字段
            for field in ['key_strengths', 'key_weaknesses', 'priority_improvements']:
                if f'"{field}":' in text:
                    start = text.find(f'"{field}":') + len(f'"{field}":')
                    start = text.find('[', start) + 1
                    end = text.find(']', start)

                    if end != -1:
                        array_text = text[start:end]
                        items = [item.strip().strip('"').strip().rstrip(',')
                                for item in array_text.split('",') if item.strip()]
                        # 清理最后一个项目的引号
                        if items:
                            items[-1] = items[-1].rstrip('"')
                        result[field] = items

            # 提取其他字段
            for field in ['score_justification', 'band_level_description',
                         'next_level_requirements', 'official_standards_alignment']:
                if f'"{field}":' in text:
                    start = text.find(f'"{field}":') + len(f'"{field}":')
                    end = text.find('",', start)
                    if end == -1:
                        # 可能是最后一个字段
                        end = text.rfind('"')
                    if end != -1 and end > start:
                        field_text = text[start:end].strip().strip('"').strip()
                        result[field] = field_text

            return result if result else None

        except Exception as e:
            logger.error(f"Error in direct JSON parsing: {str(e)}")
            return None
    
    def _format_comment_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """将JSON数据格式化为用户友好的显示格式"""
        
        formatted_parts = []
        
        # 1. 总体评语
        if "overall_comment" in data:
            formatted_parts.append("## 📋 总体评语\n")
            formatted_parts.append(data["overall_comment"])
            formatted_parts.append("\n\n")
        
        # 2. 分数分析
        if "score_breakdown" in data:
            formatted_parts.append("## 📊 各维度详细分析\n")
            score_breakdown = data["score_breakdown"]

            if "TR_analysis" in score_breakdown:
                formatted_parts.append("### 📝 任务回应（Task Response）\n")
                formatted_parts.append(score_breakdown["TR_analysis"])
                formatted_parts.append("\n\n")

            if "CC_analysis" in score_breakdown:
                formatted_parts.append("### 🔗 连贯与衔接（Coherence and Cohesion）\n")
                formatted_parts.append(score_breakdown["CC_analysis"])
                formatted_parts.append("\n\n")

            if "LR_analysis" in score_breakdown:
                formatted_parts.append("### 📚 词汇资源（Lexical Resource）\n")
                formatted_parts.append(score_breakdown["LR_analysis"])
                formatted_parts.append("\n\n")

            if "GRA_analysis" in score_breakdown:
                formatted_parts.append("### ✏️ 语法准确性（Grammatical Range and Accuracy）\n")
                formatted_parts.append(score_breakdown["GRA_analysis"])
                formatted_parts.append("\n\n")
        
        # 3. 主要优点
        if "key_strengths" in data and data["key_strengths"]:
            formatted_parts.append("## ✅ 主要优点\n")
            for strength in data["key_strengths"]:
                formatted_parts.append(f"- {strength}\n")
            formatted_parts.append("\n")

        # 4. 主要不足
        if "key_weaknesses" in data and data["key_weaknesses"]:
            formatted_parts.append("## ⚠️ 主要不足\n")
            for weakness in data["key_weaknesses"]:
                formatted_parts.append(f"- {weakness}\n")
            formatted_parts.append("\n")

        # 5. 优先改进建议
        if "priority_improvements" in data and data["priority_improvements"]:
            formatted_parts.append("## 🎯 优先改进建议\n")
            for i, improvement in enumerate(data["priority_improvements"], 1):
                formatted_parts.append(f"{i}. {improvement}\n")
            formatted_parts.append("\n")
        
        # 6. 评分说明
        if "score_justification" in data:
            formatted_parts.append("## 📈 评分说明\n")
            formatted_parts.append(data["score_justification"])
            formatted_parts.append("\n\n")

        # 7. 分数段描述
        if "band_level_description" in data:
            formatted_parts.append("## 🎖️ 分数段描述\n")
            formatted_parts.append(data["band_level_description"])
            formatted_parts.append("\n\n")

        # 8. 下一级别要求
        if "next_level_requirements" in data:
            formatted_parts.append("## 🚀 达到下一级别的要求\n")
            formatted_parts.append(data["next_level_requirements"])
            formatted_parts.append("\n\n")

        # 9. 官方标准对照
        if "official_standards_alignment" in data:
            formatted_parts.append("## 📋 官方标准对照\n")
            formatted_parts.append(data["official_standards_alignment"])
            formatted_parts.append("\n\n")
        
        # 合并所有部分 - 直接连接，因为每个部分已经包含了适当的换行符
        formatted_comment = "".join(formatted_parts).strip()
        
        return {
            "formatted_comment": formatted_comment,
            "is_formatted": True,
            "original_format": "json",
            "parsed_data": data,
            "sections": {
                "overall_comment": data.get("overall_comment", ""),
                "key_strengths": data.get("key_strengths", []),
                "key_weaknesses": data.get("key_weaknesses", []),
                "priority_improvements": data.get("priority_improvements", []),
                "score_justification": data.get("score_justification", ""),
                "band_level_description": data.get("band_level_description", ""),
                "next_level_requirements": data.get("next_level_requirements", ""),
                "official_standards_alignment": data.get("official_standards_alignment", ""),
                "score_breakdown": data.get("score_breakdown", {})
            }
        }
    
    def format_improvement_suggestions(self, suggestions: str) -> Dict[str, Any]:
        """格式化改进建议"""
        try:
            # 如果是JSON格式
            if suggestions.strip().startswith('{'):
                parsed = self._parse_json_comment(suggestions)
                if parsed:
                    return self._format_improvement_data(parsed)
            
            # 如果是普通文本，按行分割
            lines = suggestions.strip().split('\n')
            formatted_suggestions = []
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('•'):
                    formatted_suggestions.append(f"• {line}")
                elif line:
                    formatted_suggestions.append(line)
            
            return {
                "formatted_suggestions": '\n'.join(formatted_suggestions),
                "is_formatted": True,
                "suggestions_list": [s.replace('• ', '') for s in formatted_suggestions if s.strip()]
            }
            
        except Exception as e:
            logger.error(f"Error formatting improvement suggestions: {str(e)}")
            return {
                "formatted_suggestions": suggestions,
                "is_formatted": False,
                "error": str(e)
            }
    
    def _format_improvement_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化改进建议数据"""
        formatted_parts = []
        
        if "improvements" in data:
            for i, improvement in enumerate(data["improvements"], 1):
                formatted_parts.append(f"{i}. {improvement}")
        
        return {
            "formatted_suggestions": '\n'.join(formatted_parts),
            "is_formatted": True,
            "parsed_data": data
        }

# 创建全局实例
comment_formatter = CommentFormatter()
