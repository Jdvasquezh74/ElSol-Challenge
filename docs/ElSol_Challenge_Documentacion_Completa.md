# ElSol Challenge - Documentación Técnica Completa

**Proyecto:** ElSol Challenge - Plataforma Médica Inteligente  
**Versión:** 1.0.0  
**Fecha:** Enero 2025  
**Autor:** Equipo de Desarrollo ElSol Challenge  

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Arquitectura General del Sistema](#2-arquitectura-general-del-sistema)
3. [Servicios Principales](#3-servicios-principales)
   - 3.1 [Servicio de Transcripción Whisper](#31-servicio-de-transcripción-whisper)
   - 3.2 [Servicio de Extracción OpenAI](#32-servicio-de-extracción-openai)
   - 3.3 [Servicio Vector Store](#33-servicio-vector-store)
   - 3.4 [Servicio Chat RAG](#34-servicio-chat-rag)
   - 3.5 [Servicio OCR y Documentos](#35-servicio-ocr-y-documentos)
   - 3.6 [Servicio Speaker Diarization](#36-servicio-speaker-diarization)
4. [API y Endpoints](#4-api-y-endpoints)
5. [Base de Datos y Schemas](#5-base-de-datos-y-schemas)
6. [Decisiones Arquitectónicas](#6-decisiones-arquitectónicas)
7. [Migración a Microservicios](#7-migración-a-microservicios)
8. [Despliegue y Operaciones](#8-despliegue-y-operaciones)

---

## 1. Resumen Ejecutivo

ElSol Challenge es una plataforma médica inteligente que combina transcripción de audio, procesamiento de documentos, almacenamiento vectorial y un sistema de chat RAG para crear un asistente médico completo.

El sistema está construido como un **monolito modular** usando Python/FastAPI en el backend y React/TypeScript en el frontend, diseñado para evolucionar gradualmente hacia microservicios cuando sea necesario.

### Características Principales

- **🎤 Transcripción de Audio**: Whisper local para privacidad médica
- **🤖 Extracción de Información**: Azure OpenAI para datos médicos estructurados
- **🔍 Almacenamiento Vectorial**: ChromaDB para búsqueda semántica
- **💬 Chat Inteligente**: Sistema RAG completo
- **📄 Procesamiento de Documentos**: OCR y extracción de PDFs médicos
- **👥 Diferenciación de Hablantes**: Clasificación promotor vs. paciente

### Stack Tecnológico

**Backend:**
- Framework: FastAPI (Python)
- Base de Datos: SQLite (dev) / PostgreSQL (prod)
- ORM: SQLAlchemy con Alembic
- Vector DB: ChromaDB
- Embeddings: sentence-transformers
- Transcripción: OpenAI Whisper (local)
- IA: Azure OpenAI GPT-4
- OCR: Tesseract + PyPDF2

**Frontend:**
- Framework: React 18 + TypeScript
- Styling: Tailwind CSS
- Build Tool: Vite
- HTTP Client: Axios
- State Management: React Hooks

---

## 2. Arquitectura General del Sistema

### 2.1 Arquitectura de Alto Nivel

![Arquitectura Alto Nivel](images/arquitectura-alto-nivel.png)

La arquitectura sigue un patrón de capas bien definidas:

1. **Presentation Layer**: React Frontend + FastAPI
2. **Business Logic Layer**: Servicios especializados
3. **Data Access Layer**: ORM + Vector DB Client
4. **Infrastructure Layer**: Bases de datos y servicios externos

### 2.2 Flujo de Datos Principal

![Flujo de Datos](images/flujo-datos-principal.png)

**Pipeline de Audio:**
1. Audio Upload → Whisper Transcription
2. Transcription → OpenAI Information Extraction
3. Extraction → Vector Store Storage
4. Vector Storage → Speaker Diarization

**Pipeline de Documentos:**
1. Document Upload → OCR/PDF Processing
2. Text Extraction → Medical Metadata Extraction
3. Metadata → Vector Store Storage

**Pipeline RAG:**
1. User Query → RAG Pipeline
2. Vector Search → Context Ranking
3. Context → GPT-4 Response Generation

### 2.3 Arquitectura de Servicios

![Arquitectura de Servicios](images/arquitectura-servicios.png)

El sistema implementa una arquitectura modular con servicios especializados:

- **WhisperService**: Transcripción de audio local
- **OpenAIService**: Extracción de información y chat
- **VectorStoreService**: Almacenamiento vectorial
- **ChatService**: Sistema RAG completo
- **OCRService**: Procesamiento de documentos
- **SpeakerService**: Diferenciación de hablantes

---

## 3. Servicios Principales

### 3.1 Servicio de Transcripción Whisper

#### Descripción General
El servicio de transcripción Whisper es el componente central para convertir archivos de audio en texto utilizando el modelo Whisper de OpenAI ejecutado localmente. Este servicio no requiere conexión a internet ni API keys, proporcionando privacidad y control total sobre los datos médicos.

#### Clase Principal: `LocalWhisperService`

**Responsabilidades:**
- Carga lazy del modelo Whisper
- Validación de archivos de audio
- Transcripción con parámetros configurables
- Cálculo de métricas de confianza
- Detección automática de idioma

**Atributos principales:**
```python
- model_name: str        # Modelo Whisper a usar (tiny, base, small, medium, large)
- device: str           # Dispositivo de ejecución (cpu/cuda)
- model: whisper.Model  # Instancia del modelo cargado
- timeout: int          # Timeout para transcripción
```

#### Integración con Core y Database

**Configuración (`app.core.config`):**
```python
WHISPER_MODEL: str = "base"           # Modelo a usar
WHISPER_DEVICE: str = "cpu"           # cpu o cuda
TRANSCRIPTION_TIMEOUT: int = 300      # 5 minutos
UPLOAD_MAX_SIZE: int = 26_214_400     # 25MB
UPLOAD_ALLOWED_EXTENSIONS: List[str]  # [wav, mp3]
```

**Database Models (`app.database.models`):**
Integración con `AudioTranscription`:
```python
raw_transcription: str
confidence_score: str
language_detected: str
audio_duration_seconds: int
processing_time_seconds: int
whisper_model_used: str
```

#### Características Técnicas

**Modelos Whisper Disponibles:**
- **tiny**: ~39 MB, ~32x speed, precisión básica
- **base**: ~74 MB, ~16x speed, buena precisión
- **small**: ~244 MB, ~6x speed, muy buena precisión
- **medium**: ~769 MB, ~2x speed, excelente precisión
- **large**: ~1550 MB, ~1x speed, máxima precisión

**Validaciones Implementadas:**
1. Archivo existente y tamaño válido
2. Extensión permitida (wav, mp3)
3. Magic numbers (RIFF/WAVE, ID3/MP3)
4. Límites de tamaño (25MB máximo)

#### API Endpoints Asociados

- **`POST /upload-audio`**: Carga de archivos con procesamiento asíncrono
- **`GET /transcriptions/{id}`**: Consulta de estado y resultados

---

### 3.2 Servicio de Extracción OpenAI

#### Descripción General
El servicio OpenAI es responsable de extraer información estructurada y no estructurada de las transcripciones de audio utilizando modelos de Azure OpenAI. Este servicio transforma texto crudo en datos médicos organizados y útiles para análisis posterior.

#### Clase Principal: `OpenAIService`

**Responsabilidades:**
- Comunicación con Azure OpenAI API
- Extracción de información estructurada (nombres, edades, diagnósticos)
- Análisis de datos no estructurados (síntomas, emociones, contexto)
- Generación de respuestas para el chatbot
- Validación y limpieza de datos extraídos

#### Prompts Especializados

**Extracción Estructurada:**
```python
STRUCTURED_EXTRACTION_PROMPT = """
Eres un asistente médico especializado en extraer información específica 
de conversaciones médicas. Analiza esta transcripción y extrae ÚNICAMENTE 
la información que esté explícitamente mencionada.

CAMPOS A EXTRAER:
- nombre: Nombre del paciente
- edad: Edad mencionada (0-150)
- fecha: Fecha de la conversación
- diagnostico: Diagnóstico médico
- medico: Nombre del médico/profesional
- medicamentos: Lista de medicamentos mencionados
- telefono: Número de teléfono
- email: Correo electrónico
"""
```

**Análisis No Estructurado:**
```python
UNSTRUCTURED_ANALYSIS_PROMPT = """
Analiza esta conversación médica y extrae información contextual y emocional.
Enfócate en aspectos que no son datos específicos pero son importantes 
para el seguimiento médico.

CAMPOS A ANALIZAR:
- sintomas: Lista de síntomas mencionados
- contexto: Contexto general de la conversación
- observaciones: Observaciones adicionales
- emociones: Estados emocionales detectados
- urgencia: Nivel de urgencia (baja/media/alta)
- recomendaciones: Recomendaciones dadas
"""
```

#### Manejo de Rate Limiting
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(RateLimitError)
)
async def _call_openai_api():
    # Lógica de llamada con reintentos automáticos
```

---

### 3.3 Servicio Vector Store

#### Descripción General
El VectorStoreService implementa el almacenamiento vectorial usando ChromaDB para convertir transcripciones médicas en embeddings semánticamente ricos, permitiendo búsquedas avanzadas y el sistema RAG.

#### Clase Principal: `VectorStoreService`

**Responsabilidades:**
- Inicialización y gestión de ChromaDB
- Generación de embeddings con sentence-transformers
- Almacenamiento de transcripciones con metadata rica
- Búsqueda semántica avanzada
- Búsquedas especializadas (por paciente, por condición)

#### Arquitectura de Almacenamiento

**Estructura de Embeddings:**
```python
{
    "id": "conv_12345_abc123",          # ID único del vector
    "embedding": [0.1, 0.2, ...],      # Vector de 384 dimensiones
    "document": "texto_preparado",      # Texto combinado para embedding
    "metadata": {                       # Metadata rica
        "conversation_id": "12345",
        "patient_name": "Juan Pérez",
        "diagnosis": "hipertensión",
        "symptoms": "dolor de cabeza, mareos",
        "conversation_date": "2024-01-15",
        "created_at": "2024-01-15T10:30:00Z",
        "document_type": "transcription"
    }
}
```

#### Funcionalidades de Búsqueda

1. **Búsqueda Semántica General**: Similarity search con filtros
2. **Búsqueda por Paciente**: Fuzzy matching para nombres latinos
3. **Búsqueda por Condición**: Filtrado por diagnósticos médicos

---

### 3.4 Servicio Chat RAG

#### Descripción General
El ChatService implementa un sistema completo RAG (Retrieval-Augmented Generation) especializado en consultas médicas. Combina análisis de intención, búsqueda vectorial semántica y generación de respuestas contextuales.

#### Pipeline RAG Completo

![Pipeline RAG](images/pipeline-rag.png)

1. **Análisis de Query**: Normalización y detección de intención
2. **Extracción de Entidades**: Pacientes, condiciones, síntomas
3. **Búsqueda Vectorial**: Recuperación de contexto relevante
4. **Ranking de Contexto**: Ordenamiento por relevancia
5. **Generación**: Respuesta con GPT-4 y fuentes

#### Tipos de Intenciones

```python
class ChatIntent(str, Enum):
    PATIENT_INFO = "patient_info"        # "¿Qué enfermedad tiene X?"
    CONDITION_LIST = "condition_list"    # "Listame pacientes con diabetes"
    SYMPTOM_SEARCH = "symptom_search"    # "¿Quién tiene dolor de cabeza?"
    MEDICATION_INFO = "medication_info"  # "¿Qué medicamentos toma X?"
    TEMPORAL_QUERY = "temporal_query"    # "¿Qué pasó la semana pasada?"
    GENERAL_QUERY = "general_query"      # Consultas generales
```

#### Estrategias de Búsqueda por Intención

```python
if intent == ChatIntent.PATIENT_INFO:
    # Búsqueda específica por paciente
    results = await vector_service.search_by_patient(patient_name)
elif intent == ChatIntent.CONDITION_LIST:
    # Búsqueda por condición médica
    results = await vector_service.search_by_condition(condition)
else:
    # Búsqueda semántica general
    results = await vector_service.semantic_search(query)
```

---

### 3.5 Servicio OCR y Documentos

#### Descripción General
El OCRService maneja el procesamiento completo de documentos médicos (PDFs e imágenes) extrayendo texto mediante PyPDF2 y Tesseract OCR, seguido de extracción de metadata médica usando IA.

#### Clase Principal: `OCRService`

**Responsabilidades:**
- Detección automática de tipo de archivo (PDF vs imagen)
- Extracción de texto de PDFs usando PyPDF2
- OCR de imágenes usando Tesseract
- Limpieza y normalización de texto extraído
- Extracción de metadata médica usando OpenAI
- Validación de archivos y configuración de calidad

#### Pipeline de Procesamiento

![Pipeline Documentos](images/pipeline-documentos.png)

**Flujo:**
1. Upload PDF/Imagen → Detección de tipo
2. PDF → PyPDF2 Extraction | Imagen → Tesseract OCR
3. Texto Extraído → Limpieza
4. OpenAI Service → Extracción Metadata Médica
5. Document Model DB + Vector Store Service

#### Detección de Tipo de Archivo

```python
def detect_file_type(self, file_path: str) -> str:
    # Métodos de detección:
    # 1. MIME type analysis
    # 2. File extension validation
    # 3. Magic number verification
    
    if mime_type == "application/pdf":
        return "pdf"
    elif mime_type.startswith("image/"):
        return "image"
```

#### Configuración OCR

```python
# Configuración Tesseract:
OCR_LANGUAGE: str = "spa"            # Español
OCR_MIN_CONFIDENCE: int = 60         # Confianza mínima
PDF_MAX_PAGES: int = 50              # Límite de páginas
DOCUMENT_MAX_SIZE_MB: int = 10       # Tamaño máximo
```

---

### 3.6 Servicio Speaker Diarization

#### Descripción General
El SpeakerService implementa diarización de hablantes especializada en conversaciones médicas, identificando y separando automáticamente la participación del promotor de salud y el paciente.

#### Enfoque Híbrido

**Método Avanzado (Audio + Texto):**
```python
if whisper_segments and librosa_available:
    # Análisis de características de audio + texto
    segments = _diarize_with_audio_and_text()
else:
    # Método básico: solo análisis de texto
    segments = _diarize_text_only()
```

#### Características de Audio Extraídas

1. **Pitch Analysis**: Frecuencia fundamental (f0)
2. **Energy Analysis**: RMS energy
3. **Spectral Analysis**: Centroide espectral
4. **Speech Rate**: Zero crossing rate
5. **Tonal Variability**: Rango de pitch

#### Patrones de Clasificación

**Promotor de Salud:**
```python
_promotor_patterns = [
    r"buenos días|buenas tardes|hola",
    r"¿cómo se siente|¿cómo está|¿qué le pasa",
    r"vamos a revisar|le voy a|necesito que",
    r"voy a recetarle|le recomiendo|debe tomar"
]
```

**Paciente:**
```python
_paciente_patterns = [
    r"me duele|me siento|tengo dolor",
    r"desde hace|hace como|hace unos",
    r"sí doctor|no doctor|gracias doctor",
    r"mi familia|mi trabajo|en casa"
]
```

#### Estadísticas Generadas

```python
class SpeakerStats:
    total_speakers: int                    # Hablantes únicos detectados
    promotor_time: float                   # Tiempo total del promotor
    paciente_time: float                   # Tiempo total del paciente
    speaker_changes: int                   # Número de cambios de hablante
    average_segment_length: float          # Duración promedio de segmentos
```

---

## 4. API y Endpoints

### 4.1 Estructura de Rutas

```python
# Configuración de Routers
app.include_router(health.router, tags=["Health Check"])
app.include_router(upload.router, prefix="/api/v1", tags=["Audio Transcription"])
app.include_router(vector.router, prefix="/api/v1", tags=["Vector Store"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat RAG"])
app.include_router(documents.router, prefix="/api/v1", tags=["Document Processing"])
```

### 4.2 Endpoints Principales

#### Audio Transcription

**`POST /api/v1/upload-audio`**
- **Descripción**: Subir archivo de audio para transcripción automática
- **Content-Type**: `multipart/form-data`
- **Validaciones**: Tamaño máximo 25MB, extensiones wav/mp3
- **Response**: `AudioUploadResponse` con ID de transcripción

**`GET /api/v1/transcriptions/{transcription_id}`**
- **Descripción**: Obtener resultados de transcripción por ID
- **Response**: `TranscriptionResponse` con texto, datos estructurados y no estructurados

#### Chat RAG

**`POST /api/v1/chat`**
- **Descripción**: Endpoint principal para consultas médicas con sistema RAG
- **Request**: `ChatQuery` con query, max_results, filtros
- **Response**: `ChatResponse` con respuesta, fuentes, confianza

**Tipos de consultas soportadas:**
- `patient_info`: "¿Qué enfermedad tiene X?"
- `condition_list`: "Listame pacientes con diabetes"
- `symptom_search`: "¿Quién tiene dolor de cabeza?"
- `medication_info`: "¿Qué medicamentos toma X?"
- `temporal_query`: "¿Qué pasó ayer?"

#### Vector Store

**`GET /api/v1/vector-store/status`**
- **Descripción**: Estado actual del vector store y estadísticas
- **Response**: `VectorStoreStatus` con total de documentos, modelo de embeddings

**`GET /api/v1/vector-store/conversations`**
- **Descripción**: Lista de conversaciones almacenadas
- **Query Params**: `limit` (1-100, default 20)
- **Response**: Lista de `StoredConversation`

#### Document Processing

**`POST /api/v1/documents/upload`**
- **Descripción**: Subir y procesar documentos médicos
- **Content-Type**: `multipart/form-data`
- **Formatos**: PDF, JPG, PNG, TIFF hasta 10MB
- **Response**: `DocumentResponse` con ID y estado

### 4.3 Pipeline de Procesamiento API

![Pipeline API](images/pipeline-api.png)

**Flujo de Upload de Audio:**
1. Usuario → Frontend → POST /upload-audio
2. API → Database (crear registro) → Background Tasks
3. Background: Whisper → OpenAI → Vector Store → Speaker Diarization
4. Usuario consulta estado → GET /transcriptions/{id}

---

## 5. Base de Datos y Schemas

### 5.1 Arquitectura de Base de Datos

**Configuración:**
- **Desarrollo**: SQLite (`./conversations.db`)
- **Producción**: PostgreSQL
- **ORM**: SQLAlchemy con Alembic para migraciones

### 5.2 Modelos Principales

#### AudioTranscription (Tabla Principal)

```python
class AudioTranscription(Base):
    __tablename__ = "audio_transcriptions"
    
    # Clave primaria
    id = Column(String, primary_key=True)
    
    # Información del archivo
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)
    
    # Estado de procesamiento
    status = Column(Enum(TranscriptionStatus), default=TranscriptionStatus.PENDING)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Resultados de transcripción
    raw_transcription = Column(Text, nullable=True)
    confidence_score = Column(String(10), nullable=True)
    
    # Información estructurada extraída (JSON)
    structured_data = Column(JSON, nullable=True)
    
    # Información no estructurada (JSON)
    unstructured_data = Column(JSON, nullable=True)
    
    # Integración Vector Store
    vector_stored = Column(String(50), default="false")
    vector_id = Column(String(100), nullable=True)
    
    # Speaker Diarization
    speaker_segments = Column(Text, nullable=True)  # JSON array
    speaker_stats = Column(Text, nullable=True)     # JSON object
```

#### Document (Procesamiento de Documentos)

```python
class Document(Base):
    __tablename__ = "documents"
    
    # Identificación
    id = Column(String(50), primary_key=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # 'pdf', 'image'
    file_size_bytes = Column(Integer, nullable=False)
    
    # Resultados OCR/extracción
    extracted_text = Column(Text, nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    page_count = Column(Integer, nullable=True)
    
    # Metadata médica extraída por IA
    patient_name = Column(String(100), nullable=True)
    document_date = Column(String(20), nullable=True)
    document_type = Column(String(50), nullable=True)
    medical_conditions = Column(Text, nullable=True)  # JSON array
    medications = Column(Text, nullable=True)         # JSON array
    
    # Integración vector store
    vector_stored = Column(String(10), default="false")
    vector_id = Column(String(100), nullable=True)
    
    # Relación con conversaciones
    conversation_id = Column(String(50), ForeignKey("audio_transcriptions.id"))
```

### 5.3 Estructura de Datos JSON

#### Structured Data (AudioTranscription)
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

#### Unstructured Data (AudioTranscription)
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

#### Speaker Segments (JSON Text)
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

### 5.4 Diagrama Entidad-Relación

![Diagrama ER](images/diagrama-er.png)

**Relaciones:**
- `AudioTranscription` 1:N `Document` (conversation_id)
- `AudioTranscription` 1:1 `ConversationMetadata` (transcription_id)
- Integración con ChromaDB vía `vector_id`

---

## 6. Decisiones Arquitectónicas

### 6.1 Monolito Modular vs Microservicios

**Decisión**: Comenzar con monolito modular

**Razones:**
✅ **Ventajas del Monolito:**
- Simplicidad de desarrollo y despliegue
- Debugging simplificado con stack traces completos
- Transacciones ACID garantizadas
- Menor latencia (comunicación in-process)
- Setup inicial rápido sin overhead de networking

❌ **Desventajas conocidas:**
- Escalabilidad limitada por el componente más lento
- Deployment monolítico (todo o nada)
- Potencial coupling entre módulos sin disciplina

**Estrategia de mitigación:**
- Arquitectura modular estricta con interfaces bien definidas
- Dependency injection para reducir coupling
- Preparación para extraer servicios independientes

### 6.2 Stack Tecnológico: Python + FastAPI

**Decisión**: Python con FastAPI como framework principal

**Razones para FastAPI:**
✅ **Python ecosystem para ML/AI:**
- Whisper (OpenAI) tiene implementación nativa en Python
- sentence-transformers para embeddings
- Amplio ecosistema de librerías médicas

✅ **FastAPI características:**
- Performance comparable a Node.js
- Type hints nativos
- Documentación automática (OpenAPI/Swagger)
- Async/await nativo
- Validación automática con Pydantic

### 6.3 Base de Datos: SQLite + PostgreSQL

**Estrategia híbrida:**
```python
if environment == "development":
    DATABASE_URL = "sqlite:///./conversations.db"
else:
    DATABASE_URL = "postgresql://user:pass@host:port/db"
```

**Razones SQLite (Desarrollo):**
- ✅ Zero-configuration
- ✅ Ideal para desarrollo local
- ✅ Transacciones ACID completas

**Razones PostgreSQL (Producción):**
- ✅ Escalabilidad horizontal y vertical
- ✅ Concurrencia avanzada (MVCC)
- ✅ Tipos de datos avanzados (JSON, arrays)

### 6.4 Vector Database: ChromaDB

**Decisión**: ChromaDB para almacenamiento vectorial

**Razones:**
- ✅ **Simplicidad**: Instalación con pip, configuración mínima
- ✅ **Local-first**: No dependencias externas
- ✅ **Persistencia**: Datos almacenados localmente
- ✅ **Python nativo**: Integración perfecta
- ✅ **Embeddings integrados**: Soporte directo para sentence-transformers

**Consideraciones futuras:**
- Migración a Qdrant o Weaviate para escalabilidad
- pgvector para simplificar stack (un solo DB)

### 6.5 Transcripción: Whisper Local

**Decisión**: OpenAI Whisper ejecutado localmente

**Razones Whisper Local:**
- ✅ **Privacidad**: Datos médicos no salen del servidor
- ✅ **Costo predecible**: Sin costos por uso
- ✅ **Latencia controlada**: Sin dependencia de internet
- ✅ **Calidad**: Estado del arte en transcripción
- ❌ **Recursos**: Requiere GPU para modelos grandes

### 6.6 Extracción de Información: Azure OpenAI

**Razones Azure vs OpenAI directo:**
- ✅ **Compliance**: Mejor para datos médicos
- ✅ **SLA**: Garantías empresariales
- ✅ **Security**: VNet integration, private endpoints

---

## 7. Migración a Microservicios

### 7.1 Servicios Candidatos

![Microservicios Target](images/microservicios-target.png)

**1. Transcription Service**
```python
# Responsabilidades:
- Audio file upload/validation
- Whisper transcription
- Speaker diarization
- Audio metadata extraction

# API Surface:
POST /transcriptions
GET /transcriptions/{id}
GET /transcriptions/{id}/speakers
```

**2. Extraction Service**
```python
# Responsabilidades:
- Text analysis con OpenAI
- Structured data extraction
- Medical entity recognition
- Data validation

# API Surface:
POST /extractions
GET /extractions/{id}
POST /extractions/batch
```

**3. Knowledge Service**
```python
# Responsabilidades:
- Vector storage (ChromaDB)
- Semantic search
- Document processing
- Knowledge graph management

# API Surface:
POST /knowledge/store
GET /knowledge/search
POST /knowledge/documents
```

**4. Chat Service**
```python
# Responsabilidades:
- RAG pipeline
- Intent classification
- Response generation
- Chat history

# API Surface:
POST /chat/query
GET /chat/history
POST /chat/feedback
```

### 7.2 Estrategia de Migración

#### Fase 1: Strangler Fig Pattern

![Strangler Fig](images/strangler-fig.png)

**Objetivo**: Extraer servicios gradualmente sin interrumpir el monolito

**Implementación:**
1. **Feature flags** para dirigir tráfico
2. **Dual write** para sincronizar datos
3. **Shadow mode** para validar servicios nuevos

#### Fase 2: Database per Service

**Problema actual**: Base de datos compartida

**Solución**: Database decomposition pattern

![Database Decomposition](images/database-decomposition.png)

**Estrategia:**
1. Separar datos por bounded context
2. Event sourcing para sincronización
3. Change Data Capture (CDC) para transición

#### Fase 3: Service Mesh + API Gateway

**Infraestructura objetivo:**

![Service Mesh](images/service-mesh.png)

**Componentes:**
- **API Gateway**: Kong/Istio Gateway
- **Service Mesh**: Istio/Linkerd
- **Message Queue**: Redis/RabbitMQ
- **Monitoring**: Prometheus + Grafana

### 7.3 Service Communication Patterns

**Current (Monolith):**
```python
# In-process communication
async def upload_audio():
    transcription = await whisper_service.transcribe(file)
    extracted = await openai_service.extract(transcription)
    vector_id = await vector_service.store(extracted)
    return result
```

**Future (Microservices):**
```python
# Event-driven communication
async def upload_audio():
    event_bus.publish("audio.uploaded", audio_data)
    return {"status": "processing", "id": audio_id}

@event_handler("audio.uploaded")
async def handle_audio_uploaded(audio_data):
    transcription = await transcribe(audio_data)
    event_bus.publish("audio.transcribed", transcription)
```

### 7.4 Data Consistency Strategy

**Current: ACID Transactions**
```python
@db_transaction
async def process_audio(audio_file):
    # Atomicidad garantizada
    transcription = create_transcription(audio_file)
    structured_data = extract_information(transcription.text)
    vector_id = store_in_vector_db(transcription, structured_data)
    transcription.vector_id = vector_id
    commit()  # Todo o nada
```

**Future: Eventual Consistency + Saga Pattern**
```python
class AudioProcessingSaga:
    async def execute(self, audio_file):
        try:
            # Step 1: Create transcription
            transcription_id = await transcription_service.create(audio_file)
            
            # Step 2: Extract information
            extraction_id = await extraction_service.process(transcription_id)
            
            # Step 3: Store in vector DB
            vector_id = await knowledge_service.store(extraction_id)
            
            # Success: Mark as completed
            await transcription_service.mark_completed(transcription_id, vector_id)
            
        except Exception as e:
            # Compensation: Rollback steps
            await self.compensate(transcription_id, extraction_id)
```

### 7.5 Timeline de Migración

**Q1 2024: Preparación**
- [ ] Refactoring para interfaces claras
- [ ] Implementar event sourcing patterns
- [ ] Setup de infrastructure (Kubernetes, monitoring)
- [ ] Feature flags y A/B testing framework

**Q2 2024: Primer Servicio**
- [ ] Extraer Transcription Service
- [ ] Database per service pattern
- [ ] Service-to-service communication
- [ ] Comprehensive testing

**Q3 2024: Segundo y Tercer Servicio**
- [ ] Extraer Knowledge Service
- [ ] Extraer Chat Service
- [ ] API Gateway implementation
- [ ] Service mesh (Istio/Linkerd)

**Q4 2024: Completar Migración**
- [ ] Extraer servicios restantes
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Documentation y training

---

## 8. Despliegue y Operaciones

### 8.1 Desarrollo Local

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend  
cd frontend
npm install
npm run dev
```

### 8.2 Producción

**Containerización**:
```dockerfile
# Dockerfile para backend
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Orquestación**:
```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/elsol
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
    depends_on:
      - db
      - chroma
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=elsol
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  chroma:
    image: ghcr.io/chroma-core/chroma:latest
    ports:
      - "8001:8000"
    volumes:
      - chroma_data:/chroma/chroma
```

### 8.3 Monitoreo y Observabilidad

**Métricas Clave**:
- **Performance**: Latencia p95 < 500ms, Throughput > 1000 req/min
- **Reliability**: Uptime 99.9%, MTTR < 30 min
- **Business**: Accuracy > 90%, User satisfaction

**Stack de Monitoreo**:
- **Metrics**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Tracing**: Jaeger para distributed tracing
- **Alerting**: AlertManager + PagerDuty

### 8.4 Seguridad y Compliance

**Privacidad Médica**:
- **Datos Locales**: Whisper ejecuta sin enviar datos externos
- **Encriptación**: TLS en tránsito, AES-256 en reposo
- **Audit Logs**: Trazabilidad de acceso a información
- **HIPAA Ready**: Preparado para compliance médico

**Arquitectura de Seguridad**:
- **Input Validation**: Validación en todas las capas
- **Authentication**: JWT tokens con refresh
- **Authorization**: RBAC (Role-Based Access Control)
- **Rate Limiting**: Por usuario y por endpoint

---

## Conclusión

ElSol Challenge representa una solución médica moderna que combina las mejores prácticas de desarrollo de software con tecnologías de inteligencia artificial de vanguardia. La arquitectura monolítica modular permite desarrollo rápido mientras prepara el terreno para una evolución gradual hacia microservicios cuando el negocio lo requiera.

### Logros Técnicos

1. **Privacidad Médica**: Whisper local garantiza que datos sensibles no salen del servidor
2. **Escalabilidad Preparada**: Arquitectura modular lista para microservicios
3. **IA Especializada**: Prompts médicos optimizados para extracción precisa
4. **Búsqueda Inteligente**: Sistema RAG completo para consultas naturales
5. **Multi-modal**: Audio, documentos y chat en una plataforma unificada

### Roadmap Futuro

**Corto Plazo (Q1 2024)**:
- Optimización de performance y tests completos
- Security hardening y documentación API
- Mobile app integration

**Medio Plazo (Q2-Q3 2024)**:
- Real-time transcription con WebSockets
- Advanced analytics dashboard
- Multi-language support

**Largo Plazo (Q4 2024+)**:
- Migración gradual a microservicios
- Advanced ML models especializados en medicina
- Integration con sistemas hospitalarios (HL7 FHIR)
- Multi-tenancy y features enterprise

La documentación completa facilita el onboarding de nuevos desarrolladores, la comprensión del sistema por parte de stakeholders, y proporciona una guía clara para la evolución futura del proyecto.

---

**Fecha de actualización**: Enero 2025  
**Versión del documento**: 1.0.0  
**Próxima revisión**: Marzo 2025
