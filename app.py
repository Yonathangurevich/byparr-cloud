from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_chrome_options():
    """Configure Chrome for Cloud Run"""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    return options

@app.route('/health', methods=['GET'])
def health():
    """Health check for load balancer"""
    return jsonify({
        "status": "healthy",
        "instance": os.environ.get('K_SERVICE', 'byparr'),
        "timestamp": time.time()
    }), 200

@app.route('/v1', methods=['POST'])
def byparr_api():
    """Main BYPARR API - compatible with your N8N"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data"}), 400
        
        cmd = data.get('cmd')
        url = data.get('url')
        
        if cmd != 'request.get' or not url:
            return jsonify({"error": "Invalid request"}), 400
        
        logger.info(f"Processing URL: {url}")
        
        # Initialize Chrome
        options = get_chrome_options()
        driver = webdriver.Chrome(options=options)
        
        try:
            # Get page
            driver.get(url)
            time.sleep(2)  # Wait for load
            
            page_source = driver.page_source
            
            return jsonify({
                "solution": {
                    "response": page_source,
                    "status": "success",
                    "url": url
                }
            }), 200
            
        finally:
            driver.quit()
            
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({
            "error": str(e),
            "instance": os.environ.get('K_SERVICE', 'byparr')
        }), 500

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        "service": "BYPARR Cloud",
        "status": "running",
        "endpoints": ["/health", "/v1"]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
