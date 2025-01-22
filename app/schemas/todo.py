from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from fastapi import UploadFile

class TaskBase(BaseModel):
    title: str = Field(..., max_length=100)
    description: Optional[str] = None
    due_date: Optional[datetime] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(TaskBase):
    is_completed: Optional[bool] = None

class TaskAttachmentResponse(BaseModel):
    id: int
    filename: str
    content_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class TaskResponse(TaskBase):
    id: int
    created_at: datetime
    is_completed: bool
    completed_at: Optional[datetime]
    attachments: List[TaskAttachmentResponse]

    class Config:
        from_attributes = True