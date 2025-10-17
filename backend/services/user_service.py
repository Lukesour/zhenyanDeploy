import logging
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from supabase import create_client, Client
from backend.config.settings import settings
from backend.models.user_models import (
    User, UserInfo, UserProfile, UserProfileData, EmailVerificationCode, InvitationCode, UserAnalysisRecord,
    UserStatus, InvitationStatus, ALL_CREATE_STATEMENTS
)
from backend.services.email_service import EmailService
from backend.services.email_verification_service import email_verification_service
from backend.services.major_taxonomy_service import major_taxonomy_service

logger = logging.getLogger(__name__)

# 内存缓存用于存储验证码（当数据库表不存在时）
verification_code_cache = {}

class UserService:

    def _create_local_user(self, phone: str, email: str, invitation_code: Optional[str], profile_data: Optional[UserProfileData]) -> UserInfo:
        for user in self._local_users.values():
            if user['phone'] == phone:
                raise Exception('该手机号已注册')
            if user['email'] == email:
                raise Exception('该邮箱已注册，请使用其他邮箱')

        initial_analyses = 9 if invitation_code else 6
        created_at = datetime.utcnow()
        user_id = self._local_next_user_id
        self._local_next_user_id += 1

        user_invitation_code = self.generate_invitation_code()
        record = {
            'id': user_id,
            'phone': phone,
            'email': email,
            'status': 'active',
            'remaining_analyses': initial_analyses,
            'total_analyses_used': 0,
            'invitation_code': user_invitation_code,
            'invited_by_code': invitation_code,
            'invited_count': 0,
            'email_verified': True,
            'created_at': created_at,
            'last_login_at': created_at
        }
        self._local_users[user_id] = record
        if profile_data:
            self._local_profiles[user_id] = profile_data

        try:
            self.email_service.send_welcome_email(email, phone, 3)
        except Exception as email_error:
            logger.warning(f"发送欢迎邮件失败: {email_error}")

        return UserInfo(
            id=user_id,
            phone=phone,
            email=email,
            status=UserStatus.ACTIVE,
            remaining_analyses=initial_analyses,
            total_analyses_used=0,
            invitation_code=user_invitation_code,
            invited_count=0,
            created_at=created_at,
            last_login_at=created_at,
            profile_data=profile_data
        )

    """用户服务类"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self._email_service: Optional[EmailService] = None
        self.use_local_store: bool = False
        self._local_users: Dict[int, Dict[str, Any]] = {}
        self._local_profiles: Dict[int, UserProfileData] = {}
        self._local_next_user_id: int = 1
        self._initialize_client()
        if not self.use_local_store:
            self._ensure_tables_exist()

    @property
    def email_service(self) -> EmailService:
        """懒加载邮件服务"""
        if self._email_service is None:
            self._email_service = EmailService()
        return self._email_service
    
    def _initialize_client(self):
        """初始化Supabase客户端"""
        try:
            if not settings.use_supabase:
                self.use_local_store = True
                self.client = None
                logger.info("Supabase not configured. Using in-memory user store.")
                return
            
            self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            self.use_local_store = False
            logger.info("User service Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize user service Supabase client: {str(e)}")
            self.use_local_store = True
            self.client = None
            logger.warning("Falling back to in-memory user store due to Supabase initialization failure.")
    
    def _ensure_tables_exist(self):
        """确保用户相关表存在"""
        try:
            if not self.client:
                return
            
            # 注意：Supabase不支持直接执行DDL语句
            # 这些表需要在Supabase控制台中手动创建
            # 这里只是记录需要创建的表结构
            logger.info("用户表结构检查完成（需要在Supabase控制台中手动创建表）")
            
        except Exception as e:
            logger.error(f"检查用户表结构失败: {str(e)}")
    
    def generate_invitation_code(self, length: int = 8) -> str:
        """生成邀请码"""
        # 使用大写字母和数字，避免容易混淆的字符
        chars = string.ascii_uppercase + string.digits
        chars = chars.replace('0', '').replace('O', '').replace('I', '').replace('1', '')
        return ''.join(secrets.choice(chars) for _ in range(length))
    
    def generate_jwt_token(self, user_id: int) -> Dict[str, Any]:
        """生成JWT令牌"""
        try:
            payload = {
                'user_id': user_id,
                'exp': datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRE_HOURS),
                'iat': datetime.utcnow()
            }
            
            token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
            
            return {
                'access_token': token,
                'token_type': 'bearer',
                'expires_in': settings.JWT_EXPIRE_HOURS * 3600
            }
        except Exception as e:
            logger.error(f"生成JWT令牌失败: {str(e)}")
            raise Exception("令牌生成失败")
    
    def verify_jwt_token(self, token: str) -> Optional[int]:
        """验证JWT令牌并返回用户ID"""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            return payload.get('user_id')
        except jwt.ExpiredSignatureError:
            logger.warning("JWT令牌已过期")
            return None
        except jwt.InvalidTokenError:
            logger.warning("无效的JWT令牌")
            return None
    
    async def send_verification_code(self, email: str, phone: str) -> bool:
        """发送邮箱验证码"""
        try:
            # 简单的邮箱格式验证
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                raise Exception("邮箱格式不正确，请输入有效的邮箱地址")

            logger.info(f"邮箱格式验证通过: {email}")

            if self.use_local_store:
                for user in self._local_users.values():
                    if user['phone'] == phone:
                        raise Exception("该手机号已注册，请直接登录")
                    if user['email'] == email:
                        raise Exception("该邮箱已注册，请使用其他邮箱")

                verification_code = self.email_service.generate_verification_code()
                expires_at = datetime.utcnow() + timedelta(minutes=10)
                cache_key = f"{email}:{phone}"
                verification_code_cache[cache_key] = {
                    'code': verification_code,
                    'expires_at': expires_at,
                    'used': False,
                    'created_at': datetime.utcnow()
                }

                success = self.email_service.send_verification_email(email, verification_code)
                if not success:
                    raise Exception("邮件发送失败，请稍后重试")

                logger.info(f"验证码已发送到邮箱: {email}")
                return True

            if not self.client:
                raise Exception("数据库连接未初始化")

            try:
                existing_user = self.client.table('users').select('id').eq('phone', phone).execute()
                if existing_user.data:
                    raise Exception("该手机号已注册，请直接登录")
            except Exception as db_error:
                logger.warning(f"用户表检查失败，继续执行: {str(db_error)}")

            # 尝试检查邮箱是否已注册（如果表存在）
            try:
                existing_email = self.client.table('users').select('id').eq('email', email).execute()
                if existing_email.data:
                    raise Exception("该邮箱已注册，请使用其他邮箱")
            except Exception as db_error:
                logger.warning(f"邮箱表检查失败，继续执行: {str(db_error)}")
            
            # 生成验证码
            verification_code = self.email_service.generate_verification_code()
            
            # 尝试保存验证码到数据库（如果表存在）
            expires_at = datetime.utcnow() + timedelta(minutes=10)
            verification_data = {
                'email': email,
                'phone': phone,
                'code': verification_code,
                'expires_at': expires_at.isoformat(),
                'used': False
            }

            try:
                self.client.table('email_verification_codes').insert(verification_data).execute()
                logger.info(f"验证码已保存到数据库: {email}")
            except Exception as db_error:
                logger.warning(f"验证码保存到数据库失败，使用内存缓存: {str(db_error)}")
                # 保存到内存缓存
                cache_key = f"{email}:{phone}"
                verification_code_cache[cache_key] = {
                    'code': verification_code,
                    'expires_at': expires_at,
                    'used': False,
                    'created_at': datetime.utcnow()
                }
                logger.info(f"验证码已保存到内存缓存: {email}")
            
            # 发送邮件
            success = self.email_service.send_verification_email(email, verification_code)
            
            if not success:
                raise Exception("邮件发送失败，请稍后重试")
            
            logger.info(f"验证码已发送到邮箱: {email}")
            return True
            
        except Exception as e:
            logger.error(f"发送验证码失败: {str(e)}")
            raise Exception(str(e))
    
    async def verify_email_code(self, email: str, phone: str, code: str) -> bool:
        """验证邮箱验证码"""
        try:
            # 首先尝试从数据库验证
            if self.client:
                try:
                    result = self.client.table('email_verification_codes')\
                        .select('*')\
                        .eq('email', email)\
                        .eq('phone', phone)\
                        .eq('code', code)\
                        .eq('used', False)\
                        .order('created_at', desc=True)\
                        .limit(1)\
                        .execute()

                    if result.data:
                        verification_record = result.data[0]

                        # 检查是否过期
                        expires_at = datetime.fromisoformat(verification_record['expires_at'].replace('Z', '+00:00'))
                        if datetime.utcnow().replace(tzinfo=expires_at.tzinfo) > expires_at:
                            raise Exception("验证码已过期，请重新获取")

                        # 标记验证码为已使用
                        self.client.table('email_verification_codes')\
                            .update({'used': True, 'used_at': datetime.utcnow().isoformat()})\
                            .eq('id', verification_record['id'])\
                            .execute()

                        logger.info(f"数据库验证码验证成功: {email}")
                        return True

                except Exception as db_error:
                    logger.warning(f"数据库验证码验证失败，尝试内存缓存: {str(db_error)}")

            # 从内存缓存验证
            cache_key = f"{email}:{phone}"
            if cache_key in verification_code_cache:
                cached_data = verification_code_cache[cache_key]

                # 检查验证码是否匹配
                if cached_data['code'] != code:
                    raise Exception("验证码错误")

                # 检查是否已使用
                if cached_data['used']:
                    raise Exception("验证码已使用")

                # 检查是否过期
                if datetime.utcnow() > cached_data['expires_at']:
                    raise Exception("验证码已过期，请重新获取")

                # 标记为已使用
                cached_data['used'] = True
                cached_data['used_at'] = datetime.utcnow()

                logger.info(f"内存缓存验证码验证成功: {email}")
                return True

            # 都没找到验证码
            raise Exception("验证码错误或已失效")

        except Exception as e:
            logger.error(f"验证邮箱验证码失败: {str(e)}")
            raise Exception(str(e))
    
    async def register_user(self, phone: str, email: str, verification_code: str, invitation_code: Optional[str] = None, profile_data: Optional[UserProfileData] = None) -> UserInfo:
        """用户注册"""
        try:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                raise Exception("邮箱格式不正确，请输入有效的邮箱地址")

            logger.info(f"用户注册邮箱格式验证通过: {email}")

            await self.verify_email_code(email, phone, verification_code)

            if self.use_local_store or not self.client:
                return self._create_local_user(phone, email, invitation_code, profile_data)

            try:
                existing_user = self.client.table('users').select('id').eq('phone', phone).execute()
                if existing_user.data:
                    raise Exception("该手机号已注册")
            except Exception as db_error:
                logger.warning(f"用户表检查失败，继续执行: {db_error}")
            
            # 处理邀请码（如果表存在）
            invited_by_code = None
            user_invitation_code = self.generate_invitation_code()

            try:
                if invitation_code:
                    # 验证邀请码
                    invite_result = self.client.table('invitation_codes')\
                        .select('*')\
                        .eq('code', invitation_code)\
                        .eq('status', 'active')\
                        .execute()

                    if not invite_result.data:
                        raise Exception("邀请码无效或已失效")

                    invited_by_code = invitation_code

                # 生成用户自己的邀请码并确保唯一
                while True:
                    existing_code = self.client.table('users').select('id').eq('invitation_code', user_invitation_code).execute()
                    if not existing_code.data:
                        break
                    user_invitation_code = self.generate_invitation_code()

            except Exception as db_error:
                logger.warning(f"邀请码处理失败，使用默认值: {str(db_error)}")
                # 使用默认邀请码
                user_invitation_code = self.generate_invitation_code()
            
            # 创建用户（如果表存在）
            # 如果使用了有效邀请码，新用户获得5次额外分析机会（总共8次）
            initial_analyses = 5 if invited_by_code else 3

            user_data = {
                'phone': phone,
                'email': email,
                'status': 'active',
                'remaining_analyses': initial_analyses,
                'total_analyses_used': 0,
                'invitation_code': user_invitation_code,
                'invited_by_code': invited_by_code,
                'invited_count': 0,
                'email_verified': True,
                'last_login_at': datetime.utcnow().isoformat()
            }

            new_user = None
            try:
                user_result = self.client.table('users').insert(user_data).execute()

                if not user_result.data:
                    raise Exception("用户创建失败")

                new_user = user_result.data[0]

                # 创建用户的邀请码记录
                invitation_data = {
                    'code': user_invitation_code,
                    'user_id': new_user['id'],
                    'status': 'active',
                    'used_count': 0,
                    'max_uses': 999
                }

                self.client.table('invitation_codes').insert(invitation_data).execute()

                # 如果使用了邀请码，更新邀请者信息
                if invited_by_code:
                    await self._process_invitation_usage(invited_by_code, new_user['id'])
                    logger.info(f"新用户 {new_user['id']} 使用邀请码 {invited_by_code} 注册，获得5次额外分析机会（总共8次）")

                logger.info(f"用户注册成功（数据库模式）: {email}")

            except Exception as db_error:
                logger.warning(f"数据库用户创建失败，使用内存模式: {str(db_error)}")
                # 创建内存模式的用户信息
                import random
                new_user = {
                    'id': random.randint(100000, 999999),  # 生成6位随机整数ID
                    'phone': phone,
                    'email': email,
                    'status': 'active',
                    'remaining_analyses': initial_analyses,  # 使用动态分配的分析次数
                    'total_analyses_used': 0,
                    'invitation_code': user_invitation_code,
                    'invited_by_code': invited_by_code,
                    'invited_count': 0,
                    'email_verified': True,
                    'last_login_at': datetime.utcnow().isoformat(),
                    'created_at': datetime.utcnow().isoformat()
                }
                logger.info(f"用户注册成功（内存模式）: {email}")
                if invited_by_code:
                    logger.info(f"内存模式用户使用邀请码 {invited_by_code}，获得{initial_analyses}次分析机会")
            
            # 发送欢迎邮件
            self.email_service.send_welcome_email(email, phone, 3)

            # 保存用户个人信息（如果提供了）
            saved_profile_data = None
            if profile_data:
                profile_saved = await self.save_user_profile(new_user['id'], profile_data)
                if profile_saved:
                    saved_profile_data = profile_data
                    logger.info(f"用户 {new_user['id']} 个人信息已保存")
                else:
                    logger.warning(f"用户 {new_user['id']} 个人信息保存失败")

            # 返回用户信息
            return UserInfo(
                id=new_user['id'],
                phone=new_user['phone'],
                email=new_user['email'],
                status=UserStatus(new_user['status']),
                remaining_analyses=new_user['remaining_analyses'],
                total_analyses_used=new_user['total_analyses_used'],
                invitation_code=new_user['invitation_code'],
                invited_count=new_user['invited_count'],
                created_at=datetime.fromisoformat(new_user['created_at'].replace('Z', '+00:00')),
                last_login_at=datetime.fromisoformat(new_user['last_login_at'].replace('Z', '+00:00')) if new_user['last_login_at'] else None,
                profile_data=saved_profile_data
            )
            
        except Exception as e:
            logger.error(f"用户注册失败: {str(e)}")
            raise Exception(str(e))

    async def _create_user_without_code_verification(self, phone: str, email: str, invitation_code: Optional[str] = None, profile_data: Optional[UserProfileData] = None) -> UserInfo:
        """当未进行验证码验证时直接创建用户（用于自动创建账户）"""
        try:
            if self.use_local_store or not self.client:
                return self._create_local_user(phone, email, invitation_code, profile_data)

            invited_by_code = None
            user_invitation_code = self.generate_invitation_code()

            if invitation_code:
                try:
                    invite_result = self.client.table('invitation_codes')                         .select('*')                         .eq('code', invitation_code)                         .eq('status', 'active')                         .execute()

                    if invite_result.data:
                        invite_data = invite_result.data[0]
                        if invite_data['used_count'] < invite_data['max_uses']:
                            invited_by_code = invitation_code
                            logger.info(f"用户使用邀请码 {invitation_code}")
                        else:
                            logger.warning(f"邀请码已达到使用上限: {invitation_code}")
                    else:
                        logger.warning(f"无效邀请码: {invitation_code}")
                except Exception as invitation_error:
                    logger.warning(f"邀请码验证失败: {invitation_error}")

            initial_analyses = 9 if invited_by_code else 6
            user_data = {
                'phone': phone,
                'email': email,
                'status': 'active',
                'remaining_analyses': initial_analyses,
                'total_analyses_used': 0,
                'invitation_code': user_invitation_code,
                'invited_by_code': invited_by_code,
                'invited_count': 0,
                'email_verified': True,
                'created_at': datetime.utcnow().isoformat(),
                'last_login_at': datetime.utcnow().isoformat()
            }

            try:
                user_result = self.client.table('users').insert(user_data).execute()
                if not user_result.data:
                    raise Exception("用户创建失败")

                new_user = user_result.data[0]

                invitation_data = {
                    'code': user_invitation_code,
                    'user_id': new_user['id'],
                    'status': 'active',
                    'used_count': 0,
                    'max_uses': 999
                }
                self.client.table('invitation_codes').insert(invitation_data).execute()

                if invited_by_code:
                    await self._process_invitation_usage(invited_by_code, new_user['id'])

                logger.info(f"自动创建用户成功（数据库模式）: {email}")

                try:
                    self.email_service.send_welcome_email(email, phone, 3)
                except Exception as email_error:
                    logger.warning(f"发送欢迎邮件失败: {email_error}")

                saved_profile_data = None
                if profile_data:
                    profile_saved = await self.save_user_profile(new_user['id'], profile_data)
                    if profile_saved:
                        saved_profile_data = profile_data
                    else:
                        logger.warning(f"用户 {new_user['id']} 个人信息保存失败")

                return UserInfo(
                    id=new_user['id'],
                    phone=new_user['phone'],
                    email=new_user['email'],
                    status=UserStatus(new_user['status']),
                    remaining_analyses=new_user['remaining_analyses'],
                    total_analyses_used=new_user['total_analyses_used'],
                    invitation_code=new_user['invitation_code'],
                    invited_count=new_user['invited_count'],
                    created_at=datetime.fromisoformat(new_user['created_at'].replace('Z', '+00:00')),
                    last_login_at=datetime.fromisoformat(new_user['last_login_at'].replace('Z', '+00:00')) if new_user['last_login_at'] else None,
                    profile_data=saved_profile_data
                )

            except Exception as db_error:
                logger.warning(f"数据库用户创建失败，使用内存模式: {db_error}")
                return self._create_local_user(phone, email, invitation_code, profile_data)

        except Exception as e:
            logger.error(f"自动创建用户失败: {e}")
            raise Exception(str(e))

    async def _process_invitation_usage(self, invitation_code: str, new_user_id: int):
        """处理邀请码使用"""
        try:
            # 获取邀请码信息
            invite_result = self.client.table('invitation_codes')\
                .select('user_id, used_count')\
                .eq('code', invitation_code)\
                .execute()

            if invite_result.data:
                invite_data = invite_result.data[0]
                inviter_id = invite_data['user_id']
                current_used_count = invite_data['used_count']

                # 更新邀请码使用次数
                self.client.table('invitation_codes')\
                    .update({'used_count': current_used_count + 1})\
                    .eq('code', invitation_code)\
                    .execute()

                # 获取邀请者当前信息
                user_result = self.client.table('users')\
                    .select('remaining_analyses, invited_count')\
                    .eq('id', inviter_id)\
                    .execute()

                if user_result.data:
                    user_data = user_result.data[0]
                    current_remaining = user_data['remaining_analyses']
                    current_invited_count = user_data['invited_count']

                    # 给邀请者增加3次分析机会
                    self.client.table('users')\
                        .update({
                            'remaining_analyses': current_remaining + 3,
                            'invited_count': current_invited_count + 1
                        })\
                        .eq('id', inviter_id)\
                        .execute()

                    logger.info(f"邀请码 {invitation_code} 使用成功，邀请者 {inviter_id} 获得3次分析机会")

        except Exception as e:
            logger.error(f"处理邀请码使用失败: {str(e)}")
            # 不抛出异常，避免影响用户注册

    async def login_user(self, phone: str, email: str, verification_code: str, profile_data: Optional[UserProfileData] = None) -> Dict[str, Any]:
        """用户登录"""
        try:
            await self.verify_email_code(email, phone, verification_code)

            if self.use_local_store or not self.client:
                existing_user = None
                for record in self._local_users.values():
                    if record['phone'] == phone or record['email'] == email:
                        existing_user = record
                        break

                if existing_user is None:
                    user_info = self._create_local_user(phone, email, None, profile_data)
                    token_data = self.generate_jwt_token(user_info.id)
                    result = {**token_data, 'user_info': user_info, 'is_new_user': True}
                    return result

                existing_user['last_login_at'] = datetime.utcnow()
                if profile_data:
                    self._local_profiles[existing_user['id']] = profile_data

                user_info = UserInfo(
                    id=existing_user['id'],
                    phone=existing_user['phone'],
                    email=existing_user['email'],
                    status=UserStatus(existing_user['status']),
                    remaining_analyses=existing_user['remaining_analyses'],
                    total_analyses_used=existing_user['total_analyses_used'],
                    invitation_code=existing_user['invitation_code'],
                    invited_count=existing_user['invited_count'],
                    created_at=existing_user['created_at'],
                    last_login_at=existing_user['last_login_at'],
                    profile_data=self._local_profiles.get(existing_user['id'])
                )

                token_data = self.generate_jwt_token(existing_user['id'])
                return {**token_data, 'user_info': user_info}

            user_result = self.client.table('users').select('*').eq('phone', phone).execute()
            user = None
            is_new_user = False

            if not user_result.data:
                logger.info(f"用户不存在，自动创建账户: {phone}, {email}")
                user_info = await self._create_user_without_code_verification(phone, email, None, profile_data)
                user_result = self.client.table('users').select('*').eq('phone', phone).execute()
                if user_result.data:
                    user = user_result.data[0]
                else:
                    return {**self.generate_jwt_token(user_info.id), 'user_info': user_info, 'is_new_user': True}
                is_new_user = True
            else:
                user = user_result.data[0]
                if user['status'] != 'active':
                    raise Exception("账户已被暂停，请联系客服")

            if not is_new_user:
                try:
                    self.client.table('users')                        .update({'last_login_at': datetime.utcnow().isoformat()})                        .eq('id', user['id'])                        .execute()
                except Exception as update_error:
                    logger.warning(f"更新登录时间失败: {update_error}")

            token_data = self.generate_jwt_token(user['id'])
            profile = await self.get_user_profile(user['id'])
            user_info = UserInfo(
                id=user['id'],
                phone=user['phone'],
                email=user['email'],
                status=UserStatus(user['status']),
                remaining_analyses=user['remaining_analyses'],
                total_analyses_used=user['total_analyses_used'],
                invitation_code=user['invitation_code'],
                invited_count=user['invited_count'],
                created_at=datetime.fromisoformat(user['created_at'].replace('Z', '+00:00')),
                last_login_at=datetime.utcnow(),
                profile_data=profile
            )

            result = {**token_data, 'user_info': user_info}
            if is_new_user:
                result['is_new_user'] = True

            return result

        except Exception as e:
            logger.error(f"用户登录失败: {e}")
            raise Exception(str(e))

    def get_cached_verification_code(self, email: str, phone: str) -> Optional[str]:
        """获取验证码（从数据库或内存缓存，仅用于调试）"""
        try:
            # 首先尝试从数据库获取
            if self.client:
                try:
                    result = self.client.table('email_verification_codes')\
                        .select('code, expires_at, used')\
                        .eq('email', email)\
                        .eq('phone', phone)\
                        .eq('used', False)\
                        .order('created_at', desc=True)\
                        .limit(1)\
                        .execute()

                    if result.data:
                        verification_record = result.data[0]
                        expires_at = datetime.fromisoformat(verification_record['expires_at'].replace('Z', '+00:00'))
                        if datetime.utcnow().replace(tzinfo=expires_at.tzinfo) <= expires_at:
                            return verification_record['code']
                except Exception as db_error:
                    logger.warning(f"数据库验证码查询失败: {str(db_error)}")

            # 回退到内存缓存
            cache_key = f"{email}:{phone}"
            if cache_key in verification_code_cache:
                cached_data = verification_code_cache[cache_key]
                if not cached_data['used'] and datetime.utcnow() <= cached_data['expires_at']:
                    return cached_data['code']

            return None

        except Exception as e:
            logger.error(f"获取验证码失败: {str(e)}")
            return None

    async def get_user_info(self, user_id: int) -> Optional[UserInfo]:
        """获取用户信息"""
        try:
            if self.use_local_store or not self.client:
                record = self._local_users.get(user_id)
                if not record:
                    return None
                profile = self._local_profiles.get(user_id)
                return UserInfo(
                    id=record['id'],
                    phone=record['phone'],
                    email=record['email'],
                    status=UserStatus(record['status']),
                    remaining_analyses=record['remaining_analyses'],
                    total_analyses_used=record['total_analyses_used'],
                    invitation_code=record['invitation_code'],
                    invited_count=record['invited_count'],
                    created_at=record['created_at'],
                    last_login_at=record['last_login_at'],
                    profile_data=profile
                )

            user_result = self.client.table('users')                .select('*')                .eq('id', user_id)                .execute()

            if not user_result.data:
                return None

            user = user_result.data[0]
            profile_data = await self.get_user_profile(user['id'])

            return UserInfo(
                id=user['id'],
                phone=user['phone'],
                email=user['email'],
                status=UserStatus(user['status']),
                remaining_analyses=user['remaining_analyses'],
                total_analyses_used=user['total_analyses_used'],
                invitation_code=user['invitation_code'],
                invited_count=user['invited_count'],
                created_at=datetime.fromisoformat(user['created_at'].replace('Z', '+00:00')),
                last_login_at=datetime.fromisoformat(user['last_login_at'].replace('Z', '+00:00')) if user['last_login_at'] else None,
                profile_data=profile_data
            )

        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return None

    async def consume_analysis_chance(self, user_id: int) -> bool:
        """消耗一次分析机会"""
        try:
            logger.info(f"[ANALYSIS_CONSUMPTION] 用户 {user_id} 开始消耗分析机会")

            if self.use_local_store or not self.client:
                record = self._local_users.get(user_id)
                if not record:
                    raise Exception("用户不存在")
                if record['remaining_analyses'] <= 0:
                    raise Exception("分析次数已用完，请邀请好友获得更多机会")
                record['remaining_analyses'] -= 1
                record['total_analyses_used'] += 1
                logger.info(
                    f"[ANALYSIS_CONSUMPTION] 用户 {user_id} 内存模式剩余={record['remaining_analyses']}, 已用={record['total_analyses_used']}"
                )
                return True

            user_result = self.client.table('users')\
                .select('remaining_analyses, total_analyses_used')\
                .eq('id', user_id)\
                .execute()

            if not user_result.data:
                raise Exception("用户不存在")

            user_data = user_result.data[0]
            remaining = user_data['remaining_analyses']
            total_used = user_data['total_analyses_used']

            if remaining <= 0:
                logger.warning(f"[ANALYSIS_CONSUMPTION] 用户 {user_id} 分析次数不足: {remaining}")
                raise Exception("分析次数已用完，请邀请好友获得更多机会")

            new_remaining = remaining - 1
            new_total_used = total_used + 1

            self.client.table('users')\
                .update({
                    'remaining_analyses': new_remaining,
                    'total_analyses_used': new_total_used
                })\
                .eq('id', user_id)\
                .execute()

            logger.info(f"[ANALYSIS_CONSUMPTION] 用户 {user_id} 消耗完成: 剩余={new_remaining}, 已用={new_total_used}")
            return True

        except Exception as e:
            logger.error(f"[ANALYSIS_CONSUMPTION] 用户 {user_id} 消耗失败: {str(e)}")
            raise Exception(str(e))

    async def record_analysis(self, user_id: int, task_id: str, analysis_data: dict) -> bool:
        """记录用户分析"""
        try:
            if not self.client:
                raise Exception("数据库连接未初始化")

            record_data = {
                'user_id': user_id,
                'task_id': task_id,
                'analysis_data': analysis_data,
                'status': 'pending'
            }

            self.client.table('user_analysis_records').insert(record_data).execute()

            logger.info(f"用户 {user_id} 分析记录已保存，任务ID: {task_id}")
            return True

        except Exception as e:
            logger.error(f"记录用户分析失败: {str(e)}")
            return False

    async def update_analysis_result(self, task_id: str, analysis_result: dict, status: str = "completed") -> bool:
        """更新分析结果"""
        try:
            if not self.client:
                raise Exception("数据库连接未初始化")

            update_data = {
                'analysis_result': analysis_result,
                'status': status,
                'completed_at': datetime.utcnow().isoformat()
            }

            self.client.table('user_analysis_records')\
                .update(update_data)\
                .eq('task_id', task_id)\
                .execute()

            logger.info(f"分析结果已更新，任务ID: {task_id}")
            return True

        except Exception as e:
            logger.error(f"更新分析结果失败: {str(e)}")
            return False

    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            if not self.client:
                return False

            # 尝试查询用户表
            self.client.table('users').select('id').limit(1).execute()
            return True

        except Exception as e:
            logger.error(f"用户服务连接测试失败: {str(e)}")
            return False

    async def test_email_verification_service(self) -> bool:
        """测试Hunter.io邮箱验证服务连接"""
        try:
            return await email_verification_service.test_connection()
        except Exception as e:
            logger.error(f"邮箱验证服务测试失败: {str(e)}")
            return False

    async def save_user_profile(self, user_id: int, profile_data: UserProfileData) -> bool:
        """保存用户个人信息"""
        try:
            if not profile_data:
                return False

            fields_set = getattr(profile_data, 'model_fields_set', None)
            if not fields_set:
                fields_set = set(profile_data.model_dump(exclude_unset=True).keys())

            update_payload = {field: getattr(profile_data, field) for field in fields_set}

            if 'target_majors' in update_payload:
                canonical_target_majors, invalid_target_majors = major_taxonomy_service.normalise_target_majors(
                    update_payload.get('target_majors') or []
                )
                if invalid_target_majors:
                    logger.warning(
                        "用户 %s 提供的目标专业包含未定义项: %s",
                        user_id,
                        invalid_target_majors
                    )
                update_payload['target_majors'] = canonical_target_majors

            if self.use_local_store or not self.client:
                existing = self._local_profiles.get(user_id)
                base_data = existing.model_dump() if hasattr(existing, 'model_dump') else (
                    existing.dict() if hasattr(existing, 'dict') else {}
                )
                base_data.update(update_payload)
                self._local_profiles[user_id] = UserProfileData(**base_data)
                logger.info(f"用户 {user_id} 个人信息已保存（内存模式）")
                return True

            if not update_payload:
                logger.info(f"用户 {user_id} 未提供需要更新的个人信息字段")
                return True

            supabase_payload = dict(update_payload)
            supabase_payload['user_id'] = user_id

            result = self.client.table('user_profiles')                .upsert(supabase_payload, on_conflict='user_id')                .execute()

            if result.data:
                logger.info(f"用户 {user_id} 个人信息保存成功")
                return True
            else:
                logger.warning(f"用户 {user_id} 个人信息保存失败")
                return False

        except Exception as e:
            logger.error(f"保存用户个人信息失败: {e}")
            return False

    async def get_user_profile(self, user_id: int) -> Optional[UserProfileData]:
        """获取用户个人信息"""
        try:
            if self.use_local_store or not self.client:
                profile = self._local_profiles.get(user_id)
                if profile and getattr(profile, 'target_majors', None):
                    canonical_target_majors, _ = major_taxonomy_service.normalise_target_majors(
                        profile.target_majors
                    )
                    profile = profile.copy(update={'target_majors': canonical_target_majors})
                return profile

            result = self.client.table('user_profiles')                .select('*')                .eq('user_id', user_id)                .execute()

            if not result.data:
                logger.info(f"用户 {user_id} 暂无个人信息")
                return None

            profile_data = result.data[0]
            canonical_target_majors, _ = major_taxonomy_service.normalise_target_majors(
                profile_data.get('target_majors', [])
            )

            return UserProfileData(
                undergraduate_university=profile_data.get('undergraduate_university'),
                undergraduate_major=profile_data.get('undergraduate_major'),
                gpa=profile_data.get('gpa'),
                gpa_scale=profile_data.get('gpa_scale'),
                graduation_year=profile_data.get('graduation_year'),
                application_year=profile_data.get('application_year'),
                target_score=profile_data.get('target_score'),
                current_level=profile_data.get('current_level'),
                exam_date=profile_data.get('exam_date'),
                language_test_status=profile_data.get('language_test_status'),
                language_test_type=profile_data.get('language_test_type'),
                language_total_score=profile_data.get('language_total_score'),
                language_reading=profile_data.get('language_reading'),
                language_listening=profile_data.get('language_listening'),
                language_speaking=profile_data.get('language_speaking'),
                language_writing=profile_data.get('language_writing'),
                language_target_total_score=profile_data.get('language_target_total_score'),
                language_target_reading=profile_data.get('language_target_reading'),
                language_target_listening=profile_data.get('language_target_listening'),
                language_target_speaking=profile_data.get('language_target_speaking'),
                language_target_writing=profile_data.get('language_target_writing'),
                language_expected_test_date=profile_data.get('language_expected_test_date'),
                gre_test_status=profile_data.get('gre_test_status'),
                gre_total=profile_data.get('gre_total'),
                gre_verbal=profile_data.get('gre_verbal'),
                gre_quantitative=profile_data.get('gre_quantitative'),
                gre_writing=profile_data.get('gre_writing'),
                gre_target_total=profile_data.get('gre_target_total'),
                gre_target_verbal=profile_data.get('gre_target_verbal'),
                gre_target_quantitative=profile_data.get('gre_target_quantitative'),
                gre_target_writing=profile_data.get('gre_target_writing'),
                gre_expected_test_date=profile_data.get('gre_expected_test_date'),
                gmat_test_status=profile_data.get('gmat_test_status'),
                gmat_total=profile_data.get('gmat_total'),
                gmat_target_total=profile_data.get('gmat_target_total'),
                gmat_expected_test_date=profile_data.get('gmat_expected_test_date'),
                target_countries=profile_data.get('target_countries', []),
                target_majors=canonical_target_majors,
                target_degree_type=profile_data.get('target_degree_type'),
                research_experiences=profile_data.get('research_experiences', []),
                internship_experiences=profile_data.get('internship_experiences', []),
                other_experiences=profile_data.get('other_experiences', [])
            )

        except Exception as e:
            logger.error(f"获取用户个人信息失败: {e}")
            return None

    async def get_user_profile(self, user_id: int) -> Optional[UserProfileData]:
        """获取用户个人信息"""
        try:
            if not self.client:
                logger.warning("数据库连接未初始化，无法获取个人信息")
                return None

            # 查询用户个人信息
            result = self.client.table('user_profiles')\
                .select('*')\
                .eq('user_id', user_id)\
                .execute()

            if not result.data:
                logger.info(f"用户 {user_id} 暂无个人信息")
                return None

            profile_data = result.data[0]

            # 转换为UserProfileData对象
            canonical_target_majors, _ = major_taxonomy_service.normalise_target_majors(
                profile_data.get('target_majors', [])
            )

            return UserProfileData(
                undergraduate_university=profile_data.get('undergraduate_university'),
                undergraduate_major=profile_data.get('undergraduate_major'),
                gpa=profile_data.get('gpa'),
                gpa_scale=profile_data.get('gpa_scale'),
                graduation_year=profile_data.get('graduation_year'),
                application_year=profile_data.get('application_year'),
                target_score=profile_data.get('target_score'),
                current_level=profile_data.get('current_level'),
                exam_date=profile_data.get('exam_date'),
                language_test_status=profile_data.get('language_test_status'),
                language_test_type=profile_data.get('language_test_type'),
                language_total_score=profile_data.get('language_total_score'),
                language_reading=profile_data.get('language_reading'),
                language_listening=profile_data.get('language_listening'),
                language_speaking=profile_data.get('language_speaking'),
                language_writing=profile_data.get('language_writing'),
                language_target_total_score=profile_data.get('language_target_total_score'),
                language_target_reading=profile_data.get('language_target_reading'),
                language_target_listening=profile_data.get('language_target_listening'),
                language_target_speaking=profile_data.get('language_target_speaking'),
                language_target_writing=profile_data.get('language_target_writing'),
                language_expected_test_date=profile_data.get('language_expected_test_date'),
                gre_test_status=profile_data.get('gre_test_status'),
                gre_total=profile_data.get('gre_total'),
                gre_verbal=profile_data.get('gre_verbal'),
                gre_quantitative=profile_data.get('gre_quantitative'),
                gre_writing=profile_data.get('gre_writing'),
                gre_target_total=profile_data.get('gre_target_total'),
                gre_target_verbal=profile_data.get('gre_target_verbal'),
                gre_target_quantitative=profile_data.get('gre_target_quantitative'),
                gre_target_writing=profile_data.get('gre_target_writing'),
                gre_expected_test_date=profile_data.get('gre_expected_test_date'),
                gmat_test_status=profile_data.get('gmat_test_status'),
                gmat_total=profile_data.get('gmat_total'),
                gmat_target_total=profile_data.get('gmat_target_total'),
                gmat_expected_test_date=profile_data.get('gmat_expected_test_date'),
                target_countries=profile_data.get('target_countries', []),
                target_majors=canonical_target_majors,
                target_degree_type=profile_data.get('target_degree_type'),
                research_experiences=profile_data.get('research_experiences', []),
                internship_experiences=profile_data.get('internship_experiences', []),
                other_experiences=profile_data.get('other_experiences', [])
            )

        except Exception as e:
            logger.error(f"获取用户个人信息失败: {str(e)}")
            return None
