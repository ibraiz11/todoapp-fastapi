import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy import inspect
from app.core.database import engine, SessionLocal
from app.models.user import User
from app.models.todo import Task, TaskAttachment

def check_db() -> None:
    """Check database configuration and contents."""
    try:
        # Check connection
        print("Checking database connection...")
        conn = engine.connect()
        conn.close()
        print("Database connection successful!")
        
        # Check tables
        print("\nChecking database tables...")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Found tables: {', '.join(tables)}")
        
        # Check users
        db = SessionLocal()
        try:
            users = db.query(User).all()
            print(f"\nFound {len(users)} users:")
            for user in users:
                tasks_count = db.query(Task).filter(Task.user_id == user.id).count()
                print(f"- {user.email} (ID: {user.id}, Tasks: {tasks_count})")
        finally:
            db.close()
            
    except Exception as e:
        print(f"Error checking database: {e}")
        raise

if __name__ == "__main__":
    check_db()