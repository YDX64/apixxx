"""
Security utilities and authentication decorators
"""
import jwt
import time
import random
import hashlib
from collections import defaultdict, deque
from functools import wraps
from flask import request, jsonify, current_app, g
import logging

logger = logging.getLogger(__name__)

# --- Authentication Decorators ---

def require_auth(f):
    """JWT Token authentication decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Bearer Token kontrolü
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # "Bearer TOKEN"
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        # API Key kontrolü (alternatif)
        if not token:
            token = request.headers.get('X-API-Key')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # JWT doğrulama
            payload = jwt.decode(
                token, 
                current_app.config['JWT_SECRET_KEY'], 
                algorithms=['HS256']
            )
            current_user = payload.get('user_id')
            g.current_user = current_user
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated_function


def require_api_key(f):
    """API Key authentication decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'API key is required'}), 401
        
        # API key kontrolü
        if api_key != current_app.config['API_SECRET_KEY']:
            return jsonify({'error': 'Invalid API key'}), 403
        
        g.api_authenticated = True
        return f(*args, **kwargs)
    
    return decorated_function


# --- Rate Limiting Classes ---

class AdvancedRateLimit:
    """Advanced rate limiting with IP blocking"""
    
    def __init__(self):
        self.requests = defaultdict(deque)
        self.blocked_ips = {}
    
    def is_allowed(self, ip, limit=60, window=3600):  # 60 req/hour default
        now = time.time()
        
        # Blocked IP kontrolü
        if ip in self.blocked_ips:
            if now - self.blocked_ips[ip] < 3600:  # 1 saat block
                return False
            else:
                del self.blocked_ips[ip]
        
        # Request geçmişini temizle
        while self.requests[ip] and now - self.requests[ip][0] > window:
            self.requests[ip].popleft()
        
        # Limit kontrolü
        if len(self.requests[ip]) >= limit:
            self.blocked_ips[ip] = now  # IP'yi blokla
            logger.warning(f"IP {ip} blocked due to rate limit exceeded")
            return False
        
        self.requests[ip].append(now)
        return True


# --- Request Quality Manager ---

class RequestQualityManager:
    """Professional request headers and quality management"""
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]
        
        self.referers = [
            'https://www.google.com/',
            'https://www.bing.com/',
            'https://duckduckgo.com/',
            'https://yandex.com/',
            'https://www.yahoo.com/'
        ]
    
    def get_quality_headers(self):
        """Kaliteli ve gerçekçi HTTP headers üret"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'Referer': random.choice(self.referers)
        }
    
    def add_random_delay(self, min_delay=1, max_delay=3):
        """İstekler arası rastgele gecikme"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
        return delay


# --- Security Utilities ---

def get_real_ip():
    """Get real client IP address"""
    # Check for various proxy headers
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    elif request.headers.get('CF-Connecting-IP'):  # Cloudflare
        return request.headers.get('CF-Connecting-IP')
    else:
        return request.remote_addr


def generate_api_token(user_id, expires_in=3600):
    """Generate JWT token for user"""
    payload = {
        'user_id': user_id,
        'exp': time.time() + expires_in,
        'iat': time.time()
    }
    
    token = jwt.encode(
        payload, 
        current_app.config['JWT_SECRET_KEY'], 
        algorithm='HS256'
    )
    
    return token


def hash_api_key(api_key):
    """Hash API key for secure storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def validate_request_signature(request_data, signature, secret_key):
    """Validate request signature for webhook security"""
    expected_signature = hashlib.sha256(
        (request_data + secret_key).encode()
    ).hexdigest()
    
    return signature == expected_signature


# --- Security Middleware ---

class SecurityMiddleware:
    """Security middleware for request validation"""
    
    def __init__(self, app=None):
        self.app = app
        self.rate_limiter = AdvancedRateLimit()
        self.quality_manager = RequestQualityManager()
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize middleware with Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Execute before each request"""
        client_ip = get_real_ip()
        
        # Rate limiting kontrolü
        if not self.rate_limiter.is_allowed(client_ip):
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        # Security headers validation
        self._validate_security_headers()
        
        # Log security info
        g.start_time = time.time()
        g.client_ip = client_ip
    
    def after_request(self, response):
        """Execute after each request"""
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Add API version header
        response.headers['X-API-Version'] = current_app.config.get('API_VERSION', '1.0.0')
        
        return response
    
    def _validate_security_headers(self):
        """Validate important security headers"""
        suspicious_headers = [
            'X-Forwarded-Host',
            'X-Original-URL',
            'X-Rewrite-URL'
        ]
        
        for header in suspicious_headers:
            if request.headers.get(header):
                logger.warning(f"Suspicious header detected: {header} from {get_real_ip()}")


# --- Global instances ---
rate_limiter = AdvancedRateLimit()
quality_manager = RequestQualityManager()
security_middleware = SecurityMiddleware()
