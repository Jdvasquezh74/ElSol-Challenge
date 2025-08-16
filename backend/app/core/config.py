"""
Módulo de configuración para la aplicación ElSol Challenge.
Maneja variables de entorno y configuraciones de la aplicación.
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator, computed_field


class Settings(BaseSettings):
    """Configuraciones de aplicación cargadas desde variables de entorno."""
    
    # Aplicación
    APP_NAME: str = "ElSol Challenge - Audio Transcription"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    
    # Azure OpenAI Configuration (para extracción de información)
    AZURE_OPENAI_API_KEY: str = "your-azure-openai-key-here"
    AZURE_OPENAI_API_VERSION: str = "2023-12-01-preview"
    AZURE_OPENAI_API_ENDPOINT: str = "https://your-resource.openai.azure.com/"
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-35-turbo"
    
    # Whisper Local Configuration
    WHISPER_MODEL: str = "base"  # tiny, base, small, medium, large
    WHISPER_DEVICE: str = "cpu"  # cpu o cuda si tienes GPU
    
    # Base de datos
    DATABASE_URL: str = "sqlite:///./conversations.db"
    
    # Configuraciones de carga de archivos
    UPLOAD_MAX_SIZE: int = 26_214_400  # 25MB in bytes
    UPLOAD_ALLOWED_EXTENSIONS: str = "wav,mp3"  # Será convertido a lista por el validador
    UPLOAD_TEMP_DIR: str = "./temp_uploads"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 50
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Processing
    TRANSCRIPTION_TIMEOUT: int = 300  # 5 minutes
    MAX_CONCURRENT_TRANSCRIPTIONS: int = 5
    
    # Vector Store Settings (Requisito 2 - Almacenamiento Vectorial)
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "medical_conversations"
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    VECTOR_EMBEDDING_DIMENSIONS: int = 384
    
    # Document Processing Settings (PLUS Feature 4 - PDFs/Imágenes)
    DOCUMENT_UPLOAD_DIR: str = "./temp_documents"
    DOCUMENT_MAX_SIZE_MB: int = 10
    DOCUMENT_ALLOWED_EXTENSIONS: str = "pdf,jpg,jpeg,png,tiff,tif"
    OCR_LANGUAGE: str = "spa"  # Spanish for Tesseract
    OCR_MIN_CONFIDENCE: int = 60
    PDF_MAX_PAGES: int = 50
    
    # Speaker Diarization Settings (PLUS Feature 5 - Diferenciación de hablantes)
    SPEAKER_MIN_SEGMENT_LENGTH: float = 1.0  # Minimum segment length in seconds
    SPEAKER_CONFIDENCE_THRESHOLD: float = 0.7
    SPEAKER_MAX_SPEAKERS: int = 5  # Maximum number of speakers to detect
    DIARIZATION_SAMPLE_RATE: int = 16000
    
    @field_validator("UPLOAD_ALLOWED_EXTENSIONS", mode="after")
    @classmethod
    def parse_extensions(cls, v):
        """Parsear lista de extensiones separadas por comas."""
        if isinstance(v, str):
            return [ext.strip().lower() for ext in v.split(",")]
        return v
    
    @field_validator("AZURE_OPENAI_API_KEY")
    @classmethod
    def validate_azure_openai_key(cls, v):
        """Validar que la clave API de Azure OpenAI esté configurada."""
        if not v or v == "your-azure-openai-key-here":
            # Solo advertir en desarrollo, no fallar
            import warnings
            warnings.warn("Azure OpenAI API key no configurada - funcionalidad de extracción limitada")
        return v
    
    @field_validator("WHISPER_MODEL")
    @classmethod
    def validate_whisper_model(cls, v):
        """Validar modelo de Whisper."""
        valid_models = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]
        if v not in valid_models:
            raise ValueError(f"Modelo Whisper inválido. Usar uno de: {valid_models}")
        return v
    
    @computed_field
    @property
    def extensions_list(self) -> List[str]:
        """Obtener extensiones como lista."""
        if isinstance(self.UPLOAD_ALLOWED_EXTENSIONS, str):
            return [ext.strip().lower() for ext in self.UPLOAD_ALLOWED_EXTENSIONS.split(",")]
        return self.UPLOAD_ALLOWED_EXTENSIONS
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True
    }


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings


def create_upload_dir():
    """Create upload directory if it doesn't exist."""
    os.makedirs(settings.UPLOAD_TEMP_DIR, exist_ok=True)


def create_chroma_dir():
    """Create Chroma database directory if it doesn't exist."""
    os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)


def create_document_dir():
    """Create document upload directory if it doesn't exist."""
    os.makedirs(settings.DOCUMENT_UPLOAD_DIR, exist_ok=True)


def validate_file_extension(filename: str) -> bool:
    """Validar si la extensión del archivo está permitida."""
    if not filename:
        return False
    
    extension = filename.lower().split(".")[-1]
    return extension in settings.extensions_list


def validate_file_size(file_size: int) -> bool:
    """Validate if file size is within limits."""
    return file_size <= settings.UPLOAD_MAX_SIZE
