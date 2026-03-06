"""
FastAPI application for local development and testing.
This is NOT used in production - production uses AWS Lambda + API Gateway.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dev_api.routes import auth, instagram, products, campaigns, analytics

app = FastAPI(
    title="PostPilot AI - Local Dev API",
    description="Local development API for testing Lambda functions",
    version="1.0.0"
)

# CORS configuration for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(instagram.router)
app.include_router(products.router)
app.include_router(campaigns.router)
app.include_router(analytics.router)


@app.get("/health/liveness")
async def liveness():
    """Health check endpoint - always returns 200 if service is running."""
    return {"status": "ok"}


@app.get("/health/readiness")
async def readiness():
    """Health check endpoint - returns 200 if dependencies are ready."""
    # TODO: Check DynamoDB connectivity
    return {"status": "ready"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
