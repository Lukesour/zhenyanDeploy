import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from backend.models.schemas import (
    HollandAssessmentRequest, 
    HollandAssessmentResult, 
    HollandTypeScore, 
    HollandTypeInterpretation
)

logger = logging.getLogger(__name__)

class HollandService:
    """霍兰德职业兴趣评估服务"""
    
    def __init__(self):
        """初始化服务，加载霍兰德数据"""
        self.holland_data = None
        self._load_holland_data()
    
    def _load_holland_data(self):
        """从JSON文件加载霍兰德数据"""
        try:
            # 获取项目根目录下的data文件夹
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent  # 回到项目根目录
            data_file = project_root / "data" / "HollandCodes.json"
            
            if not data_file.exists():
                logger.error(f"Holland data file not found: {data_file}")
                return
            
            with open(data_file, 'r', encoding='utf-8') as f:
                self.holland_data = json.load(f)
            
            logger.info("Holland data loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Holland data: {str(e)}")
            self.holland_data = None
    
    def get_holland_data(self) -> Optional[Dict]:
        """获取霍兰德数据"""
        return self.holland_data
    
    def calculate_scores(self, request: HollandAssessmentRequest) -> HollandAssessmentResult:
        """计算霍兰德评估结果"""
        if not self.holland_data:
            raise ValueError("霍兰德数据未加载")
        
        # 初始化六个类型的得分
        type_scores = {
            'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0
        }
        
        # 获取评分映射
        scoring_map = self.holland_data.get('scoring_map', {})
        
        # 计算每个类型的得分
        for answer in request.answers:
            question_id = answer.question_id
            score = answer.score
            
            # 找到这个问题对应的类型
            for type_code, question_ids in scoring_map.items():
                if question_id in question_ids:
                    type_scores[type_code] += score
                    break
        
        # 计算总分用于百分比计算
        total_score = sum(type_scores.values())
        
        # 创建类型得分列表
        type_score_list = []
        type_names = {
            'R': '现实型',
            'I': '研究型', 
            'A': '艺术型',
            'S': '社会型',
            'E': '企业型',
            'C': '常规型'
        }
        
        for type_code, score in type_scores.items():
            percentage = (score / total_score * 100) if total_score > 0 else 0
            type_score_list.append(HollandTypeScore(
                type_code=type_code,
                type_name=type_names[type_code],
                score=score,
                percentage=round(percentage, 1)
            ))
        
        # 按得分排序，取前三名
        sorted_types = sorted(type_score_list, key=lambda x: x.score, reverse=True)
        top_three_codes = [t.type_code for t in sorted_types[:3]]
        
        # 生成霍兰德代码（前三名的字母组合）
        holland_code = ''.join(top_three_codes)
        
        # 获取前三名类型的详细解释
        results_interpretation = self.holland_data.get('results_interpretation', {})
        top_three_interpretations = []
        
        for type_code in top_three_codes:
            if type_code in results_interpretation:
                interp_data = results_interpretation[type_code]
                interpretation = HollandTypeInterpretation(
                    type_code=type_code,
                    name=interp_data.get('name', ''),
                    nickname=interp_data.get('nickname', ''),
                    characteristics=interp_data.get('characteristics', ''),
                    typical_careers=interp_data.get('typical_careers', [])
                )
                top_three_interpretations.append(interpretation)
        
        # 创建评估结果
        result = HollandAssessmentResult(
            holland_code=holland_code,
            type_scores=type_score_list,
            top_three_types=top_three_interpretations,
            assessment_date=datetime.now().isoformat()
        )
        
        return result
    
    def validate_answers(self, request: HollandAssessmentRequest) -> bool:
        """验证答案的完整性和有效性"""
        if not self.holland_data:
            return False
        
        # 获取所有问题ID
        all_question_ids = set()
        for section in self.holland_data.get('sections', []):
            for question in section.get('questions', []):
                all_question_ids.add(question.get('id'))
        
        # 检查是否所有问题都有答案
        answered_question_ids = {answer.question_id for answer in request.answers}
        
        if answered_question_ids != all_question_ids:
            logger.warning(f"Missing answers for questions: {all_question_ids - answered_question_ids}")
            return False
        
        # 检查分数是否在有效范围内
        for answer in request.answers:
            if not (1 <= answer.score <= 5):
                logger.warning(f"Invalid score {answer.score} for question {answer.question_id}")
                return False
        
        return True
