# Schemas de Base de Datos - ElSol Challenge

## Descripción General
El sistema utiliza SQLAlchemy como ORM con SQLite para desarrollo y compatibilidad con PostgreSQL/MySQL para producción. Los modelos están diseñados para almacenar tanto datos estructurados como información en formato JSON para flexibilidad en datos médicos complejos.

## Arquitectura de Base de Datos

### Configuración de Conexión
```python
# database/connection.py
DATABASE_URL = "sqlite:///./conversations.db"  # Desarrollo
# DATABASE_URL = "postgresql://user:pass@host:port/db"  # Producción

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

### Base Declarativa
```python
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
```

## Modelos de Datos

### 1. AudioTranscription (Tabla Principal)

**Propósito:** Almacenar transcripciones de audio y toda la información médica extraída.

```python
class AudioTranscription(Base):
    __tablename__ = "audio_transcriptions"
    
    # Clave primaria
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Información del archivo
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)
    original_path = Column(String(500), nullable=True)
    
    # Estado de procesamiento
    status = Column(Enum(TranscriptionStatus), default=TranscriptionStatus.PENDING, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Resultados de transcripción
    raw_transcription = Column(Text, nullable=True)
    confidence_score = Column(String(10), nullable=True)
    
    # Información estructurada extraída (JSON)
    structured_data = Column(JSON, nullable=True)
    
    # Información no estructurada (JSON)
    unstructured_data = Column(JSON, nullable=True)
    
    # Metadata de procesamiento
    processing_time_seconds = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    whisper_model_used = Column(String(50), nullable=True)
    language_detected = Column(String(10), nullable=True)
    audio_duration_seconds = Column(Integer, nullable=True)
    
    # Integración Vector Store
    vector_stored = Column(String(50), default="false", nullable=False)
    vector_id = Column(String(100), nullable=True)
    
    # Speaker Diarization
    speaker_segments = Column(Text, nullable=True)  # JSON array
    speaker_stats = Column(Text, nullable=True)     # JSON object
    diarization_processed = Column(String(10), default="false", nullable=False)
    
    # Relaciones
    documents = relationship("Document", back_populates="conversation")
```

#### Enumeración TranscriptionStatus
```python
class TranscriptionStatus(str, enum.Enum):
    PENDING = "pending"       # Archivo subido, esperando procesamiento
    PROCESSING = "processing" # En procesamiento activo
    COMPLETED = "completed"   # Procesamiento completado exitosamente
    FAILED = "failed"        # Falló el procesamiento
    CANCELLED = "cancelled"   # Procesamiento cancelado
```

#### Estructura de Datos JSON

**structured_data (JSON):**
```json
{
    "nombre": "Juan Pérez",
    "edad": 45,
    "fecha": "2024-01-15",
    "diagnostico": "hipertensión arterial",
    "medico": "Dr. García",
    "medicamentos": ["losartan", "amlodipino"],
    "telefono": "+1234567890",
    "email": "juan.perez@email.com"
}
```

**unstructured_data (JSON):**
```json
{
    "sintomas": ["dolor de cabeza", "mareos", "fatiga"],
    "contexto": "consulta de seguimiento para hipertensión",
    "observaciones": "paciente muestra buena adherencia al tratamiento",
    "emociones": ["preocupación", "alivio"],
    "urgencia": "media",
    "recomendaciones": ["continuar medicación", "dieta baja en sodio"],
    "preguntas": ["¿Cuándo debo regresar?", "¿Puedo hacer ejercicio?"],
    "respuestas": ["seguimiento en 3 meses", "ejercicio ligero recomendado"]
}
```

**speaker_segments (JSON Text):**
```json
[
    {
        "speaker": "promotor",
        "text": "Buenos días, ¿cómo se siente hoy?",
        "start_time": 0.0,
        "end_time": 3.2,
        "confidence": 0.89,
        "word_count": 6
    },
    {
        "speaker": "paciente",
        "text": "Me duele mucho la cabeza desde ayer",
        "start_time": 3.5,
        "end_time": 7.1,
        "confidence": 0.82,
        "word_count": 7
    }
]
```

**speaker_stats (JSON Text):**
```json
{
    "total_speakers": 2,
    "promotor_time": 45.3,
    "paciente_time": 38.7,
    "unknown_time": 0.0,
    "overlap_time": 0.0,
    "total_duration": 84.0,
    "speaker_changes": 12,
    "average_segment_length": 7.0
}
```

#### Métodos del Modelo
```python
# Factory method
@classmethod
def create_from_upload(cls, filename: str, file_size: int, file_type: str, file_path: str = None) -> "AudioTranscription"

# Estado de procesamiento
def mark_processing(self) -> None
def mark_completed(self, raw_transcription: str, structured_data: Dict, unstructured_data: Dict, processing_time: int, **kwargs) -> None
def mark_failed(self, error_message: str) -> None

# Vector store
def mark_vector_stored(self, vector_id: str) -> None
def mark_vector_failed(self) -> None

# Speaker diarization
def set_speaker_data(self, segments: list, stats: dict) -> None
def mark_diarization_failed(self) -> None

# Conversión
def to_dict(self) -> Dict[str, Any]
```

### 2. Document (Procesamiento de Documentos)

**Propósito:** Almacenar documentos médicos procesados (PDFs e imágenes) con OCR y metadata extraída.

```python
class Document(Base):
    __tablename__ = "documents"
    
    # Identificación
    id = Column(String(50), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # 'pdf', 'image'
    file_size_bytes = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    
    # Estado de procesamiento
    status = Column(String(20), default="pending", nullable=False)
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Resultados OCR/extracción
    extracted_text = Column(Text, nullable=True)
    ocr_confidence = Column(Float, nullable=True)  # Solo para imágenes
    page_count = Column(Integer, nullable=True)
    language_detected = Column(String(10), nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    
    # Metadata médica extraída por IA
    patient_name = Column(String(100), nullable=True, index=True)
    document_date = Column(String(20), nullable=True)
    document_type = Column(String(50), nullable=True)
    medical_conditions = Column(Text, nullable=True)  # JSON array
    medications = Column(Text, nullable=True)         # JSON array
    medical_procedures = Column(Text, nullable=True)  # JSON array
    
    # Integración vector store
    vector_stored = Column(String(10), default="false", nullable=False)
    vector_id = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relación opcional con conversaciones
    conversation_id = Column(String(50), ForeignKey("audio_transcriptions.id"), nullable=True)
    conversation = relationship("AudioTranscription", back_populates="documents")
```

#### Estructura de Metadata Médica JSON
```json
{
    "medical_conditions": ["diabetes tipo 2", "hipertensión arterial"],
    "medications": ["metformina 850mg", "losartan 50mg", "amlodipino 5mg"],
    "medical_procedures": ["química sanguínea", "hemograma completo", "electrocardiograma"]
}
```

#### Métodos del Modelo
```python
def to_dict(self) -> dict
def mark_processing(self) -> None
def mark_completed(self, processing_time_ms: int) -> None
def mark_failed(self, error_message: str) -> None
def mark_vector_stored(self, vector_id: str) -> None
def set_medical_metadata(self, metadata: dict) -> None
```

### 3. ConversationMetadata (Metadata Extendida)

**Propósito:** Almacenar metadata adicional para conversaciones (uso futuro y analytics).

```python
class ConversationMetadata(Base):
    __tablename__ = "conversation_metadata"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transcription_id = Column(String, nullable=False)  # FK a AudioTranscription
    
    # Información de hablantes
    speaker_count = Column(Integer, nullable=True)
    speaker_segments = Column(JSON, nullable=True)
    
    # Clasificación de conversación
    conversation_type = Column(String(100), nullable=True)  # "medical_consultation"
    topic_tags = Column(JSON, nullable=True)  # ["diabetes", "seguimiento"]
    
    # Métricas de calidad
    audio_quality_score = Column(String(10), nullable=True)
    transcription_quality_score = Column(String(10), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

## Funciones de Utilidad de Base de Datos

### CRUD Operations
```python
# Transcripciones
def get_transcription_by_id(db: Session, transcription_id: str) -> Optional[AudioTranscription]
def get_transcriptions(db: Session, skip: int = 0, limit: int = 100, status: Optional[TranscriptionStatus] = None) -> List[AudioTranscription]
def create_transcription(db: Session, transcription: AudioTranscription) -> AudioTranscription
def update_transcription(db: Session, transcription: AudioTranscription) -> AudioTranscription

# Documentos
def get_document_by_id(db: Session, document_id: str) -> Optional[Document]
def get_documents_by_patient(db: Session, patient_name: str) -> List[Document]
def create_document(db: Session, document: Document) -> Document
def update_document(db: Session, document: Document) -> Document
```

## Diagramas de Base de Datos

### Diagrama Entidad-Relación

```mermaid
erDiagram
    AudioTranscription {
        string id PK
        string filename
        integer file_size
        string file_type
        string status
        datetime created_at
        datetime processed_at
        datetime updated_at
        text raw_transcription
        string confidence_score
        json structured_data
        json unstructured_data
        integer processing_time_seconds
        text error_message
        string whisper_model_used
        string language_detected
        integer audio_duration_seconds
        string vector_stored
        string vector_id
        text speaker_segments
        text speaker_stats
        string diarization_processed
    }
    
    Document {
        string id PK
        string filename
        string original_filename
        string file_type
        integer file_size_bytes
        string file_path
        string status
        datetime processed_at
        text error_message
        text extracted_text
        float ocr_confidence
        integer page_count
        string language_detected
        integer processing_time_ms
        string patient_name
        string document_date
        string document_type
        text medical_conditions
        text medications
        text medical_procedures
        string vector_stored
        string vector_id
        datetime created_at
        datetime updated_at
        string conversation_id FK
    }
    
    ConversationMetadata {
        string id PK
        string transcription_id FK
        integer speaker_count
        json speaker_segments
        string conversation_type
        json topic_tags
        string audio_quality_score
        string transcription_quality_score
        datetime created_at
        datetime updated_at
    }
    
    AudioTranscription ||--o{ Document : "conversation_id"
    AudioTranscription ||--o| ConversationMetadata : "transcription_id"
```

### Diagrama de Flujo de Datos

```mermaid
flowchart TD
    A[Audio Upload] --> B[AudioTranscription Record]
    B --> C[Whisper Processing]
    C --> D[Update raw_transcription]
    D --> E[OpenAI Extraction]
    E --> F[Update structured_data]
    E --> G[Update unstructured_data]
    F --> H[Vector Store]
    G --> H
    H --> I[Update vector_stored/vector_id]
    
    J[Document Upload] --> K[Document Record]
    K --> L[OCR/PDF Processing]
    L --> M[Update extracted_text]
    M --> N[AI Metadata Extraction]
    N --> O[Update medical metadata]
    O --> P[Vector Store]
    P --> Q[Update vector_stored/vector_id]
    
    R[Speaker Diarization] --> S[Update speaker_segments]
    R --> T[Update speaker_stats]
    
    style A fill:#e1f5fe
    style J fill:#e8f5e8
    style H fill:#fff3e0
    style P fill:#fff3e0
```

## Índices y Optimizaciones

### Índices Principales
```sql
-- Índices automáticos por primary keys y foreign keys
CREATE INDEX idx_audio_transcriptions_status ON audio_transcriptions(status);
CREATE INDEX idx_audio_transcriptions_created_at ON audio_transcriptions(created_at);
CREATE INDEX idx_audio_transcriptions_vector_stored ON audio_transcriptions(vector_stored);

CREATE INDEX idx_documents_patient_name ON documents(patient_name);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_conversation_id ON documents(conversation_id);

CREATE INDEX idx_conversation_metadata_transcription_id ON conversation_metadata(transcription_id);
```

### Consultas Optimizadas
```python
# Consultas frecuentes optimizadas
def get_recent_transcriptions(db: Session, limit: int = 10):
    return db.query(AudioTranscription)\
        .filter(AudioTranscription.status == TranscriptionStatus.COMPLETED)\
        .order_by(AudioTranscription.created_at.desc())\
        .limit(limit).all()

def get_transcriptions_by_patient(db: Session, patient_name: str):
    return db.query(AudioTranscription)\
        .filter(AudioTranscription.structured_data.contains({"nombre": patient_name}))\
        .order_by(AudioTranscription.created_at.desc()).all()

def get_pending_transcriptions(db: Session):
    return db.query(AudioTranscription)\
        .filter(AudioTranscription.status.in_([TranscriptionStatus.PENDING, TranscriptionStatus.PROCESSING]))\
        .order_by(AudioTranscription.created_at.asc()).all()
```

## Validaciones y Constraints

### Validaciones a Nivel de Modelo
```python
from sqlalchemy.orm import validates

class AudioTranscription(Base):
    @validates('file_size')
    def validate_file_size(self, key, file_size):
        assert file_size > 0, "File size must be positive"
        assert file_size <= 26_214_400, "File size exceeds maximum limit (25MB)"
        return file_size
    
    @validates('status')
    def validate_status(self, key, status):
        assert status in TranscriptionStatus.__members__.values()
        return status
```

### Constraints de Base de Datos
```sql
-- Constraints adicionales para SQLite/PostgreSQL
ALTER TABLE audio_transcriptions 
ADD CONSTRAINT chk_file_size CHECK (file_size > 0);

ALTER TABLE audio_transcriptions 
ADD CONSTRAINT chk_vector_stored CHECK (vector_stored IN ('true', 'false', 'failed'));

ALTER TABLE documents 
ADD CONSTRAINT chk_file_type CHECK (file_type IN ('pdf', 'image'));

ALTER TABLE documents 
ADD CONSTRAINT chk_ocr_confidence CHECK (ocr_confidence BETWEEN 0.0 AND 1.0);
```

## Migración y Versionado

### Alembic Configuration
```python
# alembic/env.py
from app.database.models import Base
target_metadata = Base.metadata

# Migrations commands
# alembic revision --autogenerate -m "Add speaker diarization fields"
# alembic upgrade head
```

### Scripts de Migración Ejemplo
```python
# Migration: Add speaker diarization support
def upgrade():
    op.add_column('audio_transcriptions', sa.Column('speaker_segments', sa.Text(), nullable=True))
    op.add_column('audio_transcriptions', sa.Column('speaker_stats', sa.Text(), nullable=True))
    op.add_column('audio_transcriptions', sa.Column('diarization_processed', sa.String(10), server_default='false', nullable=False))

def downgrade():
    op.drop_column('audio_transcriptions', 'diarization_processed')
    op.drop_column('audio_transcriptions', 'speaker_stats')
    op.drop_column('audio_transcriptions', 'speaker_segments')
```

## Configuración para Producción

### PostgreSQL Configuration
```python
# Production database settings
DATABASE_URL = "postgresql://user:password@host:5432/elsol_db"

# Connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### Backup y Recovery
```bash
# PostgreSQL backup
pg_dump -h localhost -U user -d elsol_db > backup_$(date +%Y%m%d).sql

# SQLite backup
sqlite3 conversations.db ".backup backup_$(date +%Y%m%d).db"
```

## Monitoreo y Métricas

### Queries de Monitoreo
```sql
-- Estado de transcripciones
SELECT status, COUNT(*) as count 
FROM audio_transcriptions 
GROUP BY status;

-- Tiempo promedio de procesamiento
SELECT AVG(processing_time_seconds) as avg_processing_time
FROM audio_transcriptions 
WHERE status = 'completed';

-- Distribución de tipos de documento
SELECT document_type, COUNT(*) as count
FROM documents 
WHERE document_type IS NOT NULL
GROUP BY document_type;

-- Vector store statistics
SELECT 
    vector_stored,
    COUNT(*) as count
FROM audio_transcriptions 
GROUP BY vector_stored;
```

### Alertas Recomendadas
- Transcripciones fallidas > 5% en últimas 24h
- Tiempo promedio de procesamiento > 5 minutos
- Espacio en disco < 1GB disponible
- Documentos sin procesar > 100
- Vector store errors > 10% en último día

## Mejores Prácticas

### Gestión de Transacciones
```python
# Context manager para transacciones
@contextmanager
def db_transaction(db: Session):
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# Uso
with db_transaction(get_db()) as db:
    transcription = create_transcription(db, transcription_data)
    update_vector_status(db, transcription.id, "stored")
```

### Manejo de JSON Fields
```python
# Validación de JSON estructurado
from pydantic import BaseModel, validator

class StructuredDataModel(BaseModel):
    nombre: Optional[str]
    edad: Optional[int]
    diagnostico: Optional[str]
    medicamentos: List[str] = []
    
    @validator('edad')
    def validate_age(cls, v):
        if v is not None and (v < 0 or v > 150):
            raise ValueError('Age must be between 0 and 150')
        return v

# Al guardar en BD
structured_data = StructuredDataModel(**extracted_data).dict()
transcription.structured_data = structured_data
```

### Performance Optimization
```python
# Lazy loading para relaciones
documents = relationship("Document", back_populates="conversation", lazy="select")

# Bulk operations para grandes volúmenes
def bulk_update_vector_status(db: Session, transcription_ids: List[str], status: str):
    db.query(AudioTranscription)\
        .filter(AudioTranscription.id.in_(transcription_ids))\
        .update({"vector_stored": status}, synchronize_session=False)
    db.commit()
```
