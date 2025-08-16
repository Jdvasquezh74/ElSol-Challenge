"""
Esquemas Pydantic para validación de request/response en la aplicación ElSol Challenge.
Define objetos de transferencia de datos (DTOs) para endpoints de API.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum


class TranscriptionStatusEnum(str, Enum):
    """Enumeración para estado de transcripción en respuestas de API."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Esquemas de Request
class AudioUploadResponse(BaseModel):
    """Esquema de respuesta para endpoint de carga de audio."""
    id: str = Field(..., description="Unique identifier for the transcription job")
    filename: str = Field(..., description="Original filename of uploaded audio")
    status: TranscriptionStatusEnum = Field(..., description="Current processing status")
    created_at: datetime = Field(..., description="Timestamp when upload was received")
    file_size: int = Field(..., description="Size of uploaded file in bytes")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StructuredData(BaseModel):
    """Esquema para información estructurada extraída de transcripción."""
    nombre: Optional[str] = Field(None, description="Patient/person name mentioned")
    edad: Optional[int] = Field(None, description="Age mentioned", ge=0, le=150)
    fecha: Optional[str] = Field(None, description="Date mentioned in conversation")
    diagnostico: Optional[str] = Field(None, description="Medical diagnosis mentioned")
    medico: Optional[str] = Field(None, description="Doctor/physician name")
    medicamentos: Optional[List[str]] = Field(None, description="Medications mentioned")
    telefono: Optional[str] = Field(None, description="Phone number mentioned")
    email: Optional[str] = Field(None, description="Email address mentioned")
    
    @validator('edad')
    def validate_age(cls, v):
        if v is not None and (v < 0 or v > 150):
            raise ValueError('Age must be between 0 and 150')
        return v


class UnstructuredData(BaseModel):
    """Schema for unstructured information extracted from transcription."""
    sintomas: Optional[List[str]] = Field(None, description="Symptoms mentioned")
    contexto: Optional[str] = Field(None, description="Conversation context")
    observaciones: Optional[str] = Field(None, description="Additional observations")
    emociones: Optional[List[str]] = Field(None, description="Emotions detected")
    urgencia: Optional[str] = Field(None, description="Urgency level detected")
    recomendaciones: Optional[List[str]] = Field(None, description="Recommendations given")
    preguntas: Optional[List[str]] = Field(None, description="Questions asked")
    respuestas: Optional[List[str]] = Field(None, description="Key answers provided")


class TranscriptionResult(BaseModel):
    """Schema for complete transcription results."""
    raw_text: str = Field(..., description="Complete transcribed text")
    structured_data: StructuredData = Field(..., description="Extracted structured information")
    unstructured_data: UnstructuredData = Field(..., description="Extracted unstructured information")
    confidence_score: Optional[str] = Field(None, description="Transcription confidence score")
    language_detected: Optional[str] = Field(None, description="Detected language")
    audio_duration_seconds: Optional[int] = Field(None, description="Audio duration in seconds")
    processing_time_seconds: Optional[int] = Field(None, description="Processing time in seconds")


class TranscriptionResponse(BaseModel):
    """Response schema for completed transcription."""
    id: str = Field(..., description="Unique identifier")
    filename: str = Field(..., description="Original filename")
    status: TranscriptionStatusEnum = Field(..., description="Processing status")
    created_at: datetime = Field(..., description="Creation timestamp")
    processed_at: Optional[datetime] = Field(None, description="Processing completion timestamp")
    transcription: Optional[TranscriptionResult] = Field(None, description="Transcription results")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TranscriptionListItem(BaseModel):
    """Schema for transcription list items."""
    id: str = Field(..., description="Unique identifier")
    filename: str = Field(..., description="Original filename")
    status: TranscriptionStatusEnum = Field(..., description="Processing status")
    created_at: datetime = Field(..., description="Creation timestamp")
    processed_at: Optional[datetime] = Field(None, description="Processing completion timestamp")
    file_size: int = Field(..., description="File size in bytes")
    language_detected: Optional[str] = Field(None, description="Detected language")
    audio_duration_seconds: Optional[int] = Field(None, description="Audio duration")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TranscriptionListResponse(BaseModel):
    """Response schema for transcription list endpoint."""
    items: List[TranscriptionListItem] = Field(..., description="List of transcriptions")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Whether there are more pages")


# Query Parameters
class TranscriptionListParams(BaseModel):
    """Query parameters for transcription list endpoint."""
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(10, ge=1, le=100, description="Items per page")
    status: Optional[TranscriptionStatusEnum] = Field(None, description="Filter by status")
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size
    
    @property
    def limit(self) -> int:
        return self.size


# Health Check Schema
class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(..., description="Service health status")
    timestamp: datetime = Field(..., description="Current timestamp")
    version: str = Field(..., description="Application version")
    uptime_seconds: Optional[int] = Field(None, description="Service uptime in seconds")
    dependencies: Optional[Dict[str, str]] = Field(None, description="Dependencies health status")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Error Schemas
class ErrorDetail(BaseModel):
    """Error detail schema."""
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    field: Optional[str] = Field(None, description="Field that caused the error")


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[List[ErrorDetail]] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# File Validation Schemas
class FileValidationError(BaseModel):
    """File validation error schema."""
    filename: str = Field(..., description="Name of the problematic file")
    errors: List[str] = Field(..., description="List of validation errors")


# Processing Status Update (Internal Use)
class TranscriptionUpdate(BaseModel):
    """Internal schema for updating transcription status."""
    status: TranscriptionStatusEnum
    raw_transcription: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    unstructured_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time_seconds: Optional[int] = None
    confidence_score: Optional[str] = None
    language_detected: Optional[str] = None
    audio_duration_seconds: Optional[int] = None


# Configuration Schema
class APISettings(BaseModel):
    """API configuration schema."""
    max_file_size: int = Field(..., description="Maximum file size in bytes")
    allowed_extensions: List[str] = Field(..., description="Allowed file extensions")
    rate_limit_requests: int = Field(..., description="Rate limit requests per window")
    rate_limit_window: int = Field(..., description="Rate limit window in seconds")


# Statistics Schema (Future Feature)
class TranscriptionStats(BaseModel):
    """Statistics schema for transcription analytics."""
    total_transcriptions: int = Field(..., description="Total number of transcriptions")
    completed_transcriptions: int = Field(..., description="Number of completed transcriptions")
    failed_transcriptions: int = Field(..., description="Number of failed transcriptions")
    avg_processing_time: Optional[float] = Field(None, description="Average processing time in seconds")
    total_audio_hours: Optional[float] = Field(None, description="Total audio processed in hours")
    most_common_language: Optional[str] = Field(None, description="Most commonly detected language")
    success_rate: Optional[float] = Field(None, description="Success rate percentage")
    
    @validator('success_rate')
    def validate_success_rate(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Success rate must be between 0 and 100')
        return v


# Vector Store Schemas (Requisito 2 - Almacenamiento Vectorial)
class VectorStoreMetadata(BaseModel):
    """Metadata para almacenar en vector store."""
    conversation_id: str = Field(..., description="ID único de la conversación")
    patient_name: Optional[str] = Field(None, description="Nombre del paciente")
    diagnosis: Optional[str] = Field(None, description="Diagnóstico médico")
    date: Optional[str] = Field(None, description="Fecha de la conversación")
    symptoms: Optional[List[str]] = Field(None, description="Síntomas mencionados")
    urgency: Optional[str] = Field(None, description="Nivel de urgencia")
    created_at: datetime = Field(..., description="Timestamp de creación")
    document_type: str = Field(default="transcription", description="Tipo de documento")


class VectorStoreResponse(BaseModel):
    """Respuesta del almacenamiento vectorial."""
    stored: bool = Field(..., description="Si se almacenó correctamente")
    vector_id: str = Field(..., description="ID en el vector store")
    embedding_dimensions: int = Field(..., description="Dimensiones del embedding")
    collection_name: str = Field(..., description="Nombre de la colección")
    metadata_fields: int = Field(..., description="Cantidad de campos de metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class VectorStoreStatus(BaseModel):
    """Estado del vector store."""
    status: str = Field(..., description="Estado del vector store")
    collection_name: str = Field(..., description="Nombre de la colección")
    total_documents: int = Field(..., description="Total de documentos almacenados")
    total_embeddings: int = Field(..., description="Total de embeddings generados")
    embedding_model: str = Field(..., description="Modelo de embeddings utilizado")
    persist_directory: str = Field(..., description="Directorio de persistencia")
    last_updated: Optional[datetime] = Field(None, description="Última actualización")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StoredConversation(BaseModel):
    """Conversación almacenada en vector store."""
    vector_id: str = Field(..., description="ID en el vector store")
    conversation_id: str = Field(..., description="ID de la conversación original")
    patient_name: Optional[str] = Field(None, description="Nombre del paciente")
    stored_at: datetime = Field(..., description="Fecha de almacenamiento")
    text_preview: str = Field(..., description="Preview del texto almacenado")
    metadata: Dict[str, Any] = Field(..., description="Metadata asociada")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Chat Service Schemas (Requisito 3 - Chatbot vía API)
class ChatQuery(BaseModel):
    """Schema para consultas de chat."""
    query: str = Field(..., description="Pregunta o consulta en lenguaje natural", min_length=1, max_length=1000)
    max_results: int = Field(5, ge=1, le=20, description="Número máximo de resultados a considerar")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filtros opcionales para la búsqueda")
    include_sources: bool = Field(True, description="Si incluir fuentes en la respuesta")


class ChatSource(BaseModel):
    """Schema para fuentes de información en respuestas de chat."""
    conversation_id: str = Field(..., description="ID de la conversación origen")
    patient_name: Optional[str] = Field(None, description="Nombre del paciente")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Puntuación de relevancia")
    excerpt: str = Field(..., description="Extracto relevante del texto")
    date: Optional[str] = Field(None, description="Fecha de la conversación")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata adicional")


class ChatResponse(BaseModel):
    """Schema para respuestas del sistema de chat."""
    answer: str = Field(..., description="Respuesta generada por el sistema")
    sources: List[ChatSource] = Field(default_factory=list, description="Fuentes de información utilizadas")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Nivel de confianza de la respuesta")
    intent: str = Field(..., description="Intención detectada en la consulta")
    follow_up_suggestions: List[str] = Field(default_factory=list, description="Sugerencias de seguimiento")
    query_classification: Optional[Dict[str, Any]] = Field(None, description="Clasificación detallada de la consulta")
    processing_time_ms: Optional[int] = Field(None, description="Tiempo de procesamiento en milisegundos")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChatIntent(str, Enum):
    """Enumeración para tipos de intención en consultas de chat."""
    PATIENT_INFO = "patient_info"           # "¿Qué enfermedad tiene X?"
    CONDITION_LIST = "condition_list"       # "Listame pacientes con X"
    SYMPTOM_SEARCH = "symptom_search"       # "¿Quién tiene dolor de cabeza?"
    MEDICATION_INFO = "medication_info"     # "¿Qué medicamentos toma X?"
    GENERAL_QUERY = "general_query"         # Consultas generales
    TEMPORAL_QUERY = "temporal_query"       # "¿Qué pasó la semana pasada?"
    UNKNOWN = "unknown"                     # Intención no reconocida


class QueryAnalysis(BaseModel):
    """Schema para análisis de consultas."""
    original_query: str = Field(..., description="Consulta original")
    intent: ChatIntent = Field(..., description="Intención detectada")
    entities: Dict[str, List[str]] = Field(default_factory=dict, description="Entidades extraídas")
    normalized_query: str = Field(..., description="Consulta normalizada")
    search_terms: List[str] = Field(default_factory=list, description="Términos de búsqueda optimizados")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Filtros generados automáticamente")


class RAGContext(BaseModel):
    """Schema para contexto en el pipeline RAG."""
    query_analysis: QueryAnalysis = Field(..., description="Análisis de la consulta")
    retrieved_contexts: List[Dict[str, Any]] = Field(default_factory=list, description="Contextos recuperados")
    ranked_contexts: List[Dict[str, Any]] = Field(default_factory=list, description="Contextos ordenados por relevancia")
    final_context: str = Field(..., description="Contexto final para generación")
    context_length: int = Field(..., description="Longitud del contexto en caracteres")


class ChatStats(BaseModel):
    """Schema para estadísticas del sistema de chat."""
    total_queries: int = Field(..., description="Total de consultas procesadas")
    successful_queries: int = Field(..., description="Consultas exitosas")
    failed_queries: int = Field(..., description="Consultas fallidas")
    avg_response_time_ms: float = Field(..., description="Tiempo promedio de respuesta")
    intent_distribution: Dict[str, int] = Field(..., description="Distribución de intenciones")
    avg_confidence: float = Field(..., description="Confianza promedio de respuestas")
    most_common_queries: List[str] = Field(..., description="Consultas más frecuentes")


# Document Processing Schemas (PLUS Feature 4 - PDFs/Imágenes)
class DocumentUpload(BaseModel):
    """Schema para upload de documentos."""
    patient_name: Optional[str] = Field(None, description="Nombre del paciente (opcional)")
    document_type: Optional[str] = Field(None, description="Tipo de documento médico")
    description: Optional[str] = Field(None, description="Descripción del documento")


class DocumentProcessingStatus(str, Enum):
    """Estados de procesamiento de documentos."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class OCRResult(BaseModel):
    """Resultado del procesamiento OCR."""
    text: str = Field(..., description="Texto extraído")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confianza del OCR")
    page_count: Optional[int] = Field(None, description="Número de páginas procesadas")
    processing_time_ms: int = Field(..., description="Tiempo de procesamiento en milisegundos")
    language_detected: Optional[str] = Field(None, description="Idioma detectado")


class DocumentMetadata(BaseModel):
    """Metadata extraída de documentos."""
    patient_name: Optional[str] = Field(None, description="Nombre del paciente")
    document_date: Optional[str] = Field(None, description="Fecha del documento")
    document_type: Optional[str] = Field(None, description="Tipo de documento")
    medical_conditions: List[str] = Field(default_factory=list, description="Condiciones médicas encontradas")
    medications: List[str] = Field(default_factory=list, description="Medicamentos mencionados")
    medical_procedures: List[str] = Field(default_factory=list, description="Procedimientos médicos")


class DocumentResponse(BaseModel):
    """Respuesta del procesamiento de documentos."""
    document_id: str = Field(..., description="ID único del documento")
    filename: str = Field(..., description="Nombre del archivo")
    file_type: str = Field(..., description="Tipo de archivo (pdf, image)")
    file_size_bytes: int = Field(..., description="Tamaño del archivo en bytes")
    status: DocumentProcessingStatus = Field(..., description="Estado del procesamiento")
    ocr_result: Optional[OCRResult] = Field(None, description="Resultado del OCR")
    extracted_metadata: Optional[DocumentMetadata] = Field(None, description="Metadata extraída")
    vector_stored: bool = Field(False, description="Si fue almacenado en vector store")
    patient_association: Optional[str] = Field(None, description="Paciente asociado automáticamente")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Fecha de creación")
    processed_at: Optional[datetime] = Field(None, description="Fecha de procesamiento")
    error_message: Optional[str] = Field(None, description="Mensaje de error si falló")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Speaker Diarization Schemas (PLUS Feature 5 - Diferenciación de hablantes)
class SpeakerType(str, Enum):
    """Tipos de hablantes en contexto médico."""
    PROMOTOR = "promotor"
    PACIENTE = "paciente"
    UNKNOWN = "unknown"
    MULTIPLE = "multiple"  # Cuando hablan varios al mismo tiempo


class SpeakerSegment(BaseModel):
    """Segmento de audio con hablante identificado."""
    speaker: SpeakerType = Field(..., description="Tipo de hablante")
    text: str = Field(..., description="Texto transcrito del segmento")
    start_time: float = Field(..., ge=0.0, description="Tiempo de inicio en segundos")
    end_time: float = Field(..., gt=0.0, description="Tiempo de fin en segundos")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confianza de la clasificación")
    word_count: int = Field(..., ge=0, description="Número de palabras en el segmento")
    
    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, v, info):
        """Validar que end_time > start_time."""
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("end_time debe ser mayor que start_time")
        return v


class SpeakerStats(BaseModel):
    """Estadísticas de participación por hablante."""
    total_speakers: int = Field(..., ge=0, description="Número total de hablantes detectados")
    promotor_time: float = Field(0.0, ge=0.0, description="Tiempo total del promotor en segundos")
    paciente_time: float = Field(0.0, ge=0.0, description="Tiempo total del paciente en segundos")
    unknown_time: float = Field(0.0, ge=0.0, description="Tiempo no clasificado en segundos")
    overlap_time: float = Field(0.0, ge=0.0, description="Tiempo de solapamiento en segundos")
    total_duration: float = Field(..., gt=0.0, description="Duración total del audio en segundos")
    speaker_changes: int = Field(0, ge=0, description="Número de cambios de hablante")
    average_segment_length: float = Field(0.0, ge=0.0, description="Duración promedio de segmentos")


class DiarizationResult(BaseModel):
    """Resultado completo de la diarización de hablantes."""
    speaker_segments: List[SpeakerSegment] = Field(..., description="Segmentos con hablantes identificados")
    speaker_stats: SpeakerStats = Field(..., description="Estadísticas de participación")
    processing_time_ms: int = Field(..., description="Tiempo de procesamiento en milisegundos")
    algorithm_version: str = Field("1.0", description="Versión del algoritmo usado")
    confidence_threshold: float = Field(..., description="Umbral de confianza usado")
    
    @field_validator("speaker_segments")
    @classmethod
    def validate_segments_order(cls, v):
        """Validar que los segmentos estén ordenados cronológicamente."""
        if len(v) < 2:
            return v
        
        for i in range(1, len(v)):
            if v[i].start_time < v[i-1].start_time:
                raise ValueError("Los segmentos deben estar ordenados cronológicamente")
        return v


class TranscriptionWithSpeakers(TranscriptionResponse):
    """Transcripción extendida con información de hablantes."""
    diarization_result: Optional[DiarizationResult] = Field(None, description="Resultado de diarización")
    speaker_summary: Optional[Dict[str, Any]] = Field(None, description="Resumen por hablante")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Document Integration Schemas
class DocumentSearchQuery(BaseModel):
    """Consulta para búsqueda en documentos."""
    query: str = Field(..., description="Texto a buscar")
    patient_name: Optional[str] = Field(None, description="Filtrar por paciente")
    document_type: Optional[str] = Field(None, description="Filtrar por tipo de documento")
    date_from: Optional[str] = Field(None, description="Fecha desde (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="Fecha hasta (YYYY-MM-DD)")
    max_results: int = Field(10, ge=1, le=50, description="Máximo número de resultados")


class DocumentSearchResult(BaseModel):
    """Resultado de búsqueda en documentos."""
    document_id: str = Field(..., description="ID del documento")
    filename: str = Field(..., description="Nombre del archivo")
    patient_name: Optional[str] = Field(None, description="Paciente asociado")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Puntuación de relevancia")
    excerpt: str = Field(..., description="Extracto relevante")
    highlight: Optional[str] = Field(None, description="Texto resaltado")
    document_type: str = Field(..., description="Tipo de documento")
    created_at: datetime = Field(..., description="Fecha de creación")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }