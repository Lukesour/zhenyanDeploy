#!/usr/bin/env python3
"""
测试脚本：验证API返回的GPA数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.analysis_service import AnalysisService
from backend.models.schemas import UserBackground
import asyncio
import json

async def test_api_gpa():
    """测试API返回的GPA数据"""
    print("=== 测试API返回的GPA数据 ===\n")
    
    # 创建分析服务
    analysis_service = AnalysisService()
    
    # 创建测试用户背景
    test_user = UserBackground(
        undergraduate_university="清华大学",
        undergraduate_major="计算机科学与技术",
        gpa=3.5,
        gpa_scale="4.0",
        graduation_year=2024,
        target_countries=["美国"],
        target_majors=["计算机科学"],
        target_degree_type="硕士"
    )
    
    try:
        print("1. 调用分析API...")
        report = await analysis_service.generate_analysis_report(test_user)
        
        print(f"2. 获取到分析报告，包含 {len(report.similar_cases)} 个相似案例")
        
        print("\n3. 相似案例的GPA信息:")
        for i, case in enumerate(report.similar_cases):
            print(f"   案例 {i+1}:")
            print(f"     case_id: {case.case_id}")
            print(f"     gpa: {case.gpa} (类型: {type(case.gpa)})")
            print(f"     admitted_university: {case.admitted_university}")
            print(f"     admitted_program: {case.admitted_program}")
            print()
        
        # 检查是否有重复的GPA值
        gpa_values = [case.gpa for case in report.similar_cases]
        unique_gpas = set(gpa_values)
        print(f"4. GPA值统计:")
        print(f"   唯一GPA值: {sorted(unique_gpas)}")
        print(f"   总案例数: {len(gpa_values)}")
        print(f"   唯一GPA数: {len(unique_gpas)}")
        
        if len(unique_gpas) == 1:
            print(f"   ⚠️  警告：所有案例的GPA都是 {list(unique_gpas)[0]}！")
        else:
            print(f"   ✅ GPA值正常，有 {len(unique_gpas)} 个不同的值")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_gpa())

