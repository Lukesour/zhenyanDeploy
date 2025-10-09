import pandas as pd
from typing import List, Dict, Optional
import logging
from supabase import create_client, Client
from backend.config.settings import settings

logger = logging.getLogger(__name__)

class SupabaseService:
    def __init__(self):
        self.table_name = settings.SUPABASE_TABLE
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client"""
        try:
            if not settings.use_supabase:
                logger.info("Supabase not configured. Using in-memory fallback for cases.")
                self.client = None
                return
            
            self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            self.client = None
            logger.warning("Continuing without Supabase connection.")
    
    def get_all_cases(self) -> List[Dict]:
        """Get all processed cases from Supabase with pagination support"""
        if not self.client:
            logger.warning("Supabase client not initialized, returning empty case list.")
            return []
        
        try:
            all_cases = []
            page_size = 1000  # Supabase默认限制
            offset = 0
            
            while True:
                # 使用分页查询
                response = self.client.table(self.table_name).select("*").range(offset, offset + page_size - 1).execute()
                
                if hasattr(response, 'data'):
                    cases = response.data
                else:
                    # Fallback for older supabase-py versions
                    cases = response['data'] if isinstance(response, dict) else []
                
                if not cases:
                    break
                
                all_cases.extend(cases)
                offset += page_size
                
                # 如果返回的记录数少于page_size，说明已经到最后一页
                if len(cases) < page_size:
                    break
                
                logger.info(f"Retrieved {len(cases)} cases (offset: {offset - page_size})")
            
            logger.info(f"Retrieved total {len(all_cases)} cases from Supabase")
            return all_cases
            
        except Exception as e:
            logger.error(f"Error fetching cases from Supabase: {str(e)}")
            raise Exception(f"从Supabase获取案例失败: {str(e)}")
    
    def get_cases_by_filters(self, filters: Dict) -> List[Dict]:
        """Get cases with specific filters with pagination support"""
        if not self.client:
            logger.warning("Supabase client not initialized, returning empty filtered list.")
            return []
        
        try:
            query = self.client.table(self.table_name).select("*")
            
            # Apply filters
            for key, value in filters.items():
                if value is not None and value != "":
                    if isinstance(value, list):
                        query = query.in_(key, value)
                    else:
                        query = query.eq(key, value)
            
            # 使用分页查询获取所有匹配的记录
            all_cases = []
            page_size = 1000
            offset = 0
            
            while True:
                page_query = query.range(offset, offset + page_size - 1)
                response = page_query.execute()
                
                if hasattr(response, 'data'):
                    cases = response.data
                else:
                    cases = response['data'] if isinstance(response, dict) else []
                
                if not cases:
                    break
                
                all_cases.extend(cases)
                offset += page_size
                
                # 如果返回的记录数少于page_size，说明已经到最后一页
                if len(cases) < page_size:
                    break
                
                logger.info(f"Retrieved {len(cases)} filtered cases (offset: {offset - page_size})")
            
            logger.info(f"Retrieved total {len(all_cases)} filtered cases from Supabase")
            return all_cases
            
        except Exception as e:
            logger.error(f"Error fetching filtered cases from Supabase: {str(e)}")
            raise Exception(f"从Supabase获取筛选案例失败: {str(e)}")
    
    def get_case_by_id(self, case_id: int) -> Optional[Dict]:
        """Get a specific case by ID"""
        if not self.client:
            logger.warning("Supabase client not initialized, cannot fetch case.")
            return None
        
        try:
            response = self.client.table(self.table_name).select("*").eq("id", case_id).execute()
            
            if hasattr(response, 'data'):
                cases = response.data
            else:
                cases = response['data'] if isinstance(response, dict) else []
            
            return cases[0] if cases else None
            
        except Exception as e:
            logger.error(f"Error fetching case {case_id} from Supabase: {str(e)}")
            return None
    
    def get_cases_by_ids(self, case_ids: List[int]) -> List[Dict]:
        """Get multiple cases by IDs"""
        if not self.client:
            logger.warning("Supabase client not initialized, returning empty case list.")
            return []
        
        try:
            response = self.client.table(self.table_name).select("*").in_("id", case_ids).execute()
            
            if hasattr(response, 'data'):
                cases = response.data
            else:
                cases = response['data'] if isinstance(response, dict) else []
            
            return cases
            
        except Exception as e:
            logger.error(f"Error fetching cases by IDs from Supabase: {str(e)}")
            return []
    
    def test_connection(self) -> bool:
        """Test Supabase connection"""
        try:
            if not self.client:
                return False
            
            # Try to fetch a single record to test connection
            response = self.client.table(self.table_name).select("id").limit(1).execute()
            return True
            
        except Exception as e:
            logger.error(f"Supabase connection test failed: {str(e)}")
            return False
