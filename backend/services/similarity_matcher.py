import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple, Optional
import logging
from backend.models.schemas import UserBackground
from backend.services.university_scoring_service import UniversityScoringService
from backend.services.supabase_service import SupabaseService
from backend.services.major_classification_service import MajorClassificationService
from backend.services.major_taxonomy_service import major_taxonomy_service
from backend.config.settings import settings

logger = logging.getLogger(__name__)

class SimilarityMatcher:
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            analyzer='char_wb',
            ngram_range=(2, 4)
        )
        self.experience_vectors = None
        self.cases_df = None
        self.university_scoring_service = UniversityScoringService()
        self.supabase_service = SupabaseService()
        self.major_classification_service = MajorClassificationService()
        self._data_loaded = False
    
    def _load_cases(self):
        """Load and prepare cases for similarity matching"""
        try:
            logger.info("Loading cases from Supabase...")
            self._load_cases_from_supabase()
        except Exception as e:
            logger.error(f"Error loading cases: {str(e)}")
            raise Exception(f"数据库连接失败: {str(e)}")
    
    def _load_cases_from_supabase(self):
        """Load cases from Supabase"""
        try:
            cases = self.supabase_service.get_all_cases()

            # Convert to DataFrame for easier processing
            cases_data = []
            for case in cases:
                # Map new cases table fields to expected format
                undergraduate_category = self.major_classification_service.classify_major(
                    case.get('undergraduate_major', '')
                )
                undergraduate_category = (
                    major_taxonomy_service.normalise_direction(undergraduate_category)
                    or undergraduate_category
                )

                admitted_category = self.major_classification_service.classify_case_admitted_major(
                    case.get('admitted_major', '')
                )
                admitted_category = (
                    major_taxonomy_service.normalise_direction(admitted_category)
                    or admitted_category
                )

                cases_data.append({
                    'id': case.get('id', 0),
                    'original_id': case.get('case_id', 0),  # Use case_id as original_id
                    'gpa_4_scale': case.get('gpa_4_scale', 0.0) or 0.0,
                    'undergraduate_university_tier': self._get_university_tier(case.get('graduation_school', '')),
                    'undergraduate_major_category': undergraduate_category,
                    'admitted_major_category': admitted_category,
                    'language_total_score': self._get_language_score(case),
                    'language_test_type': self._get_language_type(case),
                    'gre_total': 0,  # Not available in new table
                    'gmat_total': 0,  # Not available in new table
                    'research_experience_count': self._count_research_experiences(case.get('experience_list', [])),
                    'internship_experience_count': self._count_internship_experiences(case.get('experience_list', [])),
                    'work_experience_years': case.get('work_experience_years', 0.0) or 0.0,
                    'experience_text': self._format_experience_text(case.get('experience_list', [])),
                    'admitted_university': case.get('admitted_school', '') or '',
                    'admitted_program': case.get('admitted_major', '') or '',
                    'admitted_country': self._extract_country(case.get('city', '')),
                    'admitted_degree_type': self._extract_degree_type(case.get('admitted_major', '')),
                    'undergraduate_university': case.get('graduation_school', '') or '',
                    'undergraduate_major': case.get('undergraduate_major', '') or '',
                    'is_recent_graduate': case.get('is_recent_graduate'),  # 添加应届生字段
                })

            self.cases_df = pd.DataFrame(cases_data)
            self._prepare_experience_vectors()

        except Exception as e:
            logger.error(f"Error loading cases from Supabase: {str(e)}")
            raise Exception(f"从Supabase加载案例失败: {str(e)}")
    
    def _prepare_experience_vectors(self):
        """Prepare experience text vectors for similarity calculation"""
        if len(self.cases_df) > 0:
            experience_texts = self.cases_df['experience_text'].fillna('').tolist()
            if any(text.strip() for text in experience_texts):
                self.experience_vectors = self.tfidf_vectorizer.fit_transform(experience_texts)
            else:
                self.experience_vectors = None
        
        logger.info(f"Loaded {len(self.cases_df)} cases for similarity matching")

    def _get_university_tier(self, university_name: str) -> str:
        """Get university tier using the university scoring service"""
        try:
            score, tier = self.university_scoring_service.get_university_score_and_tier(university_name)
            return tier
        except:
            return '未知'



    def _get_language_score(self, case: dict) -> int:
        """Extract language score from case data"""
        ielts = case.get('ielts')
        toefl = case.get('toefl')
        cet6 = case.get('cet6')

        if ielts:
            return int(ielts * 10)  # Convert IELTS to internal format
        elif toefl:
            return int(toefl)
        elif cet6:
            return int(cet6)
        else:
            return 0

    def _get_language_type(self, case: dict) -> str:
        """Extract language test type from case data"""
        if case.get('ielts'):
            return 'IELTS'
        elif case.get('toefl'):
            return 'TOEFL'
        elif case.get('cet6'):
            return 'CET6'
        else:
            return ''

    def _count_research_experiences(self, experience_list: list) -> int:
        """Count research experiences from experience list"""
        if not experience_list:
            return 0
        count = 0
        for exp in experience_list:
            exp_lower = str(exp).lower()
            if any(keyword in exp_lower for keyword in ['研究', 'research', '科研', '实验', 'lab', '项目', 'project']):
                count += 1
        return count

    def _count_internship_experiences(self, experience_list: list) -> int:
        """Count internship experiences from experience list"""
        if not experience_list:
            return 0
        count = 0
        for exp in experience_list:
            exp_lower = str(exp).lower()
            if any(keyword in exp_lower for keyword in ['实习', 'intern', '公司', 'company', '银行', 'bank', '证券', 'securities']):
                count += 1
        return count

    def _format_experience_text(self, experience_list: list) -> str:
        """Format experience list into text for similarity matching"""
        if not experience_list:
            return ''
        return ' '.join(str(exp) for exp in experience_list)

    def _extract_country(self, city: str) -> str:
        """Extract country from city field"""
        if not city:
            return '其他'

        city_str = str(city)
        if '香港' in city_str or 'Hong Kong' in city_str:
            return '中国香港'
        elif '澳门' in city_str or 'Macau' in city_str:
            return '中国澳门'
        elif '台湾' in city_str or 'Taiwan' in city_str:
            return '中国台湾'
        elif '美国' in city_str or 'USA' in city_str or 'United States' in city_str:
            return '美国'
        elif '英国' in city_str or 'UK' in city_str or 'United Kingdom' in city_str:
            return '英国'
        elif '加拿大' in city_str or 'Canada' in city_str:
            return '加拿大'
        elif '澳大利亚' in city_str or 'Australia' in city_str:
            return '澳大利亚'
        elif '新加坡' in city_str or 'Singapore' in city_str:
            return '新加坡'
        else:
            return '其他'

    def _extract_degree_type(self, major: str) -> str:
        """Extract degree type from major field"""
        if not major:
            return 'Master'  # Default to Master

        major_lower = str(major).lower()
        if '硕士' in major_lower or 'master' in major_lower:
            return 'Master'
        elif '博士' in major_lower or 'phd' in major_lower or 'doctor' in major_lower:
            return 'PhD'
        elif '学士' in major_lower or 'bachelor' in major_lower:
            return 'Bachelor'
        else:
            return 'Master'  # Default to Master
    
    def _calculate_gpa_similarity(self, user_gpa: float, case_gpa: float) -> float:
        """Calculate GPA similarity score (0-1) with stricter penalties for large gaps"""
        if user_gpa == 0 or case_gpa == 0:
            return 0.5  # Neutral score if either GPA is missing

        # Calculate the absolute difference
        diff = abs(user_gpa - case_gpa)

        # 更严格的GPA相似度计算
        if diff <= 0.2:  # 差距很小
            return 1.0
        elif diff <= 0.5:  # 小差距
            return 0.8
        elif diff <= 1.0:  # 中等差距
            return 0.6
        elif diff <= 1.5:  # 较大差距
            return 0.3
        elif diff <= 2.0:  # 很大差距
            return 0.1
        else:  # 巨大差距
            return 0.02
    
    def _calculate_university_tier_similarity(self, user_tier: str, case_tier: str) -> float:
        """Calculate university tier similarity score (0-1) with stricter tier penalties for lower tiers"""
        # 新的层级体系
        tier_hierarchy = {
            'Tier 0': 5,
            'Tier 1': 4,
            'Tier 2': 3,
            'Tier 3': 2,
            'Tier 4': 1
        }

        user_level = tier_hierarchy.get(user_tier, 1)
        case_level = tier_hierarchy.get(case_tier, 1)

        # Same tier gets full score
        if user_level == case_level:
            return 1.0

        # 对于 Tier 3 和 Tier 4 用户，只允许同层级匹配
        if user_tier in ["Tier 3", "Tier 4"]:
            return 0.0  # 不同层级直接返回0

        # 对于 Tier 0-2 用户，允许相邻层级匹配
        diff = abs(user_level - case_level)
        if diff == 1:
            # 相邻层级：根据层级高低给不同分数
            higher_level = max(user_level, case_level)
            if higher_level >= 4:  # 涉及Tier 0-1
                return 0.3  # 顶尖院校之间稍微宽松
            elif higher_level >= 3:  # 涉及Tier 1-2
                return 0.2
            else:
                return 0.1
        else:
            # 差距超过1层：完全不匹配
            return 0.0
    
    def _calculate_major_similarity(self, user_undergraduate_major: str, user_target_majors: List[str],
                                  case_undergraduate_major: str, case_admitted_major: str) -> Dict[str, float]:
        """
        计算双重专业相似度：本科专业匹配 + 目标专业匹配

        Args:
            user_undergraduate_major: 用户本科专业
            user_target_majors: 用户目标专业列表（现在只包含一个专业）
            case_undergraduate_major: 案例本科专业大类
            case_admitted_major: 案例录取专业大类

        Returns:
            包含本科专业相似度和目标专业相似度的字典
        """
        # 1. 本科专业匹配：用户本科专业 vs 案例本科专业
        user_undergraduate_category = self.major_classification_service.classify_major(user_undergraduate_major)
        undergraduate_similarity = self.major_classification_service.get_major_similarity(
            user_undergraduate_category, case_undergraduate_major
        )

        # 2. 目标专业匹配：用户目标专业 vs 案例录取专业
        target_similarity = 0.0
        if user_target_majors and len(user_target_majors) > 0:
            # 用户现在只能选择一个目标专业，直接使用该专业作为大类
            user_target_major = major_taxonomy_service.normalise_direction(user_target_majors[0]) or user_target_majors[0]

            case_major = major_taxonomy_service.normalise_direction(case_admitted_major) or case_admitted_major

            # 直接使用目标专业名称作为专业大类，不需要再次分类
            target_similarity = self.major_classification_service.get_major_similarity(
                user_target_major, case_major
            )

        return {
            'undergraduate_similarity': undergraduate_similarity,
            'target_similarity': target_similarity
        }
    
    def _calculate_language_similarity(self, user_score: int, case_score: int, 
                                     user_type: str, case_type: str) -> float:
        """Calculate language test similarity score (0-1)"""
        if user_score == 0 or case_score == 0:
            return 0.5  # Neutral score if either score is missing
        
        # Convert IELTS to TOEFL equivalent for comparison
        if user_type == 'IELTS' and case_type == 'TOEFL':
            user_score = user_score * 10  # Convert back from our internal representation
        elif user_type == 'TOEFL' and case_type == 'IELTS':
            case_score = case_score * 10  # Convert back from our internal representation
        elif user_type != case_type:
            return 0.3  # Different test types get lower similarity
        
        # Calculate similarity based on score difference
        max_score = 120 if 'TOEFL' in [user_type, case_type] else 90
        diff = abs(user_score - case_score)
        similarity = max(0, 1 - (diff / max_score))
        return similarity
    
    def _calculate_experience_similarity(self, user_background: UserBackground, 
                                       case_idx: int) -> float:
        """Calculate experience similarity score (0-1)"""
        if self.experience_vectors is None or case_idx >= len(self.cases_df):
            return 0.5
        
        # Prepare user experience text
        user_experience_parts = []
        
        for exp in user_background.research_experiences or []:
            user_experience_parts.append(f"{exp.get('name', '')} {exp.get('description', '')}")
        
        for exp in user_background.internship_experiences or []:
            user_experience_parts.append(f"{exp.get('company', '')} {exp.get('position', '')} {exp.get('description', '')}")
        
        for exp in user_background.other_experiences or []:
            user_experience_parts.append(f"{exp.get('name', '')} {exp.get('description', '')}")
        
        user_experience_text = ' '.join(user_experience_parts)
        
        if not user_experience_text.strip():
            return 0.5
        
        # Calculate text similarity
        try:
            user_vector = self.tfidf_vectorizer.transform([user_experience_text])
            case_vector = self.experience_vectors[case_idx:case_idx+1]
            similarity = cosine_similarity(user_vector, case_vector)[0][0]
            return max(0, similarity)
        except Exception as e:
            logger.warning(f"Error calculating experience similarity: {str(e)}")
            return 0.5
    
    def find_similar_cases(self, user_background: UserBackground, top_n: int = 150) -> List[Dict]:
        """Find the most similar cases to the user's background"""
        # Lazy load data on first use
        if not self._data_loaded:
            logger.info("Loading cases data for first time...")
            self._load_cases()
            self._data_loaded = True
        
        if self.cases_df is None or self.cases_df.empty:
            logger.error("No cases available for similarity matching")
            raise Exception("暂无案例，稍后重试")
        
        # Pre-filter cases based on target countries, degree type, target majors, and graduate status
        filtered_df = self.cases_df.copy()

        if user_background.target_countries:
            filtered_df = filtered_df[
                filtered_df['admitted_country'].isin(user_background.target_countries)
            ]

        if user_background.target_degree_type:
            filtered_df = filtered_df[
                filtered_df['admitted_degree_type'] == user_background.target_degree_type
            ]

        # 强限制：目标专业必须完全匹配
        if user_background.target_majors and len(user_background.target_majors) > 0:
            # 用户现在只能选择一个目标专业，直接使用该专业作为大类
            target_major_raw = user_background.target_majors[0]
            user_target_major = major_taxonomy_service.normalise_direction(target_major_raw) or target_major_raw

            # 强限制：只保留录取专业大类与用户目标专业大类完全匹配的案例
            filtered_df = filtered_df[
                filtered_df['admitted_major_category'] == user_target_major
            ]
            logger.info(
                "Applied strict target major filter: %s (raw: %s), remaining cases: %s",
                user_target_major,
                target_major_raw,
                len(filtered_df)
            )

        # 强限制：应届生状态必须完全匹配
        user_is_recent_graduate = user_background.is_recent_graduate()
        if user_is_recent_graduate is not None:
            # 强限制：只保留相同应届生状态的案例
            filtered_df = filtered_df[
                filtered_df['is_recent_graduate'] == user_is_recent_graduate
            ]
            logger.info(f"Applied strict graduate status filter: {'recent' if user_is_recent_graduate else 'non-recent'}, remaining cases: {len(filtered_df)}")

        if filtered_df.empty:
            logger.warning("No cases match the strict filtering criteria")
            # 不再回退到所有案例，因为目标专业和应届生状态是强限制条件
            # 直接返回空结果
            return []
        
        # Calculate similarity scores for each case
        similarities = []

        # Determine user's university tier
        user_tier = self._get_user_university_tier(user_background.undergraduate_university)

        # Convert user GPA to 4.0 scale
        user_gpa_4_scale = self._convert_gpa_to_4_scale(
            user_background.gpa, user_background.gpa_scale
        )

        # 添加预筛选：过滤掉层级差距过大的案例
        tier_hierarchy = {
            'Tier 0': 5, 'Tier 1': 4, 'Tier 2': 3, 'Tier 3': 2, 'Tier 4': 1
        }
        user_level = tier_hierarchy.get(user_tier, 1)

        # 进一步过滤：根据用户层级实施不同的匹配策略
        def is_tier_acceptable(case_tier):
            case_level = tier_hierarchy.get(case_tier, 1)

            # 完全相同层级总是可接受
            if user_level == case_level:
                return True

            # 对于 Tier 4 用户（普通院校），只允许同层级匹配
            # 避免与 211/985 等更高层级院校混淆
            if user_tier == "Tier 4":
                return False

            # 对于 Tier 3 用户（良好院校），只允许同层级匹配
            # 避免与 Tier 1-2 的顶尖院校混淆
            if user_tier == "Tier 3":
                return False

            # 对于 Tier 0-2 用户（顶尖和优秀院校），允许相邻层级匹配
            # 因为这些层级之间的差距相对较小
            diff = abs(user_level - case_level)
            return diff <= 1

        filtered_df = filtered_df[
            filtered_df['undergraduate_university_tier'].apply(is_tier_acceptable)
        ]

        if filtered_df.empty:
            logger.warning(f"No cases match the strict tier filtering criteria for {user_tier}")
            # 对于低层级院校，即使没有匹配案例也不放宽限制
            # 这样可以避免不合适的匹配
            if user_tier in ["Tier 3", "Tier 4"]:
                logger.info(f"Maintaining strict tier filtering for {user_tier} - no relaxation")
                # 返回空结果，因为目标专业和应届生状态是强限制条件
                return []
            else:
                logger.info(f"Relaxing tier constraints for {user_tier}")
                # 对于高层级院校，可以适当放宽学校层级限制，但仍保持目标专业和应届生状态的强限制
                filtered_df = self.cases_df.copy()
                if user_background.target_countries:
                    filtered_df = filtered_df[
                        filtered_df['admitted_country'].isin(user_background.target_countries)
                    ]
                if user_background.target_degree_type:
                    filtered_df = filtered_df[
                        filtered_df['admitted_degree_type'] == user_background.target_degree_type
                    ]

                # 重新应用目标专业和应届生状态的强限制
                if user_background.target_majors and len(user_background.target_majors) > 0:
                    target_major_raw = user_background.target_majors[0]
                    user_target_major = major_taxonomy_service.normalise_direction(target_major_raw) or target_major_raw
                    filtered_df = filtered_df[
                        filtered_df['admitted_major_category'] == user_target_major
                    ]
                    logger.info(
                        "Filtered fallback cases by target major: %s (raw: %s), remaining cases: %s",
                        user_target_major,
                        target_major_raw,
                        len(filtered_df)
                    )

                user_is_recent_graduate = user_background.is_recent_graduate()
                if user_is_recent_graduate is not None:
                    filtered_df = filtered_df[
                        filtered_df['is_recent_graduate'] == user_is_recent_graduate
                    ]

                # 如果重新应用强限制后仍然没有案例，返回空结果
                if filtered_df.empty:
                    logger.info("No cases match after re-applying strict constraints")
                    return []
        
        for idx, case in filtered_df.iterrows():
            # Calculate individual similarity components
            gpa_sim = self._calculate_gpa_similarity(user_gpa_4_scale, case['gpa_4_scale'])
            tier_sim = self._calculate_university_tier_similarity(user_tier, case['undergraduate_university_tier'])

            # 计算本科专业相似度（目标专业已经通过强限制筛选）
            user_undergraduate_category = self.major_classification_service.classify_major(user_background.undergraduate_major)
            undergraduate_major_sim = self.major_classification_service.get_major_similarity(
                user_undergraduate_category, case['undergraduate_major_category']
            )
            
            # Language similarity
            lang_sim = 0.5  # Default neutral score
            if user_background.language_total_score and case['language_total_score']:
                lang_sim = self._calculate_language_similarity(
                    user_background.language_total_score,
                    case['language_total_score'],
                    user_background.language_test_type or '',
                    case['language_test_type']
                )
            
            # Experience similarity
            exp_sim = self._calculate_experience_similarity(user_background, idx)

            # 应届生状态已经通过强限制筛选，不需要再计算相似度

            # 新的权重分配：目标专业和应届生状态已经是强限制，不再参与权重计算
            weights = {
                'undergraduate_major': 0.15,  # 本科专业匹配
                'gpa': 0.35,                  # 学术表现 (提高权重)
                'tier': 0.35,                 # 学校声誉 (提高权重)
                'language': 0.075,            # 语言能力 (提高权重)
                'experience': 0.075,          # 经历背景 (提高权重)
            }

            total_similarity = (
                weights['undergraduate_major'] * undergraduate_major_sim +
                weights['gpa'] * gpa_sim +
                weights['tier'] * tier_sim +
                weights['language'] * lang_sim +
                weights['experience'] * exp_sim
            )
            
            # 只保留相似度超过最低阈值的案例
            min_similarity_threshold = 0.3  # 最低相似度阈值
            if total_similarity >= min_similarity_threshold:
                similarities.append({
                    'case_id': case['id'],
                    'original_id': case['original_id'],
                    'similarity_score': total_similarity,
                    'component_scores': {
                        'undergraduate_major': undergraduate_major_sim,
                        'gpa': gpa_sim,
                        'tier': tier_sim,
                        'language': lang_sim,
                        'experience': exp_sim,
                        # 目标专业和应届生状态现在是强限制，不再记录相似度分数
                        'target_major_matched': True,  # 强限制确保匹配
                        'graduate_status_matched': True  # 强限制确保匹配
                    },
                    'case_data': case.to_dict()
                })

        # Sort by similarity score and return top N
        similarities.sort(key=lambda x: x['similarity_score'], reverse=True)

        # 如果符合条件的案例太少，适当降低阈值
        if len(similarities) < 10:
            logger.info(f"Only {len(similarities)} cases meet the strict criteria, relaxing threshold")
            similarities = []
            min_similarity_threshold = 0.2  # 降低阈值

            for idx, case in filtered_df.iterrows():
                # 重新计算相似度（代码重复，但为了清晰）
                gpa_sim = self._calculate_gpa_similarity(user_gpa_4_scale, case['gpa_4_scale'])
                tier_sim = self._calculate_university_tier_similarity(user_tier, case['undergraduate_university_tier'])

                # 计算本科专业相似度（目标专业已经通过强限制筛选）
                user_undergraduate_category = self.major_classification_service.classify_major(user_background.undergraduate_major)
                undergraduate_major_sim = self.major_classification_service.get_major_similarity(
                    user_undergraduate_category, case['undergraduate_major_category']
                )

                lang_sim = 0.5
                if user_background.language_total_score and case['language_total_score']:
                    lang_sim = self._calculate_language_similarity(
                        user_background.language_total_score,
                        case['language_total_score'],
                        user_background.language_test_type or '',
                        case['language_test_type']
                    )

                exp_sim = self._calculate_experience_similarity(user_background, idx)

                # 应届生状态已经通过强限制筛选，不需要再计算相似度

                total_similarity = (
                    weights['undergraduate_major'] * undergraduate_major_sim +
                    weights['gpa'] * gpa_sim +
                    weights['tier'] * tier_sim +
                    weights['language'] * lang_sim +
                    weights['experience'] * exp_sim
                )

                if total_similarity >= min_similarity_threshold:
                    similarities.append({
                        'case_id': case['id'],
                        'original_id': case['original_id'],
                        'similarity_score': total_similarity,
                        'component_scores': {
                            'undergraduate_major': undergraduate_major_sim,
                            'gpa': gpa_sim,
                            'tier': tier_sim,
                            'language': lang_sim,
                            'experience': exp_sim,
                            # 目标专业和应届生状态现在是强限制，不再记录相似度分数
                            'target_major_matched': True,  # 强限制确保匹配
                            'graduate_status_matched': True  # 强限制确保匹配
                        },
                        'case_data': case.to_dict()
                    })

            similarities.sort(key=lambda x: x['similarity_score'], reverse=True)

        return similarities[:top_n]
    
    def _get_user_university_tier(self, university_name: str) -> str:
        """Get user's university tier using new scoring service"""
        _, tier = self.university_scoring_service.get_university_score_and_tier(university_name)
        return tier

    def _calculate_graduate_status_similarity(self, user_is_recent_graduate: Optional[bool], case_is_recent_graduate: Optional[bool]) -> float:
        """计算应届生状态相似度"""
        if user_is_recent_graduate is None or case_is_recent_graduate is None:
            return 0.5  # 如果任一方状态未知，给予中等分数

        if user_is_recent_graduate == case_is_recent_graduate:
            return 1.0  # 状态相同，完全匹配
        else:
            return 0.2  # 状态不同，给予较低分数
    

    
    def _convert_gpa_to_4_scale(self, gpa: float, scale: str) -> float:
        """Convert GPA to 4.0 scale"""
        if scale == "100":
            # Convert 100-point scale to 4.0 scale
            if gpa >= 90:
                return 4.0
            elif gpa >= 85:
                return 3.7
            elif gpa >= 82:
                return 3.3
            elif gpa >= 78:
                return 3.0
            elif gpa >= 75:
                return 2.7
            elif gpa >= 72:
                return 2.3
            elif gpa >= 68:
                return 2.0
            elif gpa >= 64:
                return 1.7
            elif gpa >= 60:
                return 1.0
            else:
                return 0.0
        elif scale == "5.0":
            # Convert 5.0-point scale to 4.0 scale
            return min(gpa * 4.0 / 5.0, 4.0)
        else:
            return min(gpa, 4.0)
    
    def get_case_details(self, case_ids: List[int]) -> List[Dict]:
        """Get detailed information for specific cases"""
        # Lazy load data if needed
        if not self._data_loaded:
            self._load_cases()
            self._data_loaded = True
            
        if self.cases_df is None or self.cases_df.empty:
            return []
        
        detailed_cases = []
        for case_id in case_ids:
            case_row = self.cases_df[self.cases_df['id'] == case_id]
            if not case_row.empty:
                case_data = case_row.iloc[0].to_dict()
                detailed_cases.append(case_data)
        
        return detailed_cases
