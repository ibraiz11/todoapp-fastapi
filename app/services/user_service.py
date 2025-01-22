from datetime import datetime, timedelta
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Dict, Optional
from app.models.user import User, RefreshToken
from app.schemas.user import UserCreate
from app.core.security import SecurityService
from app.core.logging import setup_logger
from app.core.config import get_settings

logger = setup_logger(__name__)
settings = get_settings()

class UserService:
    """Service for handling user-related operations."""
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """
        Create a new user.
        
        Args:
            db: Database session
            user_data: User creation data
            
        Returns:
            User: Created user instance
            
        Raises:
            HTTPException: If email is already registered
        """
        try:
            if db.query(User).filter(User.email == user_data.email).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            
            db_user = User(
                email=user_data.email,
                password_hash=SecurityService.get_password_hash(user_data.password),
                verification_token=SecurityService.generate_verification_token(),
                token_expiry=datetime.utcnow() + timedelta(hours=24)
            )
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            logger.info(f"Created new user: {user_data.email}")
            return db_user
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise

    @staticmethod
    def authenticate_user(
        db: Session,
        email: str,
        password: str
    ) -> Optional[User]:
        """
        Authenticate a user.
        
        Args:
            db: Database session
            email: User email
            password: Plain text password
            
        Returns:
            Optional[User]: Authenticated user or None
        """
        try:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return None
            if not SecurityService.verify_password(password, user.password_hash):
                return None
            return user
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            return None
        
    @staticmethod
    def verify_email(db: Session, token: str) -> bool:
        """
        Verify user email with token.
        
        Args:
            db: Database session
            token: Verification token
            
        Returns:
            bool: True if verification successful, False otherwise
        """
        try:
            # Find user with matching token
            user = db.query(User).filter(
                User.verification_token == token,
                User.is_verified == False
            ).first()
            
            if not user:
                logger.warning(f"Invalid verification token: {token}")
                return False
            
            # Check if token is expired
            if user.token_expiry and user.token_expiry < datetime.utcnow():
                logger.warning(f"Expired verification token for user: {user.email}")
                return False
            
            # Update user verification status
            user.is_verified = True
            user.verification_token = None  # Clear the used token
            user.token_expiry = None
            
            db.commit()
            logger.info(f"Email verified successfully for user: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error during email verification: {str(e)}")
            db.rollback()
            return False
        
    
    @staticmethod
    def create_user_token(db: Session, user: User) -> Dict[str, str]:
        """
        Create access and refresh tokens for user.
        
        Args:
            db: Database session
            user: User instance
            
        Returns:
            Dict[str, str]: Dictionary containing access and refresh tokens
            
        Raises:
            HTTPException: If token creation fails
        """
        try:
            # Create access token
            access_token = SecurityService.create_access_token(
                data={"sub": user.email},
                expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            )
            
            # Create refresh token
            refresh_token_str = str(uuid.uuid4())
            refresh_token = RefreshToken(
                token=refresh_token_str,
                user_id=user.id,
                expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            )
            
            # Clean up old refresh tokens
            db.query(RefreshToken).filter(
                RefreshToken.user_id == user.id,
                RefreshToken.expires_at < datetime.utcnow()
            ).delete()
            
            # Save new refresh token
            db.add(refresh_token)
            db.commit()
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "refresh_token": refresh_token_str
            }
            
        except Exception as e:
            logger.error(f"Error creating user tokens: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create authentication tokens"
            )