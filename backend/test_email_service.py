#!/usr/bin/env python3
"""
Gmail SMTP邮件服务测试脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.email_service import EmailService
from backend.config.settings import settings

def test_email_service():
    """测试邮件服务"""
    print("🧪 Gmail SMTP邮件服务测试")
    print("="*50)
    
    # 检查配置
    print("📋 检查配置...")
    if not settings.GMAIL_SENDER_EMAIL:
        print("❌ GMAIL_SENDER_EMAIL 未配置")
        return False
    
    if not settings.GMAIL_APP_PASSWORD:
        print("❌ GMAIL_APP_PASSWORD 未配置")
        return False
    
    print(f"✅ 发送邮箱: {settings.GMAIL_SENDER_EMAIL}")
    print(f"✅ 应用密码: {'*' * len(settings.GMAIL_APP_PASSWORD)}")
    
    # 初始化邮件服务
    print("\n🚀 初始化邮件服务...")
    try:
        email_service = EmailService()
        print("✅ 邮件服务初始化成功")
    except Exception as e:
        print(f"❌ 邮件服务初始化失败: {e}")
        return False
    
    # 测试连接
    print("\n🔗 测试SMTP连接...")
    try:
        if email_service.test_connection():
            print("✅ Gmail SMTP连接成功")
        else:
            print("❌ Gmail SMTP连接失败")
            return False
    except Exception as e:
        print(f"❌ SMTP连接测试异常: {e}")
        return False
    
    # 生成验证码
    print("\n🔢 生成验证码...")
    try:
        verification_code = email_service.generate_verification_code()
        print(f"✅ 验证码生成成功: {verification_code}")
    except Exception as e:
        print(f"❌ 验证码生成失败: {e}")
        return False
    
    # 询问是否发送测试邮件
    print("\n📧 是否发送测试邮件？")
    test_email = input("请输入测试邮箱地址（回车跳过）: ").strip()
    
    if test_email:
        print(f"📤 发送测试邮件到: {test_email}")
        try:
            success = email_service.send_verification_email(
                to_email=test_email,
                verification_code=verification_code,
                user_name="测试用户"
            )
            
            if success:
                print("✅ 测试邮件发送成功！")
                print("📬 请检查您的邮箱（包括垃圾邮件文件夹）")
            else:
                print("❌ 测试邮件发送失败")
                return False
                
        except Exception as e:
            print(f"❌ 发送测试邮件异常: {e}")
            return False
    else:
        print("⏭️  跳过邮件发送测试")
    
    print("\n🎉 所有测试通过！Gmail SMTP邮件服务配置正确。")
    return True

def main():
    """主函数"""
    success = test_email_service()
    
    if success:
        print("\n✅ Gmail SMTP邮件服务测试完成，系统可以正常发送邮件。")
        sys.exit(0)
    else:
        print("\n❌ Gmail SMTP邮件服务测试失败，请检查配置。")
        print("\n📋 配置要求：")
        print("1. 在config.env中设置GMAIL_SENDER_EMAIL（您的Gmail地址）")
        print("2. 在config.env中设置GMAIL_APP_PASSWORD（16位应用专用密码）")
        print("3. 确保Gmail账号已启用两步验证")
        print("4. 确保已生成应用专用密码")
        sys.exit(1)

if __name__ == "__main__":
    main()
