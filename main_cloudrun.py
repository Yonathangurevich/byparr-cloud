#!/usr/bin/env python3
"""
Cloud Run wrapper for BYPARR
"""
import os
import sys

# Set Cloud Run specific environment variables
os.environ["PORT"] = str(os.environ.get("PORT", "8191"))
os.environ["USE_XVFB"] = "True"
os.environ["USE_HEADLESS"] = "True"
os.environ["CHROME_BINARY_LOCATION"] = "/usr/bin/google-chrome-stable"

# Configure Chrome arguments for Cloud Run environment
chrome_args = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-web-security",
    "--disable-features=VizDisplayCompositor",
    "--disable-blink-features=AutomationControlled",
    "--user-data-dir=/tmp/chrome-user-data",
    "--disable-software-rasterizer",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
    "--disable-features=TranslateUI",
    "--disable-ipc-flooding-protection",
    "--window-size=1920,1080",
    "--start-maximized",
    "--disable-extensions",
    "--disable-plugins",
    "--disable-images",
    "--disable-javascript",  # Enable only when needed
]

# Monkey patch seleniumbase settings before importing
try:
    import seleniumbase.config.settings as sb_settings
    sb_settings.CHROME_START_ARGS = chrome_args
except ImportError:
    print("Warning: Could not import seleniumbase settings")

# Configure proxy if provided
proxy = os.environ.get("HTTP_PROXY", "")
if proxy:
    os.environ["http_proxy"] = proxy
    os.environ["https_proxy"] = proxy
    chrome_args.append(f"--proxy-server={proxy}")

# Import and run the original BYPARR main
try:
    # Try to import from the BYPARR package
    from byparr import main
    
    # If BYPARR uses FastAPI, we need to get the app instance
    if hasattr(main, 'app'):
        app = main.app
    else:
        # Otherwise, try to find the app in the module
        import importlib
        import uvicorn
        
        # Load the main module
        main_module = importlib.import_module('main')
        
        # Find the FastAPI app instance
        app = None
        for attr_name in dir(main_module):
            attr = getattr(main_module, attr_name)
            if hasattr(attr, '__class__') and attr.__class__.__name__ == 'FastAPI':
                app = attr
                break
        
        if not app:
            print("Error: Could not find FastAPI app instance")
            sys.exit(1)
    
    # Run with uvicorn if this is the main module
    if __name__ == "__main__":
        port = int(os.environ.get("PORT", 8191))
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
        
except ImportError as e:
    print(f"Error importing BYPARR: {e}")
    print("Make sure BYPARR is properly installed")
    sys.exit(1)
