"""
Application configuration settings
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Security Configuration
    API_SECRET_KEY = os.getenv('API_SECRET_KEY', 'your-super-secret-api-key-change-in-production')
    API_RATE_LIMIT = os.getenv('API_RATE_LIMIT', '100 per hour')
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*').split(',')
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))  # 1 hour
    
    # Rate Limiting & Security
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
    ENABLE_CORS = os.getenv('ENABLE_CORS', 'true').lower() == 'true'
    
    # Cache Configuration
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')
    
    # API Configuration
    API_VERSION = os.getenv('API_VERSION', '1.0.0')
    MAX_CONNECTIONS = int(os.getenv('MAX_CONNECTIONS', 20))
    CONNECTION_TIMEOUT = int(os.getenv('CONNECTION_TIMEOUT', 30))

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FLASK_ENV = 'production'
    
    # Production-specific settings
    CACHE_TYPE = 'filesystem'
    CACHE_DIR = '/tmp/flask_cache'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    CACHE_TYPE = 'null'  # Disable cache for testing

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
