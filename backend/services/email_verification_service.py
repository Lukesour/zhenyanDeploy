"""
Hunter.io邮箱验证服务
用于验证邮箱地址的有效性和可达性
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional
from backend.config.settings import settings

logger = logging.getLogger(__name__)

class EmailVerificationService:
    """Hunter.io邮箱验证服务"""
    
    def __init__(self):
        self.api_key = settings.HUNTER_API_KEY
        self.base_url = "https://api.hunter.io/v2"
        self.session = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    def _get_session(self):
        """获取或创建HTTP会话"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def verify_email(self, email: str) -> Dict[str, Any]:
        """
        验证邮箱地址
        
        Args:
            email: 要验证的邮箱地址
            
        Returns:
            验证结果字典，包含：
            - valid: 是否有效
            - result: 验证结果 (deliverable, undeliverable, risky, unknown)
            - score: 可信度分数 (0-100)
            - regexp: 是否通过正则表达式验证
            - gibberish: 是否为无意义字符
            - disposable: 是否为临时邮箱
            - webmail: 是否为网页邮箱
            - mx_records: 是否有MX记录
            - smtp_server: 是否有SMTP服务器
            - smtp_check: SMTP检查结果
            - accept_all: 是否接受所有邮件
            - block: 是否被阻止
        """
        if not self.api_key:
            logger.warning("Hunter.io API密钥未配置，跳过邮箱验证")
            return {
                "valid": True,  # 默认认为有效
                "result": "unknown",
                "score": 50,
                "message": "邮箱验证服务未配置"
            }
        
        try:
            session = self._get_session()
            url = f"{self.base_url}/email-verifier"
            params = {
                "email": email,
                "api_key": self.api_key
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_verification_result(data)
                elif response.status == 401:
                    logger.error("Hunter.io API密钥无效")
                    return {
                        "valid": False,
                        "result": "error",
                        "score": 0,
                        "message": "邮箱验证服务认证失败"
                    }
                elif response.status == 429:
                    logger.warning("Hunter.io API请求限制")
                    return {
                        "valid": True,  # 限制时默认通过
                        "result": "unknown",
                        "score": 50,
                        "message": "邮箱验证服务请求过于频繁"
                    }
                else:
                    logger.error(f"Hunter.io API请求失败: {response.status}")
                    return {
                        "valid": True,  # 错误时默认通过
                        "result": "unknown",
                        "score": 50,
                        "message": "邮箱验证服务暂时不可用"
                    }
                    
        except asyncio.TimeoutError:
            logger.warning("Hunter.io API请求超时")
            return {
                "valid": True,  # 超时时默认通过
                "result": "unknown",
                "score": 50,
                "message": "邮箱验证服务超时"
            }
        except Exception as e:
            logger.error(f"邮箱验证失败: {str(e)}")
            return {
                "valid": True,  # 异常时默认通过
                "result": "unknown",
                "score": 50,
                "message": f"邮箱验证异常: {str(e)}"
            }
    
    def _parse_verification_result(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析Hunter.io验证结果"""
        try:
            verification_data = data.get("data", {})
            
            result = verification_data.get("result", "unknown")
            score = verification_data.get("score", 0)
            
            # 判断邮箱是否有效
            valid = result in ["deliverable"] and score >= 70
            
            # 如果结果是risky但分数较高，也可以认为有效
            if result == "risky" and score >= 80:
                valid = True
            
            return {
                "valid": valid,
                "result": result,
                "score": score,
                "regexp": verification_data.get("regexp", False),
                "gibberish": verification_data.get("gibberish", False),
                "disposable": verification_data.get("disposable", False),
                "webmail": verification_data.get("webmail", False),
                "mx_records": verification_data.get("mx_records", False),
                "smtp_server": verification_data.get("smtp_server", False),
                "smtp_check": verification_data.get("smtp_check", False),
                "accept_all": verification_data.get("accept_all", False),
                "block": verification_data.get("block", False),
                "message": self._get_result_message(result, score)
            }
            
        except Exception as e:
            logger.error(f"解析验证结果失败: {str(e)}")
            return {
                "valid": True,  # 解析失败时默认通过
                "result": "unknown",
                "score": 50,
                "message": "验证结果解析失败"
            }
    
    def _get_result_message(self, result: str, score: int) -> str:
        """获取验证结果的中文描述"""
        messages = {
            "deliverable": "邮箱地址有效且可接收邮件",
            "undeliverable": "邮箱地址无效或无法接收邮件",
            "risky": f"邮箱地址存在风险 (可信度: {score}%)",
            "unknown": "无法确定邮箱地址状态"
        }
        return messages.get(result, f"验证结果: {result}")
    
    async def batch_verify_emails(self, emails: list) -> Dict[str, Dict[str, Any]]:
        """
        批量验证邮箱地址
        
        Args:
            emails: 邮箱地址列表
            
        Returns:
            邮箱地址到验证结果的映射
        """
        results = {}
        
        # Hunter.io的免费计划有请求限制，所以我们需要控制并发
        semaphore = asyncio.Semaphore(3)  # 最多3个并发请求
        
        async def verify_single_email(email: str):
            async with semaphore:
                result = await self.verify_email(email)
                results[email] = result
                # 添加延迟以避免触发速率限制
                await asyncio.sleep(0.5)
        
        # 创建所有验证任务
        tasks = [verify_single_email(email) for email in emails]
        
        # 等待所有任务完成
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return results
    
    def is_email_risky(self, verification_result: Dict[str, Any]) -> bool:
        """
        判断邮箱是否存在风险
        
        Args:
            verification_result: verify_email返回的结果
            
        Returns:
            是否存在风险
        """
        # 临时邮箱
        if verification_result.get("disposable", False):
            return True
        
        # 无意义字符
        if verification_result.get("gibberish", False):
            return True
        
        # 被阻止的邮箱
        if verification_result.get("block", False):
            return True
        
        # 分数过低
        if verification_result.get("score", 0) < 30:
            return True
        
        # 结果为不可达
        if verification_result.get("result") == "undeliverable":
            return True
        
        return False
    
    def get_email_quality_score(self, verification_result: Dict[str, Any]) -> int:
        """
        获取邮箱质量分数 (0-100)
        
        Args:
            verification_result: verify_email返回的结果
            
        Returns:
            质量分数
        """
        base_score = verification_result.get("score", 50)
        
        # 根据各种因素调整分数
        if verification_result.get("disposable", False):
            base_score -= 30
        
        if verification_result.get("gibberish", False):
            base_score -= 20
        
        if verification_result.get("mx_records", False):
            base_score += 10
        
        if verification_result.get("smtp_server", False):
            base_score += 10
        
        # 确保分数在0-100范围内
        return max(0, min(100, base_score))
    
    async def test_connection(self) -> bool:
        """测试Hunter.io API连接"""
        if not self.api_key:
            return False

        try:
            # 使用异步上下文管理器确保会话正确关闭
            async with self:
                result = await self.verify_email("test@example.com")
                return "result" in result
        except Exception as e:
            logger.error(f"Hunter.io连接测试失败: {str(e)}")
            return False
    
    async def close(self):
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()
            self.session = None

# 创建全局实例
email_verification_service = EmailVerificationService()
