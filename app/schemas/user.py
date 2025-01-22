from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from app.utils.validators import ValidationUtils

class UserBase(BaseModel):
    """Base user schema with common attributes."""
    email: EmailStr = Field(..., description="User email address")

class UserCreate(UserBase):
    """
    Schema for user creation requests.
    
    Attributes:
        email: User's email address
        password: Plain text password
        confirm_password: Password confirmation
    """
    password: str = Field(
        ...,
        min_length=8,
        max_length=64,
        description="User password (8-64 characters)"
    )
    confirm_password: str = Field(..., description="Password confirmation")

    @validator('password')
    def validate_password(cls, v: str) -> str:
        if error := ValidationUtils.validate_password_strength(v):
            raise ValueError(error)
        return v

    @validator('confirm_password')
    def passwords_match(cls, v: str, values: dict) -> str:
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class UserResponse(UserBase):
    """
    Schema for user response data.
    
    Attributes:
        id: User ID
        is_verified: Email verification status
        created_at: Account creation timestamp
    """
    id: int
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True