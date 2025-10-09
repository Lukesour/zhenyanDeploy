"""
专业分类服务
统一处理本科专业、目标专业和录取专业的分类
"""
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class MajorClassificationService:
    """统一的专业分类服务"""
    
    def __init__(self):
        # 定义专业大类
        self.major_categories = {
            "计算机": {
                "keywords": [
                    "计算机", "computer", "软件", "software", "信息", "information",
                    "数据科学", "data science", "人工智能", "artificial intelligence", "ai",
                    "机器学习", "machine learning", "深度学习", "deep learning",
                    "网络工程", "network", "信息安全", "cybersecurity", "security",
                    "物联网", "iot", "大数据", "big data", "云计算", "cloud computing",
                    "区块链", "blockchain", "元宇宙", "metaverse", "虚拟现实", "vr",
                    "增强现实", "ar", "游戏开发", "game development"
                ],
                "exact_matches": [
                    "计算机科学与技术", "软件工程", "网络工程", "信息安全",
                    "数据科学与大数据技术", "人工智能", "物联网工程",
                    "数字媒体技术", "智能科学与技术", "网络空间安全",
                    "计算机", "数据科学", "人工智能理学硕士", "数据科学理学硕士",
                    "计算机科学理学硕士", "软件工程理学硕士", "信息技术理学硕士",
                    "计算机控制与自动化理学硕士", "信息科学与技术管理理学硕士",
                    "元宇宙科技理学硕士", "机器人学理学硕士", "智能制造理学硕士"
                ]
            },
            "电气电子": {
                "keywords": [
                    "电气", "electrical", "电子", "electronic", "通信", "communication",
                    "自动化", "automation", "控制", "control", "信号", "signal",
                    "微电子", "microelectronics", "集成电路", "ic", "芯片", "chip",
                    "电力", "power", "能源", "energy", "光电", "optoelectronics"
                ],
                "exact_matches": [
                    "电子信息工程", "通信工程", "电气工程及其自动化",
                    "自动化", "电子科学与技术", "微电子科学与工程",
                    "光电信息科学与工程", "信息工程", "电子信息科学与技术",
                    "电气电子", "电子及资讯工程学理学硕士", "电气工程理学硕士",
                    "通信工程理学硕士", "自动化理学硕士", "控制工程理学硕士"
                ]
            },
            "机械工程": {
                "keywords": [
                    "机械", "mechanical", "制造", "manufacturing", "材料", "material",
                    "工业", "industrial", "生产", "production", "设计", "design",
                    "汽车", "automotive", "航空", "aerospace", "船舶", "marine"
                ],
                "exact_matches": [
                    "机械工程", "机械设计制造及其自动化", "材料成型及控制工程",
                    "工业设计", "过程装备与控制工程", "车辆工程", "汽车服务工程",
                    "机械工程理学硕士", "材料工程理学硕士", "工业工程理学硕士",
                    "制造工程理学硕士", "设计学理学硕士"
                ]
            },
            "金融": {
                "keywords": [
                    "金融", "finance", "投资", "investment", "银行", "banking",
                    "保险", "insurance", "证券", "securities", "基金", "fund",
                    "风险", "risk", "量化", "quantitative", "金工", "fintech",
                    "金融科技", "financial technology", "资产", "asset"
                ],
                "exact_matches": [
                    "金融学", "金融工程", "投资学", "金融数学", "保险学",
                    "信用管理", "经济与金融", "金融", "金工金数",
                    "金融学硕士", "金融学理学硕士", "量化金融与金融科技理学硕士",
                    "金融工程理学硕士", "投资学理学硕士", "风险管理理学硕士"
                ]
            },
            "经济": {
                "keywords": [
                    "经济", "economics", "贸易", "trade", "商务", "business",
                    "国际", "international", "宏观", "macro", "微观", "micro",
                    "发展", "development", "产业", "industry"
                ],
                "exact_matches": [
                    "经济学", "国际经济与贸易", "财政学", "税收学",
                    "国民经济管理", "贸易经济", "经济统计学",
                    "经济", "经济学硕士", "经济学理学硕士", "应用经济学理学硕士",
                    "国际经济理学硕士", "发展经济学理学硕士"
                ]
            },
            "管理": {
                "keywords": [
                    "管理", "management", "工商", "business administration",
                    "市场", "marketing", "人力资源", "human resource", "hr",
                    "物流", "logistics", "供应链", "supply chain", "运营", "operations",
                    "战略", "strategy", "组织", "organization", "领导", "leadership"
                ],
                "exact_matches": [
                    "工商管理", "市场营销", "人力资源管理", "财务管理",
                    "物流管理", "电子商务", "旅游管理", "酒店管理",
                    "管理", "工商管理", "管理学理学硕士", "工程商业管理理学硕士",
                    "管理经济学理学硕士（中文授课）", "市场营销理学硕士",
                    "人力资源管理理学硕士", "物流管理理学硕士"
                ]
            },
            "会计": {
                "keywords": [
                    "会计", "accounting", "审计", "audit", "财务", "financial",
                    "成本", "cost", "税务", "tax", "预算", "budget"
                ],
                "exact_matches": [
                    "会计学", "财务管理", "审计学", "资产评估",
                    "会计", "会计学硕士", "会计学理学硕士", "会计学理学硕士（CUHK-Shenzhen）",
                    "财务管理理学硕士", "审计学理学硕士"
                ]
            },
            "商业分析": {
                "keywords": [
                    "商业分析", "business analytics", "商务分析", "business intelligence",
                    "数据分析", "data analytics", "商业智能", "bi"
                ],
                "exact_matches": [
                    "商业分析", "商业分析理学硕士", "商务分析理学硕士",
                    "数据分析理学硕士", "商业智能理学硕士"
                ]
            },
            "法律": {
                "keywords": [
                    "法学", "law", "法律", "legal", "司法", "justice",
                    "知识产权", "intellectual property", "国际法", "international law"
                ],
                "exact_matches": [
                    "法学", "知识产权", "监狱学", "法律", "法学硕士",
                    "法律硕士", "知识产权法理学硕士", "国际法理学硕士"
                ]
            },
            "教育": {
                "keywords": [
                    "教育", "education", "师范", "teaching", "pedagogy",
                    "心理", "psychology", "学前", "preschool"
                ],
                "exact_matches": [
                    "教育学", "学前教育", "小学教育", "体育教育",
                    "教育", "教育学硕士", "教育理学硕士", "心理学理学硕士",
                    "应用心理学理学硕士", "教育心理学理学硕士"
                ]
            },
            "医学": {
                "keywords": [
                    "医学", "medicine", "临床", "clinical", "护理", "nursing",
                    "药学", "pharmacy", "生物医学", "biomedical", "健康", "health",
                    "公共卫生", "public health"
                ],
                "exact_matches": [
                    "临床医学", "口腔医学", "预防医学", "中医学", "护理学",
                    "药学", "医学检验技术", "医学影像学",
                    "医学", "药学", "公共卫生", "生物医学工程理学硕士",
                    "护理学理学硕士", "药学理学硕士", "公共卫生理学硕士"
                ]
            },
            "数学": {
                "keywords": [
                    "数学", "mathematics", "统计", "statistics", "应用数学", "applied math",
                    "概率", "probability", "运筹", "operations research"
                ],
                "exact_matches": [
                    "数学与应用数学", "信息与计算科学", "统计学", "应用统计学",
                    "数学", "统计学理学硕士", "应用数学理学硕士",
                    "数据科学与统计学理学硕士", "运筹学理学硕士"
                ]
            },
            "物理": {
                "keywords": [
                    "物理", "physics", "应用物理", "applied physics",
                    "核", "nuclear", "光学", "optics"
                ],
                "exact_matches": [
                    "物理学", "应用物理学", "核物理", "光电信息科学与工程",
                    "物理", "物理学理学硕士", "应用物理学理学硕士"
                ]
            },
            "化学": {
                "keywords": [
                    "化学", "chemistry", "化工", "chemical engineering",
                    "材料化学", "material chemistry", "应用化学", "applied chemistry"
                ],
                "exact_matches": [
                    "化学", "应用化学", "化学工程与工艺", "材料化学",
                    "化学", "化工", "化学理学硕士", "化学工程理学硕士",
                    "应用化学理学硕士", "材料化学理学硕士"
                ]
            },
            "生物": {
                "keywords": [
                    "生物", "biology", "生命科学", "life science", "生物技术", "biotechnology",
                    "生物工程", "bioengineering", "生物信息", "bioinformatics"
                ],
                "exact_matches": [
                    "生物科学", "生物技术", "生物工程", "生物信息学",
                    "生态学", "生物", "生物工程", "生物科学理学硕士",
                    "生物技术理学硕士", "生物工程理学硕士", "生物信息学理学硕士"
                ]
            },
            "建筑": {
                "keywords": [
                    "建筑", "architecture", "土木", "civil engineering",
                    "城市规划", "urban planning", "景观", "landscape"
                ],
                "exact_matches": [
                    "建筑学", "土木工程", "城乡规划", "风景园林",
                    "建筑", "土木工程", "建筑学理学硕士", "土木工程理学硕士",
                    "城市规划理学硕士", "景观建筑理学硕士"
                ]
            },
            "艺术": {
                "keywords": [
                    "艺术", "art", "设计", "design", "美术", "fine arts",
                    "音乐", "music", "舞蹈", "dance", "戏剧", "drama",
                    "影视", "film", "动画", "animation", "数字媒体", "digital media"
                ],
                "exact_matches": [
                    "美术学", "绘画", "雕塑", "摄影", "艺术设计学",
                    "视觉传达设计", "环境设计", "产品设计", "数字媒体艺术",
                    "艺术", "影视", "设计学理学硕士", "艺术学理学硕士",
                    "数字媒体艺术理学硕士", "视觉传达设计理学硕士"
                ]
            },
            "新闻传播": {
                "keywords": [
                    "新闻", "journalism", "传播", "communication", "媒体", "media",
                    "广告", "advertising", "公关", "public relations", "编辑", "editing"
                ],
                "exact_matches": [
                    "新闻学", "广播电视学", "广告学", "传播学", "编辑出版学",
                    "新闻", "媒体与传播", "新媒体", "媒介与社会", "科学传播",
                    "策略传播", "媒体产业", "新闻学理学硕士", "传播学理学硕士",
                    "媒体研究理学硕士", "广告学理学硕士"
                ]
            },
            "语言文学": {
                "keywords": [
                    "语言", "language", "文学", "literature", "汉语", "chinese",
                    "英语", "english", "翻译", "translation", "外语", "foreign language"
                ],
                "exact_matches": [
                    "汉语言文学", "英语", "翻译", "日语", "法语", "德语",
                    "语言", "语言学理学硕士", "翻译学理学硕士",
                    "英语语言文学理学硕士", "汉语言文学理学硕士"
                ]
            },
            "其他": {
                "keywords": [],
                "exact_matches": []
            }
        }
    
    def classify_major(self, major_name: str) -> str:
        """
        对专业进行分类
        
        Args:
            major_name: 专业名称
            
        Returns:
            专业大类名称
        """
        if not major_name:
            return "其他"
        
        major_lower = str(major_name).lower().strip()
        
        # 首先尝试精确匹配
        for category, config in self.major_categories.items():
            if category == "其他":
                continue
                
            for exact_match in config["exact_matches"]:
                if exact_match.lower() == major_lower or exact_match in major_name:
                    logger.debug(f"专业 '{major_name}' 通过精确匹配归类为: {category}")
                    return category
        
        # 然后尝试关键词匹配
        for category, config in self.major_categories.items():
            if category == "其他":
                continue
                
            for keyword in config["keywords"]:
                if keyword.lower() in major_lower:
                    logger.debug(f"专业 '{major_name}' 通过关键词 '{keyword}' 归类为: {category}")
                    return category
        
        logger.debug(f"专业 '{major_name}' 未找到匹配，归类为: 其他")
        return "其他"

    def classify_case_admitted_major(self, major_name: str) -> str:
        """
        对案例录取专业进行分类，映射到前端定义的目标专业大类

        Args:
            major_name: 案例录取专业名称

        Returns:
            对应的前端目标专业大类名称
        """
        if not major_name:
            return "其他"

        major_lower = str(major_name).lower().strip()

        # 定义案例录取专业到前端目标专业的映射规则
        # 注意：更具体的匹配应该放在前面，避免被通用匹配覆盖
        mapping_rules = {
            # 商科类映射 - 先匹配更具体的专业
            "工商管理": ["工商管理", "mba", "business administration", "工商管理硕士"],
            "金工金数": ["金融工程", "金融数学", "quantitative finance", "financial engineering", "mathematical finance"],
            "金融": ["金融", "finance", "金融学", "金融硕士", "应用金融", "国际金融"],
            "商业分析": ["商业分析", "business analytics", "商务分析", "数据分析", "business intelligence"],
            "经济": ["经济", "economics", "经济学", "应用经济", "国际经济"],
            "会计": ["会计", "accounting", "会计学", "财务管理", "审计"],
            "市场营销": ["市场营销", "marketing", "市场学", "品牌管理"],
            "信息系统": ["信息系统", "information systems", "管理信息系统", "信息管理"],
            "人力资源管理": ["人力资源", "human resources", "人事管理"],
            "供应链管理": ["供应链", "supply chain", "物流管理", "运营管理"],
            "创业与创新": ["创业", "entrepreneurship", "创新管理", "innovation"],
            "房地产": ["房地产", "real estate", "物业管理"],
            "旅游酒店管理": ["旅游", "tourism", "酒店管理", "hospitality"],
            "管理": ["管理", "management", "企业管理", "管理学"],  # 放在最后，避免过度匹配

            # 社科类映射
            "教育": ["教育", "education", "教育学", "师范", "教学"],
            "建筑": ["建筑", "architecture", "建筑学", "城市规划"],
            "法律": ["法学", "law", "法律", "法律硕士", "法学硕士"],
            "社会学与社工": ["社会学", "sociology", "社会工作", "social work"],
            "国际关系": ["国际关系", "international relations", "外交", "国际事务"],
            "哲学": ["哲学", "philosophy"],
            "历史": ["历史", "history", "史学"],
            "公共政策与事务": ["公共管理", "public administration", "公共政策", "public policy"],
            "艺术": ["艺术", "art", "美术", "设计", "艺术设计"],
            "公共卫生": ["公共卫生", "public health", "卫生管理"],
            "心理学": ["心理学", "psychology", "应用心理"],
            "体育": ["体育", "sports", "运动", "体育教育"],
            "药学": ["药学", "pharmacy", "药物", "制药"],
            "医学": ["医学", "medicine", "临床医学", "基础医学"],
            "新闻": ["新闻", "journalism", "新闻学"],
            "影视": ["影视", "film", "电影", "广播电视"],
            "文化": ["文化", "culture", "文化产业", "文化管理"],
            "媒体与传播": ["传播", "communication", "媒体", "media"],
            "新媒体": ["新媒体", "new media", "数字媒体"],
            "媒介与社会": ["媒介", "media studies"],
            "科学传播": ["科学传播", "science communication"],
            "策略传播": ["策略传播", "strategic communication"],
            "媒体产业": ["媒体产业", "media industry"],
            "语言": ["语言", "language", "语言学", "外语", "英语", "中文"],

            # 工科类映射
            "计算机": ["计算机", "computer", "软件", "software", "信息技术", "it"],
            "电气电子": ["电气", "electrical", "电子", "electronics", "通信", "communication"],
            "数据科学": ["数据科学", "data science", "大数据", "big data", "人工智能", "ai"],
            "机械工程": ["机械", "mechanical", "机械工程", "自动化"],
            "材料": ["材料", "materials", "材料科学", "材料工程"],
            "化工": ["化工", "chemical engineering", "化学工程"],
            "生物工程": ["生物工程", "bioengineering", "生物技术", "biotechnology"],
            "土木工程": ["土木", "civil engineering", "建筑工程"],
            "工程管理": ["工程管理", "engineering management", "项目管理"],
            "环境工程": ["环境", "environmental", "环境工程", "环保"],
            "工业工程": ["工业工程", "industrial engineering", "系统工程"],
            "能源": ["能源", "energy", "新能源", "可再生能源"],
            "航空工程": ["航空", "aerospace", "航天", "飞行器"],
            "地球科学": ["地质", "geology", "地球科学", "地理"],
            "交通运输": ["交通", "transportation", "运输", "物流"],
            "海洋技术": ["海洋", "marine", "海洋工程"],
            "食品科学": ["食品", "food science", "食品工程"],

            # 理科类映射
            "物理": ["物理", "physics", "应用物理"],
            "化学": ["化学", "chemistry", "应用化学"],
            "数学": ["数学", "mathematics", "应用数学", "统计"],
            "生物": ["生物", "biology", "生物科学", "生命科学"]
        }

        # 遍历映射规则进行匹配
        for target_category, keywords in mapping_rules.items():
            for keyword in keywords:
                if keyword.lower() in major_lower:
                    logger.debug(f"案例录取专业 '{major_name}' 通过关键词 '{keyword}' 映射为: {target_category}")
                    return target_category

        # 如果没有匹配到，返回"其他"
        logger.debug(f"案例录取专业 '{major_name}' 未找到匹配，归类为: 其他")
        return "其他"

    def get_major_similarity(self, category1: str, category2: str) -> float:
        """
        计算两个专业大类之间的相似度
        
        Args:
            category1: 第一个专业大类
            category2: 第二个专业大类
            
        Returns:
            相似度分数 (0-1)
        """
        if category1 == category2:
            return 1.0
        
        # 定义相关专业大类
        # 基于前端定义的目标专业重新定义相关专业关系
        related_categories = {
            # 商科类专业相关性
            "金工金数": ["金融", "数学", "商业分析"],
            "金融": ["金工金数", "经济", "管理", "会计", "商业分析"],
            "商业分析": ["计算机", "金融", "管理", "数学", "数据科学"],
            "经济": ["金融", "管理", "会计"],
            "会计": ["金融", "经济", "管理"],
            "市场营销": ["管理", "商业分析"],
            "信息系统": ["计算机", "管理", "商业分析"],
            "管理": ["金融", "经济", "会计", "商业分析", "工商管理"],
            "人力资源管理": ["管理", "心理学"],
            "供应链管理": ["管理", "工业工程"],
            "创业与创新": ["管理", "工商管理"],
            "房地产": ["管理", "建筑"],
            "旅游酒店管理": ["管理"],
            "工商管理": ["管理", "金融", "经济"],
            "其他商科": ["管理", "金融"],

            # 社科类专业相关性
            "教育": ["心理学", "语言"],
            "建筑": ["艺术", "房地产"],
            "法律": ["公共政策与事务"],
            "社会学与社工": ["心理学", "公共政策与事务"],
            "国际关系": ["法律", "公共政策与事务"],
            "哲学": ["历史"],
            "历史": ["哲学", "文化"],
            "公共政策与事务": ["法律", "国际关系", "社会学与社工"],
            "艺术": ["建筑", "新闻", "影视", "文化"],
            "公共卫生": ["医学"],
            "心理学": ["教育", "社会学与社工", "人力资源管理"],
            "体育": [],
            "药学": ["医学", "化学"],
            "医学": ["生物", "药学", "公共卫生"],
            "新闻": ["媒体与传播", "艺术"],
            "影视": ["艺术", "媒体与传播"],
            "文化": ["艺术", "历史"],
            "媒体与传播": ["新闻", "影视", "新媒体"],
            "新媒体": ["媒体与传播", "计算机"],
            "媒介与社会": ["媒体与传播", "社会学与社工"],
            "科学传播": ["媒体与传播"],
            "策略传播": ["媒体与传播", "市场营销"],
            "媒体产业": ["媒体与传播", "管理"],
            "语言": ["教育"],
            "其他社科": [],

            # 工科类专业相关性
            "计算机": ["电气电子", "数学", "商业分析", "数据科学", "信息系统"],
            "电气电子": ["计算机", "机械工程"],
            "数据科学": ["计算机", "数学", "商业分析"],
            "机械工程": ["电气电子", "工业工程"],
            "材料": ["化学", "化工"],
            "化工": ["化学", "材料"],
            "生物工程": ["生物", "医学"],
            "土木工程": ["建筑"],
            "工程管理": ["管理", "工业工程"],
            "环境工程": ["化学", "地球科学"],
            "工业工程": ["机械工程", "管理", "工程管理"],
            "能源": ["化学", "物理"],
            "航空工程": ["机械工程", "物理"],
            "地球科学": ["物理", "化学", "环境工程"],
            "交通运输": ["机械工程"],
            "海洋技术": ["地球科学"],
            "食品科学": ["化学", "生物"],
            "其他工科": [],

            # 理科类专业相关性
            "物理": ["数学", "化学", "能源"],
            "化学": ["物理", "生物", "材料", "化工"],
            "数学": ["计算机", "物理", "商业分析", "数据科学", "金工金数"],
            "生物": ["化学", "医学", "生物工程"]
        }
        
        # 检查是否为相关专业
        if category2 in related_categories.get(category1, []):
            return 0.6

        return 0.1
