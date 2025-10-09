#!/usr/bin/env python3
"""
调试脚本：追踪GPA数据处理的每个步骤
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.supabase_service import SupabaseService
from backend.services.similarity_matcher import SimilarityMatcher
from backend.services.gemini_service import GeminiService
from backend.models.schemas import UserBackground
import asyncio

async def debug_gpa_flow():
    """调试GPA数据流"""
    print("=== 开始调试GPA数据流 ===\n")
    
    # 1. 从Supabase获取原始数据
    print("1. 从Supabase获取原始数据...")
    supabase_service = SupabaseService()
    try:
        cases = supabase_service.get_all_cases()
        print(f"   获取到 {len(cases)} 个案例")
        
        # 显示前5个案例的GPA信息
        print("\n   前5个案例的GPA信息:")
        for i, case in enumerate(cases[:5]):
            print(f"   案例 {i+1}:")
            print(f"     ID: {case.get('id')}")
            print(f"     gpa_4_scale: {case.get('gpa_4_scale')} (类型: {type(case.get('gpa_4_scale'))})")
            print(f"     gpa_original: {case.get('gpa_original')}")
            print(f"     gpa_scale_type: {case.get('gpa_scale_type')}")
            print()
    except Exception as e:
        print(f"   错误: {e}")
        return
    
    # 2. 测试SimilarityMatcher的数据加载
    print("2. 测试SimilarityMatcher的数据加载...")
    try:
        matcher = SimilarityMatcher()
        matcher._load_cases()
        
        if matcher.cases_df is not None:
            print(f"   成功加载 {len(matcher.cases_df)} 个案例到DataFrame")
            print("\n   DataFrame前5行的GPA信息:")
            for i, row in matcher.cases_df.head().iterrows():
                print(f"   行 {i}: gpa_4_scale = {row['gpa_4_scale']} (类型: {type(row['gpa_4_scale'])})")
        else:
            print("   错误: DataFrame为空")
    except Exception as e:
        print(f"   错误: {e}")
        return
    
    # 3. 测试相似案例查找
    print("\n3. 测试相似案例查找...")
    try:
        # 创建一个测试用户背景
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
        
        similar_cases = matcher.find_similar_cases(test_user, top_n=5)
        print(f"   找到 {len(similar_cases)} 个相似案例")
        
        print("\n   相似案例的GPA信息:")
        for i, case in enumerate(similar_cases):
            case_data = case.get('case_data', {})
            print(f"   案例 {i+1}:")
            print(f"     case_id: {case.get('case_id')}")
            print(f"     gpa_4_scale: {case_data.get('gpa_4_scale')} (类型: {type(case_data.get('gpa_4_scale'))})")
            print(f"     similarity_score: {case.get('similarity_score')}")
            print()
    except Exception as e:
        print(f"   错误: {e}")
        return
    
    # 4. 测试单个案例分析
    print("4. 测试单个案例分析...")
    try:
        gemini_service = GeminiService()
        
        if similar_cases:
            first_case = similar_cases[0]
            case_data = first_case.get('case_data', {})
            
            print(f"   分析第一个案例 (ID: {case_data.get('id')})...")
            print(f"   原始gpa_4_scale: {case_data.get('gpa_4_scale')}")
            
            # 注意：这里需要实际的Gemini API调用，可能会失败
            try:
                case_analysis = await gemini_service.analyze_single_case(test_user, case_data)
                if case_analysis:
                    print(f"   分析结果GPA: {case_analysis.gpa} (类型: {type(case_analysis.gpa)})")
                else:
                    print("   分析失败，返回None")
            except Exception as e:
                print(f"   Gemini API调用失败: {e}")
                print("   这是预期的，因为需要有效的API密钥")
        else:
            print("   没有相似案例可供分析")
    except Exception as e:
        print(f"   错误: {e}")
        return
    
    print("\n=== 调试完成 ===")

if __name__ == "__main__":
    asyncio.run(debug_gpa_flow())

