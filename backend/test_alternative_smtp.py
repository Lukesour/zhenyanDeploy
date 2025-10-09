#!/usr/bin/env python3
"""
测试替代SMTP配置
"""

import smtplib
import ssl
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.config.settings import settings

def test_gmail_ssl():
    """测试Gmail SSL连接（端口465）"""
    print("🔐 测试Gmail SSL连接（端口465）...")
    
    try:
        # 使用SSL连接而不是STARTTLS
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context)
        
        print("✅ SSL连接建立成功")
        
        # 尝试登录
        server.login(settings.GMAIL_SENDER_EMAIL, settings.GMAIL_APP_PASSWORD)
        print("✅ SSL认证成功")
        
        server.quit()
        return True
        
    except Exception as e:
        print(f"❌ SSL连接失败: {e}")
        return False

def test_gmail_with_timeout():
    """测试带超时的Gmail连接"""
    print("\n⏰ 测试带超时的Gmail连接...")
    
    try:
        # 设置更长的超时时间
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=30)
        server.set_debuglevel(0)  # 关闭调试输出
        
        print("✅ SMTP连接建立")
        
        # 尝试EHLO
        server.ehlo()
        print("✅ EHLO成功")
        
        # 启用TLS
        context = ssl.create_default_context()
        server.starttls(context=context)
        print("✅ STARTTLS成功")
        
        # 再次EHLO
        server.ehlo()
        print("✅ TLS后EHLO成功")
        
        # 尝试登录
        server.login(settings.GMAIL_SENDER_EMAIL, settings.GMAIL_APP_PASSWORD)
        print("✅ 认证成功")
        
        server.quit()
        return True
        
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

def test_send_via_ssl():
    """通过SSL发送测试邮件"""
    print("\n📧 通过SSL发送测试邮件...")
    
    test_email = input("请输入测试邮箱地址（回车跳过）: ").strip()
    if not test_email:
        print("⏭️  跳过邮件发送测试")
        return True
    
    try:
        # 创建邮件
        message = MIMEMultipart("alternative")
        message["Subject"] = "箴言留学 - 测试邮件"
        message["From"] = f"箴言留学 <{settings.GMAIL_SENDER_EMAIL}>"
        message["To"] = test_email
        
        text_content = """
        箴言留学 - 测试邮件
        
        这是一封测试邮件，用于验证Gmail SMTP配置是否正确。
        
        如果您收到这封邮件，说明邮件服务配置成功！
        
        © 2024 箴言留学
        """
        
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>测试邮件</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #667eea;">📧 箴言留学 - 测试邮件</h2>
                <p>这是一封测试邮件，用于验证Gmail SMTP配置是否正确。</p>
                <div style="background: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <strong>✅ 如果您收到这封邮件，说明邮件服务配置成功！</strong>
                </div>
                <p style="color: #666; font-size: 14px;">© 2024 箴言留学</p>
            </div>
        </body>
        </html>
        """
        
        text_part = MIMEText(text_content, "plain", "utf-8")
        html_part = MIMEText(html_content, "html", "utf-8")
        
        message.attach(text_part)
        message.attach(html_part)
        
        # 使用SSL发送
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
            server.login(settings.GMAIL_SENDER_EMAIL, settings.GMAIL_APP_PASSWORD)
            server.sendmail(settings.GMAIL_SENDER_EMAIL, test_email, message.as_string())
        
        print("✅ 测试邮件发送成功！")
        return True
        
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🔄 Gmail SMTP 替代配置测试")
    print("=" * 50)
    
    if not settings.GMAIL_SENDER_EMAIL or not settings.GMAIL_APP_PASSWORD:
        print("❌ Gmail配置不完整")
        return False
    
    print(f"📧 邮箱: {settings.GMAIL_SENDER_EMAIL}")
    print(f"🔑 密码: {'*' * len(settings.GMAIL_APP_PASSWORD)}")
    
    # 测试SSL连接
    ssl_success = test_gmail_ssl()
    
    if ssl_success:
        print("\n🎉 SSL连接成功！建议使用SSL配置。")
        
        # 测试发送邮件
        test_send_via_ssl()
        
    else:
        print("\n🔄 尝试带超时的STARTTLS连接...")
        starttls_success = test_gmail_with_timeout()
        
        if not starttls_success:
            print("\n❌ 所有连接方式都失败了")
            print("\n💡 可能的解决方案:")
            print("1. 检查网络防火墙是否阻止了SMTP连接")
            print("2. 尝试使用VPN或其他网络环境")
            print("3. 联系网络管理员检查SMTP端口限制")
            print("4. 考虑使用其他邮件服务提供商")
            return False
    
    return True

if __name__ == "__main__":
    main()
