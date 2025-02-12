from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import AsyncGenerator

# Import database and models
from app.core.database import Base, engine
from app.models import user  # This ensures models are registered with SQLAlchemy

# Import routers, middleware, and config
from app.api.v1.endpoints.auth import router as auth_router
from app.utils.logging import logging_middleware
from app.utils.rate_limit import rate_limit_middleware
from app.core.config import get_settings
from app.core.logging import setup_logger
# from prometheus_fastapi_instrumentator import Instrumentator

# Set up logging
logger = setup_logger(__name__)
settings = get_settings()

# Lifespan event handler
@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator:
    """
    Lifespan event handler for FastAPI application.
    Handles startup and shutdown events.
    """
    try:
        # Create database tables on startup
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise
    finally:
        # Cleanup on shutdown
        logger.info("Shutting down application...")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:8000",
    # Add other allowed origins as needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
@app.middleware("http")
async def add_logging_middleware(request, call_next):
    return await logging_middleware(request, call_next)

@app.middleware("http")
async def add_rate_limit_middleware(request, call_next):
    return await rate_limit_middleware(request, call_next)

# Include routers
app.include_router(
    auth_router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["auth"]
)

from app.api.v1.endpoints import tasks

# Add to existing router includes
app.include_router(
    tasks.router,
    prefix=f"{settings.API_V1_STR}/tasks",
    tags=["tasks"]
)

# Health check endpoint
@app.get("/", tags=["health"])
async def health_check():
    """
    Root endpoint for health check.
    Returns basic API information.
    """
    try:
        return {
            "status": "healthy",
            "message": f"Welcome to {settings.PROJECT_NAME}",
            "version": settings.VERSION
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "message": "API is experiencing issues"
        }

# Development server configuration
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

# from fastapi import FastAPI

# app = FastAPI()

# def get_app_description():
#     return(
#         "Welcome to the Iris Species Prediction API!"
#     	"This API allows you to predict the species of an iris flower based on its sepal and petal measurements."
#     	"Use the '/predict/' endpoint with a POST request to make predictions."
#     	"Example usage: POST to '/predict/' with JSON data containing sepal_length, sepal_width, petal_length, and petal_width."
#     )

# @app.get("/")
# def read_root():
#     return {"message": get_app_description()}

# from sklearn.datasets import load_iris
# from sklearn.linear_model import LogisticRegression

# iris = load_iris()
# X = iris.data
# y = iris.target

# model = LogisticRegression(max_iter=1000)
# model.fit(X, y)

# def predict_iris_species(sepal_length, sepal_width, petal_length, petal_width):
#     features = [[sepal_length, sepal_width, petal_length, petal_width]]
#     prediction = model.predict(features)
#     return iris.target_names[prediction[0]]

# from pydantic import BaseModel

# class IrisData(BaseModel):
#     sepal_length: float
#     sepal_width: float
#     petal_length: float
#     petal_width: float

# @app.post("/predict/")
# async def predict_species_api(data: IrisData):
#     species = predict_iris_species(data.sepal_length, data.sepal_width, data.petal_length, data.petal_width)
#     return {"species": species}
