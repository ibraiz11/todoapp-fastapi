from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import RefreshToken, BlacklistedToken
from app.core.security import SecurityService
from app.core.config import get_settings
from app.core.logging import setup_logger

logger = setup_logger(__name__)
settings = get_settings()

class TokenService:
    """Service for handling token operations."""

    @staticmethod
    async def validate_access_token(token: str, db: Session) -> bool:
        """Check if access token is valid and not blacklisted."""
        try:
            # Check if token is blacklisted
            blacklisted = db.query(BlacklistedToken).filter(
                BlacklistedToken.token == token,
                BlacklistedToken.expires_at > datetime.utcnow()
            ).first()
            
            if blacklisted:
                return False

            # Verify token signature and expiration
            payload = SecurityService.decode_token(token)
            return True if payload else False

        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return False

    @staticmethod
    async def validate_refresh_token(token: str, db: Session) -> bool:
        """Check if refresh token is valid and not revoked."""
        try:
            refresh_token = db.query(RefreshToken).filter(
                RefreshToken.token == token,
                RefreshToken.expires_at > datetime.utcnow(),
                RefreshToken.is_revoked == False
            ).first()
            
            return bool(refresh_token)

        except Exception as e:
            logger.error(f"Refresh token validation error: {str(e)}")
            return False

    @staticmethod
    async def revoke_all_user_tokens(user_id: int, db: Session) -> None:
        """Revoke all tokens for a user (useful for logout or security breach)."""
        try:
            # Revoke refresh tokens
            db.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False
            ).update({
                "is_revoked": True,
                "revoked_at": datetime.utcnow()
            })

            db.commit()
        except Exception as e:
            logger.error(f"Error revoking user tokens: {str(e)}")
            db.rollback()
            raise

    @staticmethod
    async def cleanup_expired_tokens(db: Session) -> None:
        """Clean up expired tokens from database."""
        try:
            now = datetime.utcnow()
            
            # Delete expired refresh tokens
            db.query(RefreshToken).filter(
                RefreshToken.expires_at < now
            ).delete()
            
            # Delete expired blacklisted tokens
            db.query(BlacklistedToken).filter(
                BlacklistedToken.expires_at < now
            ).delete()
            
            db.commit()
        except Exception as e:
            logger.error(f"Error cleaning up tokens: {str(e)}")
            db.rollback()