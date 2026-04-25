#!/usr/bin/env python3
"""
Standalone FastAPI server for testing
"""
import uvicorn
from backend.routes import app

if __name__ == "__main__":
    print("Starting FastAPI server on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")