from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from typing import List
from app.core.config import get_settings
from app.core.logging import setup_logger
from pathlib import Path
logger = setup_logger(__name__)
settings = get_settings()

templates_dir = Path("app/email-templates")
templates_dir.mkdir(parents=True, exist_ok=True)

conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.EMAILS_FROM_EMAIL,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    TEMPLATE_FOLDER=str(templates_dir)
)

class EmailService:
    """Service for handling email operations."""
    
    @staticmethod
    async def send_verification_email(email: str, token: str) -> None:
        """
        Send verification email to user.
        
        Args:
            email: Recipient email address
            token: Verification token
        """
        try:
            verification_url = f"{settings.BASE_URL}{settings.API_V1_STR}/auth/verify/{token}"
            
            message = MessageSchema(
                subject="Verify your email",
                recipients=[email],
                body=f"""
                <h1>Email Verification</h1>
                <p>Please click the link below to verify your email:</p>
                <p><a href="{verification_url}">{verification_url}</a></p>
                <p>This link will expire in 24 hours.</p>
                """,
                subtype="html"
            )

            fm = FastMail(conf)
            await fm.send_message(message)
            logger.info(f"Verification email sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {str(e)}")
            raise