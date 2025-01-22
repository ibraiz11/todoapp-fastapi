import re
from typing import Optional
from app.core.logging import setup_logger

logger = setup_logger(__name__)

class ValidationUtils:
    """Utility class for validation operations."""
    
    @staticmethod
    def validate_password_strength(password: str) -> Optional[str]:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            Optional[str]: Error message if validation fails, None otherwise
        """
        try:
            if len(password) < 8:
                return "Password must be at least 8 characters long"
            
            if not re.search(r"[A-Z]", password):
                return "Password must contain at least one uppercase letter"
                
            if not re.search(r"[a-z]", password):
                return "Password must contain at least one lowercase letter"
                
            if not re.search(r"\d", password):
                return "Password must contain at least one number"
                
            if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
                return "Password must contain at least one special character"
            
            return None
        except Exception as e:
            logger.error(f"Error validating password strength: {str(e)}")
            return "Password validation failed"