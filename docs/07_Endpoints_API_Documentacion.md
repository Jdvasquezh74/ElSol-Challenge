# Documentación de Endpoints API - ElSol Challenge

## Descripción General
La API de ElSol Challenge está construida con FastAPI y sigue una arquitectura RESTful organizada por módulos funcionales. Cada endpoint está documentado con OpenAPI/Swagger y maneja validación automática de datos usando Pydantic schemas.

## Estructura de Rutas

### Configuración de Routers
```python
# main.py - Configuración central
app.include_router(health.router, tags=["Health Check"])
app.include_router(upload.router, prefix="/api/v1", tags=["Audio Transcription"])
app.include_router(vector.router, prefix="/api/v1", tags=["Vector Store"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat RAG"])
app.include_router(documents.router, prefix="/api/v1", tags=["Document Processing"])
```

## 1. Health Check Endpoints (`/health`)

### `GET /health`
**Descripción:** Verificación básica de salud de la aplicación.

**Response Schema:** `HealthResponse`
```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "1.0.0",
    "uptime_seconds": 3600,
    "dependencies": {
        "openai_api": "healthy",
        "database": "healthy",
        "file_system": "healthy"
    }
}
```

**Verificaciones realizadas:**
- Estado de configuración de Azure OpenAI
- Conectividad de base de datos
- Acceso al sistema de archivos
- Tiempo de actividad del servicio

### `GET /health/detailed`
**Descripción:** Health check extendido con métricas del sistema.

**Información adicional:**
- Métricas de memoria y disco
- Versión de Python y plataforma
- Configuración de la aplicación
- Estadísticas de rendimiento

### `GET /health/dependencies`
**Descripción:** Verificación específica de dependencias externas.

## 2. Audio Transcription Endpoints (`/api/v1`)

### `POST /api/v1/upload-audio`
**Descripción:** Subir archivo de audio para transcripción automática.

**Request:**
- **Content-Type:** `multipart/form-data`
- **Body:** Archivo de audio (.wav, .mp3)

**Validaciones:**
- Tamaño máximo: 25MB
- Extensiones permitidas: wav, mp3
- Content-type verification
- Magic number validation

**Response Schema:** `AudioUploadResponse`
```json
{
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "filename": "conversacion_medica.wav",
    "status": "pending",
    "created_at": "2024-01-15T10:30:00Z",
    "file_size": 1024000
}
```

**Pipeline de procesamiento automático:**
1. Validación y almacenamiento de archivo
2. Creación de registro en base de datos
3. **Background Task:** Transcripción con Whisper
4. **Background Task:** Extracción de información con OpenAI
5. **Background Task:** Almacenamiento en Vector Store
6. Limpieza de archivos temporales

### `GET /api/v1/transcriptions/{transcription_id}`
**Descripción:** Obtener resultados de transcripción por ID.

**Path Parameters:**
- `transcription_id`: UUID de la transcripción

**Response Schema:** `TranscriptionResponse`
```json
{
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "filename": "conversacion_medica.wav",
    "status": "completed",
    "created_at": "2024-01-15T10:30:00Z",
    "processed_at": "2024-01-15T10:32:30Z",
    "transcription": {
        "raw_text": "Doctor: Buenos días, ¿cómo se siente hoy?...",
        "structured_data": {
            "nombre": "Juan Pérez",
            "edad": 45,
            "diagnostico": "hipertensión arterial",
            "medicamentos": ["losartan", "amlodipino"]
        },
        "unstructured_data": {
            "sintomas": ["dolor de cabeza", "mareos"],
            "urgencia": "media",
            "contexto": "consulta de seguimiento"
        },
        "confidence_score": "high",
        "language_detected": "es",
        "audio_duration_seconds": 180,
        "processing_time_seconds": 45
    }
}
```

### `GET /api/v1/transcriptions`
**Descripción:** Lista paginada de transcripciones con filtros opcionales.

**Query Parameters:**
- `page`: Número de página (default: 1)
- `size`: Elementos por página (1-100, default: 10)
- `status`: Filtro por estado (opcional)

**Response Schema:** `TranscriptionListResponse`
```json
{
    "items": [
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "filename": "conversacion1.wav",
            "status": "completed",
            "created_at": "2024-01-15T10:30:00Z",
            "processed_at": "2024-01-15T10:32:30Z",
            "file_size": 1024000,
            "language_detected": "es",
            "audio_duration_seconds": 180
        }
    ],
    "total": 25,
    "page": 1,
    "size": 10,
    "has_next": true
}
```

## 3. Chat RAG Endpoints (`/api/v1`)

### `POST /api/v1/chat`
**Descripción:** Endpoint principal para consultas médicas con sistema RAG.

**Request Schema:** `ChatQuery`
```json
{
    "query": "¿Qué enfermedad tiene Juan Pérez?",
    "max_results": 5,
    "filters": {
        "patient_name": "Juan Pérez"
    },
    "include_sources": true
}
```

**Response Schema:** `ChatResponse`
```json
{
    "answer": "Según la información disponible, Juan Pérez fue diagnosticado con hipertensión arterial. En su última consulta reportó síntomas de dolor de cabeza y mareos. Está en tratamiento con losartan y amlodipino.",
    "sources": [
        {
            "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
            "patient_name": "Juan Pérez",
            "relevance_score": 0.95,
            "excerpt": "Doctor: Buenos días Sr. Pérez, veo que viene por seguimiento de su hipertensión...",
            "date": "2024-01-15",
            "metadata": {
                "diagnosis": "hipertensión arterial",
                "symptoms": "dolor de cabeza, mareos"
            }
        }
    ],
    "confidence": 0.87,
    "intent": "patient_info",
    "follow_up_suggestions": [
        "¿Qué tratamiento se recomendó para Juan Pérez?",
        "¿Cuándo fue la última consulta de Juan Pérez?",
        "¿Qué síntomas reportó Juan Pérez?"
    ],
    "query_classification": {
        "entities": {
            "patients": ["Juan Pérez"],
            "conditions": ["hipertensión"],
            "symptoms": []
        },
        "search_terms": ["Juan Pérez", "enfermedad", "diagnóstico"],
        "normalized_query": "que enfermedad tiene juan perez"
    },
    "processing_time_ms": 1250
}
```

**Tipos de consultas soportadas:**
- **patient_info**: "¿Qué enfermedad tiene X?"
- **condition_list**: "Listame pacientes con diabetes"
- **symptom_search**: "¿Quién tiene dolor de cabeza?"
- **medication_info**: "¿Qué medicamentos toma X?"
- **temporal_query**: "¿Qué pasó ayer?"
- **general_query**: Consultas generales

### `POST /api/v1/chat/quick`
**Descripción:** Endpoint simplificado para consultas rápidas.

**Request Body:**
```json
{
    "query": "Pacientes con diabetes",
    "max_results": 3
}
```

### `GET /api/v1/chat/examples`
**Descripción:** Ejemplos de consultas que el sistema puede manejar.

**Response:**
```json
{
    "examples": {
        "patient_info": {
            "description": "Consultas sobre información específica de pacientes",
            "examples": [
                "¿Qué enfermedad tiene Juan Pérez?",
                "¿Cuál es el diagnóstico de María García?"
            ]
        },
        "condition_list": {
            "description": "Listas de pacientes por condición médica",
            "examples": [
                "Listame los pacientes con diabetes",
                "¿Quiénes tienen hipertensión?"
            ]
        }
    },
    "tips": [
        "Usa nombres específicos para mejores resultados",
        "Incluye términos médicos cuando sea posible"
    ],
    "supported_intents": [
        "patient_info",
        "condition_list",
        "symptom_search",
        "medication_info",
        "temporal_query",
        "general_query"
    ]
}
```

### `POST /api/v1/chat/validate`
**Descripción:** Validar consulta antes de procesamiento completo.

### `GET /api/v1/chat/health`
**Descripción:** Health check específico del sistema de chat.

## 4. Vector Store Endpoints (`/api/v1`)

### `GET /api/v1/vector-store/status`
**Descripción:** Estado actual del vector store y estadísticas.

**Response Schema:** `VectorStoreStatus`
```json
{
    "status": "operational",
    "collection_name": "medical_conversations",
    "total_documents": 1250,
    "total_embeddings": 1250,
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "persist_directory": "./chroma_db",
    "last_updated": "2024-01-15T10:30:00Z"
}
```

### `GET /api/v1/vector-store/conversations`
**Descripción:** Lista de conversaciones almacenadas en vector store.

**Query Parameters:**
- `limit`: Número máximo de conversaciones (1-100, default: 20)

**Response Schema:** `List[StoredConversation]`
```json
[
    {
        "vector_id": "conv_123e4567_abc123",
        "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
        "patient_name": "Juan Pérez",
        "stored_at": "2024-01-15T10:32:45Z",
        "text_preview": "Doctor: Buenos días, ¿cómo se siente hoy? Paciente: Me duele mucho la cabeza...",
        "metadata": {
            "patient_name": "Juan Pérez",
            "diagnosis": "hipertensión arterial",
            "symptoms": "dolor de cabeza, mareos",
            "conversation_date": "2024-01-15",
            "document_type": "transcription"
        }
    }
]
```

### `GET /api/v1/vector-store/conversations/{conversation_id}`
**Descripción:** Obtener conversación específica del vector store.

### `GET /api/v1/vector-store/health`
**Descripción:** Health check específico del vector store.

## 5. Document Processing Endpoints (`/api/v1`)

### `POST /api/v1/documents/upload`
**Descripción:** Subir y procesar documentos médicos (PDFs e imágenes).

**Request:**
- **Content-Type:** `multipart/form-data`
- **Body:** 
  - `file`: Archivo PDF o imagen
  - `patient_name`: Nombre del paciente (opcional)
  - `document_type`: Tipo de documento (opcional)
  - `description`: Descripción (opcional)

**Validaciones:**
- Tamaño máximo: 10MB
- Formatos soportados: PDF, JPG, PNG, TIFF
- Validación de content-type
- Magic number verification

**Response Schema:** `DocumentResponse`
```json
{
    "document_id": "doc_123456",
    "filename": "examen_juan_perez.pdf",
    "file_type": "pdf",
    "file_size_bytes": 1024000,
    "status": "processing",
    "created_at": "2024-01-15T10:30:00Z"
}
```

### `GET /api/v1/documents/{document_id}`
**Descripción:** Obtener resultados de procesamiento de documento.

**Response Schema:** `DocumentResponse` (completa)
```json
{
    "document_id": "doc_123456",
    "filename": "examen_juan_perez.pdf",
    "file_type": "pdf",
    "status": "completed",
    "ocr_result": {
        "text": "LABORATORIO CLÍNICO\nPaciente: Juan Pérez\nExamen: Química Sanguínea\nGlucosa: 180 mg/dl...",
        "confidence": 0.87,
        "page_count": 3,
        "processing_time_ms": 2500,
        "language_detected": "spa"
    },
    "extracted_metadata": {
        "patient_name": "Juan Pérez",
        "document_date": "2024-01-10",
        "document_type": "examen de laboratorio",
        "medical_conditions": ["diabetes tipo 2"],
        "medications": ["metformina"],
        "medical_procedures": ["química sanguínea", "hemograma"]
    },
    "vector_stored": true,
    "patient_association": "Juan Pérez",
    "processed_at": "2024-01-15T10:32:30Z"
}
```

### `POST /api/v1/documents/search`
**Descripción:** Búsqueda semántica en documentos procesados.

**Request Schema:** `DocumentSearchQuery`
```json
{
    "query": "exámenes de diabetes",
    "patient_name": "Juan Pérez",
    "document_type": "examen",
    "date_from": "2024-01-01",
    "date_to": "2024-01-31",
    "max_results": 10
}
```

## Características Técnicas

### Autenticación y Autorización
- **Actual**: Sin autenticación (desarrollo)
- **Producción**: JWT tokens recomendados
- **Roles**: Admin, Médico, Usuario

### Rate Limiting
```python
# Configuración actual
RATE_LIMIT_REQUESTS: int = 50
RATE_LIMIT_WINDOW: int = 60  # seconds
```

### Validación de Datos
- **Pydantic Schemas**: Validación automática
- **FastAPI Dependencies**: Validación de parámetros
- **Custom Validators**: Validaciones específicas médicas

### Error Handling
```python
# Estructura estándar de errores
{
    "error": "HTTP Error",
    "message": "Descripción del error",
    "details": [
        {
            "message": "Error específico",
            "code": "ERROR_CODE",
            "field": "campo_problematico"
        }
    ],
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_123456"
}
```

### CORS Configuration
```python
# Configuración CORS
allow_origins=["http://localhost:3000", "http://localhost:8080"]
allow_credentials=True
allow_methods=["*"]
allow_headers=["*"]
```

## Integración con Servicios

### Background Tasks
```python
# Tareas asíncronas para:
- Transcripción de audio (Whisper)
- Extracción de información (OpenAI)
- Almacenamiento vectorial (ChromaDB)
- Procesamiento OCR (documentos)
- Diarización de hablantes
```

### Database Operations
```python
# Patrón de integración:
@router.post("/endpoint")
async def endpoint_handler(
    data: Schema,
    db: Session = Depends(get_db),
    service: Service = Depends(get_service)
):
    # 1. Validación con Pydantic
    # 2. Procesamiento con Service
    # 3. Persistencia con Database
    # 4. Response con Schema
```

### Service Layer Integration
- **Dependency Injection**: FastAPI Depends()
- **Singleton Services**: Instancias únicas reutilizables
- **Error Propagation**: Manejo estructurado de errores
- **Logging**: Structured logging con contexto

## Monitoreo y Observabilidad

### Structured Logging
```python
logger.info("Request processed",
           endpoint="/api/v1/chat",
           query=query_data.query,
           processing_time_ms=1250,
           confidence=0.87)
```

### Métricas de Performance
- Tiempo de respuesta por endpoint
- Tasa de éxito/error por operación
- Uso de recursos por request
- Queue length para tareas background

### Health Checks
- Endpoint-specific health checks
- Dependency monitoring
- System resource monitoring
- Service availability checks

## Documentación API

### OpenAPI/Swagger
- **URL**: `/docs` (en development)
- **Redoc**: `/redoc` (en development)
- **Schema**: `/openapi.json`

### Características de Documentación
- Descripciones detalladas de endpoints
- Ejemplos de request/response
- Schemas Pydantic integrados
- Códigos de error documentados
- Tags organizacionales

## Migración a Microservicios

### Endpoints por Microservicio
```python
# Transcription Service
- POST /upload-audio
- GET /transcriptions/{id}
- GET /transcriptions

# Chat Service  
- POST /chat
- POST /chat/quick
- GET /chat/examples

# Document Service
- POST /documents/upload
- GET /documents/{id}
- POST /documents/search

# Vector Service
- GET /vector-store/status
- GET /vector-store/conversations
```

### API Gateway Pattern
- Routing centralizado
- Authentication/Authorization
- Rate limiting global
- Request/Response logging
- Circuit breaker pattern

### Inter-Service Communication
- **Sync**: HTTP REST calls
- **Async**: Message queues (Redis/RabbitMQ)
- **Discovery**: Service registry
- **Load Balancing**: Round-robin/Weighted
