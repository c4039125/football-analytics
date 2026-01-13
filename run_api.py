#!/usr/bin/env python3
"""Run the FastAPI application."""

import uvicorn
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    print("=" * 60)
    print("  Football Analytics API - Swagger Documentation")
    print("=" * 60)
    print("")
    print("Starting API server...")
    print("")
    print("📊 Access Swagger UI at: http://localhost:8002/docs")
    print("📖 Access ReDoc at: http://localhost:8002/redoc")
    print("🔗 API Base URL: http://localhost:8002")
    print("")
    print("Features:")
    print("  ✓ Nigerian Football (NPFL) endpoints")
    print("  ✓ Real-time analytics endpoints")
    print("  ✓ Event ingestion endpoints")
    print("  ✓ Live match simulation")
    print("")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print("")

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )
