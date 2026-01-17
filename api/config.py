from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "SA Compliance API"
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # Will add these later when you get CIPC API access
    CIPC_API_KEY: str = ""
    CIPC_API_URL: str = "https://eservices.cipc.co.za"
    
    # Rate limiting
    MAX_REQUESTS_PER_HOUR: int = 100
    
    # Cache settings (in-memory for now)
    CACHE_TTL_DAYS: int = 90
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()