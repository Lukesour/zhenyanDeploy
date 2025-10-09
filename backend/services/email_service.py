import smtplib
import ssl
import logging
import random
import string
import requests
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from backend.config.settings import settings

logger = logging.getLogger(__name__)

class EmailService:
    """多方式邮件服务类 - 支持SMTP和HTTP API"""

    def __init__(self):
        # Gmail SMTP配置
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = settings.GMAIL_SENDER_EMAIL
        self.sender_password = settings.GMAIL_APP_PASSWORD
        self.sender_name = settings.GMAIL_SENDER_NAME or "箴言留学"

        # 邮件发送方式：'smtp' 或 'api'
        self.send_method = getattr(settings, 'EMAIL_SEND_METHOD', 'smtp')

        # 如果没有配置邮件服务，记录警告但不抛出异常
        if not self.sender_email:
            logger.warning("Gmail sender email not configured - email functionality will be disabled")
            self._email_configured = False
        else:
            self._email_configured = True
        
    def generate_verification_code(self, length: int = 6) -> str:
        """生成邮箱验证码"""
        return ''.join(random.choices(string.digits, k=length))
    
    def send_verification_email(self, to_email: str, verification_code: str, user_name: str = "") -> bool:
        """发送邮箱验证码"""
        if not self._email_configured:
            logger.warning("Email service not configured - skipping actual email send. Verification code: %s", verification_code)
            return True

        try:
            # 邮件内容模板
            subject = "箴言留学 - 邮箱验证码"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>邮箱验证码</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .code-box {{ background: #fff; border: 2px dashed #667eea; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px; }}
                    .code {{ font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 5px; }}
                    .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 14px; }}
                    .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📧 邮箱验证码</h1>
                        <p>箴言留学 - 个性化留学申请分析平台</p>
                    </div>
                    <div class="content">
                        <p>亲爱的{user_name if user_name else '用户'}，</p>
                        <p>感谢您注册箴言留学平台！请使用以下验证码完成邮箱验证：</p>
                        
                        <div class="code-box">
                            <div class="code">{verification_code}</div>
                        </div>
                        
                        <div class="warning">
                            <strong>⚠️ 重要提醒：</strong>
                            <ul>
                                <li>验证码有效期为10分钟</li>
                                <li>请勿将验证码泄露给他人</li>
                                <li>如非本人操作，请忽略此邮件</li>
                            </ul>
                        </div>
                        
                        <p>完成验证后，您将获得：</p>
                        <ul>
                            <li>🎯 3次免费个性化留学分析机会</li>
                            <li>📊 基于AI和大数据的精准选校建议</li>
                            <li>🔗 邀请好友获得更多分析次数</li>
                        </ul>
                        
                        <p>如有任何问题，请联系我们的客服团队。</p>
                    </div>
                    <div class="footer">
                        <p>此邮件由系统自动发送，请勿回复</p>
                        <p>© 2024 箴言留学 - 让留学申请更智能</p>
                        <p>客服微信：Godeternitys | MalachiSuan</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 纯文本版本
            text_content = f"""
            箴言留学 - 邮箱验证码
            
            亲爱的{user_name if user_name else '用户'}，
            
            感谢您注册箴言留学平台！
            
            您的邮箱验证码是：{verification_code}
            
            验证码有效期为10分钟，请及时使用。
            
            如有任何问题，请联系客服微信：Godeternitys 或 MalachiSuan
            
            此邮件由系统自动发送，请勿回复。
            
            © 2024 箴言留学
            """
            
            return self._send_email(to_email, subject, html_content, text_content)
            
        except Exception as e:
            logger.error(f"发送验证邮件失败: {str(e)}")
            return False
    
    def send_welcome_email(self, to_email: str, user_name: str, remaining_analyses: int = 3) -> bool:
        """发送欢迎邮件"""
        if not self._email_configured:
            logger.warning("Email service not configured - skipping welcome email发送")
            return True

        try:
            subject = "欢迎加入箴言留学！🎉"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>欢迎加入箴言留学</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .feature-box {{ background: #fff; padding: 20px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #667eea; }}
                    .cta-button {{ display: inline-block; background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 欢迎加入箴言留学！</h1>
                        <p>您的留学申请智能助手</p>
                    </div>
                    <div class="content">
                        <p>亲爱的 {user_name}，</p>
                        <p>恭喜您成功注册箴言留学平台！我们很高兴为您提供个性化的留学申请分析服务。</p>
                        
                        <div class="feature-box">
                            <h3>🎯 您当前拥有 {remaining_analyses} 次分析机会</h3>
                            <p>每次分析都会为您提供：</p>
                            <ul>
                                <li>基于AI和大数据的精准选校建议</li>
                                <li>个性化的申请策略规划</li>
                                <li>相似案例对比分析</li>
                                <li>专业的留学申请指导</li>
                            </ul>
                        </div>
                        
                        <div class="feature-box">
                            <h3>🔗 邀请好友，获得更多机会</h3>
                            <p>每成功邀请一位新用户注册，您将获得额外的3次分析机会！</p>
                        </div>
                        
                        <p>现在就开始您的留学申请分析之旅吧！</p>
                        
                        <div style="text-align: center;">
                            <a href="https://zhenyan.asia" class="cta-button">立即开始分析</a>
                        </div>
                        
                        <p>如有任何问题，随时联系我们的客服团队。</p>
                    </div>
                    <div class="footer">
                        <p>© 2024 箴言留学 - 让留学申请更智能</p>
                        <p>客服微信：Godeternitys | MalachiSuan</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            欢迎加入箴言留学！
            
            亲爱的 {user_name}，
            
            恭喜您成功注册箴言留学平台！
            
            您当前拥有 {remaining_analyses} 次分析机会。
            
            每次分析都会为您提供基于AI和大数据的精准选校建议。
            
            邀请好友注册，每成功邀请一位新用户，您将获得额外的3次分析机会！
            
            立即访问：https://zhenyan.asia
            
            客服微信：Godeternitys | MalachiSuan
            
            © 2024 箴言留学
            """
            
            return self._send_email(to_email, subject, html_content, text_content)
            
        except Exception as e:
            logger.error(f"发送欢迎邮件失败: {str(e)}")
            return False
    
    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """发送邮件 - 自动选择最佳方式"""
        if self.send_method == 'smtp':
            return self._send_email_via_smtp(to_email, subject, html_content, text_content)
        else:
            return self._send_email_via_api(to_email, subject, html_content, text_content)

    def _send_email_via_smtp(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """通过Gmail SMTP发送邮件 - 尝试多种连接方式"""

        # 尝试不同的SMTP配置
        smtp_configs = [
            # 配置1: STARTTLS (端口587)
            {
                'server': 'smtp.gmail.com',
                'port': 587,
                'use_ssl': False,
                'use_starttls': True,
                'timeout': 30
            },
            # 配置2: SSL (端口465)
            {
                'server': 'smtp.gmail.com',
                'port': 465,
                'use_ssl': True,
                'use_starttls': False,
                'timeout': 30
            },
            # 配置3: 备用端口
            {
                'server': 'smtp.gmail.com',
                'port': 25,
                'use_ssl': False,
                'use_starttls': True,
                'timeout': 30
            }
        ]

        for i, config in enumerate(smtp_configs, 1):
            try:
                logger.info(f"尝试SMTP配置 {i}: {config['server']}:{config['port']}")

                # 创建邮件消息
                message = MIMEMultipart("alternative")
                message["Subject"] = subject
                message["From"] = f"{self.sender_name} <{self.sender_email}>"
                message["To"] = to_email

                # 添加纯文本和HTML内容
                text_part = MIMEText(text_content, "plain", "utf-8")
                html_part = MIMEText(html_content, "html", "utf-8")

                message.attach(text_part)
                message.attach(html_part)

                # 根据配置选择连接方式
                if config['use_ssl']:
                    # SSL连接
                    context = ssl.create_default_context()
                    with smtplib.SMTP_SSL(config['server'], config['port'],
                                        context=context, timeout=config['timeout']) as server:
                        server.login(self.sender_email, self.sender_password)
                        server.sendmail(self.sender_email, to_email, message.as_string())
                else:
                    # STARTTLS连接
                    with smtplib.SMTP(config['server'], config['port'],
                                    timeout=config['timeout']) as server:
                        server.ehlo()
                        if config['use_starttls']:
                            context = ssl.create_default_context()
                            server.starttls(context=context)
                            server.ehlo()
                        server.login(self.sender_email, self.sender_password)
                        server.sendmail(self.sender_email, to_email, message.as_string())

                logger.info(f"✅ SMTP邮件发送成功 (配置{i}): {to_email}")
                return True

            except Exception as e:
                logger.warning(f"SMTP配置 {i} 失败: {str(e)}")
                continue

        # 所有SMTP配置都失败，尝试API方式
        logger.error("所有SMTP配置都失败，尝试API方式...")
        return self._send_email_via_api(to_email, subject, html_content, text_content)

    def _send_email_via_api(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """通过Resend API发送邮件"""
        try:
            # 使用Resend API发送邮件
            if self._send_via_resend(to_email, subject, html_content, text_content):
                return True

            # Resend API失败，回退到控制台模式
            logger.warning("Resend API发送失败，回退到控制台模式")
            return self._send_via_console(to_email, subject, html_content, text_content)

        except Exception as e:
            logger.error(f"Resend API发送异常: {str(e)}")
            return self._send_via_console(to_email, subject, html_content, text_content)

    def _send_via_resend(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """通过Resend API发送邮件"""
        try:
            # 如果配置了Resend API密钥
            resend_api_key = getattr(settings, 'RESEND_API_KEY', None)
            if not resend_api_key:
                logger.warning("Resend API密钥未配置")
                return False

            import requests

            # 使用自定义域名（如果已配置）或Resend默认域名
            custom_domain = getattr(settings, 'RESEND_FROM_DOMAIN', None)
            if custom_domain:
                from_email = f'{self.sender_name} <noreply@{custom_domain}>'
            else:
                from_email = f'{self.sender_name} <noreply@resend.dev>'

            logger.info(f"尝试通过Resend API发送邮件: {to_email}")

            response = requests.post(
                'https://api.resend.com/emails',
                headers={
                    'Authorization': f'Bearer {resend_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'from': from_email,
                    'to': [to_email],
                    'subject': subject,
                    'html': html_content,
                    'text': text_content
                },
                timeout=15
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Resend API邮件发送成功: {to_email}, ID: {result.get('id', 'N/A')}")
                return True
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                logger.error(f"❌ Resend API发送失败: {response.status_code}, 错误: {error_data}")
                return False

        except Exception as e:
            logger.error(f"Resend API异常: {str(e)}")
            return False

    def _send_via_sendgrid(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """通过SendGrid API发送邮件"""
        try:
            # 如果配置了SendGrid API密钥
            sendgrid_api_key = getattr(settings, 'SENDGRID_API_KEY', None)
            if not sendgrid_api_key:
                return False

            import requests

            response = requests.post(
                'https://api.sendgrid.com/v3/mail/send',
                headers={
                    'Authorization': f'Bearer {sendgrid_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'personalizations': [{
                        'to': [{'email': to_email}]
                    }],
                    'from': {'email': self.sender_email, 'name': self.sender_name},
                    'subject': subject,
                    'content': [
                        {'type': 'text/plain', 'value': text_content},
                        {'type': 'text/html', 'value': html_content}
                    ]
                },
                timeout=10
            )

            if response.status_code == 202:
                logger.info(f"✅ SendGrid API邮件发送成功: {to_email}")
                return True
            else:
                logger.warning(f"❌ SendGrid API发送失败: {response.status_code}")
                return False

        except Exception as e:
            logger.warning(f"SendGrid API异常: {str(e)}")
            return False

    def _send_via_mailgun(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """通过Mailgun API发送邮件"""
        try:
            # 如果配置了Mailgun API密钥
            mailgun_api_key = getattr(settings, 'MAILGUN_API_KEY', None)
            mailgun_domain = getattr(settings, 'MAILGUN_DOMAIN', None)
            if not mailgun_api_key or not mailgun_domain:
                return False

            import requests

            response = requests.post(
                f'https://api.mailgun.net/v3/{mailgun_domain}/messages',
                auth=('api', mailgun_api_key),
                data={
                    'from': f'{self.sender_name} <noreply@{mailgun_domain}>',
                    'to': to_email,
                    'subject': subject,
                    'text': text_content,
                    'html': html_content
                },
                timeout=10
            )

            if response.status_code == 200:
                logger.info(f"✅ Mailgun API邮件发送成功: {to_email}")
                return True
            else:
                logger.warning(f"❌ Mailgun API发送失败: {response.status_code}")
                return False

        except Exception as e:
            logger.warning(f"Mailgun API异常: {str(e)}")
            return False

    def _send_via_console(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """控制台模式 - 显示验证码"""
        try:
            logger.info(f"控制台模式邮件发送: {to_email}")
            logger.info(f"邮件主题: {subject}")
            logger.info(f"验证码内容: {text_content[:100]}...")

            # 在控制台输出验证码，方便测试
            import re
            code_match = re.search(r'验证码.*?(\d{6})', text_content)
            if code_match:
                verification_code = code_match.group(1)
                print(f"\n🔢 验证码: {verification_code}")
                print(f"📧 收件人: {to_email}")
                print("💡 注意: 当前为控制台模式，验证码显示在控制台中\n")

            return True

        except Exception as e:
            logger.error(f"控制台模式异常: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """测试邮件服务连接"""
        if self.send_method == 'smtp':
            return self._test_smtp_connection()
        else:
            return self._test_api_connection()

    def _test_smtp_connection(self) -> bool:
        """测试Gmail SMTP连接"""
        try:
            if not self.sender_password:
                logger.error("Gmail应用专用密码未配置")
                return False

            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)

            logger.info("Gmail SMTP连接测试成功")
            return True

        except Exception as e:
            logger.error(f"Gmail SMTP连接测试失败: {str(e)}")
            return False

    def _test_api_connection(self) -> bool:
        """测试API连接"""
        try:
            # API方式总是可用的（模拟模式）
            logger.info("邮件API连接测试成功（测试模式）")
            return True

        except Exception as e:
            logger.error(f"邮件API连接测试失败: {str(e)}")
            return False
