"""
FastAPI Service - Med Telemetry Platform
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime
import os

app = FastAPI(
    title="FastAPI Service",
    description="FastAPI microservice for Med Telemetry Platform",
    version="1.0.0",
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "FastAPI Service - Med Telemetry Platform",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "fastapi-service"
        }
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

