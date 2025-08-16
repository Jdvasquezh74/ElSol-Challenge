"""
Endpoints de API para Procesamiento de Documentos - ElSol Challenge.

Endpoints para upload y procesamiento de PDFs e imágenes con OCR.
PLUS Feature 4: Subida de PDFs/Imágenes con OCR
"""

import os
import uuid
import time
import aiofiles
from pathlib import Path
from typing import List, Optional
import structlog
from fastapi import (
    APIRouter, HTTPException, Depends, File, UploadFile, 
    Form, BackgroundTasks, Query
)
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.schemas import (
    DocumentResponse, DocumentUpload, DocumentProcessingStatus,
    DocumentSearchQuery, DocumentSearchResult, ErrorResponse
)
from app.database.connection import get_db
from app.database.models import Document
from app.services.ocr_service import get_ocr_service, OCRService, OCRServiceError
from app.services.vector_service import get_vector_service

logger = structlog.get_logger(__name__)
settings = get_settings()

router = APIRouter()


def validate_document_file(file: UploadFile) -> tuple[bool, str]:
    """
    Validar archivo de documento antes del upload.
    
    Args:
        file: Archivo uploadado
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    # Verificar que hay archivo
    if not file or not file.filename:
        return False, "No se proporcionó archivo"
    
    # Verificar extensión
    allowed_extensions = settings.DOCUMENT_ALLOWED_EXTENSIONS.split(',')
    file_extension = Path(file.filename).suffix.lower().lstrip('.')
    
    if file_extension not in allowed_extensions:
        return False, f"Extensión no permitida. Permitidas: {', '.join(allowed_extensions)}"
    
    # Verificar tamaño (si está disponible)
    if hasattr(file, 'size') and file.size:
        max_size = settings.DOCUMENT_MAX_SIZE_MB * 1024 * 1024
        if file.size > max_size:
            return False, f"Archivo demasiado grande ({file.size / 1024 / 1024:.1f}MB). Máximo: {settings.DOCUMENT_MAX_SIZE_MB}MB"
    
    return True, "Archivo válido"


async def save_uploaded_document(file: UploadFile, document_id: str) -> str:
    """
    Guardar archivo de documento en el sistema de archivos.
    
    Args:
        file: Archivo uploadado
        document_id: ID único del documento
        
    Returns:
        Ruta donde se guardó el archivo
        
    Raises:
        HTTPException: Si no se puede guardar el archivo
    """
    try:
        # Crear directorio si no existe
        os.makedirs(settings.DOCUMENT_UPLOAD_DIR, exist_ok=True)
        
        # Generar nombre de archivo único
        file_extension = Path(file.filename).suffix.lower()
        filename = f"{document_id}{file_extension}"
        file_path = os.path.join(settings.DOCUMENT_UPLOAD_DIR, filename)
        
        # Guardar archivo
        async with aiofiles.open(file_path, 'wb') as buffer:
            content = await file.read()
            await buffer.write(content)
        
        logger.info("Document file saved", 
                   original_filename=file.filename,
                   saved_path=file_path,
                   size_bytes=len(content))
        
        return file_path
        
    except Exception as e:
        logger.error("Failed to save document file", 
                    filename=file.filename, 
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error guardando archivo: {str(e)}"
        )


async def process_document_background(
    document_id: str,
    file_path: str,
    original_filename: str,
    db: Session
) -> None:
    """
    Procesar documento en background task.
    
    Args:
        document_id: ID del documento
        file_path: Ruta al archivo
        original_filename: Nombre original del archivo
        db: Sesión de base de datos
    """
    try:
        logger.info("Starting background document processing",
                   document_id=document_id,
                   file_path=file_path)
        
        # Obtener documento de la base de datos
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error("Document not found for processing", document_id=document_id)
            return
        
        # Marcar como procesando
        document.mark_processing()
        db.commit()
        
        # Procesar con OCR service
        ocr_service = get_ocr_service()
        
        # Validar archivo
        is_valid, error_msg = ocr_service.validate_file(file_path)
        if not is_valid:
            document.mark_failed(error_msg)
            db.commit()
            return
        
        # Procesar documento
        ocr_result, metadata = await ocr_service.process_document(file_path, original_filename)
        
        # Actualizar documento con resultados
        document.extracted_text = ocr_result.text
        document.ocr_confidence = ocr_result.confidence
        document.page_count = ocr_result.page_count
        document.language_detected = ocr_result.language_detected
        
        # Agregar metadata médica si se extrajo
        if metadata:
            document.set_medical_metadata(metadata.dict())
        
        # Marcar como completado
        document.mark_completed(ocr_result.processing_time_ms)
        db.commit()
        
        # Almacenar en vector store si hay texto
        if ocr_result.text.strip():
            try:
                vector_service = get_vector_service()
                
                # Preparar metadata para vector store
                vector_metadata = {
                    "document_id": document_id,
                    "patient_name": document.patient_name,
                    "document_type": document.document_type,
                    "document_date": document.document_date,
                    "file_type": document.file_type,
                    "source": "document"
                }
                
                # Combinar texto con metadata para mejor contexto
                combined_text = f"Documento: {original_filename}\n"
                if document.patient_name:
                    combined_text += f"Paciente: {document.patient_name}\n"
                if document.document_type:
                    combined_text += f"Tipo: {document.document_type}\n"
                combined_text += f"\nContenido:\n{ocr_result.text}"
                
                # Almacenar en vector store
                vector_id = await vector_service.store_conversation_data(
                    conversation_id=document_id,
                    transcription=combined_text,
                    structured_data=metadata.dict() if metadata else {},
                    unstructured_data={"extracted_text": ocr_result.text},
                    metadata=vector_metadata
                )
                
                if vector_id:
                    document.mark_vector_stored(vector_id)
                    db.commit()
                    logger.info("Document stored in vector database",
                               document_id=document_id,
                               vector_id=vector_id)
                
            except Exception as e:
                logger.error("Failed to store document in vector database",
                           document_id=document_id,
                           error=str(e))
                # No fallar el procesamiento completo por esto
        
        logger.info("Document processing completed successfully",
                   document_id=document_id,
                   text_length=len(ocr_result.text),
                   confidence=ocr_result.confidence)
        
    except OCRServiceError as e:
        logger.error("OCR processing failed",
                    document_id=document_id,
                    error=str(e))
        
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.mark_failed(str(e))
            db.commit()
        
    except Exception as e:
        logger.error("Unexpected error in document processing",
                    document_id=document_id,
                    error=str(e))
        
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.mark_failed(f"Error inesperado: {str(e)}")
            db.commit()


@router.post(
    "/upload-document",
    response_model=DocumentResponse,
    summary="Upload Document",
    description="""
    Upload y procesamiento de documentos médicos (PDFs e imágenes).
    
    Formatos soportados:
    - PDFs: Extracción de texto con PyPDF2
    - Imágenes: JPG, PNG, TIFF con OCR Tesseract
    
    El procesamiento incluye:
    - Extracción de texto
    - Identificación automática de paciente
    - Extracción de metadata médica con IA
    - Almacenamiento en vector store para búsquedas
    
    Tamaño máximo: 10MB
    """
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Archivo PDF o imagen"),
    patient_name: Optional[str] = Form(None, description="Nombre del paciente (opcional)"),
    document_type: Optional[str] = Form(None, description="Tipo de documento médico"),
    description: Optional[str] = Form(None, description="Descripción del documento"),
    db: Session = Depends(get_db),
    ocr_service: OCRService = Depends(get_ocr_service)
):
    """
    Upload y procesar documento médico.
    
    Args:
        file: Archivo PDF o imagen
        patient_name: Nombre del paciente (opcional)
        document_type: Tipo de documento
        description: Descripción
        background_tasks: Para procesamiento asíncrono
        db: Sesión de base de datos
        ocr_service: Servicio OCR
        
    Returns:
        Información del documento uploadado
    """
    request_start = time.time()
    
    try:
        logger.info("Processing document upload",
                   filename=file.filename,
                   content_type=file.content_type,
                   patient_name=patient_name)
        
        # Validar archivo
        is_valid, error_msg = validate_document_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Generar ID único para el documento
        document_id = str(uuid.uuid4())
        
        # Guardar archivo
        file_path = await save_uploaded_document(file, document_id)
        file_size = os.path.getsize(file_path)
        
        # Detectar tipo de archivo
        try:
            file_type = ocr_service.detect_file_type(file_path)
        except OCRServiceError as e:
            # Limpiar archivo si hay error
            try:
                os.remove(file_path)
            except:
                pass
            raise HTTPException(status_code=400, detail=str(e))
        
        # Crear registro en base de datos
        document = Document(
            id=document_id,
            filename=os.path.basename(file_path),
            original_filename=file.filename,
            file_type=file_type,
            file_size_bytes=file_size,
            file_path=file_path,
            status="pending",
            patient_name=patient_name,
            document_type=document_type
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Agregar tarea de procesamiento en background
        background_tasks.add_task(
            process_document_background,
            document_id,
            file_path,
            file.filename,
            db
        )
        
        # Preparar respuesta
        response = DocumentResponse(
            document_id=document_id,
            filename=file.filename,
            file_type=file_type,
            file_size_bytes=file_size,
            status=DocumentProcessingStatus.PENDING,
            patient_association=patient_name,
            created_at=document.created_at
        )
        
        request_time = int((time.time() - request_start) * 1000)
        logger.info("Document upload completed",
                   document_id=document_id,
                   filename=file.filename,
                   file_type=file_type,
                   size_mb=file_size / 1024 / 1024,
                   request_time_ms=request_time)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        request_time = int((time.time() - request_start) * 1000)
        logger.error("Document upload failed",
                    filename=file.filename if file else "unknown",
                    error=str(e),
                    request_time_ms=request_time)
        
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando documento: {str(e)}"
        )


@router.get(
    "/documents",
    response_model=List[DocumentResponse],
    summary="List Documents",
    description="Obtener lista de documentos procesados con filtros opcionales"
)
async def list_documents(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(20, ge=1, le=100, description="Número máximo de registros"),
    patient_name: Optional[str] = Query(None, description="Filtrar por nombre de paciente"),
    status: Optional[DocumentProcessingStatus] = Query(None, description="Filtrar por estado"),
    file_type: Optional[str] = Query(None, description="Filtrar por tipo de archivo"),
    db: Session = Depends(get_db)
):
    """
    Obtener lista de documentos con filtros opcionales.
    
    Args:
        skip: Registros a saltar para paginación
        limit: Límite de registros
        patient_name: Filtro por paciente
        status: Filtro por estado
        file_type: Filtro por tipo de archivo
        db: Sesión de base de datos
        
    Returns:
        Lista de documentos
    """
    try:
        logger.info("Listing documents",
                   skip=skip,
                   limit=limit,
                   patient_name=patient_name,
                   status=status)
        
        # Construir query con filtros
        query = db.query(Document)
        
        if patient_name:
            query = query.filter(Document.patient_name.ilike(f"%{patient_name}%"))
        
        if status:
            query = query.filter(Document.status == status.value)
        
        if file_type:
            query = query.filter(Document.file_type == file_type)
        
        # Ordenar por fecha de creación (más reciente primero)
        query = query.order_by(Document.created_at.desc())
        
        # Aplicar paginación
        documents = query.offset(skip).limit(limit).all()
        
        # Convertir a response models
        response_list = []
        for doc in documents:
            response = DocumentResponse(
                document_id=doc.id,
                filename=doc.original_filename,
                file_type=doc.file_type,
                file_size_bytes=doc.file_size_bytes,
                status=DocumentProcessingStatus(doc.status),
                patient_association=doc.patient_name,
                created_at=doc.created_at,
                processed_at=doc.processed_at,
                error_message=doc.error_message,
                vector_stored=(doc.vector_stored == "true")
            )
            
            # Agregar resultados OCR si están disponibles
            if doc.status == "completed" and doc.extracted_text:
                from app.core.schemas import OCRResult
                response.ocr_result = OCRResult(
                    text=doc.extracted_text[:200] + "..." if len(doc.extracted_text) > 200 else doc.extracted_text,
                    confidence=doc.ocr_confidence or 0.0,
                    page_count=doc.page_count,
                    processing_time_ms=doc.processing_time_ms or 0,
                    language_detected=doc.language_detected
                )
            
            response_list.append(response)
        
        logger.info("Documents list retrieved",
                   total_found=len(response_list))
        
        return response_list
        
    except Exception as e:
        logger.error("Failed to list documents", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo documentos: {str(e)}"
        )


@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    summary="Get Document",
    description="Obtener información detallada de un documento específico"
)
async def get_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Obtener información completa de un documento.
    
    Args:
        document_id: ID del documento
        db: Sesión de base de datos
        
    Returns:
        Información completa del documento
    """
    try:
        logger.info("Getting document details", document_id=document_id)
        
        # Buscar documento
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Documento no encontrado: {document_id}"
            )
        
        # Preparar respuesta completa
        response = DocumentResponse(
            document_id=document.id,
            filename=document.original_filename,
            file_type=document.file_type,
            file_size_bytes=document.file_size_bytes,
            status=DocumentProcessingStatus(document.status),
            patient_association=document.patient_name,
            created_at=document.created_at,
            processed_at=document.processed_at,
            error_message=document.error_message,
            vector_stored=(document.vector_stored == "true")
        )
        
        # Agregar resultados OCR/PDF si están disponibles
        if document.status == "completed":
            from app.core.schemas import OCRResult, DocumentMetadata
            
            if document.extracted_text:
                response.ocr_result = OCRResult(
                    text=document.extracted_text,
                    confidence=document.ocr_confidence or 0.0,
                    page_count=document.page_count,
                    processing_time_ms=document.processing_time_ms or 0,
                    language_detected=document.language_detected
                )
            
            # Agregar metadata médica
            metadata = DocumentMetadata(
                patient_name=document.patient_name,
                document_date=document.document_date,
                document_type=document.document_type,
                medical_conditions=document.to_dict().get("medical_conditions", []),
                medications=document.to_dict().get("medications", []),
                medical_procedures=document.to_dict().get("medical_procedures", [])
            )
            response.extracted_metadata = metadata
        
        logger.info("Document details retrieved",
                   document_id=document_id,
                   status=document.status)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get document details",
                    document_id=document_id,
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo documento: {str(e)}"
        )


@router.delete(
    "/documents/{document_id}",
    summary="Delete Document",
    description="Eliminar documento y su archivo asociado"
)
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Eliminar documento y su archivo del sistema.
    
    Args:
        document_id: ID del documento
        db: Sesión de base de datos
        
    Returns:
        Confirmación de eliminación
    """
    try:
        logger.info("Deleting document", document_id=document_id)
        
        # Buscar documento
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Documento no encontrado: {document_id}"
            )
        
        # Eliminar archivo físico si existe
        if document.file_path and os.path.exists(document.file_path):
            try:
                os.remove(document.file_path)
                logger.info("Document file deleted", file_path=document.file_path)
            except Exception as e:
                logger.warning("Failed to delete document file",
                             file_path=document.file_path,
                             error=str(e))
        
        # Eliminar registro de base de datos
        db.delete(document)
        db.commit()
        
        logger.info("Document deleted successfully", document_id=document_id)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Documento eliminado exitosamente",
                "document_id": document_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete document",
                    document_id=document_id,
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando documento: {str(e)}"
        )


@router.get(
    "/documents/search",
    response_model=List[DocumentSearchResult],
    summary="Search Documents",
    description="Buscar en el contenido de documentos procesados"
)
async def search_documents(
    query: str = Query(..., description="Texto a buscar"),
    patient_name: Optional[str] = Query(None, description="Filtrar por paciente"),
    document_type: Optional[str] = Query(None, description="Filtrar por tipo"),
    max_results: int = Query(10, ge=1, le=50, description="Máximo número de resultados"),
    db: Session = Depends(get_db)
):
    """
    Buscar en el contenido extraído de documentos.
    
    Args:
        query: Texto a buscar
        patient_name: Filtro opcional por paciente
        document_type: Filtro opcional por tipo
        max_results: Límite de resultados
        db: Sesión de base de datos
        
    Returns:
        Lista de resultados de búsqueda
    """
    try:
        logger.info("Searching documents",
                   query=query,
                   patient_name=patient_name,
                   max_results=max_results)
        
        # Construir query base
        sql_query = db.query(Document).filter(
            Document.status == "completed",
            Document.extracted_text.isnot(None),
            Document.extracted_text.contains(query)
        )
        
        # Aplicar filtros opcionales
        if patient_name:
            sql_query = sql_query.filter(Document.patient_name.ilike(f"%{patient_name}%"))
        
        if document_type:
            sql_query = sql_query.filter(Document.document_type.ilike(f"%{document_type}%"))
        
        # Ordenar por relevancia (simple: por fecha de creación)
        sql_query = sql_query.order_by(Document.created_at.desc())
        
        # Limitar resultados
        documents = sql_query.limit(max_results).all()
        
        # Preparar resultados con extractos relevantes
        results = []
        for doc in documents:
            # Crear extracto con contexto
            text = doc.extracted_text or ""
            query_lower = query.lower()
            text_lower = text.lower()
            
            # Encontrar posición de la consulta
            pos = text_lower.find(query_lower)
            if pos >= 0:
                # Extraer contexto alrededor
                start = max(0, pos - 100)
                end = min(len(text), pos + len(query) + 100)
                excerpt = text[start:end]
                
                if start > 0:
                    excerpt = "..." + excerpt
                if end < len(text):
                    excerpt = excerpt + "..."
                
                highlight = query
            else:
                # Si no se encuentra exacto, usar inicio del texto
                excerpt = text[:200] + ("..." if len(text) > 200 else "")
                highlight = None
            
            result = DocumentSearchResult(
                document_id=doc.id,
                filename=doc.original_filename,
                patient_name=doc.patient_name,
                relevance_score=0.8,  # Score simple por ahora
                excerpt=excerpt,
                highlight=highlight,
                document_type=doc.document_type or "unknown",
                created_at=doc.created_at
            )
            
            results.append(result)
        
        logger.info("Document search completed",
                   query=query,
                   results_found=len(results))
        
        return results
        
    except Exception as e:
        logger.error("Document search failed",
                    query=query,
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error en búsqueda de documentos: {str(e)}"
        )
