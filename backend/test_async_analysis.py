#!/usr/bin/env python3
"""
测试异步分析功能的脚本
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

# 测试配置
API_BASE_URL = "http://localhost:8000"
TEST_USER_BACKGROUND = {
    "undergraduate_university": "清华大学",
    "undergraduate_major": "计算机科学与技术",
    "gpa": 3.8,
    "gpa_scale": "4.0",
    "graduation_year": 2024,
    "target_countries": ["美国", "加拿大"],
    "target_majors": ["计算机科学", "人工智能"],
    "target_degree_type": "Master",
    "language_test_type": "TOEFL",
    "language_total_score": 105,
    "gre_total": 325
}

async def test_async_analysis():
    """测试异步分析功能"""
    print("🚀 开始测试异步分析功能...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. 启动分析任务
            print("\n📝 步骤 1: 启动分析任务")
            start_response = await session.post(
                f"{API_BASE_URL}/api/analyze",
                json=TEST_USER_BACKGROUND
            )
            
            if start_response.status != 200:
                print(f"❌ 启动任务失败: {start_response.status}")
                return
            
            start_data = await start_response.json()
            task_id = start_data.get("task_id")
            print(f"✅ 任务启动成功，任务ID: {task_id}")
            print(f"   状态: {start_data.get('status')}")
            print(f"   消息: {start_data.get('message')}")
            
            # 2. 轮询任务状态
            print("\n🔄 步骤 2: 轮询任务状态")
            max_poll_time = 60  # 测试时只轮询60秒
            poll_interval = 3   # 3秒轮询一次
            start_time = time.time()
            
            while time.time() - start_time < max_poll_time:
                try:
                    status_response = await session.get(
                        f"{API_BASE_URL}/api/analyze/{task_id}"
                    )
                    
                    if status_response.status == 200:
                        status_data = await status_response.json()
                        current_status = status_data.get("status")
                        progress = status_data.get("progress", 0)
                        
                        print(f"   轮询 {time.time() - start_time:.1f}s: 状态={current_status}, 进度={progress}%")
                        
                        if current_status == "completed":
                            print(f"✅ 任务完成！")
                            print(f"   结果: {json.dumps(status_data.get('result', {}), indent=2, ensure_ascii=False)}")
                            return
                        elif current_status == "failed":
                            print(f"❌ 任务失败: {status_data.get('error')}")
                            return
                        elif current_status == "cancelled":
                            print(f"⚠️  任务已取消")
                            return
                    
                    # 等待下次轮询
                    await asyncio.sleep(poll_interval)
                    
                except Exception as e:
                    print(f"   轮询出错: {e}")
                    await asyncio.sleep(poll_interval)
            
            print(f"⏰ 轮询超时 ({max_poll_time}秒)")
            
            # 3. 测试取消任务
            print("\n🛑 步骤 3: 测试取消任务")
            try:
                cancel_response = await session.delete(
                    f"{API_BASE_URL}/api/analyze/{task_id}"
                )
                
                if cancel_response.status == 200:
                    cancel_data = await cancel_response.json()
                    print(f"✅ 任务取消成功: {cancel_data.get('message')}")
                else:
                    print(f"❌ 任务取消失败: {cancel_response.status}")
                    
            except Exception as e:
                print(f"❌ 取消任务时出错: {e}")
                
        except Exception as e:
            print(f"❌ 测试过程中出错: {e}")

async def test_health_endpoints():
    """测试健康检查端点"""
    print("\n🏥 测试健康检查端点...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 基础健康检查
            health_response = await session.get(f"{API_BASE_URL}/health")
            if health_response.status == 200:
                health_data = await health_response.json()
                print(f"✅ 基础健康检查: {health_data}")
            else:
                print(f"❌ 基础健康检查失败: {health_response.status}")
            
            # 详细健康检查
            detailed_health_response = await session.get(f"{API_BASE_URL}/health/detailed")
            if detailed_health_response.status == 200:
                detailed_health_data = await detailed_health_response.json()
                print(f"✅ 详细健康检查: {json.dumps(detailed_health_data, indent=2, ensure_ascii=False)}")
            else:
                print(f"❌ 详细健康检查失败: {detailed_health_response.status}")
                
        except Exception as e:
            print(f"❌ 健康检查测试出错: {e}")

async def main():
    """主函数"""
    print("🧪 异步分析功能测试套件")
    print("=" * 50)
    
    # 测试健康检查
    await test_health_endpoints()
    
    # 测试异步分析
    await test_async_analysis()
    
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())
