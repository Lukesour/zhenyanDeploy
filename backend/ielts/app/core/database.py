from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from backend.ielts.app.core.config import settings

load_dotenv()

DATABASE_URL = settings.database_url

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基础模型类
Base = declarative_base()

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """创建所有数据表"""
    # 导入所有模型以确保它们被注册
    import backend.ielts.app.models.user
    import backend.ielts.app.models.essay
    import backend.ielts.app.models.reference_data

    Base.metadata.create_all(bind=engine)
