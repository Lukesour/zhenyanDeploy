import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from config.env (relative to this module or backend root)
# In production (like Fly.io), environment variables are set directly
_BASE_DIR = Path(__file__).resolve().parent
_POSSIBLE_ENV_PATHS = [
    _BASE_DIR / "config.env",
    _BASE_DIR.parent / "config.env",
]
for _env_path in _POSSIBLE_ENV_PATHS:
    if _env_path.exists():
        load_dotenv(_env_path)
        break

class Settings:
    # Database Configuration
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 5432))
    DB_USER = os.getenv("DB_USER", "suan")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME_SOURCE = os.getenv("DB_NAME_SOURCE", "compass_cases_details")
    DB_NAME_TARGET = os.getenv("DB_NAME_TARGET", "compass_analytics_preprocessed")
    
    # Supabase Configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "cases")
    
    # Gemini API Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # Gmail SMTP Configuration
    GMAIL_SENDER_EMAIL = os.getenv("GMAIL_SENDER_EMAIL", "")
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
    GMAIL_SENDER_NAME = os.getenv("GMAIL_SENDER_NAME", "箴言留学")

    # JWT Configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

    # Hunter.io Email Verification Configuration
    HUNTER_API_KEY = os.getenv("HUNTER_API_KEY", "")

    # Third-party Email API Configuration
    RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
    RESEND_FROM_DOMAIN = os.getenv("RESEND_FROM_DOMAIN", "")
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
    MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY", "")
    MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN", "")
    EMAIL_SEND_METHOD = os.getenv("EMAIL_SEND_METHOD", "smtp")

    # Application Configuration
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Similar Cases Configuration
    SIMILAR_CASES_LIMIT = int(os.getenv("SIMILAR_CASES_LIMIT", "150"))
    SIMILAR_CASES_ANALYSIS_LIMIT = int(os.getenv("SIMILAR_CASES_ANALYSIS_LIMIT", "10"))
    SIMILAR_CASES_API_LIMIT = int(os.getenv("SIMILAR_CASES_API_LIMIT", "200"))
    
    @property
    def source_database_url(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME_SOURCE}"
    
    @property
    def target_database_url(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME_TARGET}"
    
    @property
    def use_supabase(self):
        """Check if Supabase should be used instead of local database"""
        return bool(self.SUPABASE_URL and self.SUPABASE_KEY)

settings = Settings()
