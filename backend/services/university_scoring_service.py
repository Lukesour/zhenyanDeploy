import json
import logging
from typing import Dict, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class UniversityScoringService:
    """
    院校评分服务 - 基于手动维护的分级列表进行院校评分和分级
    """
    
    def __init__(self):
        self.tier_data = self._load_tier_data()
        self.university_to_tier_map = self._build_university_map()
        logger.info("University scoring service initialized with manual tier data")
    
    def _load_tier_data(self) -> Dict:
        """加载院校分级数据"""
        try:
            config_path = Path(__file__).parent.parent / "config" / "university_tiers.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load university tier data: {str(e)}")
            raise Exception(f"院校层级配置文件缺失或损坏: {str(e)}")
    
    def _build_university_map(self) -> Dict[str, str]:
        """构建大学名称到层级的映射"""
        university_map = {}
        for tier, universities in self.tier_data.get("university_tiers", {}).items():
            for university in universities:
                university_map[university] = tier
        return university_map
    
    def get_university_score_and_tier(self, university_name: str) -> Tuple[float, str]:
        """
        获取大学的评分和层级
        
        Args:
            university_name: 大学名称
            
        Returns:
            Tuple[float, str]: (评分, 层级)
        """
        if not university_name:
            return self._get_default_score_and_tier()
        
        # 清理大学名称（去除空格等）
        cleaned_name = university_name.strip()
        
        # 查找精确匹配
        tier = self.university_to_tier_map.get(cleaned_name)
        
        if tier:
            score = self.tier_data["tier_definitions"][tier]["fixed_score"]
            logger.debug(f"Found university '{cleaned_name}' in {tier} with score {score}")
            return score, tier
        

        
        # 如果都没找到，归为Tier 4
        score, tier = self._get_default_score_and_tier()
        logger.debug(f"University '{cleaned_name}' not found, assigned to {tier} with score {score}")
        return score, tier
    

    
    def _get_default_score_and_tier(self) -> Tuple[float, str]:
        """获取默认的评分和层级（Tier 4）"""
        tier = "Tier 4"
        score = self.tier_data["tier_definitions"][tier]["fixed_score"]
        return score, tier
    
    def get_tier_info(self, tier: str) -> Dict:
        """获取层级信息"""
        return self.tier_data["tier_definitions"].get(tier, {})
    
    def get_all_universities_in_tier(self, tier: str) -> list:
        """获取指定层级的所有大学"""
        return self.tier_data["university_tiers"].get(tier, [])
    

    
    def get_tier_score_for_similarity(self, tier: str) -> float:
        """
        为相似度计算获取层级分数
        返回0-1之间的分数，用于相似度计算
        """
        tier_scores = {
            "Tier 0": 1.0,
            "Tier 1": 0.8,
            "Tier 2": 0.6,
            "Tier 3": 0.4,
            "Tier 4": 0.2
        }
        return tier_scores.get(tier, 0.2)