# Arquitectura General - ElSol Challenge

## Visión General del Sistema

ElSol Challenge es una plataforma médica inteligente que combina transcripción de audio, procesamiento de documentos, almacenamiento vectorial y un sistema de chat RAG para proporcionar un asistente médico completo. La arquitectura está diseñada como un monolito modular que puede evolucionar hacia microservicios.

## Arquitectura de Alto Nivel

```mermaid
graph TB
    subgraph "Frontend (React + TypeScript)"
        A[Web Application]
        A1[Audio Upload Component]
        A2[Chat Interface]
        A3[Document Upload Component]
        A4[Transcription List]
        A5[Conversation Detail]
    end
    
    subgraph "Backend API (FastAPI + Python)"
        B[API Gateway / Main App]
        B1[Audio Upload Endpoints]
        B2[Chat RAG Endpoints]
        B3[Document Processing Endpoints]
        B4[Vector Store Endpoints]
        B5[Health Check Endpoints]
    end
    
    subgraph "Core Services Layer"
        C1[Whisper Service]
        C2[OpenAI Service]
        C3[Vector Store Service]
        C4[Chat Service]
        C5[OCR Service]
        C6[Speaker Service]
    end
    
    subgraph "Data Storage Layer"
        D1[SQLite/PostgreSQL Database]
        D2[ChromaDB Vector Store]
        D3[File System Storage]
    end
    
    subgraph "External Services"
        E1[Azure OpenAI API]
        E2[Whisper Models Local]
        E3[Tesseract OCR]
    end
    
    A --> B
    B1 --> C1
    B1 --> C2
    B2 --> C4
    B3 --> C5
    B4 --> C3
    
    C1 --> E2
    C2 --> E1
    C4 --> C3
    C4 --> C2
    C5 --> E3
    C6 --> C1
    
    C1 --> D1
    C2 --> D1
    C3 --> D2
    C5 --> D1
    
    D1 --> D3
    D2 --> D3
    
    style A fill:#e3f2fd
    style B fill:#e8f5e8
    style C1 fill:#fff3e0
    style C2 fill:#fff3e0
    style C3 fill:#fff3e0
    style C4 fill:#fff3e0
    style C5 fill:#fff3e0
    style C6 fill:#fff3e0
    style D1 fill:#fce4ec
    style D2 fill:#fce4ec
    style E1 fill:#f3e5f5
    style E2 fill:#f3e5f5
```

## Pipeline de Procesamiento de Audio

```mermaid
sequenceDiagram
    participant U as Usuario
    participant F as Frontend
    participant API as FastAPI
    participant WS as Whisper Service
    participant OS as OpenAI Service
    participant VS as Vector Service
    participant SS as Speaker Service
    participant DB as Database
    
    U->>F: Subir archivo de audio
    F->>API: POST /upload-audio
    API->>DB: Crear registro transcripción
    API->>F: Respuesta con ID
    F->>U: Confirmación de carga
    
    Note over API: Background Tasks
    API->>WS: Transcribir audio
    WS->>WS: Procesar con Whisper
    WS->>API: Texto transcrito
    
    API->>OS: Extraer información
    OS->>OS: Procesar con GPT-4
    OS->>API: Datos estructurados/no estructurados
    
    API->>VS: Almacenar en vector store
    VS->>VS: Generar embeddings
    VS->>API: Vector ID
    
    API->>SS: Diarizar hablantes
    SS->>SS: Clasificar promotor/paciente
    SS->>API: Segmentos con hablantes
    
    API->>DB: Actualizar registro completo
    
    Note over U,DB: Consulta de resultados
    U->>F: Consultar estado
    F->>API: GET /transcriptions/{id}
    API->>DB: Obtener datos
    DB->>API: Datos completos
    API->>F: Transcripción + metadata
    F->>U: Mostrar resultados
```

## Sistema RAG (Retrieval-Augmented Generation)

```mermaid
flowchart TD
    A[Consulta Usuario] --> B[Chat Service]
    B --> C[Análisis de Query]
    C --> D[Detección de Intención]
    C --> E[Extracción de Entidades]
    
    D --> F{Tipo de Consulta}
    E --> F
    
    F -->|patient_info| G[Búsqueda por Paciente]
    F -->|condition_list| H[Búsqueda por Condición]
    F -->|general_query| I[Búsqueda Semántica]
    
    G --> J[Vector Store Service]
    H --> J
    I --> J
    
    J --> K[ChromaDB]
    K --> L[Embeddings + Metadata]
    L --> M[Resultados Relevantes]
    
    M --> N[Ranking de Contexto]
    N --> O[Preparar Contexto Final]
    
    O --> P[OpenAI Service]
    P --> Q[Azure OpenAI GPT-4]
    Q --> R[Respuesta Generada]
    
    R --> S[Validación + Fuentes]
    S --> T[Respuesta Final]
    T --> U[Frontend]
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style J fill:#fff3e0
    style P fill:#e8f5e8
    style Q fill:#ffebee
    style U fill:#e1f5fe
```

## Arquitectura de Datos

```mermaid
erDiagram
    AudioTranscription {
        string id PK
        string filename
        string status
        text raw_transcription
        json structured_data
        json unstructured_data
        string vector_id
        text speaker_segments
        datetime created_at
    }
    
    Document {
        string id PK
        string filename
        string file_type
        text extracted_text
        string patient_name
        json medical_metadata
        string vector_id
        string conversation_id FK
    }
    
    ChromaDB {
        string vector_id PK
        vector embeddings
        text document_content
        json metadata
        string collection_name
    }
    
    AudioTranscription ||--o{ Document : "conversation_id"
    AudioTranscription ||--|| ChromaDB : "vector_id"
    Document ||--|| ChromaDB : "vector_id"
```

## Flujo de Procesamiento de Documentos

```mermaid
flowchart LR
    A[Upload PDF/Imagen] --> B{Tipo de Archivo}
    
    B -->|PDF| C[PyPDF2 Extraction]
    B -->|Imagen| D[Tesseract OCR]
    
    C --> E[Texto Extraído]
    D --> E
    
    E --> F[OCR Service]
    F --> G[Limpieza de Texto]
    G --> H[OpenAI Service]
    H --> I[Extracción Metadata Médica]
    
    I --> J[Document Model DB]
    I --> K[Vector Store Service]
    K --> L[Embeddings Generation]
    L --> M[ChromaDB Storage]
    
    J --> N[API Response]
    M --> N
    
    style A fill:#e3f2fd
    style C fill:#fff3e0
    style D fill:#fff3e0
    style H fill:#e8f5e8
    style K fill:#f3e5f5
    style M fill:#ffebee
```

## Arquitectura de Servicios

```mermaid
graph TB
    subgraph "Presentation Layer"
        WEB[React Frontend]
        API[FastAPI Application]
    end
    
    subgraph "Business Logic Layer"
        subgraph "Core Services"
            WS[Whisper Service]
            OS[OpenAI Service]
            VS[Vector Store Service]
            CS[Chat Service]
            OCS[OCR Service]
            SS[Speaker Service]
        end
        
        subgraph "Cross-Cutting Concerns"
            LOG[Logging Service]
            CFG[Configuration Service]
            VAL[Validation Service]
        end
    end
    
    subgraph "Data Access Layer"
        ORM[SQLAlchemy ORM]
        VDB[Vector Database Client]
        FS[File System Access]
    end
    
    subgraph "Infrastructure Layer"
        DB[SQLite/PostgreSQL]
        CHROMA[ChromaDB]
        FILES[Local File Storage]
        AZURE[Azure OpenAI]
        WHISPER_LOCAL[Local Whisper Models]
    end
    
    WEB --> API
    API --> WS
    API --> OS
    API --> VS
    API --> CS
    API --> OCS
    API --> SS
    
    WS --> LOG
    OS --> LOG
    VS --> LOG
    CS --> LOG
    OCS --> LOG
    SS --> LOG
    
    WS --> CFG
    OS --> CFG
    VS --> CFG
    
    CS --> VS
    CS --> OS
    OCS --> OS
    SS --> WS
    
    WS --> ORM
    OS --> ORM
    OCS --> ORM
    VS --> VDB
    
    ORM --> DB
    VDB --> CHROMA
    FS --> FILES
    OS --> AZURE
    WS --> WHISPER_LOCAL
    
    style WEB fill:#e3f2fd
    style API fill:#e8f5e8
    style WS fill:#fff3e0
    style OS fill:#fff3e0
    style VS fill:#fff3e0
    style CS fill:#fff3e0
    style OCS fill:#fff3e0
    style SS fill:#fff3e0
```

## Patrones de Diseño Implementados

### 1. Service Layer Pattern
```mermaid
classDiagram
    class ServiceInterface {
        <<interface>>
        +process()
        +validate()
        +handle_error()
    }
    
    class WhisperService {
        +transcribe_audio()
        +validate_audio_file()
        +get_model_info()
    }
    
    class OpenAIService {
        +extract_information()
        +generate_chat_response()
        +validate_api_key()
    }
    
    class VectorStoreService {
        +store_conversation()
        +semantic_search()
        +get_status()
    }
    
    ServiceInterface <|-- WhisperService
    ServiceInterface <|-- OpenAIService
    ServiceInterface <|-- VectorStoreService
```

### 2. Repository Pattern
```mermaid
classDiagram
    class Repository {
        <<interface>>
        +get_by_id()
        +create()
        +update()
        +delete()
    }
    
    class TranscriptionRepository {
        +get_transcription_by_id()
        +create_transcription()
        +update_transcription()
        +get_transcriptions()
    }
    
    class DocumentRepository {
        +get_document_by_id()
        +create_document()
        +get_documents_by_patient()
    }
    
    Repository <|-- TranscriptionRepository
    Repository <|-- DocumentRepository
```

### 3. Dependency Injection Pattern
```python
# FastAPI Dependency Injection
@app.post("/upload-audio")
async def upload_audio(
    file: UploadFile,
    whisper_service: WhisperService = Depends(get_whisper_service),
    db: Session = Depends(get_db)
):
    # Service injection automático
    pass
```

## Configuración y Despliegue

### Estructura de Configuración
```mermaid
graph LR
    A[Environment Variables] --> B[Settings Class]
    B --> C[Service Configuration]
    C --> D[Service Initialization]
    
    subgraph "Configuration Sources"
        E[.env file]
        F[OS Environment]
        G[Default Values]
    end
    
    E --> A
    F --> A
    G --> A
    
    subgraph "Service Config"
        H[Database Config]
        I[OpenAI Config]
        J[Vector Store Config]
        K[File Storage Config]
    end
    
    C --> H
    C --> I
    C --> J
    C --> K
```

### Arquitectura de Despliegue

```mermaid
deployment
    node "Development Environment" {
        component [FastAPI App]
        database [SQLite DB]
        artifact [Local Files]
        component [ChromaDB Local]
    }
    
    node "Production Environment" {
        component [FastAPI App Load Balanced]
        database [PostgreSQL Cluster]
        artifact [S3/MinIO Storage]
        component [ChromaDB Distributed]
        component [Redis Cache]
        component [Nginx Reverse Proxy]
    }
    
    cloud "External Services" {
        component [Azure OpenAI]
        component [Monitoring Services]
        component [Backup Services]
    }
```

## Escalabilidad y Performance

### Estrategias de Escalabilidad
```mermaid
graph TD
    A[Escalabilidad Horizontal] --> B[Load Balancing]
    A --> C[Database Sharding]
    A --> D[Microservices Migration]
    
    E[Escalabilidad Vertical] --> F[Resource Optimization]
    E --> G[Caching Strategies]
    E --> H[Background Processing]
    
    I[Performance Optimization] --> J[Async Processing]
    I --> K[Database Indexing]
    I --> L[Connection Pooling]
    
    style A fill:#e8f5e8
    style E fill:#fff3e0
    style I fill:#f3e5f5
```

### Caching Strategy
```mermaid
flowchart LR
    A[Request] --> B{Cache Hit?}
    B -->|Yes| C[Return Cached]
    B -->|No| D[Process Request]
    D --> E[Store in Cache]
    E --> F[Return Response]
    
    subgraph "Cache Layers"
        G[Memory Cache]
        H[Redis Cache]
        I[Database Cache]
    end
    
    B --> G
    D --> H
    I --> D
```

## Seguridad y Compliance

### Arquitectura de Seguridad
```mermaid
graph TB
    subgraph "Security Layers"
        A[Input Validation]
        B[Authentication/Authorization]
        C[Data Encryption]
        D[Audit Logging]
        E[Network Security]
    end
    
    subgraph "Medical Data Protection"
        F[HIPAA Compliance]
        G[Data Anonymization]
        H[Access Controls]
        I[Audit Trails]
    end
    
    A --> B
    B --> C
    C --> D
    D --> E
    
    F --> G
    G --> H
    H --> I
    
    style F fill:#ffebee
    style G fill:#ffebee
    style H fill:#ffebee
    style I fill:#ffebee
```

## Monitoreo y Observabilidad

### Monitoring Architecture
```mermaid
graph TB
    subgraph "Application Layer"
        A[FastAPI App]
        B[Service Metrics]
        C[Business Metrics]
    end
    
    subgraph "Infrastructure Layer"
        D[System Metrics]
        E[Database Metrics]
        F[Network Metrics]
    end
    
    subgraph "Observability Stack"
        G[Logging System]
        H[Metrics Collection]
        I[Tracing System]
        J[Alerting System]
    end
    
    subgraph "Dashboards"
        K[Operations Dashboard]
        L[Business Dashboard]
        M[Performance Dashboard]
    end
    
    A --> G
    B --> H
    C --> H
    D --> H
    E --> H
    F --> H
    
    G --> K
    H --> L
    I --> M
    J --> K
```

## Evolución hacia Microservicios

### Microservices Target Architecture
```mermaid
graph TB
    subgraph "API Gateway"
        GW[Kong/Nginx Gateway]
    end
    
    subgraph "Core Services"
        MS1[Transcription Service]
        MS2[Chat Service]
        MS3[Document Service]
        MS4[Vector Store Service]
        MS5[User Management Service]
    end
    
    subgraph "Shared Services"
        SS1[Configuration Service]
        SS2[Logging Service]
        SS3[Notification Service]
    end
    
    subgraph "Data Layer"
        DB1[Transcription DB]
        DB2[User DB]
        DB3[Document DB]
        DB4[Vector DB]
    end
    
    GW --> MS1
    GW --> MS2
    GW --> MS3
    GW --> MS4
    GW --> MS5
    
    MS1 --> SS1
    MS2 --> SS1
    MS3 --> SS1
    
    MS1 --> DB1
    MS2 --> DB4
    MS3 --> DB3
    MS5 --> DB2
    
    style GW fill:#e3f2fd
    style MS1 fill:#e8f5e8
    style MS2 fill:#e8f5e8
    style MS3 fill:#e8f5e8
    style MS4 fill:#e8f5e8
    style MS5 fill:#e8f5e8
```

## Decisiones Arquitectónicas Clave

### 1. Monolito Modular vs Microservicios
**Decisión:** Comenzar con monolito modular
**Razones:**
- Simplicidad de desarrollo y despliegue
- Menor complejidad operacional
- Equipos pequeños
- Funcionalidades fuertemente acopladas

### 2. SQLite vs PostgreSQL
**Decisión:** SQLite para desarrollo, PostgreSQL para producción
**Razones:**
- SQLite: Sin configuración, ideal para desarrollo
- PostgreSQL: Escalabilidad, concurrencia, características avanzadas

### 3. ChromaDB vs Alternatives
**Decisión:** ChromaDB para vector storage
**Razones:**
- Simplicidad de uso
- Persistencia local
- Integración nativa con embeddings
- No requiere infrastructure compleja

### 4. Whisper Local vs API
**Decisión:** Whisper local
**Razones:**
- Control total sobre datos médicos sensibles
- No dependencia de conectividad
- Costos predecibles
- Latencia controlada

### 5. FastAPI vs Alternatives
**Decisión:** FastAPI
**Razones:**
- Performance excepcional
- Type hints nativos
- Documentación automática
- Ecosistema Python ML

## Consideraciones Futuras

### Roadmap Técnico
1. **Fase 1**: Monolito estable con todas las características
2. **Fase 2**: Optimización de performance y escalabilidad
3. **Fase 3**: Migración gradual a microservicios
4. **Fase 4**: Multi-tenancy y características enterprise

### Mejoras Planificadas
- Real-time transcription con WebSockets
- Advanced speaker diarization con deep learning
- Multi-language support
- Mobile app integration
- Advanced analytics y reporting
- Integration con sistemas hospitalarios (HL7 FHIR)
