import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Any

# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)

# Configure logging format
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL: str = "INFO"

def setup_logger(name: str) -> logging.Logger:
    """
    Set up logger with file and console handlers.
    
    Args:
        name: Logger name
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    
    # File handler
    file_handler = RotatingFileHandler(
        f"logs/{name}.log",
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(console_handler)
    
    return logger

# Create main application logger
logger: logging.Logger = setup_logger("fastapi-todolist-app")