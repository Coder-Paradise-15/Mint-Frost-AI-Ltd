import os
from datetime import timedelta

class Config:
    """Application configuration class"""
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE = 10
    RATE_LIMIT_WINDOW = 60
    
    # OpenAI configuration
    OPENAI_MODEL = "gpt-4o-mini"
    OPENAI_MAX_TOKENS = 50000
    OPENAI_TEMPERATURE = 0.7
    
    # Chat configuration
    MAX_MESSAGE_LENGTH = 2000
    MAX_CHAT_HISTORY = 50
    CONTEXT_MESSAGES = 10

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'default': DevelopmentConfig
}