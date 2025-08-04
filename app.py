# app.py - Real BYPARR with Selenium for Google Cloud Run

from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import logging
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_chrome_options():
    """Configure Chrome for Cloud Run with anti-detection"""
    options = Options()
    
    # Basic headless options
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # Anti-detection options
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    
    # Window and viewport
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    
    # Random user agents
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    options.add_argument(f"--user-agent={random.choice(user_agents)}")
    
    # Performance optimizations
    options.add_argument("--memory-pressure-off")
    options.add_argument("--max_old_space_size=4096")
    options.add_argument("--aggressive-cache-discard")
    
    # Prefs to avoid detection
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Additional prefs
    prefs = {
        "profile.default_content_setting_values": {
            "notifications": 2,
            "media_stream": 2,
        },
        "profile.managed_default_content_settings": {
            "images": 2
        }
    }
    options.add_experimental_option("prefs", prefs)
    
    return options

def bypass_cloudflare(driver, url, max_attempts=3):
    """Try to bypass Cloudflare protection"""
    for attempt in range(max_attempts):
        try:
            logger.info(f"Attempt {attempt + 1} to load: {url}")
            driver.get(url)
            
            # Wait a bit for page to load
            time.sleep(random.uniform(3, 6))
            
            # Check if we hit Cloudflare challenge
            page_source = driver.page_source.lower()
            
            if any(phrase in page_source for phrase in [
                "just a moment", 
                "checking your browser", 
                "cloudflare", 
                "challenge-running",
                "verifying you are human"
            ]):
                logger.info(f"Cloudflare detected on attempt {attempt + 1}, waiting...")
                
                # Wait for challenge to complete
                max_wait = 30
                for i in range(max_wait):
                    time.sleep(1)
                    current_url = driver.current_url
                    new_source = driver.page_source.lower()
                    
                    # Check if we passed the challenge
                    if not any(phrase in new_source for phrase in [
                        "just a moment", 
                        "checking your browser",
                        "challenge-running"
                    ]):
                        logger.info(f"Cloudflare bypass successful after {i+1} seconds")
                        return driver.page_source
                
                if attempt < max_attempts - 1:
                    logger.info("Cloudflare challenge timeout, retrying...")
                    time.sleep(random.uniform(2, 5))
                    continue
            else:
                logger.info("No Cloudflare challenge detected")
                return driver.page_source
                
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_attempts - 1:
                time.sleep(random.uniform(2, 4))
                continue
    
    # If all attempts failed, return what we have
    logger.warning("All bypass attempts failed, returning current page source")
    return driver.page_source

@app.route('/health', methods=['GET'])
def health():
    """Health check for load balancer"""
    return jsonify({
        "status": "healthy",
        "service": "BYPARR Cloud Real",
        "instance": os.environ.get('K_SERVICE', 'byparr'),
        "timestamp": time.time(),
        "version": "2.0-selenium"
    }), 200

@app.route('/v1', methods=['POST'])
def byparr_api():
    """Main BYPARR API with real Selenium"""
    start_time = time.time()
    driver = None
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data"}), 400
        
        cmd = data.get('cmd')
        url = data.get('url')
        max_timeout = data.get('maxTimeout', 35000)
        
        if cmd != 'request.get' or not url:
            return jsonify({"error": "Invalid request"}), 400
        
        logger.info(f"Processing URL with real Selenium: {url}")
        
        # Initialize Chrome driver
        chrome_options = get_chrome_options()
        driver = webdriver.Chrome(options=chrome_options)
        
        # Set timeouts
        driver.set_page_load_timeout(max_timeout / 1000)
        driver.implicitly_wait(10)
        
        # Execute anti-detection script
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Load page with Cloudflare bypass
        page_source = bypass_cloudflare(driver, url)
        
        processing_time = time.time() - start_time
        logger.info(f"Successfully processed in {processing_time:.2f}s")
        
        return jsonify({
            "solution": {
                "response": page_source,
                "status": "success",
                "url": url,
                "processing_time": processing_time,
                "instance": os.environ.get('K_SERVICE', 'byparr'),
                "user_agent": driver.execute_script("return navigator.userAgent;")
            }
        }), 200
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error processing request: {str(e)}")
        
        return jsonify({
            "error": str(e),
            "processing_time": processing_time,
            "instance": os.environ.get('K_SERVICE', 'byparr'),
            "url": url if 'url' in locals() else 'unknown'
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
        "service": "BYPARR Cloud Real",
        "status": "running",
        "endpoints": ["/health", "/v1"],
        "region": "me-west1",
        "selenium": True,
        "cloudflare_bypass": True
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting Real BYPARR on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
