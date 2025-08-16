"""
Endpoints de carga de audio y transcripción para la aplicación ElSol Challenge.

Maneja cargas de archivos, validación y orquesta el pipeline de transcripción.
"""

import os
import uuid
import time
import asyncio
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import structlog

from app.core.config import get_settings, Settings, create_upload_dir, validate_file_extension, validate_file_size
from app.core.schemas import (
    AudioUploadResponse, 
    TranscriptionResponse, 
    TranscriptionListResponse,
    TranscriptionListParams,
    ErrorResponse
)
from app.database.models import (
    AudioTranscription, 
    TranscriptionStatus,
    create_transcription,
    get_transcription_by_id,
    get_transcriptions,
    update_transcription
)
from app.services.whisper_service import get_whisper_service, WhisperTranscriptionError
from app.services.openai_service import get_openai_service, OpenAIExtractionError
from app.database.connection import get_db


logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post(
    "/upload-audio",
    response_model=AudioUploadResponse,
    summary="Upload Audio File",
    description="Upload an audio file for transcription processing",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file or validation error"},
        413: {"model": ErrorResponse, "description": "File too large"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def upload_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Archivo de audio (.wav o .mp3)"),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db)
) -> AudioUploadResponse:
    """
    Subir un archivo de audio e iniciar procesamiento de transcripción.
    
    Args:
        background_tasks: Tareas en segundo plano de FastAPI
        file: Archivo de audio subido
        settings: Configuraciones de la aplicación
        db: Sesión de base de datos
        
    Returns:
        AudioUploadResponse con confirmación de carga
        
    Raises:
        HTTPException: Para varios errores de validación y procesamiento
    """
    # Generar ID único para esta transcripción
    transcription_id = str(uuid.uuid4())
    
    logger.info(
        "Audio upload started",
        transcription_id=transcription_id,
        filename=file.filename,
        content_type=file.content_type
    )
    
    try:
        # Validar archivo
        await validate_uploaded_file(file, settings)
        
        # Crear directorio de carga si es necesario
        create_upload_dir()
        
        # Save uploaded file
        file_path = await save_uploaded_file(file, transcription_id, settings)
        
        # Get file metadata
        file_size = os.path.getsize(file_path)
        
        # Create database record
        transcription = AudioTranscription.create_from_upload(
            filename=file.filename or "unknown",
            file_size=file_size,
            file_type=file.content_type or "unknown",
            file_path=file_path
        )
        transcription.id = transcription_id
        
        # Save to database
        created_transcription = create_transcription(db, transcription)
        
        # Schedule background processing
        background_tasks.add_task(
            process_transcription_pipeline,
            transcription_id,
            file_path,
            settings
        )
        
        logger.info(
            "Audio upload completed successfully",
            transcription_id=transcription_id,
            filename=file.filename,
            file_size=file_size
        )
        
        return AudioUploadResponse(
            id=created_transcription.id,
            filename=created_transcription.filename,
            status=created_transcription.status,
            created_at=created_transcription.created_at,
            file_size=created_transcription.file_size
        )
        
    except ValueError as e:
        logger.warning(
            "File validation failed",
            transcription_id=transcription_id,
            filename=file.filename,
            error=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(
            "Audio upload failed",
            transcription_id=transcription_id,
            filename=file.filename,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Internal server error during upload")


@router.get(
    "/transcriptions/{transcription_id}",
    response_model=TranscriptionResponse,
    summary="Get Transcription",
    description="Retrieve transcription results by ID",
    responses={
        404: {"model": ErrorResponse, "description": "Transcription not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def get_transcription(
    transcription_id: str,
    db: Session = Depends(get_db)
) -> TranscriptionResponse:
    """
    Get transcription results by ID.
    
    Args:
        transcription_id: Unique transcription identifier
        db: Database session
        
    Returns:
        TranscriptionResponse with results
        
    Raises:
        HTTPException: If transcription not found
    """
    logger.info(
        "Transcription retrieval requested",
        transcription_id=transcription_id
    )
    
    # Get transcription from database
    transcription = get_transcription_by_id(db, transcription_id)
    
    if not transcription:
        logger.warning(
            "Transcription not found",
            transcription_id=transcription_id
        )
        raise HTTPException(status_code=404, detail="Transcription not found")
    
    # Build response
    response_data = {
        "id": transcription.id,
        "filename": transcription.filename,
        "status": transcription.status,
        "created_at": transcription.created_at,
        "processed_at": transcription.processed_at,
        "error_message": transcription.error_message
    }
    
    # Include transcription results if completed
    if transcription.status == TranscriptionStatus.COMPLETED and transcription.raw_transcription:
        from app.core.schemas import TranscriptionResult, StructuredData, UnstructuredData
        
        response_data["transcription"] = TranscriptionResult(
            raw_text=transcription.raw_transcription,
            structured_data=StructuredData(**(transcription.structured_data or {})),
            unstructured_data=UnstructuredData(**(transcription.unstructured_data or {})),
            confidence_score=transcription.confidence_score,
            language_detected=transcription.language_detected,
            audio_duration_seconds=transcription.audio_duration_seconds,
            processing_time_seconds=transcription.processing_time_seconds
        )
    
    logger.info(
        "Transcription retrieved successfully",
        transcription_id=transcription_id,
        status=transcription.status.value
    )
    
    return TranscriptionResponse(**response_data)


@router.get(
    "/transcriptions",
    response_model=TranscriptionListResponse,
    summary="List Transcriptions",
    description="Get a paginated list of transcriptions with optional filtering"
)
async def list_transcriptions(
    params: TranscriptionListParams = Depends(),
    db: Session = Depends(get_db)
) -> TranscriptionListResponse:
    """
    Get a paginated list of transcriptions.
    
    Args:
        params: Query parameters for pagination and filtering
        db: Database session
        
    Returns:
        TranscriptionListResponse with paginated results
    """
    logger.info(
        "Transcription list requested",
        page=params.page,
        size=params.size,
        status_filter=params.status
    )
    
    # Get transcriptions from database
    transcriptions = get_transcriptions(
        db, 
        skip=params.offset, 
        limit=params.limit,
        status=params.status
    )
    
    # Convert to response format
    from app.core.schemas import TranscriptionListItem
    
    items = [
        TranscriptionListItem(
            id=t.id,
            filename=t.filename,
            status=t.status,
            created_at=t.created_at,
            processed_at=t.processed_at,
            file_size=t.file_size,
            language_detected=t.language_detected,
            audio_duration_seconds=t.audio_duration_seconds
        )
        for t in transcriptions
    ]
    
    # Calculate pagination info
    total_count = len(items)  # In production, do a separate count query
    has_next = len(items) == params.size  # Simplified logic
    
    logger.info(
        "Transcription list retrieved",
        total_items=len(items),
        page=params.page,
        has_next=has_next
    )
    
    return TranscriptionListResponse(
        items=items,
        total=total_count,
        page=params.page,
        size=params.size,
        has_next=has_next
    )


# Helper functions

async def validate_uploaded_file(file: UploadFile, settings: Settings) -> None:
    """
    Validate uploaded file for size, type, and format.
    
    Args:
        file: Uploaded file object
        settings: Application settings
        
    Raises:
        ValueError: If file validation fails
    """
    # Check filename
    if not file.filename:
        raise ValueError("No filename provided")
    
    # Check file extension
    if not validate_file_extension(file.filename):
        allowed_extensions = ", ".join(settings.extensions_list)
        raise ValueError(f"Tipo de archivo no permitido. Formatos soportados: {allowed_extensions}")
    
    # Check file size
    if file.size and not validate_file_size(file.size):
        max_size_mb = settings.UPLOAD_MAX_SIZE / (1024 * 1024)
        raise ValueError(f"File size exceeds maximum limit of {max_size_mb:.1f}MB")
    
    # Validate content type
    allowed_content_types = [
        "audio/wav", "audio/wave", "audio/x-wav",
        "audio/mpeg", "audio/mp3", "audio/x-mp3"
    ]
    
    if file.content_type and file.content_type not in allowed_content_types:
        logger.warning(
            "Unexpected content type",
            filename=file.filename,
            content_type=file.content_type
        )
        # Don't fail for content type mismatch, as browsers can be inconsistent


async def save_uploaded_file(file: UploadFile, transcription_id: str, settings: Settings) -> str:
    """
    Save uploaded file to temporary directory.
    
    Args:
        file: Uploaded file object
        transcription_id: Unique transcription ID
        settings: Application settings
        
    Returns:
        Path to saved file
        
    Raises:
        ValueError: If file cannot be saved
    """
    try:
        # Generate unique filename
        file_extension = Path(file.filename or "").suffix.lower()
        filename = f"{transcription_id}{file_extension}"
        file_path = os.path.join(settings.UPLOAD_TEMP_DIR, filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            if not content:
                raise ValueError("Empty file uploaded")
            buffer.write(content)
        
        # Validate saved file size
        saved_size = os.path.getsize(file_path)
        if not validate_file_size(saved_size):
            os.remove(file_path)  # Clean up
            max_size_mb = settings.UPLOAD_MAX_SIZE / (1024 * 1024)
            raise ValueError(f"File size {saved_size} exceeds maximum limit of {max_size_mb:.1f}MB")
        
        logger.info(
            "File saved successfully",
            transcription_id=transcription_id,
            file_path=file_path,
            file_size=saved_size
        )
        
        return file_path
        
    except Exception as e:
        logger.error(
            "Failed to save uploaded file",
            transcription_id=transcription_id,
            filename=file.filename,
            error=str(e)
        )
        raise ValueError(f"Failed to save file: {str(e)}")


async def process_transcription_pipeline(
    transcription_id: str,
    file_path: str,
    settings: Settings
) -> None:
    """
    Background task to process audio transcription pipeline.
    
    Args:
        transcription_id: Unique transcription identifier
        file_path: Path to audio file
        settings: Application settings
    """
    from app.database.connection import SessionLocal
    
    logger.info(
        "Starting transcription pipeline",
        transcription_id=transcription_id,
        file_path=file_path
    )
    
    db = SessionLocal()
    start_time = time.time()
    
    try:
        # Get transcription record
        transcription = get_transcription_by_id(db, transcription_id)
        if not transcription:
            logger.error(
                "Transcription record not found in pipeline",
                transcription_id=transcription_id
            )
            return
        
        # Mark as processing
        transcription.mark_processing()
        update_transcription(db, transcription)
        
        # Step 1: Transcribe audio using Whisper
        whisper_service = get_whisper_service()
        
        logger.info(
            "Starting Whisper transcription",
            transcription_id=transcription_id
        )
        
        transcription_result = await whisper_service.transcribe_audio(
            file_path=file_path,
            language="es",  # Assume Spanish for medical conversations
            prompt="Esta es una conversación médica entre doctor y paciente."
        )
        
        # Step 2: Extract information using Azure OpenAI
        openai_service = get_openai_service()
        
        logger.info(
            "Starting information extraction",
            transcription_id=transcription_id
        )
        
        structured_data, unstructured_data = await openai_service.extract_information(
            transcription_text=transcription_result["text"],
            context="Conversación médica"
        )
        
        # Calculate processing time
        processing_time = int(time.time() - start_time)
        
        # Mark as completed
        transcription.mark_completed(
            raw_transcription=transcription_result["text"],
            structured_data=structured_data,
            unstructured_data=unstructured_data,
            processing_time=processing_time,
            confidence_score=transcription_result.get("confidence_score"),
            language_detected=transcription_result.get("language"),
            audio_duration=transcription_result.get("duration")
        )
        
        update_transcription(db, transcription)
        
        # Step 3: Store in vector database (Requisito 2 - Almacenamiento Vectorial)
        try:
            from app.services.vector_service import store_conversation_data
            
            logger.info(
                "Starting vector store storage",
                transcription_id=transcription_id
            )
            
            vector_response = await store_conversation_data(
                conversation_id=transcription_id,
                transcription=transcription_result["text"],
                structured_data=structured_data,
                unstructured_data=unstructured_data,
                metadata={
                    "filename": transcription.filename,
                    "file_size": transcription.file_size,
                    "audio_duration": transcription_result.get("duration")
                }
            )
            
            # Mark as stored in vector database
            transcription.mark_vector_stored(vector_response.vector_id)
            update_transcription(db, transcription)
            
            logger.info(
                "Vector store storage completed successfully",
                transcription_id=transcription_id,
                vector_id=vector_response.vector_id
            )
            
        except Exception as e:
            logger.warning(
                "Vector store storage failed (non-critical)",
                transcription_id=transcription_id,
                error=str(e)
            )
            # Mark vector storage as failed but don't fail the entire pipeline
            transcription.mark_vector_failed()
            update_transcription(db, transcription)
        
        logger.info(
            "Transcription pipeline completed successfully",
            transcription_id=transcription_id,
            processing_time_seconds=processing_time
        )
        
    except (WhisperTranscriptionError, OpenAIExtractionError) as e:
        processing_time = int(time.time() - start_time)
        
        logger.error(
            "Transcription pipeline failed",
            transcription_id=transcription_id,
            error=str(e),
            processing_time_seconds=processing_time
        )
        
        # Mark as failed
        if transcription:
            transcription.mark_failed(str(e))
            update_transcription(db, transcription)
            
    except Exception as e:
        processing_time = int(time.time() - start_time)
        
        logger.error(
            "Unexpected error in transcription pipeline",
            transcription_id=transcription_id,
            error=str(e),
            processing_time_seconds=processing_time
        )
        
        # Mark as failed
        if transcription:
            transcription.mark_failed(f"Unexpected error: {str(e)}")
            update_transcription(db, transcription)
            
    finally:
        # Clean up uploaded file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(
                    "Temporary file cleaned up",
                    transcription_id=transcription_id,
                    file_path=file_path
                )
        except Exception as e:
            logger.warning(
                "Failed to clean up temporary file",
                transcription_id=transcription_id,
                file_path=file_path,
                error=str(e)
            )
        
        db.close()
