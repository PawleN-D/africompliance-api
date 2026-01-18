from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    """Application settings and configuration"""
    
    # Application
    APP_NAME: str = "AfriCompliance SA API"
    VERSION: str = "1.0.0-pilot"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # API Configuration
    API_PREFIX: str = "/v1"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    
    # POPIA Compliance
    INFORMATION_OFFICER_NAME: str = "Compliance Officer"
    INFORMATION_OFFICER_EMAIL: str = "compliance@africompliance.co.za"
    INFORMATION_OFFICER_REG_NUMBER: str = "Pending"
    DATA_RETENTION_DAYS: int = 90
    ENABLE_AUDIT_LOGGING: bool = True
    ENABLE_PII_MASKING: bool = True
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    MAX_REQUESTS_PER_HOUR: int = 100  # Alias for compatibility
    RATE_LIMIT_WINDOW_SECONDS: int = 3600
    
    # CIPC API (for production)
    CIPC_API_KEY: Optional[str] = None
    CIPC_API_URL: str = "https://eservices.cipc.co.za"
    CIPC_TIMEOUT_SECONDS: int = 10
    
    # Cache Settings
    CACHE_TTL_SECONDS: int = 7776000  # 90 days
    ENABLE_CACHING: bool = True
    
    # Sanctions Screening
    SANCTIONS_CHECK_ENABLED: bool = True
    
    # Monitoring
    ENABLE_HEALTH_CHECK: bool = True
    
    # Pilot Features
    PILOT_FEEDBACK_WEBHOOK: Optional[str] = None
    ENABLE_PILOT_FEATURES: bool = True
    
    # Security
    ALLOWED_ORIGINS: list = ["*"]
    API_KEY_HEADER: str = "X-API-Key"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        # Important for Vercel
        extra = "ignore"  # Ignore extra env vars from Vercel

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()