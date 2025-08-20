# Servicio Chat RAG - ElSol Challenge

## Descripción General
El ChatService implementa un sistema completo RAG (Retrieval-Augmented Generation) especializado en consultas médicas. Combina análisis de intención, búsqueda vectorial semántica y generación de respuestas contextuales para proporcionar un asistente médico inteligente.

## Clases Principales

### `ChatService`
Clase principal que orquesta todo el pipeline RAG para consultas médicas.

**Responsabilidades:**
- Análisis y clasificación de consultas en lenguaje natural
- Detección de intenciones médicas específicas
- Extracción de entidades (pacientes, condiciones, síntomas)
- Coordinación con VectorStoreService para recuperación de contexto
- Generación de respuestas usando OpenAI con contexto médico
- Cálculo de confianza y sugerencias de seguimiento

**Atributos principales:**
```python
- vector_service: VectorStoreService  # Servicio de búsqueda vectorial
- openai_service: OpenAIService      # Servicio de generación
- _intent_patterns: Dict             # Patrones para detección de intención
- _medical_terms: Dict               # Diccionario de términos médicos
```

**Métodos principales:**
- `process_chat_query()`: Pipeline RAG completo
- `_analyze_query()`: Análisis de intención y entidades
- `_retrieve_context()`: Recuperación de contexto relevante
- `_generate_answer()`: Generación de respuesta contextual

## Pipeline RAG Completo

### 1. Análisis de Consulta (`_analyze_query`)
```python
# Proceso:
query → normalize → detect_intent → extract_entities → generate_search_terms → filters

# Normalización:
- Conversión a minúsculas
- Eliminación de acentos y caracteres especiales
- Limpieza de espacios múltiples

# Detección de intención:
- Patrones regex especializados por tipo de consulta
- Clasificación automática según contexto médico
```

### 2. Clasificación de Intenciones (`ChatIntent`)
```python
PATIENT_INFO = "patient_info"        # "¿Qué enfermedad tiene X?"
CONDITION_LIST = "condition_list"    # "Listame pacientes con diabetes"
SYMPTOM_SEARCH = "symptom_search"    # "¿Quién tiene dolor de cabeza?"
MEDICATION_INFO = "medication_info"  # "¿Qué medicamentos toma X?"
GENERAL_QUERY = "general_query"      # Consultas generales
TEMPORAL_QUERY = "temporal_query"    # "¿Qué pasó la semana pasada?"
UNKNOWN = "unknown"                  # Intención no reconocida
```

### 3. Extracción de Entidades (`_extract_entities`)
```python
# Entidades detectadas:
{
    "patients": ["Juan Pérez", "María García"],      # Nombres de pacientes
    "conditions": ["diabetes", "hipertensión"],      # Condiciones médicas
    "symptoms": ["dolor de cabeza", "mareos"],       # Síntomas
    "medications": ["metformina", "losartan"],       # Medicamentos
    "dates": ["ayer", "semana pasada", "2024-01-15"] # Referencias temporales
}
```

## Integración con Core y Database

### Configuración (`app.core.config`)
```python
# Hereda configuración de servicios dependientes:
- AZURE_OPENAI_*: Para generación de respuestas
- CHROMA_*: Para búsqueda vectorial
- VECTOR_EMBEDDING_*: Para similaridad semántica
```

### Schemas (`app.core.schemas`)
**Input Schemas:**
- `ChatQuery`: Consulta del usuario con parámetros
- `QueryAnalysis`: Análisis interno de consulta
- `RAGContext`: Contexto completo para generación

**Output Schemas:**
- `ChatResponse`: Respuesta completa con fuentes
- `ChatSource`: Fuentes de información utilizadas
- `ChatStats`: Estadísticas del sistema

### No hay Database directa
El ChatService es stateless y no persiste datos, solo consulta:
- Vector Store para contexto
- Database vía servicios para metadata

## Librerías Utilizadas

### Core Processing
```python
import re                    # Regex para detección de patrones
import time                  # Métricas de performance
import asyncio               # Operaciones asíncronas
from typing import Dict, Any, List, Optional, Tuple  # Type hints
```

### Integration
```python
from app.services.vector_service import VectorStoreService
from app.services.openai_service import OpenAIService
```

## Análisis de Intención Avanzado

### Patrones de Detección
```python
# Ejemplos de patrones regex especializados:
PATIENT_INFO_PATTERNS = [
    r"qu[eé].*(enfermedad|tiene|diagn[oó]stico).*([\w\s]+)",
    r"informaci[oó]n.*(paciente|de).*([\w\s]+)",
    r"qu[eé].*(le pasa|padece).*([\w\s]+)"
]

CONDITION_LIST_PATTERNS = [
    r"lista.*pacientes.*(con|que tienen).*([\w\s]+)",
    r"qui[eé]nes.*(tienen|padecen).*([\w\s]+)",
    r"pacientes.*(diabetes|hipertensi[oó]n|cancer|asma)"
]
```

### Diccionario Médico
```python
_medical_terms = {
    "diabetes": ["diabetes", "diabético", "glucosa", "azúcar", "insulina"],
    "hipertensión": ["hipertensión", "presión alta", "presión arterial", "hipertenso"],
    "asma": ["asma", "asmático", "bronquial", "respiratorio"],
    "migraña": ["migraña", "jaqueca", "dolor de cabeza", "cefalea"]
}
```

## Estrategias de Recuperación de Contexto

### Estrategia por Intención
```python
if intent == ChatIntent.PATIENT_INFO and entities.get("patients"):
    # Búsqueda específica por paciente
    results = await vector_service.search_by_patient(
        patient_name=patient_name,
        max_results=max_results
    )

elif intent == ChatIntent.CONDITION_LIST and entities.get("conditions"):
    # Búsqueda por condición médica
    results = await vector_service.search_by_condition(
        condition=condition,
        max_results=max_results
    )

else:
    # Búsqueda semántica general
    results = await vector_service.semantic_search(
        query=search_query,
        max_results=max_results,
        similarity_threshold=0.6
    )
```

### Ranking de Contexto (`_rank_contexts`)
```python
# Factores de ranking:
1. Base Score: Similitud semántica del vector store
2. Entity Bonus: +0.1 por coincidencia de paciente, +0.15 por condición
3. Symptom Bonus: +0.05 por síntoma coincidente  
4. Date Bonus: +0.02 por fecha reciente
5. Final Score: min(base + bonuses, 1.0)
```

## Generación de Respuestas

### Prompts Especializados por Intención
```python
# PATIENT_INFO template:
"""
Eres un asistente médico. Responde la consulta sobre el paciente basándote 
ÚNICAMENTE en la información médica proporcionada.

INFORMACIÓN MÉDICA DISPONIBLE:
{context}

PREGUNTA DEL USUARIO: {query}

INSTRUCCIONES:
1. Analiza la información médica disponible
2. Responde de manera clara y directa a la pregunta
3. Incluye detalles relevantes como diagnóstico, síntomas y fecha
4. Si la información es incompleta, menciona qué falta
5. NUNCA inventes información que no esté en el contexto
"""

# CONDITION_LIST template:
"""
Basándote en la información médica proporcionada, genera una lista de 
pacientes que cumplen con el criterio solicitado.

INSTRUCCIONES:
- Lista SOLO pacientes que aparezcan en la información proporcionada
- Incluye información relevante de cada paciente
- Organiza la lista de manera clara y estructurada
- Indica el número total de pacientes encontrados
"""
```

### Validación de Respuestas (`_validate_response`)
```python
# Validaciones aplicadas:
1. Limpieza básica de formato
2. Agregar disclaimer médico automático
3. Limitación de longitud (2000 caracteres)
4. Verificación de coherencia con contexto
```

## API Endpoints Asociados

### `/chat/query` (POST)
**Request:**
```json
{
    "query": "¿Qué enfermedad tiene Juan Pérez?",
    "max_results": 5,
    "filters": {"patient_name": "Juan"},
    "include_sources": true
}
```

**Response:**
```json
{
    "answer": "Respuesta generada contextual...",
    "sources": [
        {
            "conversation_id": "12345",
            "patient_name": "Juan Pérez",
            "relevance_score": 0.95,
            "excerpt": "Fragmento relevante...",
            "date": "2024-01-15"
        }
    ],
    "confidence": 0.87,
    "intent": "patient_info",
    "follow_up_suggestions": ["¿Qué tratamiento...?"],
    "processing_time_ms": 1250
}
```

## Características Técnicas

### Cálculo de Confianza (`_calculate_confidence`)
```python
# Factores considerados:
1. Similitud promedio de contextos (peso: 60%)
2. Bonus por coincidencia de entidades (peso: 20%)
3. Bonus por número de fuentes (peso: 15%)
4. Penalty por información incompleta (peso: 5%)

# Rango: 0.1 - 0.95 (nunca 100% para evitar overconfidence)
```

### Sugerencias de Seguimiento (`_generate_follow_up_suggestions`)
```python
# Por intención detectada:
PATIENT_INFO → [
    "¿Qué tratamiento se recomendó para {paciente}?",
    "¿Cuándo fue la última consulta de {paciente}?",
    "¿Qué síntomas reportó {paciente}?"
]

CONDITION_LIST → [
    "¿Qué tratamientos hay para {condición}?",
    "¿Cuántos pacientes nuevos con {condición} hay este mes?",
    "¿Qué síntomas son más comunes en {condición}?"
]
```

## Integración con Otros Servicios

### Vector Service (Recuperación)
```python
# Métodos utilizados:
- semantic_search(): Búsqueda general por similitud
- search_by_patient(): Búsqueda específica fuzzy por nombre
- search_by_condition(): Búsqueda por condición médica

# Datos recibidos:
- Contexto relevante con metadata
- Scores de similitud
- Excerpts contextuales
```

### OpenAI Service (Generación)
```python
# Método específico para chat:
await openai_service._call_openai_chat_api([
    {"role": "system", "content": "Eres un asistente médico..."},
    {"role": "user", "content": prompt_con_contexto}
])

# Configuración especializada:
- Temperature: Baja para consistencia médica
- Max tokens: Limitado para respuestas concisas
- Stop sequences: Para evitar información inventada
```

## Error Handling y Robustez

### Manejo de Errores
```python
- ChatServiceError: Errores del pipeline RAG
- Fallback graceful: Respuesta genérica si falla todo
- Timeout handling: Límites de tiempo por operación
- Context validation: Validación de contexto recuperado
```

### Degraded Service
```python
# Niveles de degradación:
1. Full RAG: Análisis + Vector Search + Generation
2. Simple Search: Solo búsqueda sin análisis avanzado
3. Fallback Response: Respuesta genérica sin contexto
4. Error Response: Mensaje de error amigable
```

## Casos de Uso Específicos

### Consultas de Información de Pacientes
```python
# Entrada: "¿Qué le pasa a María García?"
# Procesamiento:
1. Intent: PATIENT_INFO
2. Entities: {"patients": ["María García"]}
3. Vector search: search_by_patient("María García")
4. Context ranking: Conversaciones más relevantes
5. Generation: Respuesta con diagnóstico y síntomas
```

### Listas por Condición
```python
# Entrada: "Lista pacientes con diabetes"
# Procesamiento:
1. Intent: CONDITION_LIST  
2. Entities: {"conditions": ["diabetes"]}
3. Vector search: search_by_condition("diabetes")
4. Aggregation: Agrupar por paciente único
5. Generation: Lista estructurada con detalles
```

### Consultas Temporales
```python
# Entrada: "¿Qué consultas hubo ayer?"
# Procesamiento:
1. Intent: TEMPORAL_QUERY
2. Entities: {"dates": ["ayer"]}
3. Filters: Date filtering en metadata
4. Context: Conversaciones del día anterior
5. Generation: Resumen de actividad
```

## Configuración de Producción

### Performance Tuning
```python
# Optimizaciones:
MAX_CONTEXT_LENGTH = 4000      # Caracteres de contexto
MAX_RESULTS_PER_SEARCH = 20    # Resultados por búsqueda
SIMILARITY_THRESHOLD = 0.6     # Umbral mínimo de similitud
CONFIDENCE_THRESHOLD = 0.3     # Mínimo para respuesta válida
```

### Monitoreo y Métricas
```python
# Métricas clave:
- Query volume y distribución por intención
- Latencia promedio del pipeline RAG
- Confidence scores distribution
- User satisfaction (implicit via follow-ups)
- Error rates por tipo de fallo
```

## Mejores Prácticas

### Optimización de Consultas
```python
# Mejores resultados:
1. Consultas específicas > generales
2. Incluir nombres exactos de pacientes
3. Usar terminología médica correcta
4. Consultas contextuales sobre conversaciones específicas
```

### Gestión de Contexto
```python
# Balance contexto vs. relevancia:
- Múltiples fuentes para completitud
- Ranking por relevancia para priorización
- Excerpts para información específica
- Metadata para filtering preciso
```
