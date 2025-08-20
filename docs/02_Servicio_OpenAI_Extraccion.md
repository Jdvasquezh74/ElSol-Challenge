# Servicio de Extracción de Información OpenAI - ElSol Challenge

## Descripción General
El servicio OpenAI es responsable de extraer información estructurada y no estructurada de las transcripciones de audio utilizando modelos de Azure OpenAI. Este servicio transforma texto crudo en datos médicos organizados y útiles para análisis posterior.

## Clases Principales

### `OpenAIService`
Clase principal que maneja toda la comunicación con Azure OpenAI y el procesamiento de información médica.

**Responsabilidades:**
- Comunicación con Azure OpenAI API
- Extracción de información estructurada (nombres, edades, diagnósticos)
- Análisis de datos no estructurados (síntomas, emociones, contexto)
- Generación de respuestas para el chatbot
- Validación y limpieza de datos extraídos

**Atributos principales:**
```python
- api_key: str           # Azure OpenAI API key
- endpoint: str          # Azure OpenAI endpoint
- api_version: str       # Versión de API
- deployment: str        # Deployment name (modelo)
- client: AsyncOpenAI    # Cliente asíncrono
```

**Métodos principales:**
- `extract_structured_information()`: Extrae datos estructurados de transcripciones
- `extract_unstructured_information()`: Analiza contexto y patrones
- `generate_chat_response()`: Respuestas para el sistema RAG
- `validate_extraction_results()`: Validación de datos extraídos

## Integración con Core y Database

### Configuración (`app.core.config`)
```python
# Variables de Azure OpenAI:
AZURE_OPENAI_API_KEY: str = "azure-openai-key"
AZURE_OPENAI_API_VERSION: str = "api-version"
AZURE_OPENAI_API_ENDPOINT: str = "https://resource.openai.azure.com/"
AZURE_OPENAI_DEPLOYMENT: str = "model"
```

### Schemas (`app.core.schemas`)
**Input Schemas:**
- Recibe texto de transcripción crudo
- Utiliza contexto de archivos de audio

**Output Schemas:**
- `StructuredData`: Información médica estructurada
- `UnstructuredData`: Análisis contextual y emocional
- `ChatResponse`: Respuestas del sistema RAG

### Database Models (`app.database.models`)
Actualiza campos en `AudioTranscription`:
```python
structured_data: JSON      # Información extraída estructurada
unstructured_data: JSON    # Análisis no estructurado
```

## Librerías Utilizadas

### Azure OpenAI Integration
```python
import openai              # Cliente oficial de OpenAI
from openai import AsyncOpenAI  # Cliente asíncrono
import httpx               # HTTP client para requests robustos
import asyncio             # Ejecución asíncrona
```

### Data Processing
```python
import json                # Parsing de respuestas JSON
import re                  # Expresiones regulares para validación
from typing import Dict, Any, List  # Type hints
```

### Error Handling
```python
import structlog           # Logging estructurado
from tenacity import retry # Reintentos automáticos
```

## Prompts Especializados

### Extracción Estructurada
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

FORMATO DE RESPUESTA (JSON):
{
    "nombre": "string o null",
    "edad": number o null,
    "fecha": "YYYY-MM-DD o null",
    "diagnostico": "string o null",
    "medico": "string o null",
    "medicamentos": ["array de strings"],
    "telefono": "string o null",
    "email": "string o null"
}
"""
```

### Análisis No Estructurado
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
- preguntas: Preguntas importantes formuladas
- respuestas: Respuestas clave proporcionadas

FORMATO JSON:
{
    "sintomas": ["array de síntomas"],
    "contexto": "string descriptivo",
    "observaciones": "string con observaciones",
    "emociones": ["array de emociones"],
    "urgencia": "baja|media|alta",
    "recomendaciones": ["array de recomendaciones"],
    "preguntas": ["array de preguntas"],
    "respuestas": ["array de respuestas clave"]
}
"""
```

## API Endpoints Asociados

### Procesamiento Automático
**Flujo en `/upload-audio`:**
1. Whisper genera transcripción
2. OpenAI Service extrae información estructurada
3. OpenAI Service analiza datos no estructurados
4. Resultados se almacenan en BD

### Sistema RAG en `/chat`
**Flujo en ChatService:**
1. Consulta del usuario se analiza
2. Vector Service recupera contexto relevante
3. OpenAI Service genera respuesta contextual
4. Respuesta se envía al usuario

## Características Técnicas

### Manejo de Rate Limiting
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(RateLimitError)
)
async def _call_openai_api():
    # Lógica de llamada con reintentos automáticos
```

### Validación de Respuestas
- **JSON Schema Validation**: Estructura de respuestas
- **Data Type Validation**: Tipos de datos correctos
- **Range Validation**: Valores dentro de rangos válidos (ej. edad 0-150)
- **Medical Term Validation**: Terminología médica coherente

### Optimizaciones de Tokens
- **Prompt Engineering**: Prompts concisos pero completos
- **Context Truncation**: Limitación de contexto a 4000 caracteres
- **Response Parsing**: Extracción eficiente de JSON de respuestas

## Seguridad y Privacidad

### Manejo de Datos Sensibles
- **No Logging**: Datos médicos no se registran en logs
- **Memory Cleanup**: Limpieza de variables sensibles
- **API Key Security**: Manejo seguro de credenciales
- **Data Minimization**: Solo se procesa información necesaria

### Compliance Médico
- **HIPAA Considerations**: Preparado para cumplimiento HIPAA
- **Data Retention**: Control sobre retención de datos
- **Audit Trail**: Logging de operaciones sin datos sensibles

## Error Handling y Robustez

### Tipos de Errores Manejados
```python
- OpenAIAPIError: Errores de API
- RateLimitError: Límites de velocidad
- InvalidJSONError: Respuestas mal formateadas
- ValidationError: Datos fuera de rangos válidos
- NetworkError: Problemas de conectividad
```

### Estrategias de Fallback
1. **Reintentos Automáticos**: 3 intentos con backoff exponencial
2. **Degraded Service**: Extracción parcial si falla completamente
3. **Cache de Prompts**: Reutilización de prompts exitosos
4. **Default Values**: Valores por defecto para campos críticos

## Integración con Otros Servicios

### → Vector Service
Los datos extraídos se usan para:
- Enriquecer metadata en embeddings
- Mejorar calidad de búsqueda semántica
- Crear índices por campos específicos

### → Chat Service
Proporciona capacidades de:
- Generación de respuestas contextuales
- Análisis de intención de consultas
- Expansión de términos médicos

### → Document Service (OCR)
Para documentos procesados:
- Extracción de metadata de PDFs médicos
- Análisis de información en imágenes OCR
- Categorización automática de documentos

## Configuración de Producción

### Azure OpenAI Setup
```python
# Configuración recomendada:
AZURE_OPENAI_DEPLOYMENT = "gpt-4"  # Para mejor precisión
AZURE_OPENAI_API_VERSION = "2024-02-01"  # Versión estable

# Rate limiting:
MAX_REQUESTS_PER_MINUTE = 60
MAX_TOKENS_PER_REQUEST = 4000
```

### Monitoreo y Métricas
- **API Usage**: Tokens consumidos por operación
- **Response Quality**: Validación de extracciones
- **Latency**: Tiempo de respuesta de API
- **Error Rates**: Porcentaje de fallos por tipo

## Casos de Uso Específicos

### Información Estructurada
- **Datos Demográficos**: Nombre, edad, contacto
- **Información Médica**: Diagnósticos, medicamentos, fechas
- **Datos de Consulta**: Médico tratante, tipo de consulta

### Análisis Contextual
- **Estado Emocional**: Ansiedad, preocupación, alivio
- **Nivel de Urgencia**: Evaluación automática de prioridad
- **Calidad de Comunicación**: Comprensión mutua, claridad

### Respuestas RAG
- **Consultas de Pacientes**: "¿Qué enfermedad tiene Juan?"
- **Búsquedas por Síntomas**: "¿Quién tiene dolor de cabeza?"
- **Análisis Temporal**: "¿Qué pasó la semana pasada?"

## Mejores Prácticas

### Prompt Engineering
- **Especificidad**: Prompts muy específicos para cada tipo de extracción
- **Ejemplos**: Few-shot learning con ejemplos médicos
- **Formato Constante**: JSON schema consistente
- **Validación**: Instrucciones claras de validación

### Gestión de Costos
- **Token Optimization**: Prompts mínimos pero efectivos
- **Batch Processing**: Agrupación de extracciones similares
- **Caching**: Cache de respuestas para consultas similares
- **Model Selection**: Balance entre costo y calidad
