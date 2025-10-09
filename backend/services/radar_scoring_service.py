"""
雷达图评分服务
根据用户背景信息计算五大维度的能力得分
"""
import logging
import re
from typing import List, Optional, Dict, Any
from backend.models.schemas import UserBackground
from backend.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

class RadarScoringService:
    """雷达图评分服务"""
    
    def __init__(self):
        self.gemini_service = GeminiService()
        
        # 院校分层数据
        self.university_tiers = {
            # Tier 0 (99-100分): 清华、北大
            "tier_0": {
                "score_range": (99, 100),
                "universities": ["清华大学", "北京大学", "哈佛大学", "麻省理工学院", "斯坦福大学", "牛津大学", "加利福尼亚大学伯克利分校", "剑桥大学", "耶鲁大学", "多伦多大学", "芝加哥大学", "密歇根大学安娜堡分校", "加州理工学院", "普林斯顿大学"]
            },
            
            # Tier 1 (95-98分): 顶尖院校
            "tier_1": {
                "score_range": (95, 98),
                "universities": ["复旦大学", "上海交通大学", "浙江大学", "中国科学技术大学", "南京大学", 
                                 "中国人民大学", "北京航空航天大学", "北京理工大学", "哈尔滨工业大学", "西安交通大学", "墨尔本大学", "悉尼大学", "苏黎世联邦理工学院", "新加坡国立大学", "南洋理工大学", "哥本哈根大学", "爱丁堡大学", "纽约大学", "伦敦大学学院", "华盛顿大学", "帝国理工学院", "哥伦比亚大学", "墨尔本", "杜克大学", "约翰斯·霍普金斯大学", "宾夕法尼亚大学", "加利福尼亚大学洛杉矶分校", "康奈尔大学", "卡内基梅隆大学", "伦敦政治经济学院", "加利福尼亚大学圣迭戈分校"]
            },
            
            # Tier 2 (85-94分): 优秀院校
            "tier_2": {
                "score_range": (85, 94),
                "universities": [
                    "中国农业大学", "南开大学", "北京师范大学", "天津大学", "吉林大学",
                    "大连理工大学", "同济大学", "东北大学", "华东师范大学", "东南大学",
                    "厦门大学", "山东大学", "中国海洋大学", "武汉大学", "华中科技大学",
                    "湖南大学", "中南大学", "国防科学技术大学", "中山大学", "华南理工大学",
                    "四川大学", "电子科技大学", "重庆大学", "西北工业大学", "西北农林科技大学",
                    "兰州大学", "中央民族大学", "南方科技大学", "深圳大学", "上海财经大学",
                    "对外经济贸易大学", "中央财经大学", "中国政法大学", "西安电子科技大学",
                    "北京邮电大学", "南京航空航天大学", "南京理工大学", "西南财经大学",
                    "华中师范大学", "中国科学院大学", "首都医科大学", "东北财经大学", "上海科技大学",
                    "香港中文大学（深圳）","东北大学秦皇岛分校","中国人民大学（苏州）","东北大学（中国）",
                    "山东大学（威海）"
                ]
            },
            
            # Tier 3 (75-84分): 良好院校
            "tier_3": {
                "score_range": (75, 84),
                "universities": [
                    "北京交通大学", "北京工业大学", "北京科技大学", "北京化工大学", "北京林业大学",
                    "中国传媒大学", "中央音乐学院", "北京中医药大学", "北京外国语大学",
                    "中国地质大学(北京)", "中国矿业大学(北京)", "中国石油大学(北京)", "华北电力大学",
                    "北京体育大学", "上海外国语大学", "上海大学", "东华大学", "华东理工大学",
                    "第二军医大学", "天津医科大学", "苏州大学", "中国矿业大学", "南京邮电大学",
                    "河海大学", "江南大学", "南京农业大学", "南京师范大学", "中国药科大学",
                    "西北大学", "长安大学", "陕西师范大学", "第四军医大学", "武汉理工大学",
                    "中南财经政法大学", "华中农业大学", "中国地质大学(武汉)", "西南交通大学",
                    "四川农业大学", "哈尔滨工程大学", "东北林业大学", "东北农业大学", "辽宁大学",
                    "大连海事大学", "东北师范大学", "延边大学", "暨南大学", "华南师范大学",
                    "湖南师范大学", "安徽大学", "合肥工业大学", "河北工业大学", "郑州大学",
                    "中国石油大学(华东)", "新疆大学", "石河子大学", "云南大学", "广西大学",
                    "贵州大学", "海南大学", "内蒙古大学", "南昌大学", "宁夏大学", "青海大学",
                    "太原理工大学", "西藏大学", "福州大学","香港浸会大学","上海海事大学","维克森林大学"
                ]
            },
            
            # Tier 4 (60-74分): 普通本科
            "tier_4": {
                "score_range": (60, 74),
                "universities": []  # 其他所有本科院校
            }
        }
        
        # 语言考试评分标准
        self.language_scoring = {
            "TOEFL": {
                (110, 120): (95, 100),  # 卓越
                (100, 109): (85, 94),   # 优秀
                (90, 99): (75, 84),     # 良好
                (80, 89): (65, 74),     # 中等
                (70, 79): (60, 64),     # 基础
                (0, 69): (0, 59)        # 低于60分
            },
            "IELTS": {
                (8.0, 9.0): (95, 100),  # 卓越
                (7.5, 7.9): (85, 94),   # 优秀
                (7.0, 7.4): (75, 84),   # 良好
                (6.5, 6.9): (65, 74),   # 中等
                (6.0, 6.4): (60, 64),   # 基础
                (0, 5.9): (0, 59)       # 低于60分
            },
            "GRE": {
                (330, 340): (95, 100),  # 卓越
                (325, 329): (85, 94),   # 优秀
                (320, 324): (75, 84),   # 良好
                (315, 319): (65, 74),   # 中等
                (310, 314): (60, 64),   # 基础
                (0, 309): (0, 59)       # 低于60分
            },
            "GMAT": {
                (730, 800): (95, 100),  # 卓越
                (700, 729): (85, 94),   # 优秀
                (650, 699): (75, 84),   # 良好
                (600, 649): (65, 74),   # 中等
                (550, 599): (60, 64),   # 基础
                (0, 549): (0, 59)       # 低于60分
            }
        }
    
    def calculate_radar_scores(self, user_background: UserBackground) -> List[int]:
        """
        计算雷达图五项能力得分
        返回: [学术能力, 语言能力, 科研背景, 实习背景, 院校背景]
        """
        try:
            logger.info("开始计算雷达图评分")
            
            # 1. 学术能力评分
            academic_score = self._calculate_academic_score(user_background)
            logger.info(f"学术能力得分: {academic_score}")
            
            # 2. 语言能力评分
            language_score = self._calculate_language_score(user_background)
            logger.info(f"语言能力得分: {language_score}")
            
            # 3. 科研背景评分
            research_score = self._calculate_research_score(user_background)
            logger.info(f"科研背景得分: {research_score}")
            
            # 4. 实习背景评分
            internship_score = self._calculate_internship_score(user_background)
            logger.info(f"实习背景得分: {internship_score}")
            
            # 5. 院校背景评分
            university_score = self._calculate_university_score(user_background)
            logger.info(f"院校背景得分: {university_score}")
            
            scores = [academic_score, language_score, research_score, internship_score, university_score]
            logger.info(f"雷达图最终得分: {scores}")
            
            return scores
            
        except Exception as e:
            logger.error(f"计算雷达图评分失败: {str(e)}")
            # 返回默认分数，避免系统崩溃
            return [70, 65, 60, 55, 75]
    
    def _calculate_academic_score(self, user_background: UserBackground) -> int:
        """计算学术能力得分"""
        try:
            gpa = user_background.gpa
            gpa_scale = user_background.gpa_scale
            
            if gpa_scale == "4.0":
                # 4.0制转换为百分制
                score = int((gpa / 4.0) * 100)
            elif gpa_scale == "100":
                # 已经是百分制
                score = int(gpa)
            else:
                # 尝试解析其他格式，如 "3.8/4.0"
                if "/" in str(gpa):
                    parts = str(gpa).split("/")
                    if len(parts) == 2:
                        numerator = float(parts[0])
                        denominator = float(parts[1])
                        score = int((numerator / denominator) * 100)
                    else:
                        score = 70  # 默认分数
                else:
                    score = 70  # 默认分数
            
            # 确保分数在合理范围内
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"计算学术能力得分失败: {str(e)}")
            return 70
    
    def _calculate_language_score(self, user_background: UserBackground) -> int:
        """计算语言能力得分"""
        try:
            scores = []
            
            # 检查托福成绩
            if (user_background.language_test_type == "TOEFL" and 
                user_background.language_total_score is not None):
                toefl_score = self._get_language_score("TOEFL", user_background.language_total_score)
                scores.append(toefl_score)
            
            # 检查雅思成绩
            if (user_background.language_test_type == "IELTS" and 
                user_background.language_total_score is not None):
                ielts_score = self._get_language_score("IELTS", user_background.language_total_score)
                scores.append(ielts_score)
            
            # 检查GRE成绩
            if user_background.gre_total is not None:
                gre_score = self._get_language_score("GRE", user_background.gre_total)
                scores.append(gre_score)
            
            # 检查GMAT成绩
            if user_background.gmat_total is not None:
                gmat_score = self._get_language_score("GMAT", user_background.gmat_total)
                scores.append(gmat_score)
            
            # 择优选择最高分
            if scores:
                return max(scores)
            else:
                # 没有语言成绩，给予基础分
                return 50
                
        except Exception as e:
            logger.error(f"计算语言能力得分失败: {str(e)}")
            return 50
    
    def _get_language_score(self, test_type: str, score: float) -> int:
        """根据考试类型和分数获取评分"""
        if test_type not in self.language_scoring:
            return 50
        
        scoring_rules = self.language_scoring[test_type]
        
        for score_range, rating_range in scoring_rules.items():
            if score_range[0] <= score <= score_range[1]:
                # 在范围内取中位数
                return int((rating_range[0] + rating_range[1]) / 2)
        
        return 50
    
    def _calculate_research_score(self, user_background: UserBackground) -> int:
        """计算科研背景得分"""
        try:
            if not user_background.research_experiences:
                return 30  # 没有科研经历
            
            # 将科研经历转换为文本
            research_text = self._format_experiences(user_background.research_experiences)
            
            if not research_text.strip():
                return 30
            
            # 使用Gemini评估科研背景质量
            research_score = self.gemini_service.evaluate_research_experience(research_text)
            
            # 基础保底分50分，然后根据LLM评估结果调整
            base_score = 50
            final_score = max(base_score, research_score)
            
            return min(100, final_score)
            
        except Exception as e:
            logger.error(f"计算科研背景得分失败: {str(e)}")
            return 40
    
    def _calculate_internship_score(self, user_background: UserBackground) -> int:
        """计算实习背景得分"""
        try:
            if not user_background.internship_experiences:
                return 30  # 没有实习经历
            
            # 将实习经历转换为文本
            internship_text = self._format_experiences(user_background.internship_experiences)
            
            if not internship_text.strip():
                return 30
            
            # 使用Gemini评估实习背景质量
            internship_score = self.gemini_service.evaluate_internship_experience(internship_text)
            
            # 基础保底分50分，然后根据LLM评估结果调整
            base_score = 50
            final_score = max(base_score, internship_score)
            
            return min(100, final_score)
            
        except Exception as e:
            logger.error(f"计算实习背景得分失败: {str(e)}")
            return 40
    
    def _calculate_university_score(self, user_background: UserBackground) -> int:
        """计算院校背景得分"""
        try:
            university_name = user_background.undergraduate_university
            
            # 查找院校所属层级
            for tier_name, tier_info in self.university_tiers.items():
                if university_name in tier_info["universities"]:
                    score_range = tier_info["score_range"]
                    # 返回范围中位数
                    return int((score_range[0] + score_range[1]) / 2)
            
            # 如果没有找到，默认为Tier 4（普通本科）
            tier_4_range = self.university_tiers["tier_4"]["score_range"]
            return int((tier_4_range[0] + tier_4_range[1]) / 2)
            
        except Exception as e:
            logger.error(f"计算院校背景得分失败: {str(e)}")
            return 65
    
    def _format_experiences(self, experiences: List[Dict[str, str]]) -> str:
        """将经历列表格式化为文本"""
        if not experiences:
            return ""
        
        formatted_text = []
        for exp in experiences:
            if isinstance(exp, dict):
                # 提取所有值并组合
                exp_text = " ".join([str(v) for v in exp.values() if v])
                if exp_text.strip():
                    formatted_text.append(exp_text.strip())
        
        return "\n".join(formatted_text)