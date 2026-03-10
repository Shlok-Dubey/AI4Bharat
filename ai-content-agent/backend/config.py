"""
Application configuration settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings loaded from environment variables"""
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # AWS Configuration
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    
    # DynamoDB Tables
    DYNAMODB_TABLE_USERS: str = os.getenv("DYNAMODB_TABLE_USERS", "ai_content_users")
    DYNAMODB_TABLE_OAUTH_ACCOUNTS: str = os.getenv("DYNAMODB_TABLE_OAUTH_ACCOUNTS", "ai_content_oauth_accounts")
    DYNAMODB_TABLE_CAMPAIGNS: str = os.getenv("DYNAMODB_TABLE_CAMPAIGNS", "ai_content_campaigns")
    DYNAMODB_TABLE_CAMPAIGN_ASSETS: str = os.getenv("DYNAMODB_TABLE_CAMPAIGN_ASSETS", "ai_content_campaign_assets")
    DYNAMODB_TABLE_GENERATED_CONTENT: str = os.getenv("DYNAMODB_TABLE_GENERATED_CONTENT", "ai_content_generated_content")
    DYNAMODB_TABLE_SCHEDULED_POSTS: str = os.getenv("DYNAMODB_TABLE_SCHEDULED_POSTS", "ai_content_scheduled_posts")
    DYNAMODB_TABLE_POST_ANALYTICS: str = os.getenv("DYNAMODB_TABLE_POST_ANALYTICS", "ai_content_post_analytics")
    
    # S3 Configuration
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "ai-content-agent-assets")
    
    # AWS Bedrock
    BEDROCK_MODEL_ID: str = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-5-sonnet-20241022-v2:0")
    BEDROCK_REGION: str = os.getenv("BEDROCK_REGION", "us-east-1")
    
    # AWS Lambda Configuration (for automatic posting via EventBridge)
    AWS_LAMBDA_POST_HANDLER_ARN: str = os.getenv("AWS_LAMBDA_POST_HANDLER_ARN", "")
    
    # Instagram OAuth Configuration
    INSTAGRAM_APP_ID: str = os.getenv("INSTAGRAM_APP_ID", os.getenv("META_APP_ID", ""))
    INSTAGRAM_APP_SECRET: str = os.getenv("INSTAGRAM_APP_SECRET", os.getenv("META_APP_SECRET", ""))
    
    # Meta OAuth (legacy support)
    META_APP_ID: str = os.getenv("META_APP_ID", "")
    META_APP_SECRET: str = os.getenv("META_APP_SECRET", "")
    META_REDIRECT_URI: str = os.getenv("META_REDIRECT_URI", "http://localhost:8000/auth/meta/callback")
    
    # Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    # Meta API URLs
    META_OAUTH_URL: str = "https://www.facebook.com/v19.0/dialog/oauth"
    META_TOKEN_URL: str = "https://graph.facebook.com/v19.0/oauth/access_token"
    META_GRAPH_API_URL: str = "https://graph.facebook.com/v19.0"
    
    # OAuth Scopes for Instagram
    META_SCOPES: str = "instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement"

settings = Settings()
