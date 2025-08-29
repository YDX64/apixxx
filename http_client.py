"""
HTTP client utilities for external API requests
"""
import asyncio
import aiohttp
import time
import logging
import json
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

# Global session for connection pooling
global_session = None

# --- Async HTTP Functions ---

async def get_global_session():
    """Get or create global aiohttp session"""
    global global_session
    if global_session is None or global_session.closed:
        connector = aiohttp.TCPConnector(
            limit=20,
            limit_per_host=10,
            keepalive_timeout=300,
            enable_cleanup_closed=True
        )
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.9',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        global_session = aiohttp.ClientSession(
            headers=headers,
            connector=connector,
            timeout=timeout
        )
    return global_session

async def fetch_url(session, url, key):
    """Asynchronously fetch a single URL and return the result with enhanced error handling."""
    start_time = time.time()
    
    try:
        logger.debug(f"Fetching {key} from {url}")
        
        async with session.get(url) as response:
            response.raise_for_status()
            
            fetch_time = time.time() - start_time
            logger.debug(f"Fetched {key} in {fetch_time:.2f}s")
            
            if key == 'h2h_details':
                text = await response.text()
                return key, text, 'html', fetch_time
            else:
                # For AJAX endpoints, try to get JSON
                content_type = response.headers.get('content-type', '').lower()
                if 'application/json' in content_type or 'text/javascript' in content_type:
                    json_data = await response.json()
                    return key, json_data, 'json', fetch_time
                else:
                    # If not JSON, still try to parse as JSON (sometimes servers return wrong content-type)
                    text = await response.text()
                    try:
                        json_data = json.loads(text)
                        return key, json_data, 'json', fetch_time
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse JSON for {key}: {text[:100]}...")
                        return key, {"error": f"Response is not JSON", "content": text[:200]}, 'error', fetch_time
                        
    except aiohttp.ClientError as e:
        fetch_time = time.time() - start_time
        logger.error(f"Client error fetching {key}: {str(e)}")
        return key, {"error": f"Failed to fetch {url}", "details": str(e)}, 'error', fetch_time
    except json.JSONDecodeError as e:
        fetch_time = time.time() - start_time
        logger.error(f"JSON decode error for {key}: {str(e)}")
        return key, {"error": f"Failed to decode JSON from {url}", "details": str(e)}, 'error', fetch_time
    except Exception as e:
        fetch_time = time.time() - start_time
        logger.error(f"Unexpected error fetching {key}: {str(e)}")
        return key, {"error": f"Unexpected error: {str(e)}"}, 'error', fetch_time

async def fetch_all_urls(urls):
    """Fetch all URLs concurrently using global session."""
    session = await get_global_session()
    
    try:
        tasks = [fetch_url(session, url, key) for key, url in urls.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    except Exception as e:
        logger.error(f"Error in fetch_all_urls: {str(e)}")
        from models import APIError  # Import here to avoid circular import
        raise APIError(f"Failed to fetch data: {str(e)}", 500)

def fetch_date_data_simple(api_url):
    """Simple synchronous function to fetch date data"""
    try:
        # Use high-quality headers for date requests
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://live20.nowgoal25.com/football/fixture',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'Cache-Control': 'public, max-age=5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            from models import APIError  # Import here to avoid circular import
            raise APIError(f"API returned status {response.status_code}")
        
        return response.text
            
    except Exception as e:
        logger.error(f"Failed to fetch date data from {api_url}: {e}")
        from models import APIError  # Import here to avoid circular import
        raise APIError(f"Failed to fetch data: {str(e)}", 500)

# --- Request Header Utilities ---

def get_request_headers():
    """Get standard request headers for external API calls"""
    return {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.9',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://live20.nowgoal25.com/'
    }

# --- Cleanup Functions ---

async def cleanup_session():
    """Cleanup function for global session"""
    global global_session
    if global_session and not global_session.closed:
        try:
            logger.info("Closing global HTTP session...")
            await global_session.close()
        except Exception as e:
            logger.warning(f"Error closing session: {str(e)}")
        finally:
            global_session = None

def register_cleanup():
    """Register cleanup function for app shutdown"""
    import atexit
    
    def cleanup():
        asyncio.run(cleanup_session())
    
    atexit.register(cleanup)
