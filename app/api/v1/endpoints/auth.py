from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer
from sqlalchemy.orm import Session
from typing import Any, Dict
from datetime import datetime, timedelta
from app.api.deps import get_db, get_current_active_user
from app.core.security import SecurityService
from app.models.user import RefreshToken, User
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService
from app.services.email_service import EmailService
from app.services.token_service import TokenService
from app.core.database import get_db
from app.core.logging import setup_logger
from app.core.config import get_settings

logger = setup_logger(__name__)

router = APIRouter()

security = HTTPBearer()

settings = get_settings()

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    background_tasks: BackgroundTasks
) -> Any:
    """
    Create new user with email verification.
    """
    try:
        # Check if user exists
        if db.query(User).filter(User.email == user_in.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create user
        user = User(
            email=user_in.email,
            password_hash=SecurityService.get_password_hash(user_in.password),
            verification_token=SecurityService.generate_verification_token(),
            token_expiry=datetime.utcnow() + timedelta(hours=24),
            is_verified=False
        )

        try:
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Send verification email in background
            background_tasks.add_task(
                EmailService.send_verification_email,
                user.email,
                user.verification_token
            )
            
            logger.info(f"User created successfully: {user.email}")
            return user
            
        except Exception as e:
            db.rollback()
            logger.error(f"Database error during signup: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating user"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing signup"
        )

@router.post("/token")
async def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login.
    """
    try:
        user = UserService.authenticate_user(
            db, form_data.username, form_data.password
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email not verified"
            )
        
        return UserService.create_user_token(db, user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/verify/{token}")
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Verify user email.
    """
    try:
        if UserService.verify_email(db, token):
            return {"message": "Email verified successfully"}
        return {"message": "Invalid verification token"}
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification failed"
        )

@router.post("/refresh")
async def refresh_token(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: str = Cookie(None)
) -> Dict[str, str]:
    """Refresh access token using refresh token."""
    try:
        # Validate refresh token
        is_valid = await TokenService.validate_refresh_token(refresh_token, db)
        if not is_valid:
            raise HTTPException(
                status_code=401, 
                detail="Invalid refresh token"
            )

        # Get user from refresh token
        token_record = db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token
        ).first()
        user = token_record.user

        # Create new tokens
        tokens = UserService.create_user_token(db, user)

        # Set new refresh token cookie
        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh_token"],
            httponly=True,
            secure=settings.ENVIRONMENT == "production",
            samesite="strict",
            path="/api/v1/auth/refresh",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )

        return {
            "access_token": tokens["access_token"],
            "token_type": "bearer"
        }

    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Token refresh failed"
        )
    
async def verify_token(request: Request):
    """Verify access token in request."""
    if request.url.path in ["/api/v1/auth/login", "/api/v1/auth/signup"]:
        return
        
    try:
        auth = await security(request)
        token = auth.credentials
        db = next(get_db())
        
        is_valid = await TokenService.validate_access_token(token, db)
        if not is_valid:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
            
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication")