"""
Modelos de base de datos para la aplicación ElSol Challenge.
Define modelos SQLAlchemy para transcripciones de audio y datos relacionados.
"""

import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, DateTime, Text, Integer, JSON, Enum, Float, ForeignKey

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Session, relationship
import enum


Base = declarative_base()


class TranscriptionStatus(str, enum.Enum):
    """Enumeración para estado de procesamiento de transcripción."""
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AudioTranscription(Base):
    """
    Modelo para almacenar datos de transcripción de audio y metadatos.
    
    Esta tabla almacena información sobre archivos de audio subidos,
    su estado de transcripción e información extraída.
    """
    __tablename__ = "audio_transcriptions"
    
    # Clave primaria
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Información del archivo
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)
    original_path = Column(String(500), nullable=True)
    
    # Processing status
    status = Column(Enum(TranscriptionStatus), default=TranscriptionStatus.PENDING, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Transcription results
    raw_transcription = Column(Text, nullable=True)
    confidence_score = Column(String(10), nullable=True)  # Whisper confidence if available
    
    # Extracted structured information (JSON format)
    structured_data = Column(JSON, nullable=True)
    
    # Extracted unstructured information (JSON format)  
    unstructured_data = Column(JSON, nullable=True)
    
    # Processing metadata
    processing_time_seconds = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    whisper_model_used = Column(String(50), nullable=True)
    
    # Additional metadata
    language_detected = Column(String(10), nullable=True)
    audio_duration_seconds = Column(Integer, nullable=True)
    
    # Vector Store Integration (Requisito 2 - Almacenamiento Vectorial)
    vector_stored = Column(String(50), default="false", nullable=False)  # "true", "false", "failed"
    vector_id = Column(String(100), nullable=True)  # ID en Chroma DB
    
    # Speaker Diarization (PLUS Feature 5 - Diferenciación de hablantes)
    speaker_segments = Column(Text, nullable=True)  # JSON array of speaker segments
    speaker_stats = Column(Text, nullable=True)  # JSON object with speaker statistics
    diarization_processed = Column(String(10), default="false", nullable=False)  # "true", "false", "failed"
    
    # Relationships
    documents = relationship("Document", back_populates="conversation")

    def __repr__(self) -> str:
        return f"<AudioTranscription(id={self.id}, filename={self.filename}, status={self.status})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            "id": self.id,
            "filename": self.filename,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "raw_transcription": self.raw_transcription,
            "confidence_score": self.confidence_score,
            "structured_data": self.structured_data,
            "unstructured_data": self.unstructured_data,
            "processing_time_seconds": self.processing_time_seconds,
            "error_message": self.error_message,
            "language_detected": self.language_detected,
            "audio_duration_seconds": self.audio_duration_seconds,
            "vector_stored": self.vector_stored,
            "vector_id": self.vector_id,
            "speaker_segments": self.speaker_segments,
            "speaker_stats": self.speaker_stats,
            "diarization_processed": self.diarization_processed
        }
    
    @classmethod
    def create_from_upload(
        cls,
        filename: str,
        file_size: int,
        file_type: str,
        file_path: Optional[str] = None
    ) -> "AudioTranscription":
        """Factory method to create a new transcription from file upload."""
        return cls(
            filename=filename,
            file_size=file_size,
            file_type=file_type,
            original_path=file_path,
            status=TranscriptionStatus.PENDING
        )
    
    def mark_processing(self) -> None:
        """Mark transcription as currently being processed."""
        self.status = TranscriptionStatus.PROCESSING
        self.updated_at = datetime.utcnow()
    
    def mark_completed(
        self,
        raw_transcription: str,
        structured_data: Dict[str, Any],
        unstructured_data: Dict[str, Any],
        processing_time: int,
        confidence_score: Optional[str] = None,
        language_detected: Optional[str] = None,
        audio_duration: Optional[int] = None
    ) -> None:
        """Mark transcription as completed with results."""
        self.status = TranscriptionStatus.COMPLETED
        self.processed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.raw_transcription = raw_transcription
        self.structured_data = structured_data
        self.unstructured_data = unstructured_data
        self.processing_time_seconds = processing_time
        self.confidence_score = confidence_score
        self.language_detected = language_detected
        self.audio_duration_seconds = audio_duration
    
    def mark_failed(self, error_message: str) -> None:
        """Mark transcription as failed with error message."""
        self.status = TranscriptionStatus.FAILED
        self.processed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.error_message = error_message
    
    def mark_vector_stored(self, vector_id: str) -> None:
        """Mark transcription as stored in vector database."""
        self.vector_stored = "true"
        self.vector_id = vector_id
        self.updated_at = datetime.utcnow()
    
    def mark_vector_failed(self) -> None:
        """Mark vector storage as failed."""
        self.vector_stored = "failed"
        self.updated_at = datetime.utcnow()
    
    def set_speaker_data(self, segments: list, stats: dict) -> None:
        """Set speaker diarization data."""
        self.speaker_segments = json.dumps(segments, ensure_ascii=False)
        self.speaker_stats = json.dumps(stats, ensure_ascii=False)
        self.diarization_processed = "true"
        self.updated_at = datetime.utcnow()
    
    def mark_diarization_failed(self) -> None:
        """Mark speaker diarization as failed."""
        self.diarization_processed = "failed"
        self.updated_at = datetime.utcnow()


# PLUS Feature 4: Document Processing Model
class Document(Base):
    """Modelo para documentos procesados (PDFs e imágenes)."""
    __tablename__ = "documents"
    
    id = Column(String(50), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # 'pdf', 'image'
    file_size_bytes = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    
    # Processing status
    status = Column(String(20), default="pending", nullable=False)
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # OCR/PDF extraction results
    extracted_text = Column(Text, nullable=True)
    ocr_confidence = Column(Float, nullable=True)  # Solo para imágenes
    page_count = Column(Integer, nullable=True)
    language_detected = Column(String(10), nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    
    # Medical metadata extracted by AI
    patient_name = Column(String(100), nullable=True, index=True)
    document_date = Column(String(20), nullable=True)
    document_type = Column(String(50), nullable=True)
    medical_conditions = Column(Text, nullable=True)  # JSON array
    medications = Column(Text, nullable=True)  # JSON array
    medical_procedures = Column(Text, nullable=True)  # JSON array
    
    # Vector store integration
    vector_stored = Column(String(10), default="false", nullable=False)
    vector_id = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship (optional association with conversations)
    conversation_id = Column(String(50), ForeignKey("audio_transcriptions.id"), nullable=True)
    conversation = relationship("AudioTranscription", back_populates="documents")
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        try:
            medical_conditions = json.loads(self.medical_conditions) if self.medical_conditions else []
        except (json.JSONDecodeError, TypeError):
            medical_conditions = []
            
        try:
            medications = json.loads(self.medications) if self.medications else []
        except (json.JSONDecodeError, TypeError):
            medications = []
            
        try:
            medical_procedures = json.loads(self.medical_procedures) if self.medical_procedures else []
        except (json.JSONDecodeError, TypeError):
            medical_procedures = []
        
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_type": self.file_type,
            "file_size_bytes": self.file_size_bytes,
            "status": self.status,
            "processed_at": self.processed_at,
            "error_message": self.error_message,
            "extracted_text": self.extracted_text,
            "ocr_confidence": self.ocr_confidence,
            "page_count": self.page_count,
            "language_detected": self.language_detected,
            "processing_time_ms": self.processing_time_ms,
            "patient_name": self.patient_name,
            "document_date": self.document_date,
            "document_type": self.document_type,
            "medical_conditions": medical_conditions,
            "medications": medications,
            "medical_procedures": medical_procedures,
            "vector_stored": self.vector_stored,
            "vector_id": self.vector_id,
            "conversation_id": self.conversation_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def mark_processing(self) -> None:
        """Mark document as being processed."""
        self.status = "processing"
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self, processing_time_ms: int) -> None:
        """Mark document processing as completed."""
        self.status = "completed"
        self.processed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.processing_time_ms = processing_time_ms
    
    def mark_failed(self, error_message: str) -> None:
        """Mark document processing as failed."""
        self.status = "failed"
        self.processed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.error_message = error_message
    
    def mark_vector_stored(self, vector_id: str) -> None:
        """Mark document as stored in vector database."""
        self.vector_stored = "true"
        self.vector_id = vector_id
        self.updated_at = datetime.utcnow()
    
    def set_medical_metadata(self, metadata: dict) -> None:
        """Set medical metadata extracted by AI."""
        if "patient_name" in metadata:
            self.patient_name = metadata["patient_name"]
        if "document_date" in metadata:
            self.document_date = metadata["document_date"]
        if "document_type" in metadata:
            self.document_type = metadata["document_type"]
        if "medical_conditions" in metadata:
            self.medical_conditions = json.dumps(metadata["medical_conditions"], ensure_ascii=False)
        if "medications" in metadata:
            self.medications = json.dumps(metadata["medications"], ensure_ascii=False)
        if "medical_procedures" in metadata:
            self.medical_procedures = json.dumps(metadata["medical_procedures"], ensure_ascii=False)
        
        self.updated_at = datetime.utcnow()


class ConversationMetadata(Base):
    """
    Extended metadata for conversations (future use).
    
    This table can store additional conversation-specific information
    that might be needed for advanced features like speaker diarization.
    """
    __tablename__ = "conversation_metadata"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transcription_id = Column(String, nullable=False)  # Foreign key to AudioTranscription
    
    # Speaker information (for future diarization feature)
    speaker_count = Column(Integer, nullable=True)
    speaker_segments = Column(JSON, nullable=True)  # List of speaker segments
    
    # Conversation classification
    conversation_type = Column(String(100), nullable=True)  # e.g., "medical_consultation"
    topic_tags = Column(JSON, nullable=True)  # List of detected topics
    
    # Quality metrics
    audio_quality_score = Column(String(10), nullable=True)
    transcription_quality_score = Column(String(10), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<ConversationMetadata(id={self.id}, transcription_id={self.transcription_id})>"


# Database utility functions
def get_transcription_by_id(db: Session, transcription_id: str) -> Optional[AudioTranscription]:
    """Get transcription by ID."""
    return db.query(AudioTranscription).filter(AudioTranscription.id == transcription_id).first()


def get_transcriptions(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    status: Optional[TranscriptionStatus] = None
) -> list[AudioTranscription]:
    """Get list of transcriptions with optional filtering."""
    query = db.query(AudioTranscription)
    
    if status:
        query = query.filter(AudioTranscription.status == status)
    
    return query.offset(skip).limit(limit).all()


def create_transcription(db: Session, transcription: AudioTranscription) -> AudioTranscription:
    """Create new transcription record."""
    db.add(transcription)
    db.commit()
    db.refresh(transcription)
    return transcription


def update_transcription(db: Session, transcription: AudioTranscription) -> AudioTranscription:
    """Update existing transcription record."""
    db.commit()
    db.refresh(transcription)
    return transcription
