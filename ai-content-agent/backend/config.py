"""
Application configuration settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings loaded from environment variables"""
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/ai_content_agent"
    )
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Meta OAuth
    META_APP_ID: str = os.getenv("META_APP_ID", "")
    META_APP_SECRET: str = os.getenv("META_APP_SECRET", "")
    META_REDIRECT_URI: str = os.getenv("META_REDIRECT_URI", "http://localhost:8000/auth/meta/callback")
    
    # Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    # Meta API URLs
    META_OAUTH_URL: str = "https://www.facebook.com/v18.0/dialog/oauth"
    META_TOKEN_URL: str = "https://graph.facebook.com/v18.0/oauth/access_token"
    META_GRAPH_API_URL: str = "https://graph.facebook.com/v18.0"
    
    # OAuth Scopes for Instagram
    # Required scopes for posting content to Instagram
    META_SCOPES: str = "instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement"

settings = Settings()
