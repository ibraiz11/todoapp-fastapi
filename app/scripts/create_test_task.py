import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.todo import Task

def create_test_task() -> None:
    """Create a test task for the test user."""
    try:
        db = SessionLocal()
        
        # Get test user
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            print("Test user not found!")
            return
            
        # Create test task
        test_task = Task(
            title="Test Task",
            description="This is a test task",
            due_date=datetime.utcnow() + timedelta(days=7),
            user_id=test_user.id
        )
        
        db.add(test_task)
        db.commit()
        
        print(f"Created test task for user {test_user.email}")
        
    except Exception as e:
        print(f"Error creating test task: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_test_task()