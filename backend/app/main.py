"""
Aplicación principal FastAPI para el ElSol Challenge.

Este es el punto de entrada para el servicio de transcripción de audio.
Configura la aplicación FastAPI, incluye routers y configura middleware.
"""

import os
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
#from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from app.core.config import get_settings, create_upload_dir, create_chroma_dir
from app.database.connection import create_database, check_database_connection
from app.api import health, upload, vector, chat
from app.core.schemas import ErrorResponse


# Configurar logging estructurado
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestor de contexto del ciclo de vida de la aplicación.
    Maneja eventos de inicio y cierre.
    """
    # Inicio
    logger.info("Starting ElSol Challenge application")
    
    settings = get_settings()
    
    # Create necessary directories
    create_upload_dir()
    logger.info("Upload directory created", path=settings.UPLOAD_TEMP_DIR)
    
    create_chroma_dir()
    logger.info("Chroma directory created", path=settings.CHROMA_PERSIST_DIRECTORY)
    
    # Initialize database
    try:
        create_database()
        if check_database_connection():
            logger.info("Database connection established")
        else:
            logger.error("Database connection failed")
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
    
    # Initialize vector store
    try:
        from app.services.vector_service import get_vector_service
        vector_service = get_vector_service()
        logger.info("Vector store initialized successfully")
    except Exception as e:
        logger.error("Vector store initialization failed", error=str(e))
    
    # Validate configuration
    try:
        if not settings.AZURE_OPENAI_API_KEY or settings.AZURE_OPENAI_API_KEY == "your-azure-openai-key-here":
            logger.warning("Azure OpenAI API key not properly configured")
    except Exception as e:
        logger.error("Configuration validation failed", error=str(e))
    
    logger.info("Application startup completed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ElSol Challenge application")
    
    # Cleanup temporary files
    try:
        temp_dir = settings.UPLOAD_TEMP_DIR
        if os.path.exists(temp_dir):
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                if os.path.isfile(file_path) and not filename.startswith('.'):
                    os.remove(file_path)
            logger.info("Temporary files cleaned up")
    except Exception as e:
        logger.warning("Failed to cleanup temporary files", error=str(e))
    
    logger.info("Application shutdown completed")


# Create FastAPI application
def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    settings = get_settings()
    
    app = FastAPI(
        title="ElSol Challenge - Audio Transcription API",
        description="""
        API for audio transcription and information extraction from medical conversations.
        
        ## Features
        
        * **Audio Upload**: Upload .wav or .mp3 files for transcription
        * **Transcription**: OpenAI Whisper-powered audio transcription
        * **Information Extraction**: Structured and unstructured data extraction
        * **Real-time Status**: Track processing status of uploaded files
        
        ## Supported Audio Formats
        
        * WAV files (.wav)
        * MP3 files (.mp3)
        * Maximum file size: 25MB
        
        ## Workflow
        
        1. Upload audio file via `/upload-audio`
        2. Get transcription ID in response
        3. Poll `/transcriptions/{id}` for results
        4. Retrieve structured and unstructured information
        """,
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8080"],  # Frontend URLs
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(
        health.router,
        tags=["Health Check"],
        responses={404: {"description": "Not found"}}
    )
    
    app.include_router(
        upload.router,
        prefix=settings.API_V1_STR,
        tags=["Audio Transcription"],
        responses={404: {"description": "Not found"}}
    )
    
    app.include_router(
        vector.router,
        prefix=settings.API_V1_STR,
        tags=["Vector Store"],
        responses={404: {"description": "Not found"}}
    )
    
    app.include_router(
        chat.router,
        prefix=settings.API_V1_STR,
        tags=["Chat RAG"],
        responses={404: {"description": "Not found"}}
    )
    
    return app


# Create app instance
app = create_application()


# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured error responses."""
    logger.warning(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTP Error",
            message=exc.detail,
            timestamp=None,  # Will be set by Pydantic default
            request_id=request.headers.get("X-Request-ID")
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with structured error responses."""
    logger.error(
        "Unhandled exception occurred",
        error=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            message="An unexpected error occurred. Please try again later.",
            timestamp=None,  # Will be set by Pydantic default
            request_id=request.headers.get("X-Request-ID")
        ).dict()
    )


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and responses."""
    import time
    
    start_time = time.time()
    
    logger.info(
        "Request started",
        method=request.method,
        path=request.url.path,
        query_params=str(request.query_params),
        client_ip=request.client.host if request.client else None
    )
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    logger.info(
        "Request completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time_seconds=round(process_time, 3)
    )
    
    # Add custom headers
    response.headers["X-Process-Time"] = str(round(process_time, 3))
    
    return response


# Root endpoint
@app.get(
    "/",
    summary="API Root",
    description="Get basic API information and status"
)
async def root():
    """Root endpoint with API information."""
    settings = get_settings()
    
    return {
        "message": "ElSol Challenge - Audio Transcription API",
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs_url": "/docs" if settings.DEBUG else "Documentation not available in production",
        "health_check": "/health",
        "upload_endpoint": f"{settings.API_V1_STR}/upload-audio"
    }


# Custom OpenAPI schema for better documentation
def custom_openapi():
    """Generate custom OpenAPI schema with additional metadata."""
    if app.openapi_schema:
        return app.openapi_schema
    
    settings = get_settings()
    
    openapi_schema = get_openapi(
        title="ElSol Challenge - Audio Transcription API",
        version=settings.APP_VERSION,
        description="""
        Advanced audio transcription service for medical conversations.
        
        Built with FastAPI, OpenAI Whisper, and structured information extraction.
        """,
        routes=app.routes,
    )
    
    # Add custom metadata
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    openapi_schema["info"]["contact"] = {
        "name": "ElSol Challenge Support",
        "email": "support@elsol-challenge.com"
    }
    
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    
    logger.info("Starting application server")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
