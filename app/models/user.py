from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List
import uuid
from app.core.database import Base

class User(Base):
    """
    User model for database representation.
    
    Attributes:
        id: Unique identifier
        email: User's email address
        password_hash: Hashed password
        is_verified: Email verification status
        verification_token: Token for email verification
        token_expiry: Expiration time for verification token
        created_at: Account creation timestamp
        refresh_tokens: Related refresh tokens
        tasks: Related tasks
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), unique=True)
    token_expiry = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")

class RefreshToken(Base):
    """
    RefreshToken model for database representation.
    
    Attributes:
        id: Unique identifier
        token: Refresh token string
        expires_at: Token expiration timestamp
        user_id: Related user ID
        created_at: Token creation timestamp
    """
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True)
    token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="refresh_tokens")


class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"

    id = Column(Integer, primary_key=True)
    token = Column(String(255), unique=True, nullable=False)
    blacklisted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)