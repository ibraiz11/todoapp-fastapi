import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.todo import Task
from app.core.security import SecurityService

def init_db() -> None:
    """Initialize database with tables and test user."""
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        db = SessionLocal()
        
        # Check if test user exists
        test_email = "test@example.com"
        if db.query(User).filter(User.email == test_email).first():
            print(f"Test user {test_email} already exists")
            return
        
        # Create test user
        test_user = User(
            email=test_email,
            password_hash=SecurityService.get_password_hash("Test123!@#"),
            is_verified=True,
            verification_token="test_token",
            token_expiry=datetime.utcnow()
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print(f"Created test user: {test_email}")
        print("Password: Test123!@#")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialization completed")