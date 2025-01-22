from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Task(Base):
    """
    Task model for todo list items.
    
    Attributes:
        id: Unique identifier
        title: Task title
        description: Task description
        created_at: Task creation timestamp
        due_date: Task due date
        is_completed: Task completion status
        completed_at: Task completion timestamp
        user_id: Owner user ID
        attachments: Related file attachments
    """
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    user = relationship("User", back_populates="tasks")
    attachments = relationship("TaskAttachment", back_populates="task", cascade="all, delete-orphan")

class TaskAttachment(Base):
    """
    TaskAttachment model for file attachments.
    
    Attributes:
        id: Unique identifier
        filename: Original filename
        file_path: Path to stored file
        content_type: File MIME type
        created_at: Upload timestamp
        task_id: Related task ID
    """
    __tablename__ = "task_attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    
    task = relationship("Task", back_populates="attachments")