#!/usr/bin/env python3
"""
测试前端API调用
"""

import requests
import json

def test_frontend_to_backend():
    """测试前端到后端的API调用"""
    print("🧪 测试前端到后端的API调用")
    print("=" * 50)
    
    # 测试数据
    test_data = {
        "email": "h133239238@gmail.com",
        "phone": "13800138000"
    }
    
    # 测试直接调用后端API
    print("1. 直接调用后端API (localhost:8000)")
    try:
        response = requests.post(
            "http://localhost:8000/api/auth/send-verification-code",
            headers={"Content-Type": "application/json"},
            json=test_data,
            timeout=10
        )
        
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        if response.status_code == 200:
            print("   ✅ 后端API正常工作")
        else:
            print("   ❌ 后端API返回错误")
            
    except Exception as e:
        print(f"   ❌ 后端API调用失败: {e}")
    
    print()
    
    # 测试通过前端代理调用
    print("2. 通过前端代理调用 (localhost:3001)")
    try:
        response = requests.post(
            "http://localhost:3001/api/auth/send-verification-code",
            headers={"Content-Type": "application/json"},
            json=test_data,
            timeout=10
        )
        
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        if response.status_code == 200:
            print("   ✅ 前端代理正常工作")
        else:
            print("   ❌ 前端代理返回错误")
            
    except Exception as e:
        print(f"   ❌ 前端代理调用失败: {e}")
    
    print()
    
    # 测试健康检查
    print("3. 测试健康检查")
    try:
        # 直接调用后端
        backend_health = requests.get("http://localhost:8000/api/auth/health", timeout=5)
        print(f"   后端健康检查: {backend_health.status_code} - {backend_health.json()}")
        
        # 通过前端代理调用
        frontend_health = requests.get("http://localhost:3001/api/auth/health", timeout=5)
        print(f"   前端代理健康检查: {frontend_health.status_code} - {frontend_health.json()}")
        
    except Exception as e:
        print(f"   ❌ 健康检查失败: {e}")

def main():
    """主函数"""
    print("🔍 前端API连接测试")
    print("这个测试检查前端是否能正确调用后端API")
    print()
    
    test_frontend_to_backend()
    
    print("\n" + "=" * 50)
    print("📋 如果测试失败，请检查:")
    print("1. 后端服务是否运行在 localhost:8000")
    print("2. 前端服务是否运行在 localhost:3001")
    print("3. package.json 中是否配置了 proxy")
    print("4. 前端服务是否重启以应用代理配置")

if __name__ == "__main__":
    main()
