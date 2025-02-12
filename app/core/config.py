from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional, Dict, Any

class Settings(BaseSettings):
    """
    Application settings.
    
    Attributes:
        PROJECT_NAME: Fastapi Todo App
        VERSION: API version
        API_V1_STR: API version string for URL
        SECRET_KEY: Secret key for token generation
        DATABASE_URL: Database connection string
        EMAIL_TEMPLATES_DIR: Directory containing email templates
        EMAILS_FROM_EMAIL: Default sender email address
        EMAILS_FROM_NAME: Default sender name
        EMAIL_RESET_TOKEN_EXPIRE_HOURS: Hours until reset token expires
        EMAIL_TEMPLATES_DIR: Directory containing email templates
        SMTP_TLS: Enable TLS
        SMTP_PORT: SMTP port
        SMTP_HOST: SMTP host
        SMTP_USER: SMTP user
        SMTP_PASSWORD: SMTP password
        RATE_LIMIT_PER_MINUTE: Default rate limit per minute
    """
    
    PROJECT_NAME: str = "FastAPI Todo App"
    VERSION: str
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    SERVER_HOST: str
    SERVER_PORT: int = 8000
    DEBUG: bool = False
    
    # Environment
    ENVIRONMENT: str = "development"  # development, testing, production

    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int = 5432
    DB_NAME: str
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DATABASE_URL: Optional[str] = None
    
    # Email settings
    EMAILS_FROM_EMAIL: str
    EMAILS_FROM_NAME: str
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    EMAIL_TEMPLATES_DIR: str = "app/email-templates"
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    #JWT Settings
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Redis
    REDIS_URL: Optional[str] = None
    
    # AWS (for production)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: Optional[str] = None
    S3_BUCKET: Optional[str] = None

    # Metrics
    ENABLE_METRICS: bool = False
    
    @property
    def BASE_URL(self) -> str:
        """Get base URL based on environment."""
        if self.ENVIRONMENT == "production":
            return f"https://{self.SERVER_HOST}"
        elif self.ENVIRONMENT == "testing":
            return f"http://{self.SERVER_HOST}:{self.SERVER_PORT}"
        return f"http://localhost:{self.SERVER_PORT}"
    

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings: Application settings instance
    """
    return Settings()