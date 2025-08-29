
import json
import os
import re
import asyncio
import aiohttp
import time
import logging
import random
from datetime import datetime
from functools import wraps
from flask import Flask, jsonify, request, g
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from marshmallow import Schema, fields, ValidationError
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Import security modules
from config import config
from security import (
    require_auth, 
    require_api_key, 
    rate_limiter, 
    quality_manager,
    security_middleware,
    get_real_ip
)
from parsers import (
    MatchDateParser,
    parse_player_list,
    parse_standings_table,
    parse_match_list_table,
    parse_standings,
    parse_injury_suspension,
    parse_last_match_lineups,
    parse_fixture,
    parse_match_info,
    parse_h2h_details,
    parse_first_half_odds,
    debug_table_structure
)
from http_client import (
    get_global_session,
    fetch_url,
    fetch_all_urls,
    fetch_date_data_simple,
    get_request_headers,
    cleanup_session
)
from models import (
    APIError,
    MatchRequestSchema,
    validate_match_id,
    validate_date_string,
    build_success_response,
    build_error_response
)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Load configuration
env = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[env])

# Configuration from environment
app.config['CACHE_TYPE'] = app.config.get('CACHE_TYPE', 'simple')
app.config['CACHE_DEFAULT_TIMEOUT'] = app.config.get('CACHE_DEFAULT_TIMEOUT', 300)

# Initialize extensions
cache = Cache(app)

# CORS Configuration
if app.config.get('ENABLE_CORS', True):
    CORS(app, origins=app.config.get('ALLOWED_ORIGINS', ['*']))

# Rate Limiter
limiter = Limiter(
    key_func=get_real_ip,  # Use our custom IP function
    default_limits=[app.config.get('API_RATE_LIMIT', "100 per hour")]
)
limiter.init_app(app)

# Initialize security middleware
security_middleware.init_app(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global session now managed in http_client.py

# --- Validation Schemas and Error Classes moved to models.py ---

# Parser instance (imported from parsers.py)
date_parser = MatchDateParser()

@app.errorhandler(APIError)
def handle_api_error(error):
    logger.error(f"API Error: {error.message}")
    response = {'error': error.message}
    if error.payload:
        response.update(error.payload)
    return jsonify(response), error.status_code

@app.errorhandler(ValidationError)
def handle_validation_error(error):
    logger.error(f"Validation Error: {error.messages}")
    return jsonify({'error': 'Validation failed', 'details': error.messages}), 400

@app.errorhandler(429)
def handle_rate_limit(error):
    logger.warning(f"Rate limit exceeded from {request.remote_addr}")
    return jsonify({'error': 'Rate limit exceeded', 'message': str(error)}), 429

@app.errorhandler(500)
def handle_internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

# --- Decorators ---

def log_requests(f):
    """Decorator to log requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.start_time = time.time()
        logger.info(f"Request started: {request.method} {request.path} from {request.remote_addr}")
        
        try:
            response = f(*args, **kwargs)
            duration = time.time() - g.start_time
            logger.info(f"Request completed: {request.path} in {duration:.2f}s")
            return response
        except Exception as e:
            duration = time.time() - g.start_time
            logger.error(f"Request failed: {request.path} in {duration:.2f}s - Error: {str(e)}")
            raise
    return decorated_function

def validate_json(schema_class):
    """Decorator to validate JSON input"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            schema = schema_class()
            try:
                data = schema.load(request.get_json() or {})
                request.validated_data = data
                return f(*args, **kwargs)
            except ValidationError as err:
                raise APIError('Validation failed', 400, {'details': err.messages})
        return decorated_function
    return decorator

# --- Utility Functions moved to http_client.py ---

# --- Health Check Endpoints ---

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@app.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """Detailed health check"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'cache': 'operational',
        'session': 'managed by http_client'
    }
    
    # Test cache
    try:
        cache.set('health_test', 'ok', timeout=5)
        cache_test = cache.get('health_test')
        if cache_test != 'ok':
            health_status['cache'] = 'error'
            health_status['status'] = 'degraded'
    except Exception as e:
        health_status['cache'] = f'error: {str(e)}'
        health_status['status'] = 'degraded'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code

# --- Async HTTP Functions moved to http_client.py ---

# --- Main API Route ---

# --- Cached Data Fetching Functions ---

@cache.memoize(timeout=300)  # Cache for 5 minutes
def fetch_match_data_cached(match_id):
    """Cached version of match data fetching"""
    return fetch_match_data_sync(match_id)

def fetch_match_data_sync(match_id):
    """Synchronous wrapper for async match data fetching"""
    # Validate match_id
    if not isinstance(match_id, int) or match_id <= 0:
        raise APIError("Invalid match ID", 400)
    
    # Define URLs
    urls = {
        "h2h_details": f"https://live20.nowgoal25.com/match/h2h-{match_id}",
        "ah_odds": f"https://live20.nowgoal25.com/ajax/soccerajax?type=14&t=2&id={match_id}",
        "corner_odds": f"https://live20.nowgoal25.com/ajax/soccerajax?type=14&t=4&id={match_id}",
        "correct_score_odds": f"https://live20.nowgoal25.com/ajax/soccerajax?type=14&t=5&id={match_id}",
        "double_chance_odds": f"https://live20.nowgoal25.com/ajax/soccerajax?type=14&t=7&id={match_id}",
        "odds_comp": f"https://live20.nowgoal25.com/ajax/soccerajax?type=14&t=1&id={match_id}",
        "over_under_odds": f"https://live20.nowgoal25.com/ajax/soccerajax?type=14&t=3&id={match_id}",
        "first_half_odds": f"https://live20.nowgoal25.com/ajax/soccerajax?type=14&t=1&id={match_id}&h=1&s=0&flesh={random.random()}"
    }

    # Güvenli event loop yönetimi
    loop = None
    try:
        # Mevcut event loop'u kontrol et
        try:
            loop = asyncio.get_event_loop()
            # Eğer loop kapalıysa yeni bir tane oluştur
            if loop.is_closed():
                loop = None
        except RuntimeError:
            # Thread'de event loop yoksa yeni oluştur
            loop = None
        
        # Yeni loop gerekiyorsa oluştur
        if loop is None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        logger.info(f"Fetching match data for match_id: {match_id}")
        results = loop.run_until_complete(fetch_all_urls(urls))
        
        data = {
            'match_id': match_id,
            'timestamp': datetime.utcnow().isoformat(),
            'fetch_times': {},
            'cached': False
        }
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                # Handle exceptions from asyncio.gather
                logger.error(f"Exception in result: {str(result)}")
                data['general_error'] = {"error": f"Request failed with exception: {str(result)}"}
                continue
                
            key, content, content_type, fetch_time = result
            data['fetch_times'][key] = fetch_time
            
            if content_type == 'error':
                data[key] = content
            elif content_type == 'html' and key == 'h2h_details':
                try:
                    soup = BeautifulSoup(content, 'lxml')
                    data['match_info'] = parse_match_info(soup)
                    data['fixture'] = parse_fixture(soup)
                    data['h2h_details'] = parse_h2h_details(soup)
                except Exception as e:
                    logger.error(f"Error parsing HTML for {key}: {str(e)}")
                    data[key] = {"error": f"Failed to parse HTML: {str(e)}"}
            elif content_type == 'json':
                if key == 'first_half_odds':
                    # Parse first half odds with custom parser
                    data[key] = parse_first_half_odds(content)
                else:
                    data[key] = content
            else:
                data[key] = {"error": f"Unknown content type: {content_type}"}
        
        total_fetch_time = sum(data['fetch_times'].values())
        logger.info(f"Completed fetching match {match_id} in {total_fetch_time:.2f}s total")
        
        return data
                
    except Exception as e:
        logger.error(f"Failed to fetch match data for {match_id}: {str(e)}")
        raise APIError(f"Failed to fetch match data: {str(e)}", 500)
    finally:
        # Loop'u sadece bizim oluşturduğumuz durumda kapat
        if loop and not loop.is_closed():
            try:
                # Pending task'ları temizle
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                
                # Task'ların tamamlanmasını bekle
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                
                # Session'ı temizle
                loop.run_until_complete(cleanup_session())
                
            except Exception as cleanup_error:
                logger.warning(f"Error during loop cleanup: {str(cleanup_error)}")
            finally:
                # Loop'u kapat
                try:
                    loop.close()
                except Exception as close_error:
                    logger.warning(f"Error closing loop: {str(close_error)}")

# --- Authentication Endpoints ---

@app.route('/api/v1/auth/token', methods=['POST'])
@limiter.limit("5 per minute")
@log_requests
def generate_token():
    """Generate JWT token for authentication"""
    from security import generate_api_token
    
    data = request.get_json() or {}
    api_key = data.get('api_key') or request.headers.get('X-API-Key')
    
    if not api_key:
        return jsonify({'error': 'API key is required'}), 400
    
    # Validate API key
    if api_key != app.config['API_SECRET_KEY']:
        return jsonify({'error': 'Invalid API key'}), 403
    
    # Generate token for the API key holder
    user_id = f"api_user_{hash(api_key) % 10000}"
    token = generate_api_token(user_id, app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    
    return jsonify({
        'access_token': token,
        'token_type': 'Bearer',
        'expires_in': app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600)
    })

# --- Main API Routes ---

@app.route('/api/v1/match/<int:match_id>', methods=['GET'])
@limiter.limit("10 per minute")  # Rate limiting
@log_requests
def get_match_details(match_id):
    """
    Get comprehensive match details including odds, team info, and statistics.
    
    Args:
        match_id (int): The unique identifier for the match
        
    Returns:
        JSON response with match details or error
    """
    try:
        # Check cache first
        cache_key = f"match_data_{match_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Cache hit for match {match_id}")
            cached_data['cached'] = True
            cached_data['cache_timestamp'] = datetime.utcnow().isoformat()
            return jsonify(cached_data)
        
        # Fetch fresh data
        logger.info(f"Cache miss for match {match_id}, fetching fresh data")
        data = fetch_match_data_cached(match_id)
        
        # Store in cache
        cache.set(cache_key, data, timeout=300)
        
        return jsonify(data)
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_match_details: {str(e)}")
        raise APIError("Internal server error", 500)

# Legacy endpoint for backward compatibility
@app.route('/match/<int:match_id>', methods=['GET'])
@limiter.limit("5 per minute")  # Lower rate limit for legacy endpoint
@log_requests
def get_match_details_legacy(match_id):
    """Legacy endpoint - redirects to new API"""
    logger.warning(f"Legacy endpoint used for match {match_id}")
    return get_match_details(match_id)

# --- Additional API Endpoints ---

@app.route('/api/v1/cache/clear', methods=['DELETE'])
@limiter.limit("1 per minute")
@require_api_key  # Güvenli endpoint
def clear_cache():
    """Clear all cache entries (for debugging)"""
    try:
        cache.clear()
        logger.info("Cache cleared manually")
        return jsonify({'message': 'Cache cleared successfully'})
    except Exception as e:
        logger.error(f"Failed to clear cache: {str(e)}")
        raise APIError("Failed to clear cache", 500)

@app.route('/api/v1/cache/stats', methods=['GET'])
def cache_stats():
    """Get cache statistics"""
    # Note: Flask-Caching simple backend doesn't provide detailed stats
    # This is a placeholder for future implementation
    return jsonify({
        'cache_type': app.config['CACHE_TYPE'],
        'default_timeout': app.config['CACHE_DEFAULT_TIMEOUT'],
        'message': 'Detailed cache stats not available with simple cache backend'
    })

# --- New Date-based Match Endpoints ---

@app.route('/api/v1/matches/date/<date_str>')
@limiter.limit("20 per minute")
@log_requests
def get_matches_by_date(date_str):
    """Tarih bazlı maç listesi"""
    try:
        # Tarih format kontrolü: YYYY-MM-DD
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Cache kontrolü
        cache_key = f"matches_date_{date_str}"
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for date {date_str}")
            return jsonify(cached_data)
        
        logger.info(f"Cache miss for date {date_str}, fetching fresh data")
        
        # API URL'sini oluştur
        formatted_date = f"{date_obj.year}-{date_obj.month}-{date_obj.day}"
        api_url = f"https://live20.nowgoal25.com/ajax/SoccerAjax?type=6&date={formatted_date}&order=league&timezone=3&flesh={random.random()}"
        
        # Veri çek (synchronous requests)
        response_text = fetch_date_data_simple(api_url)
        
        # Parse et
        parsed_data = date_parser.parse_date_response(response_text)
        if not parsed_data:
            raise APIError("Failed to parse match data")
        
        # Sonuçları filtrele ve formatla
        matches = []
        for match in parsed_data['matches']:
            # Tarih filtresi geçici olarak kaldır - tüm maçları döndür
            # if match['match_time'] and match['match_time'].date() == date_obj.date():
            if match['match_time']:
                
                # Lig bilgisini ekle
                league_info = parsed_data['leagues'].get(match['league_id'], {})
                
                matches.append({
                    'match_id': match['match_id'],
                    'home_team': match['home_team'],
                    'away_team': match['away_team'],
                    'match_time': match['match_time'].isoformat() if match['match_time'] else None,
                    'league': {
                        'id': match['league_id'],
                        'name': league_info.get('league_name', 'Unknown'),
                        'code': league_info.get('league_code', '')
                    }
                })
        
        result = {
            'date': date_str,
            'match_count': len(matches),
            'matches': matches,
            'cached_at': datetime.now().isoformat()
        }
        
        # Cache'e kaydet (2 saat)
        cache.set(cache_key, result, timeout=7200)
        
        logger.info(f"Returning {len(matches)} matches for date {date_str}")
        return jsonify(result)
        
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except APIError as e:
        logger.error(f"API error for date {date_str}: {e}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error for date {date_str}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/matches/today')
@limiter.limit("30 per minute")
@log_requests
def get_todays_matches():
    """Bugünkü maçlar"""
    today = datetime.now().strftime('%Y-%m-%d')
    return get_matches_by_date(today)

@app.route('/api/v1/debug/table/<int:match_id>')
@limiter.limit("3 per minute")
def debug_table_data(match_id):
    """Debug endpoint to analyze table structure"""
    try:
        # Fetch match HTML data
        h2h_url = f"https://live20.nowgoal25.com/match/h2h-{match_id}"
        
        # Use requests for simple sync call
        import requests
        response = requests.get(h2h_url, headers=get_request_headers(), timeout=30)
        
        if response.status_code != 200:
            return jsonify({'error': f'Failed to fetch data, status: {response.status_code}'}), 500
        
        # Parse HTML
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Debug all relevant tables
        debug_results = {}
        table_ids = ['table_v1', 'table_v2', 'table_v3']
        
        for table_id in table_ids:
            debug_results[table_id] = debug_table_structure(soup, table_id)
        
        return jsonify({
            'match_id': match_id,
            'tables_debug': debug_results,
            'url_used': h2h_url
        })
        
    except Exception as e:
        logger.error(f"Debug error for match {match_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/debug/date/<date_str>')
@limiter.limit("5 per minute")
def debug_date_data(date_str):
    """Debug endpoint to see raw data"""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = f"{date_obj.year}-{date_obj.month}-{date_obj.day}"
        api_url = f"https://live20.nowgoal25.com/ajax/SoccerAjax?type=6&date={formatted_date}&order=league&timezone=3&flesh={random.random()}"
        
        response_text = fetch_date_data_simple(api_url)
        parsed_data = date_parser.parse_date_response(response_text)
        
        return jsonify({
            'api_url': api_url,
            'response_length': len(response_text),
            'response_preview': response_text[:500],
            'parsed_matches_count': len(parsed_data['matches']) if parsed_data else 0,
            'parsed_leagues_count': len(parsed_data['leagues']) if parsed_data else 0,
            'first_few_matches': parsed_data['matches'][:3] if parsed_data and parsed_data['matches'] else []
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# fetch_date_data_simple moved to http_client.py

# --- Application Lifecycle ---

@app.teardown_appcontext
def close_session(error):
    """Clean up session on request end"""
    if error:
        logger.error(f"Request ended with error: {str(error)}")

# Initialize logging on module load
logger.info("Application starting up...")

# Cleanup on app shutdown
import atexit

def cleanup():
    """Cleanup function for app shutdown"""
    logger.info("Cleaning up HTTP session...")
    asyncio.run(cleanup_session())

atexit.register(cleanup)

# --- Secure Premium Endpoints ---

@app.route('/api/v1/secure/match/<int:match_id>')
@limiter.limit("5 per minute")
@require_auth  # JWT authentication required
@log_requests
def secure_match_details(current_user, match_id):
    """Güvenli maç detayları endpoint'i - JWT token gerekli"""
    logger.info(f"Secure access by user: {current_user} for match: {match_id}")
    
    # Premium kullanıcı kontrolü (opsiyonel)
    # Burada kullanıcı tier'ı kontrol edilebilir
    
    return get_match_details(match_id)

@app.route('/api/v1/secure/matches/date/<date_str>')
@limiter.limit("10 per minute")
@require_api_key  # API Key required
@log_requests
def secure_matches_by_date(date_str):
    """Güvenli tarih bazlı maç listesi - API Key gerekli"""
    logger.info(f"Secure date access for: {date_str}")
    return get_matches_by_date(date_str)

@app.route('/api/v1/admin/stats')
@limiter.limit("2 per minute")
@require_auth  # JWT authentication required
@log_requests
def admin_stats(current_user):
    """Admin istatistikleri - yüksek yetki gerekli"""
    logger.info(f"Admin stats accessed by: {current_user}")
    
    # Rate limiter istatistikleri
    try:
        stats = {
            'timestamp': datetime.utcnow().isoformat(),
            'active_requests': len(rate_limiter.requests),
            'blocked_ips': len(rate_limiter.blocked_ips),
            'blocked_ips_list': list(rate_limiter.blocked_ips.keys()),
            'cache_type': app.config['CACHE_TYPE'],
            'api_version': app.config.get('API_VERSION', '1.0.0'),
            'security_enabled': True
        }
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Failed to get admin stats: {str(e)}")
        return jsonify({'error': 'Failed to get stats'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
