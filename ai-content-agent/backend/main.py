"""
FastAPI main application entry point.

For AWS deployment with DynamoDB:
- Update database imports to use DynamoDB client
- Configure AWS credentials via environment variables
- Use AWS Lambda handler for serverless deployment
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from database_sqlite import get_db, engine
from base import Base
from routes import auth_router, protected_router, oauth_router, campaigns_router, content_router, content_management_router, schedule_router

# Create FastAPI app
app = FastAPI(
    title="AI Content Agent API",
    description="AI-driven social media campaign platform",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.31.75:5173",
        "http://localhost:8002",
        "http://127.0.0.1:8002",
        "https://studentless-insensitive-renna.ngrok-free.dev"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(protected_router)
app.include_router(oauth_router)
app.include_router(campaigns_router)
app.include_router(content_router)
app.include_router(content_management_router)
app.include_router(schedule_router)

# Create tables on startup (for development only)
# For production, use Alembic migrations
@app.on_event("startup")
def on_startup():
    """Initialize database tables on startup"""
    Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "AI Content Agent API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint with database connectivity test.
    
    For DynamoDB: Test DynamoDB connection instead
    """
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }
