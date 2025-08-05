#!/usr/bin/env python3
"""
Simple wrapper for BYPARR on Cloud Run
"""
import os
import sys

# Set Chrome options for Cloud Run
os.environ["CHROME_ARGS"] = "--no-sandbox --disable-setuid-sandbox --disable-dev-shm-usage --disable-gpu --headless"

# Get PORT from Cloud Run
PORT = int(os.environ.get("PORT", 8191))
print(f"Starting BYPARR on port {PORT}")

# Import and run BYPARR
try:
    from main import app
    import uvicorn
    
    if __name__ == "__main__":
        uvicorn.run(app, host="0.0.0.0", port=PORT)
except Exception as e:
    print(f"Error starting BYPARR: {e}")
    sys.exit(1)
