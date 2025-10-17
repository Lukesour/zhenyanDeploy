"""
OCR服务 - 图片文字提取功能
"""

import os
import io
import logging
from typing import Dict, Any, Optional
from PIL import Image
import pytesseract
import cv2
import numpy as np

logger = logging.getLogger(__name__)

class OCRService:
    """OCR文字提取服务"""
    
    def __init__(self):
        # 配置Tesseract路径（优先使用环境变量，其次常见安装路径）
        tess_cmd = os.getenv('TESSERACT_CMD')
        if tess_cmd and os.path.exists(tess_cmd):
            pytesseract.pytesseract.tesseract_cmd = tess_cmd
        elif os.path.exists('/opt/homebrew/bin/tesseract'):
            pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'
        elif os.path.exists('/usr/local/bin/tesseract'):
            pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
        elif os.path.exists('/usr/bin/tesseract'):
            pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
        else:
            logger.warning("未找到 Tesseract 可执行文件，请确保在生产环境中安装并配置 Tesseract。")
        
        # 支持的图片格式
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        
    def extract_text_from_image(self, image_data: bytes, filename: str = "") -> Dict[str, Any]:
        """
        从图片中提取文字
        
        Args:
            image_data: 图片二进制数据
            filename: 文件名（用于格式检测）
            
        Returns:
            包含提取结果的字典
        """
        try:
            # 检查文件格式
            if filename:
                file_ext = os.path.splitext(filename.lower())[1]
                if file_ext not in self.supported_formats:
                    return {
                        "success": False,
                        "error": f"不支持的文件格式: {file_ext}",
                        "supported_formats": list(self.supported_formats)
                    }
            
            # 加载图片
            image = Image.open(io.BytesIO(image_data))
            
            # 转换为RGB格式（如果需要）
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 预处理图片以提高OCR准确性
            processed_image = self._preprocess_image(image)
            
            # 执行OCR
            # 使用中英文混合识别
            custom_config = r'--oem 3 --psm 6 -l chi_sim+eng'
            
            # 提取文字
            extracted_text = pytesseract.image_to_string(
                processed_image, 
                config=custom_config
            ).strip()
            
            # 获取置信度信息
            confidence_data = pytesseract.image_to_data(
                processed_image, 
                config=custom_config,
                output_type=pytesseract.Output.DICT
            )
            
            # 计算平均置信度
            confidences = [int(conf) for conf in confidence_data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # 清理提取的文字
            cleaned_text = self._clean_extracted_text(extracted_text)
            
            return {
                "success": True,
                "text": cleaned_text,
                "raw_text": extracted_text,
                "confidence": round(avg_confidence, 2),
                "word_count": len(cleaned_text.split()) if cleaned_text else 0,
                "char_count": len(cleaned_text) if cleaned_text else 0
            }
            
        except Exception as e:
            logger.error(f"OCR处理失败: {str(e)}")
            return {
                "success": False,
                "error": f"OCR处理失败: {str(e)}"
            }
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        预处理图片以提高OCR准确性
        """
        try:
            # 转换为numpy数组
            img_array = np.array(image)
            
            # 转换为灰度图
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # 应用高斯模糊去噪
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # 自适应阈值处理
            thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # 形态学操作去除噪点
            kernel = np.ones((1, 1), np.uint8)
            processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel)
            
            # 转换回PIL Image
            return Image.fromarray(processed)
            
        except Exception as e:
            logger.warning(f"图片预处理失败，使用原图: {str(e)}")
            return image
    
    def _clean_extracted_text(self, text: str) -> str:
        """
        清理提取的文字
        """
        if not text:
            return ""
        
        # 移除多余的空白字符
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # 移除行首行尾空白
            line = line.strip()
            # 跳过空行
            if line:
                # 移除多余的空格
                line = ' '.join(line.split())
                cleaned_lines.append(line)
        
        # 合并行，保持段落结构
        result = '\n'.join(cleaned_lines)
        
        # 移除连续的换行符
        while '\n\n\n' in result:
            result = result.replace('\n\n\n', '\n\n')
        
        return result
    


    def extract_title_only(self, image_data: bytes, filename: str = "") -> Dict[str, Any]:
        """
        从图片中仅提取题目

        Args:
            image_data: 图片二进制数据
            filename: 文件名

        Returns:
            包含题目的字典
        """
        try:
            # 先提取所有文字
            text_result = self.extract_text_from_image(image_data, filename)

            if not text_result["success"]:
                return text_result

            full_text = text_result["text"]

            # 提取题目部分
            title = self._extract_title_from_text(full_text)

            return {
                "success": True,
                "title": title,
                "confidence": text_result["confidence"],
                "word_count": len(title.split()) if title else 0
            }

        except Exception as e:
            logger.error(f"题目提取失败: {str(e)}")
            return {
                "success": False,
                "error": f"题目提取失败: {str(e)}"
            }

    def extract_content_only(self, image_data: bytes, filename: str = "") -> Dict[str, Any]:
        """
        从图片中仅提取作文内容

        Args:
            image_data: 图片二进制数据
            filename: 文件名

        Returns:
            包含内容的字典
        """
        try:
            # 先提取所有文字
            text_result = self.extract_text_from_image(image_data, filename)

            if not text_result["success"]:
                return text_result

            full_text = text_result["text"]

            # 提取内容部分
            content = self._extract_content_from_text(full_text)

            return {
                "success": True,
                "content": content,
                "confidence": text_result["confidence"],
                "word_count": len(content.split()) if content else 0
            }

        except Exception as e:
            logger.error(f"内容提取失败: {str(e)}")
            return {
                "success": False,
                "error": f"内容提取失败: {str(e)}"
            }

    def _extract_title_from_text(self, text: str) -> str:
        """
        从文本中提取题目
        """
        lines = text.split('\n')
        if not lines:
            return ""

        # 寻找最可能的题目行
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 如果包含问号且长度适中，很可能是题目
            if ('?' in line or '？' in line) and 10 <= len(line) <= 300:
                return line

        # 如果没找到问号，返回第一个非空行
        for line in lines:
            line = line.strip()
            if line and len(line) >= 10:
                return line

        return lines[0].strip() if lines else ""

    def _extract_content_from_text(self, text: str) -> str:
        """
        从文本中提取作文内容（排除题目）
        """
        lines = text.split('\n')
        if not lines:
            return ""

        # 找到题目行的位置
        title_line_idx = -1
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # 如果包含问号且长度适中，很可能是题目
            if ('?' in line or '？' in line) and 10 <= len(line) <= 300:
                title_line_idx = i
                break

        # 如果找到了题目，返回题目之后的内容
        if title_line_idx >= 0:
            content_lines = lines[title_line_idx + 1:]
        else:
            # 如果没找到明确的题目，跳过第一行
            content_lines = lines[1:] if len(lines) > 1 else lines

        # 清理并合并内容行
        content_parts = []
        for line in content_lines:
            line = line.strip()
            if line:
                content_parts.append(line)

        return '\n'.join(content_parts)

# 全局OCR服务实例
ocr_service = OCRService()
