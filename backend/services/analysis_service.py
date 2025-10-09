import logging
from typing import List, Dict, Optional
import asyncio
import random
from backend.models.schemas import UserBackground, AnalysisReport, SchoolRecommendations, CompetitivenessAnalysis
from backend.services.similarity_matcher import SimilarityMatcher
from backend.services.gemini_service import GeminiService
from backend.services.radar_scoring_service import RadarScoringService
from backend.services.retry import async_retry_full_jitter


logger = logging.getLogger(__name__)

class AnalysisService:
    def __init__(self):
        self.similarity_matcher = SimilarityMatcher()
        self.gemini_service = GeminiService()
        self.radar_scoring_service = RadarScoringService()
        # allow tests to inject fake sleep/rng for retry without real waiting
        self._retry_sleep = None
        self._retry_rng = None
        
        logger.info("Initializing Analysis Service with Gemini API")
    

    
    async def generate_analysis_report(self, user_background: UserBackground) -> Optional[AnalysisReport]:
        """Generate complete analysis report for user with progress tracking"""
        try:
            logger.info("Starting analysis report generation")
            

            
            # Step 1: Find similar cases
            logger.info("Finding similar cases...")
            
            try:
                similar_cases = self.similarity_matcher.find_similar_cases(user_background, top_n=150)
            except Exception as e:
                logger.error(f"Failed to find similar cases: {str(e)}")
                raise Exception(f"数据库查询失败: {str(e)}")
            
            if not similar_cases:
                logger.warning("No similar cases found")
                # 继续生成报告，但使用空的相似案例与推荐
                similar_cases = []
            
            logger.info(f"Found {len(similar_cases)} similar cases")
            

            
            # Step 2: Call Gemini API for analysis
            logger.info("Calling Gemini API for analysis...")
            
            # Task 1: Competitiveness analysis
            logger.info("Analyzing competitiveness...")
            
            competitiveness = await async_retry_full_jitter(
                self.gemini_service.analyze_competitiveness,
                user_background,
                exceptions=(RuntimeError, TimeoutError),
                max_attempts=3,
                base=2,
                sleep=self._retry_sleep or asyncio.sleep,
                rng=self._retry_rng or random.random,
            )
            if not competitiveness:
                logger.error("Failed to get competitiveness analysis")
                raise Exception("无法获取竞争力分析，请检查网络连接")
            
            # Task 2: School recommendations
            logger.info("Generating school recommendations...")
            
            if similar_cases:
                school_recommendations = await async_retry_full_jitter(
                    self.gemini_service.generate_school_recommendations,
                    user_background,
                    similar_cases,
                    exceptions=(RuntimeError, TimeoutError),
                    max_attempts=3,
                    base=2,
                    sleep=self._retry_sleep or asyncio.sleep,
                    rng=self._retry_rng or random.random,
                )
                if not school_recommendations:
                    logger.error("Failed to get school recommendations")
                    raise Exception("无法获取学校推荐，请检查网络连接")
            else:
                # 无相似案例时返回空推荐与说明
                school_recommendations = SchoolRecommendations(recommendations=[], analysis_summary="未找到相似案例，返回空推荐列表")
            
            # Task 3: Case analyses (处理前10个案例)
            logger.info("Analyzing similar cases...")
            case_analyses = []
            partial_failures: Dict[str, str] = {}
            total_cases = min(10, len(similar_cases))
            
            for i, case in enumerate(similar_cases[:total_cases]):
                case_data = case.get('case_data', {})
                try:
                    result = await async_retry_full_jitter(
                        self.gemini_service.analyze_single_case,
                        user_background,
                        case_data,
                        exceptions=(RuntimeError, TimeoutError),
                        max_attempts=3,
                        base=2,
                        sleep=self._retry_sleep or asyncio.sleep,
                        rng=self._retry_rng or random.random,
                    )
                    if result:
                        case_analyses.append(result)
                        logger.info(f"Completed case analysis {i+1}")
                except Exception as e:
                    logger.warning(f"Case analysis {i+1} failed: {str(e)}")
                    # 记录部分失败，不因单个案例失败而中断
                    partial_failures[f"case_{i+1}"] = str(e)
                    continue
            
            # Step 4: Generate background improvement suggestions
            logger.info("Generating background improvement suggestions...")
            
            background_improvement = None
            if competitiveness and getattr(competitiveness, 'weaknesses', None):
                try:
                    background_improvement = await async_retry_full_jitter(
                        self.gemini_service.generate_background_improvement,
                        user_background,
                        competitiveness.weaknesses,
                        exceptions=(RuntimeError, TimeoutError),
                        max_attempts=3,
                        base=2,
                        sleep=self._retry_sleep or asyncio.sleep,
                        rng=self._retry_rng or random.random,
                    )
                except Exception as e:
                    logger.warning(f"Background improvement generation failed: {str(e)}")
                    # 背景改进建议失败不影响整体报告
                    partial_failures["background_improvement"] = str(e)
            
            # Step 5: Calculate radar scores
            logger.info("Calculating radar scores...")
            
            radar_scores = self.radar_scoring_service.calculate_radar_scores(user_background)
            logger.info(f"Radar scores calculated: {radar_scores}")
            
            # Step 6: Assemble final report
            degraded = True if partial_failures else False
            report = AnalysisReport(
                competitiveness=competitiveness,
                school_recommendations=school_recommendations,
                similar_cases=case_analyses,
                background_improvement=background_improvement,
                radar_scores=radar_scores,
                degraded=degraded if degraded else None,
                partial_failures=partial_failures or None
            )
            

            
            logger.info("Analysis report generation completed successfully")
            return report
            
        except Exception as e:
            logger.error(f"Error generating analysis report: {str(e)}")
            # 重新抛出异常，让上层处理
            raise e
    
    def get_case_details(self, case_ids: List[int]) -> List[Dict]:
        """Get detailed information for specific cases"""
        return self.similarity_matcher.get_case_details(case_ids)
    
    def refresh_similarity_data(self):
        """Refresh similarity matching data"""
        logger.info("Refreshing similarity matching data...")
        self.similarity_matcher._load_cases()
        logger.info("Similarity matching data refreshed")