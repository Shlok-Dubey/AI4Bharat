"""
FastAPI main application entry point.

For AWS deployment with DynamoDB:
- Update database imports to use DynamoDB client
- Configure AWS credentials via environment variables
- Use AWS Lambda handler for serverless deployment
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth_router, oauth_router, campaigns_router, content_router, content_management_router, schedule_router, analytics_router

# Create FastAPI app
app = FastAPI(
    title="AI Content Agent API",
    description="AI-driven social media campaign platform",
    version="1.0.0"
)

# Configure CORS - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(oauth_router)
app.include_router(campaigns_router)
app.include_router(content_router)
app.include_router(content_management_router)
app.include_router(schedule_router)
app.include_router(analytics_router)

@app.on_event("startup")
def on_startup():
    """Application startup"""
    print("🚀 AI Content Agent API started")
    print("📋 Manual publishing mode (EventBridge/Lambda disabled)")
    print("📊 Using DynamoDB for data storage")
    print("📦 Using S3 for media storage")

@app.on_event("shutdown")
def on_shutdown():
    """Application shutdown"""
    print("👋 AI Content Agent API shutting down")

@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "AI Content Agent API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        import dynamodb_client
        # Test DynamoDB connection by checking if tables exist
        dynamodb_client.users_table.table_status
        
        return {
            "status": "healthy",
            "database": "DynamoDB connected",
            "mode": "manual_publishing"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "DynamoDB disconnected",
            "error": str(e)
        }
