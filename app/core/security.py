from datetime import datetime, timedelta
import bcrypt
from jose import jwt, JWTError
from typing import Optional
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import secrets
from .logging import setup_logger
from app.core.config import get_settings

logger = setup_logger(__name__)
settings = get_settings()

class Token(BaseModel):
    """
    Token schema for authentication responses.
    
    Attributes:
        access_token: JWT access token
        token_type: Token type (bearer)
    """
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """
    Token data schema for decoded tokens.
    
    Attributes:
        email: User email from token
    """
    email: Optional[str] = None

class SecurityService:
    """Service for handling security-related operations."""

    """Service for handling security-related operations."""
    
    @staticmethod
    def generate_verification_token() -> str:
        """
        Generate a secure verification token.
        
        Returns:
            str: Random verification token
        """
        try:
            # Generate a 32-byte random token and convert to hex
            return secrets.token_urlsafe(32)
        except Exception as e:
            logger.error(f"Error generating verification token: {str(e)}")
            raise
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """
        Generate password hash using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        try:
            salt = bcrypt.gensalt()
            return bcrypt.hashpw(password.encode(), salt).decode()
        except Exception as e:
            logger.error(f"Error hashing password: {str(e)}")
            raise

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash using bcrypt.
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to check against
            
        Returns:
            bool: True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode(), 
                hashed_password.encode()
            )
        except Exception as e:
            logger.error(f"Error verifying password: {str(e)}")
            return False
        
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token.
        
        Args:
            data: Data to encode in token
            expires_delta: Token expiration time
            
        Returns:
            str: Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
            
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
    
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> dict:
        """
        Decode and verify JWT token.
        
        Args:
            token: JWT token to decode
            
        Returns:
            dict: Decoded token payload
            
        Raises:
            JWTError: If token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError as e:
            logger.error(f"Error decoding token: {str(e)}")
            raise

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")