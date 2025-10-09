#!/usr/bin/env python3
"""
Gmail SMTP 详细诊断脚本
"""

import smtplib
import ssl
import socket
import sys
import os
from backend.config.settings import settings

def test_network_connectivity():
    """测试网络连接"""
    print("🌐 测试网络连接...")
    
    # 测试DNS解析
    try:
        import socket
        ip = socket.gethostbyname('smtp.gmail.com')
        print(f"✅ DNS解析成功: smtp.gmail.com -> {ip}")
    except Exception as e:
        print(f"❌ DNS解析失败: {e}")
        return False
    
    # 测试端口连接
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex(('smtp.gmail.com', 587))
        sock.close()
        
        if result == 0:
            print("✅ 端口587连接成功")
            return True
        else:
            print(f"❌ 端口587连接失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 端口连接测试异常: {e}")
        return False

def test_smtp_handshake():
    """测试SMTP握手"""
    print("\n🤝 测试SMTP握手...")
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.set_debuglevel(1)  # 启用调试输出
        
        print("✅ SMTP连接建立")
        
        # 测试STARTTLS
        context = ssl.create_default_context()
        server.starttls(context=context)
        print("✅ TLS加密启用")
        
        server.quit()
        return True
        
    except Exception as e:
        print(f"❌ SMTP握手失败: {e}")
        return False

def test_authentication():
    """测试认证"""
    print("\n🔐 测试Gmail认证...")
    
    email = settings.GMAIL_SENDER_EMAIL
    password = settings.GMAIL_APP_PASSWORD
    
    if not email or not password:
        print("❌ 邮箱或密码未配置")
        return False
    
    print(f"📧 邮箱: {email}")
    print(f"🔑 密码长度: {len(password)} 字符")
    
    # 检查密码格式
    if len(password) != 16:
        print("⚠️  警告: 应用专用密码通常是16位字符")
    
    if ' ' in password:
        print("⚠️  警告: 密码中包含空格，这可能导致问题")
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        context = ssl.create_default_context()
        server.starttls(context=context)
        
        # 尝试登录
        server.login(email, password)
        print("✅ Gmail认证成功")
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ 认证失败: {e}")
        print("💡 可能的原因:")
        print("   1. 应用专用密码错误")
        print("   2. 两步验证未启用")
        print("   3. 应用专用密码已过期")
        return False
    except Exception as e:
        print(f"❌ 认证测试异常: {e}")
        return False

def test_send_email():
    """测试发送邮件"""
    print("\n📤 测试发送邮件...")
    
    test_email = input("请输入测试邮箱地址（回车跳过）: ").strip()
    if not test_email:
        print("⏭️  跳过邮件发送测试")
        return True
    
    try:
        from backend.services.email_service import EmailService
        
        email_service = EmailService()
        success = email_service.send_verification_email(
            to_email=test_email,
            verification_code="123456",
            user_name="测试用户"
        )
        
        if success:
            print("✅ 测试邮件发送成功")
            return True
        else:
            print("❌ 测试邮件发送失败")
            return False
            
    except Exception as e:
        print(f"❌ 邮件发送异常: {e}")
        return False

def main():
    """主诊断函数"""
    print("🔍 Gmail SMTP 详细诊断")
    print("=" * 50)
    
    # 检查配置
    print("📋 检查配置...")
    print(f"邮箱: {settings.GMAIL_SENDER_EMAIL}")
    print(f"密码: {'*' * len(settings.GMAIL_APP_PASSWORD) if settings.GMAIL_APP_PASSWORD else '未配置'}")
    
    if not settings.GMAIL_SENDER_EMAIL or not settings.GMAIL_APP_PASSWORD:
        print("❌ Gmail配置不完整")
        return False
    
    # 运行诊断测试
    tests = [
        ("网络连接", test_network_connectivity),
        ("SMTP握手", test_smtp_handshake),
        ("Gmail认证", test_authentication),
        ("发送邮件", test_send_email)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            
            if not result:
                print(f"\n❌ {test_name}测试失败，停止后续测试")
                break
                
        except KeyboardInterrupt:
            print("\n⏹️  用户中断测试")
            break
        except Exception as e:
            print(f"\n💥 {test_name}测试异常: {e}")
            results.append((test_name, False))
            break
    
    # 输出总结
    print("\n" + "=" * 50)
    print("📊 诊断总结")
    print("=" * 50)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 所有测试通过！Gmail SMTP配置正确。")
    else:
        print("\n💡 故障排除建议:")
        print("1. 确认Gmail账号已启用两步验证")
        print("2. 重新生成应用专用密码")
        print("3. 检查网络防火墙设置")
        print("4. 尝试使用其他网络环境")
        print("5. 确认Gmail账号没有被限制")
    
    return all_passed

if __name__ == "__main__":
    main()
