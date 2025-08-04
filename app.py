# app.py - Fixed BYPARR with proper type handling

from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import time
import logging
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_chrome_options():
    """Configure Chrome for Cloud Run"""
    options = Options()
    
    # Basic headless options
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # Anti-detection options
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    
    # Window settings
    options.add_argument("--window-size=1920,1080")
    
    # Random user agent
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    options.add_argument(f"--user-agent={random.choice(user_agents)}")
    
    # Anti-detection prefs
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    return options

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "service": "BYPARR Cloud Fixed",
        "instance": os.environ.get('K_SERVICE', 'byparr'),
        "timestamp": time.time(),
        "version": "2.1-fixed"
    }), 200

@app.route('/v1', methods=['POST'])
def byparr_api():
    """Main BYPARR API - Fixed version"""
    start_time = time.time()
    driver = None
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data"}), 400
        
        cmd = data.get('cmd')
        url = data.get('url')
        max_timeout = data.get('maxTimeout', 35000)
        
        # 🔧 Fix: Convert timeout to int if it's string
        try:
            max_timeout = int(max_timeout)
        except (ValueError, TypeError):
            max_timeout = 35000
        
        if cmd != 'request.get' or not url:
            return jsonify({"error": "Invalid request"}), 400
        
        logger.info(f"Processing URL: {url} (timeout: {max_timeout}ms)")
        
        # Initialize Chrome driver
        chrome_options = get_chrome_options()
        driver = webdriver.Chrome(options=chrome_options)
        
        # 🔧 Fix: Proper timeout conversion
        driver.set_page_load_timeout(max_timeout / 1000.0)
        driver.implicitly_wait(10)
        
        # Execute anti-detection script
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Load page
        driver.get(url)
        
        # Wait for page load
        time.sleep(random.uniform(2, 4))
        
        # Check for Cloudflare and wait if needed
        page_source = driver.page_source
        if "just a moment" in page_source.lower() or "checking your browser" in page_source.lower():
            logger.info("Cloudflare challenge detected, waiting...")
            
            # Wait up to 30 seconds for challenge
            for i in range(30):
                time.sleep(1)
                current_source = driver.page_source
                if "just a moment" not in current_source.lower():
                    logger.info(f"Cloudflare bypass successful after {i+1} seconds")
                    page_source = current_source
                    break
        
        processing_time = time.time() - start_time
        logger.info(f"Successfully processed in {processing_time:.2f}s")
        
        return jsonify({
            "solution": {
                "response": page_source,
                "status": "success",
                "url": url,
                "processing_time": processing_time,
                "instance": os.environ.get('K_SERVICE', 'byparr')
            }
        }), 200
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error: {str(e)}")
        
        return jsonify({
            "error": str(e),
            "processing_time": processing_time,
            "instance": os.environ.get('K_SERVICE', 'byparr')
        }), 500
        
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        "service": "BYPARR Cloud Fixed",
        "status": "running",
        "selenium": True,
        "version": "2.1"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting Fixed BYPARR on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
