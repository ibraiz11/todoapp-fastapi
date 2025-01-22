from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os
from datetime import datetime

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.models.todo import Task, TaskAttachment
from app.schemas.todo import TaskCreate, TaskUpdate, TaskResponse
from app.core.config import get_settings
from app.core.logging import setup_logger

router = APIRouter()
logger = setup_logger(__name__)
settings = get_settings()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", response_model=TaskResponse)
async def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new task."""
    # Check task limit
    if db.query(Task).filter(Task.user_id == current_user.id).count() >= 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task limit reached (max 50 tasks)"
        )
    
    task = Task(**task_in.dict(), user_id=current_user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a task."""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_in.dict(exclude_unset=True)
    if task_in.is_completed and not task.is_completed:
        update_data["completed_at"] = datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    return task

@router.post("/{task_id}/attachments")
async def add_attachment(
    task_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add file attachment to task."""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    file_path = os.path.join(UPLOAD_DIR, f"{task_id}_{file.filename}")
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    attachment = TaskAttachment(
        filename=file.filename,
        file_path=file_path,
        content_type=file.content_type,
        task_id=task_id
    )
    
    db.add(attachment)
    db.commit()
    return {"filename": file.filename}

@router.get("/{task_id}/attachments/{attachment_id}")
async def download_attachment(
    task_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Download task attachment."""
    attachment = db.query(TaskAttachment).join(Task).filter(
        TaskAttachment.id == attachment_id,
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    return FileResponse(
        attachment.file_path,
        filename=attachment.filename,
        media_type=attachment.content_type
    )

@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a task."""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(task)
    db.commit()
    return {"message": "Task deleted"}