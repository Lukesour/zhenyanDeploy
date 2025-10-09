#!/usr/bin/env python3
"""
测试异步任务功能的脚本
"""
import asyncio
import json
import time
from datetime import datetime
from app.main import execute_analysis_task
from backend.models.schemas import UserBackground

# 模拟用户背景数据
test_user_background = UserBackground(
    undergraduate_university="清华大学",
    undergraduate_major="计算机科学与技术",
    gpa=3.8,
    gpa_scale="4.0",
    graduation_year=2024,
    language_test_type="TOEFL",
    language_total_score=105,
    target_countries=["美国", "加拿大"],
    target_majors=["计算机科学", "人工智能"],
    target_degree_type="硕士"
)

async def test_async_task():
    """测试异步任务执行"""
    print(f"[{datetime.now()}] 开始测试异步任务...")
    
    # 模拟任务ID
    task_id = "test-task-001"
    
    try:
        # 启动异步任务
        print(f"[{datetime.now()}] 启动分析任务 {task_id}...")
        
        # 创建后台任务
        await execute_analysis_task(task_id, test_user_background)
        
        print(f"[{datetime.now()}] 任务 {task_id} 执行完成")
        
    except Exception as e:
        print(f"[{datetime.now()}] 任务执行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("异步任务测试脚本")
    print("=" * 50)
    
    # 运行测试
    asyncio.run(test_async_task())
