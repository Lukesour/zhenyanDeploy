"""
图表分析服务 - 使用Gemini 2.5 Flash Lite分析Task1图表
"""

import google.generativeai as genai
import base64
import io
from PIL import Image
from typing import Dict, Any, List
import json
import logging
from backend.ielts.app.core.config import settings

logger = logging.getLogger(__name__)

class ChartAnalysisService:
    def __init__(self):
        """初始化图表分析服务"""
        # 配置Gemini API
        genai.configure(api_key=settings.google_api_key)

        # 多模态模型优先级（使用系统配置的模型列表）
        # 注意：图表分析需要多模态模型，gemma-3-27b不支持图像，所以使用Gemini系列
        self.model_names = [    
            'gemini-2.0-flash-exp',
            'gemini-2.5-flash-lite',
            'gemini-2.5-flash',
            'gemini-2.5-pro'           
        ]

        # 图表分析提示词（扩展字段：动态图/静态图、坐标轴/单位、类别、时态建议）
        self.analysis_prompt = """
你是一个专业的IELTS Task 1图表分析专家。请分析这张图表并提供以下信息：

1. 图表类型识别（柱状图、折线图、饼图、表格、流程图、地图等）
2. 图表描述（整体概述）
3. 关键特征（主要数据点、趋势、对比）
4. 数据要点（具体数值、时间范围、类别、坐标轴、单位等）
5. 趋势分析（上升、下降、波动、稳定等）
6. 写作建议（如何组织Task 1作文的结构和要点）
7. 动/静态判断与时态建议（是否有时间轴，建议主要使用的一致时态）

请用中文回答，并以JSON格式返回结果：
{
    "chart_type": "图表类型",
    "description": "图表整体描述",
    "temporal_dimension": "dynamic | static",
    "axes": {"x_axis": "X轴含义", "y_axis": "Y轴含义", "units": "单位(如%)"},
    "categories": ["类别1", "类别2"],
    "key_features": ["关键特征1", "关键特征2", "关键特征3"],
    "data_points": ["数据要点1", "数据要点2", "数据要点3"],
    "trends": ["趋势1", "趋势2"],
    "tense_recommendation": "建议主要时态（如一般现在/一般过去）",
    "writing_suggestions": {
        "introduction": "开头段建议",
        "overview": "概述段建议",
        "body_paragraphs": ["主体段1建议", "主体段2建议"],
        "key_vocabulary": ["关键词汇1", "关键词汇2", "关键词汇3"]
    }
}

请确保返回的是有效的JSON格式，不要包含任何其他文字。
"""

    async def analyze_chart(self, image_data: bytes, filename: str = "") -> Dict[str, Any]:
        """
        分析图表图片
        
        Args:
            image_data: 图片二进制数据
            filename: 文件名
            
        Returns:
            分析结果字典
        """
        try:
            # 预处理图片
            processed_image = self._preprocess_image(image_data)
            
            # 将图片转换为base64
            image_base64 = self._image_to_base64(processed_image)
            
            # 调用Gemini API进行分析
            response = await self._call_gemini_api(image_base64)
            
            # 解析响应
            analysis_result = self._parse_response(response)
            
            return {
                "success": True,
                "chart_type": analysis_result.get("chart_type", "未知图表类型"),
                "description": analysis_result.get("description", ""),
                "temporal_dimension": analysis_result.get("temporal_dimension"),
                "axes": analysis_result.get("axes"),
                "categories": analysis_result.get("categories"),
                "key_features": analysis_result.get("key_features", []),
                "data_points": analysis_result.get("data_points", []),
                "trends": analysis_result.get("trends", []),
                "tense_recommendation": analysis_result.get("tense_recommendation"),
                "writing_suggestions": analysis_result.get("writing_suggestions", {})
            }
            
        except Exception as e:
            logger.error(f"图表分析失败: {str(e)}")
            return {
                "success": False,
                "error": f"图表分析失败: {str(e)}"
            }

    def _preprocess_image(self, image_data: bytes) -> Image.Image:
        """预处理图片以提高分析质量"""
        try:
            # 打开图片
            image = Image.open(io.BytesIO(image_data))
            
            # 转换为RGB模式
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 调整图片大小（保持宽高比）
            max_size = 1024
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            logger.error(f"图片预处理失败: {str(e)}")
            raise Exception(f"图片预处理失败: {str(e)}")

    def _image_to_base64(self, image: Image.Image) -> str:
        """将PIL图片转换为base64字符串"""
        try:
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return image_base64
            
        except Exception as e:
            logger.error(f"图片转换base64失败: {str(e)}")
            raise Exception(f"图片转换失败: {str(e)}")

    async def _call_gemini_api(self, image_base64: str) -> str:
        """调用Gemini API进行图表分析（带模型回退）"""
        try:
            # 准备图片数据
            image_part = {
                "mime_type": "image/png",
                "data": image_base64
            }

            last_error: Exception | None = None
            for model_name in self.model_names:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content([
                        self.analysis_prompt,
                        image_part
                    ])
                    if getattr(response, 'text', None):
                        return response.text
                    else:
                        last_error = Exception(f"Empty response from model: {model_name}")
                except Exception as e:
                    logger.error(f"Gemini API调用失败（{model_name}）: {str(e)}")
                    last_error = e
                    continue

            if last_error:
                raise last_error
            raise Exception("AI分析失败: 所有可用多模态模型均返回空响应")
        except Exception as e:
            logger.error(f"Gemini API调用失败: {str(e)}")
            raise Exception(f"AI分析失败: {str(e)}")

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """解析Gemini API响应"""
        try:
            # 清理响应文本
            cleaned_text = response_text.strip()
            
            # 移除可能的markdown代码块标记
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]
            
            cleaned_text = cleaned_text.strip()
            
            # 解析JSON
            result = json.loads(cleaned_text)
            
            # 验证必要字段
            required_fields = ["chart_type", "description", "key_features", "data_points", "trends", "writing_suggestions"]
            for field in required_fields:
                if field not in result:
                    result[field] = [] if field in ["key_features", "data_points", "trends"] else ""
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}, 原始响应: {response_text}")
            # 返回默认结构
            return {
                "chart_type": "图表类型识别失败",
                "description": "图表分析失败，请重试",
                "key_features": [],
                "data_points": [],
                "trends": [],
                "writing_suggestions": {
                    "introduction": "请重新上传图片进行分析",
                    "overview": "",
                    "body_paragraphs": [],
                    "key_vocabulary": []
                }
            }
        except Exception as e:
            logger.error(f"响应解析失败: {str(e)}")
            raise Exception(f"响应解析失败: {str(e)}")

    def get_supported_chart_types(self) -> List[str]:
        """获取支持的图表类型"""
        return [
            "柱状图 (Bar Chart)",
            "折线图 (Line Graph)", 
            "饼图 (Pie Chart)",
            "表格 (Table)",
            "流程图 (Process Diagram)",
            "地图 (Map)",
            "混合图表 (Mixed Charts)"
        ]

# 创建全局实例
chart_analysis_service = ChartAnalysisService()
