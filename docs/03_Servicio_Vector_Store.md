# Servicio Vector Store - ElSol Challenge

## Descripción General
El VectorStoreService implementa el almacenamiento vectorial usando ChromaDB para convertir transcripciones médicas en embeddings semánticamente ricos, permitiendo búsquedas avanzadas y el sistema RAG. Este servicio es fundamental para la funcionalidad de chat inteligente del sistema.

## Clases Principales

### `VectorStoreService`
Clase principal que gestiona todo el ecosistema de almacenamiento vectorial.

**Responsabilidades:**
- Inicialización y gestión de ChromaDB
- Generación de embeddings con sentence-transformers
- Almacenamiento de transcripciones con metadata rica
- Búsqueda semántica avanzada
- Búsquedas especializadas (por paciente, por condición)
- Gestión de similitud y ranking de resultados

**Atributos principales:**
```python
- client: chromadb.PersistentClient  # Cliente ChromaDB persistente
- collection: chromadb.Collection    # Colección de conversaciones médicas
- embedding_model: SentenceTransformer  # Modelo de embeddings
- persist_directory: str             # Directorio de persistencia
```

**Métodos principales:**
- `store_conversation()`: Almacenamiento completo con embeddings
- `semantic_search()`: Búsqueda semántica general
- `search_by_patient()`: Búsqueda específica por paciente
- `search_by_condition()`: Búsqueda por condición médica
- `get_conversation_by_id()`: Recuperación por ID específico

## Integración con Core y Database

### Configuración (`app.core.config`)
```python
# Configuración ChromaDB:
CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
CHROMA_COLLECTION_NAME: str = "medical_conversations"

# Configuración Embeddings:
EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_EMBEDDING_DIMENSIONS: int = 384
```

### Schemas (`app.core.schemas`)
**Input Schemas:**
- `VectorStoreMetadata`: Metadata estructurada para embeddings
- Datos de transcripción completos

**Output Schemas:**
- `VectorStoreResponse`: Confirmación de almacenamiento
- `VectorStoreStatus`: Estado del sistema vectorial
- `StoredConversation`: Conversaciones almacenadas

### Database Models (`app.database.models`)
Campos relacionados en `AudioTranscription`:
```python
vector_stored: str = "false"     # Estado: "true", "false", "failed"
vector_id: str                   # ID único en ChromaDB
```

## Librerías Utilizadas

### Vector Database
```python
import chromadb                    # Base de datos vectorial
from chromadb.config import Settings  # Configuración ChromaDB
import numpy as np                 # Operaciones numéricas
```

### Embeddings y ML
```python
from sentence_transformers import SentenceTransformer  # Modelo de embeddings
import torch                       # Backend ML (opcional)
```

### Async Operations
```python
import asyncio                     # Operaciones asíncronas
from typing import Dict, Any, List, Optional  # Type hints
```

## Arquitectura de Almacenamiento

### Estructura de Embeddings
```python
# Cada documento almacenado contiene:
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

### Preparación de Texto para Embeddings
La función `_prepare_text_for_embedding()` crea texto enriquecido:
```python
# Combina múltiples fuentes:
texto_base = transcripción_original
+ "Paciente: " + nombre_paciente
+ "Diagnóstico: " + diagnóstico  
+ "Medicamentos: " + lista_medicamentos
+ "Síntomas: " + lista_síntomas
+ "Contexto: " + contexto_conversación
```

## Funcionalidades de Búsqueda

### 1. Búsqueda Semántica General (`semantic_search`)
```python
# Parámetros:
- query: str                    # Consulta en lenguaje natural
- max_results: int = 5         # Número máximo de resultados
- similarity_threshold: float = 0.7  # Umbral mínimo de similitud
- metadata_filters: Dict       # Filtros adicionales

# Retorna:
- Lista de resultados con contexto, metadata y puntuaciones
- Excerpts relevantes del texto
- Scores de similitud coseno
```

### 2. Búsqueda por Paciente (`search_by_patient`)
Implementa búsqueda fuzzy optimizada para nombres latinos:
```python
# Características:
- Similitud de nombres con múltiples partes
- Normalización de acentos y caracteres especiales
- Coincidencias parciales y exactas
- Ranking por relevancia de nombres

# Algoritmo de similitud de nombres:
def _calculate_name_similarity(search_name, stored_name):
    # Normalización
    # Coincidencia exacta = 1.0
    # Coincidencias de palabras comunes
    # Bonificaciones por orden y completitud
    # Penalizaciones por palabras extra
```

### 3. Búsqueda por Condición (`search_by_condition`)
```python
# Estrategia híbrida:
1. Búsqueda semántica amplia con "diagnóstico [condición] enfermedad"
2. Filtrado por presencia en campos diagnosis/symptoms/content
3. Agrupación por paciente único
4. Limitación de resultados por paciente
```

## API Endpoints Asociados

### `/vector/status` (GET)
Proporciona estado del vector store:
- Número total de documentos
- Modelo de embeddings usado
- Directorio de persistencia
- Última actualización

### `/vector/conversations` (GET)
Lista conversaciones almacenadas con:
- Preview de texto
- Metadata asociada
- Timestamps de almacenamiento

### Integración Automática
**Flujo en `/upload-audio`:**
1. Transcripción completada por Whisper
2. Extracción de datos por OpenAI
3. **Almacenamiento automático en Vector Store**
4. Actualización de BD con vector_id

## Características Técnicas

### Modelo de Embeddings
```python
# all-MiniLM-L6-v2 características:
- Dimensiones: 384
- Velocidad: Alta (optimizado para producción)
- Calidad: Excelente para textos en español
- Tamaño: ~90MB
- Soporte multilenguaje: Sí
```

### Persistencia y Rendimiento
```python
# ChromaDB configuración:
- Persistencia: Directorio local
- Índice: HNSW (Hierarchical Navigable Small World)
- Distancia: Coseno (convertida a similitud)
- Batch operations: Soportadas
- Concurrencia: Thread-safe
```

### Optimizaciones de Búsqueda
1. **Excerpt Generation**: Fragmentos relevantes contextuales
2. **Score Normalization**: Conversión distancia → similitud
3. **Metadata Filtering**: Filtros eficientes por campos
4. **Result Ranking**: Múltiples factores de relevancia

## Integración con Chat Service

### Pipeline RAG Completo
```python
# Flujo en ChatService:
1. Análisis de consulta → entidades y términos
2. Vector Service → búsqueda semántica
3. Ranking y filtrado → contexto final
4. OpenAI Service → generación de respuesta
```

### Tipos de Búsquedas RAG
```python
# Por intención detectada:
ChatIntent.PATIENT_INFO → search_by_patient()
ChatIntent.CONDITION_LIST → search_by_condition() 
ChatIntent.GENERAL_QUERY → semantic_search()
```

## Error Handling y Robustez

### Manejo de Errores
```python
- VectorStoreError: Errores del vector store
- Embedding failures → embeddings por defecto
- ChromaDB connection issues → reintentos automáticos
- Memory issues → procesamiento por lotes
```

### Validaciones
- **Text Length**: Límite de 8000 caracteres para embeddings
- **Metadata Validation**: Tipos correctos para filtros
- **Encoding Issues**: Manejo de caracteres especiales
- **Similarity Thresholds**: Validación de rangos 0.0-1.0

## Configuración de Producción

### Escalabilidad
```python
# Para volúmenes altos:
- Batch embedding generation
- Índice HNSW optimizado
- Memoria compartida para modelo
- Particionado por fecha/tipo

# Hardware recomendado:
- RAM: 8GB+ para modelo y índices
- Storage: SSD para mejor I/O
- CPU: Multi-core para embeddings paralelos
```

### Monitoreo
- **Collection Size**: Número de documentos almacenados
- **Query Performance**: Latencia de búsquedas
- **Embedding Quality**: Distribución de similitudes
- **Storage Usage**: Espacio en disco utilizado

## Casos de Uso Específicos

### Sistema RAG Médico
```python
# Consultas típicas:
"¿Qué enfermedad tiene Juan Pérez?"
→ search_by_patient("Juan Pérez")

"Pacientes con diabetes"  
→ search_by_condition("diabetes")

"Síntomas de dolor de cabeza"
→ semantic_search("dolor de cabeza síntomas")
```

### Análisis de Tendencias
- **Patrones de síntomas**: Clustering de embeddings similares
- **Evolución de pacientes**: Búsquedas temporales
- **Efectividad de tratamientos**: Análisis longitudinal

## Mejores Prácticas

### Preparación de Datos
```python
# Optimización de embeddings:
1. Combinar información estructurada y no estructurada
2. Normalizar terminología médica
3. Incluir contexto temporal
4. Mantener información del paciente
```

### Gestión de Memoria
```python
# Para grandes volúmenes:
- Lazy loading del modelo de embeddings
- Procesamiento asíncrono en thread pools
- Limpieza periódica de caché
- Monitoreo de uso de memoria
```

### Calidad de Búsqueda
```python
# Mejores resultados:
- Umbrales de similitud ajustados por tipo de consulta
- Metadata rica para filtrado preciso
- Excerpts contextuales para relevancia
- Ranking multi-factor (similitud + entidades + fecha)
```
