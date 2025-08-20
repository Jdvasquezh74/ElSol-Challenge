# Servicio de Transcripción Whisper - ElSol Challenge

## Descripción General
El servicio de transcripción Whisper es el componente central para convertir archivos de audio en texto utilizando el modelo Whisper de OpenAI ejecutado localmente. Este servicio no requiere conexión a internet ni API keys, proporcionando privacidad y control total sobre los datos médicos.

## Clases Principales

### `LocalWhisperService`
Clase principal que maneja toda la funcionalidad de transcripción de audio.

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

**Métodos principales:**
- `transcribe_audio()`: Transcripción principal con validaciones
- `validate_audio_file()`: Validación completa de archivos
- `get_model_info()`: Información del modelo y hardware

## Integración con Core y Database

### Configuración (`app.core.config`)
```python
# Variables relevantes de Settings:
WHISPER_MODEL: str = "base"           # Modelo a usar
WHISPER_DEVICE: str = "cpu"           # cpu o cuda
TRANSCRIPTION_TIMEOUT: int = 300      # 5 minutos
UPLOAD_MAX_SIZE: int = 26_214_400     # 25MB
UPLOAD_ALLOWED_EXTENSIONS: List[str]  # [wav, mp3]
```

### Schemas (`app.core.schemas`)
El servicio utiliza y produce:
- `TranscriptionStatusEnum`: Estados de procesamiento
- `TranscriptionResult`: Resultado completo con texto y metadata
- `TranscriptionResponse`: Respuesta API con timestamps

### Database Models (`app.database.models`)
Integración con `AudioTranscription`:
```python
# Campos actualizados por el servicio:
raw_transcription: str
confidence_score: str
language_detected: str
audio_duration_seconds: int
processing_time_seconds: int
whisper_model_used: str
```

## Librerías Utilizadas

### Core Dependencies
```python
import whisper           # Modelo Whisper de OpenAI
import torch             # Backend de ML y gestión GPU
import asyncio           # Ejecución asíncrona
import structlog         # Logging estructurado
```

### Audio Processing
```python
# Formatos soportados nativamente por Whisper:
- WAV (RIFF/WAVE)
- MP3 (ID3v2 y frames de audio)
```

### Hardware Requirements
```python
# CPU: Funciona en cualquier CPU moderna
# GPU: CUDA opcional para aceleración
# RAM: 
#   - tiny: ~1GB
#   - base: ~1GB
#   - small: ~2GB
#   - medium: ~5GB
#   - large: ~10GB
```

## API Endpoints Asociados

### `/upload-audio` (POST)
**Flujo de procesamiento:**
1. Validación de archivo en `upload.py`
2. Creación de registro en BD
3. Llamada asíncrona a `WhisperService.transcribe_audio()`
4. Actualización de BD con resultados

### `/transcriptions/{id}` (GET)
Consulta el estado y resultados de transcripción almacenados en BD.

## Características Técnicas

### Modelos Whisper Disponibles
```python
WHISPER_MODELS_INFO = {
    "tiny": {"size": "~39 MB", "speed": "~32x", "accuracy": "Básica"},
    "base": {"size": "~74 MB", "speed": "~16x", "accuracy": "Buena"},
    "small": {"size": "~244 MB", "speed": "~6x", "accuracy": "Muy buena"},
    "medium": {"size": "~769 MB", "speed": "~2x", "accuracy": "Excelente"},
    "large": {"size": "~1550 MB", "speed": "~1x", "accuracy": "Máxima"}
}
```

### Validaciones Implementadas
1. **Archivo existente y tamaño válido**
2. **Extensión permitida** (wav, mp3)
3. **Magic numbers** (RIFF/WAVE, ID3/MP3)
4. **Límites de tamaño** (25MB máximo)

### Características Avanzadas
- **Word timestamps**: Para futura diarización de hablantes
- **Confianza calculada**: Basada en probabilidades de segmentos
- **Detección de idioma**: Automática por Whisper
- **Prompt de contexto**: Optimizado para conversaciones médicas

## Prompt Médico Especializado
```python
MEDICAL_CONVERSATION_PROMPT = """
Esta es una transcripción de una conversación médica entre un doctor y un paciente. 
El diálogo puede incluir información como nombres, edades, síntomas, diagnósticos, 
medicamentos, y recomendaciones médicas. Por favor transcribe con precisión todos 
los términos médicos y datos personales mencionados.
"""
```

## Error Handling
- `WhisperTranscriptionError`: Excepción personalizada
- Fallbacks para fallos de GPU → CPU
- Validación robusta de archivos corruptos
- Timeouts configurables

## Performance y Optimizaciones
- **Lazy loading**: Modelo se carga solo cuando se necesita
- **Thread pool**: Ejecución no-bloqueante con `asyncio`
- **Configuración GPU**: Detección automática de CUDA
- **Logging estructurado**: Métricas de performance

## Integración con Otros Servicios

### → Vector Service
Los resultados de transcripción se envían automáticamente al `VectorStoreService` para:
- Generación de embeddings
- Almacenamiento en ChromaDB
- Indexación para búsqueda semántica

### → Speaker Service
Los segmentos con timestamps se usan en `SpeakerService` para:
- Diarización de hablantes
- Identificación promotor vs paciente
- Análisis de patrones de conversación

### → OpenAI Service
El texto transcrito se procesa con `OpenAIService` para:
- Extracción de información estructurada
- Análisis de datos no estructurados
- Clasificación de contenido médico

## Configuración de Producción

### Recomendaciones de Hardware
```python
# Para volumen bajo-medio:
WHISPER_MODEL = "base"    # Balance velocidad/precisión
WHISPER_DEVICE = "cpu"    # Suficiente para ~5 transcripciones/hora

# Para volumen alto:
WHISPER_MODEL = "small"   # Mejor precisión
WHISPER_DEVICE = "cuda"   # GPU para paralelización
```

### Monitoreo y Métricas
- Tiempo de procesamiento por archivo
- Uso de memoria y GPU
- Tasa de éxito/fallo
- Confianza promedio de transcripciones

## Casos de Uso Específicos

### Conversaciones Médicas
- Extrae nombres de pacientes
- Identifica terminología médica
- Preserva números y dosis
- Mantiene contexto temporal

### Manejo de Errores Comunes
- Audio de baja calidad → confianza "low"
- Archivos corruptos → validación previa
- Idiomas no soportados → fallback a español
- Modelos no disponibles → downgrade automático
