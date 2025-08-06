#!/usr/bin/env python3
"""
Simple test application to verify basic FastAPI functionality
"""

from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="AI Video Generator - Simple Test", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "AI Video Generator is running!", "timestamp": datetime.utcnow().isoformat()}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)