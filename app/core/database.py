from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

settings = get_settings()

# Construct Database URL
def get_database_url():
    """Construct database URL from environment variables."""
    try:
        return (
            f"postgresql+psycopg2://"
            f"{settings.DB_USER}:{settings.DB_PASSWORD}@"
            f"{settings.DB_HOST}:{settings.DB_PORT}/"
            f"{settings.DB_NAME}"
        )
    
    except AttributeError:
        # Fallback to full DATABASE_URL if individual settings are not available
        return settings.DATABASE_URL
    
    
engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    """
    Get database session.
    
    Yields:
        Session: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()