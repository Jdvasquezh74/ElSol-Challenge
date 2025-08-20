# Servicio de Diferenciación de Hablantes - ElSol Challenge

## Descripción General
El SpeakerService implementa diarización de hablantes (speaker diarization) especializada en conversaciones médicas, identificando y separando automáticamente la participación del promotor de salud y el paciente. Utiliza un enfoque híbrido que combina análisis de audio y procesamiento de texto para lograr precisión en contextos médicos específicos.

## Clases Principales

### `SpeakerService`
Clase principal que maneja toda la funcionalidad de diferenciación de hablantes.

**Responsabilidades:**
- Análisis de características de audio (pitch, energía, ritmo)
- Clustering de voces usando machine learning
- Análisis semántico del contenido transcrito
- Clasificación híbrida promotor vs. paciente
- Generación de estadísticas de participación
- Segmentación temporal con confianza

**Atributos principales:**
```python
- _promotor_patterns: List[str]       # Patrones de habla del promotor
- _paciente_patterns: List[str]       # Patrones de habla del paciente
- _medical_professional_keywords: List[str]  # Terminología médica
- _patient_keywords: List[str]        # Palabras típicas de pacientes
```

**Métodos principales:**
- `diarize_conversation()`: Diarización completa híbrida
- `_diarize_with_audio_and_text()`: Método avanzado con audio
- `_diarize_text_only()`: Método fallback solo con texto
- `_calculate_speaker_stats()`: Estadísticas de participación

## Arquitectura de Diarización

### Enfoque Híbrido
```python
# Estrategia adaptativa:
if whisper_segments and librosa_available:
    # Método avanzado: análisis de audio + texto
    segments = _diarize_with_audio_and_text()
else:
    # Método básico: solo análisis de texto
    segments = _diarize_text_only()
```

### Pipeline de Audio + Texto
```python
# Proceso completo:
audio_file → feature_extraction → clustering → text_analysis → hybrid_classification → segments

# Características de audio extraídas:
1. Pitch (frecuencia fundamental)
2. Intensidad (RMS energy)  
3. Espectro (centroide espectral)
4. Velocidad de habla (zero crossing rate)
5. Variabilidad tonal (pitch range)
6. Pausas y ritmo
```

## Integración con Core y Database

### Configuración (`app.core.config`)
```python
# Configuración de diarización:
SPEAKER_MIN_SEGMENT_LENGTH: float = 1.0      # Duración mínima de segmento
SPEAKER_CONFIDENCE_THRESHOLD: float = 0.7    # Umbral de confianza
SPEAKER_MAX_SPEAKERS: int = 5                # Máximo número de hablantes
DIARIZATION_SAMPLE_RATE: int = 16000         # Sample rate para análisis
```

### Schemas (`app.core.schemas`)
**Core Schemas:**
- `SpeakerType`: Enum (PROMOTOR, PACIENTE, UNKNOWN, MULTIPLE)
- `SpeakerSegment`: Segmento individual con hablante identificado
- `SpeakerStats`: Estadísticas agregadas de participación
- `DiarizationResult`: Resultado completo con segmentos y estadísticas

**Output Integration:**
- `TranscriptionWithSpeakers`: Transcripción extendida con diarización

### Database Models (`app.database.models`)
Campos en `AudioTranscription`:
```python
# Speaker diarization results:
speaker_segments: str              # JSON array de segmentos
speaker_stats: str                 # JSON object de estadísticas  
diarization_processed: str         # "true", "false", "failed"

# Métodos de modelo:
set_speaker_data(segments, stats)  # Almacenar resultados
mark_diarization_failed()          # Marcar como fallido
```

## Librerías Utilizadas

### Audio Processing (Dependencias Opcionales)
```python
import librosa                     # Análisis de audio y features
import scipy.signal                # Procesamiento de señales
from sklearn.cluster import KMeans # Clustering de características
from sklearn.preprocessing import StandardScaler  # Normalización
import numpy as np                 # Operaciones numéricas
```

### Text Processing
```python
import re                          # Regex para patrones de habla
import time                        # Métricas de performance
from typing import List, Dict, Any, Tuple, Optional
```

### Graceful Degradation
```python
# Manejo de dependencias faltantes:
try:
    import librosa
    import scipy.signal
    from sklearn.cluster import KMeans
except ImportError:
    # Fallback a análisis solo de texto
    logger.warning("Audio processing dependencies missing")
```

## Análisis de Características de Audio

### Extracción de Features (`_extract_audio_features`)
```python
# Características extraídas por segmento:
1. Pitch Analysis:
   - f0 = librosa.yin(audio, fmin=50, fmax=400)
   - pitch_mean, pitch_std, pitch_range

2. Energy Analysis:
   - rms = librosa.feature.rms(audio)
   - energy_mean

3. Spectral Analysis:
   - spectral_centroid = librosa.feature.spectral_centroid(audio)
   - spectrum_mean

4. Speech Rate:
   - zcr = librosa.feature.zero_crossing_rate(audio)
   - speech_rate

# Vector de características: [pitch_mean, pitch_std, energy, spectrum, rate, range]
```

### Clustering de Hablantes (`_cluster_speakers`)
```python
# Algoritmo K-Means con k=2:
1. Normalización con StandardScaler
2. KMeans(n_clusters=2, random_state=42)
3. Asignación: cluster 0 = paciente, cluster 1 = promotor
4. Fallback: clustering por pitch mediano si no hay scikit-learn

# Características distintivas típicas:
- Promotor: Pitch más estable, energía constante, vocabulario técnico
- Paciente: Pitch variable, pausas frecuentes, lenguaje coloquial
```

## Análisis Semántico de Contenido

### Patrones de Habla del Promotor
```python
_promotor_patterns = [
    r"buenos días|buenas tardes|hola",           # Saludos profesionales
    r"¿cómo se siente|¿cómo está|¿qué le pasa", # Preguntas médicas
    r"vamos a revisar|le voy a|necesito que",    # Direcciones médicas
    r"¿desde cuándo|¿cuánto tiempo|¿con qué frecuencia", # Anamnesis
    r"voy a recetarle|le recomiendo|debe tomar", # Prescripciones
    r"¿tiene alguna alergia|¿toma algún medicamento", # Historia médica
    r"doctor|doctora|médico|enfermero|enfermera" # Identificación profesional
]
```

### Patrones de Habla del Paciente
```python
_paciente_patterns = [
    r"me duele|me siento|tengo dolor",          # Expresión de síntomas
    r"desde hace|hace como|hace unos",          # Referencias temporales
    r"no puedo|no me deja|me impide",          # Limitaciones funcionales
    r"sí doctor|no doctor|gracias doctor",     # Respuestas a autoridad
    r"tomo|estoy tomando|me tomo",             # Medicación actual
    r"mi familia|mi trabajo|en casa"           # Contexto personal
]
```

### Análisis de Contenido (`_analyze_text_content`)
```python
# Scoring system:
texto → normalización → búsqueda_patrones → conteo_keywords → score

# Cálculo de score (-1.0 a +1.0):
- Promotor patterns: +1 punto cada uno
- Paciente patterns: +1 punto cada uno  
- Medical keywords: +0.5 promotor
- Personal keywords: +0.5 paciente
- Score final: (promotor_score - paciente_score) / total_score
```

## Clasificación Híbrida

### Método Avanzado (`_classify_speaker_hybrid`)
```python
# Combinación de evidencia:
audio_weight = 0.3    # Peso características de audio
text_weight = 0.7     # Peso análisis de texto

# Proceso:
1. audio_cluster (0 o 1) → audio_score (-1 o +1)
2. text_analysis → text_score (-1 a +1)
3. combined_score = (audio_weight * audio_score) + (text_weight * text_score)

# Clasificación:
if combined_score > 0.2:   → PROMOTOR
elif combined_score < -0.2: → PACIENTE  
else:                      → UNKNOWN

# Boost de confianza para patrones muy claros:
- Patrones médicos claros: +0.2 confianza
- Respuestas típicas de paciente: +0.2 confianza
```

### Método Fallback (`_classify_speaker_by_text`)
```python
# Solo análisis de texto cuando no hay audio:
text_score = _analyze_text_content(text)

if text_score > 0.3:    → PROMOTOR (confianza 0.5-0.8)
elif text_score < -0.3: → PACIENTE (confianza 0.5-0.8)
else:                   → UNKNOWN (confianza 0.3)
```

## Segmentación de Transcripciones

### Segmentación Inteligente (`_segment_transcription`)
```python
# Patrones de cambio de hablante:
split_patterns = [
    r'\?\s+[A-ZÁÉÍÓÚ]',                    # Pregunta + mayúscula
    r'\.\s+[A-ZÁÉÍÓÚ][a-z]+\s+(días?|tardes?)', # Saludos
    r'\.\s+[A-ZÁÉÍÓÚ][a-z]+\s+(doctor|doctora)', # Dirigirse al doctor
    r'\.\s+[A-ZÁÉÍÓÚ][a-z]+\s+(me|mi|yo)',       # Primera persona
    r'\.\s+[A-ZÁÉÍÓÚ][a-z]+\s+(le voy|vamos)'    # Acciones médicas
]

# Fallback:
Si no hay divisiones claras → división por oraciones largas (>200 chars)
```

### Estimación Temporal
```python
# Para texto sin timestamps de Whisper:
duración_estimada = palabra_count * 0.6  # ~0.6 segundos por palabra
segmentos_consecutivos = suma_acumulativa de duraciones
```

## Estadísticas de Participación

### Cálculo de Stats (`_calculate_speaker_stats`)
```python
# Métricas calculadas:
class SpeakerStats:
    total_speakers: int                    # Hablantes únicos detectados
    promotor_time: float                   # Tiempo total del promotor
    paciente_time: float                   # Tiempo total del paciente  
    unknown_time: float                    # Tiempo no clasificado
    overlap_time: float                    # Tiempo de solapamiento (futuro)
    total_duration: float                  # Duración total de conversación
    speaker_changes: int                   # Número de cambios de hablante
    average_segment_length: float          # Duración promedio de segmentos

# Análisis de patrones:
- Dominancia de conversación
- Frecuencia de interrupciones
- Participación balanceada vs. desequilibrada
```

## API Endpoints Asociados

### Procesamiento Automático
**Integración en `/upload-audio`:**
```python
# Flujo automático tras transcripción:
1. Whisper genera transcripción + segmentos
2. SpeakerService procesa diarización
3. Resultados se almacenan en AudioTranscription
4. Vector store incluye información de hablantes
```

### Consulta de Resultados
**En `/transcriptions/{id}`:**
```json
{
    "diarization_result": {
        "speaker_segments": [
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
        ],
        "speaker_stats": {
            "total_speakers": 2,
            "promotor_time": 45.3,
            "paciente_time": 38.7,
            "speaker_changes": 12,
            "total_duration": 84.0
        }
    }
}
```

## Características Técnicas

### Validación de Resultados
```python
# Validaciones en schemas:
1. end_time > start_time para cada segmento
2. Segmentos ordenados cronológicamente  
3. Speakers válidos (enum SpeakerType)
4. Confianzas en rango 0.0-1.0
5. Consistencia en duración total
```

### Manejo de Casos Edge
```python
# Situaciones especiales:
- Audio muy corto (<1 segundo): Un segmento UNKNOWN
- Solo un hablante detectado: Clasificación por contenido
- Múltiples hablantes simultáneos: Marcado como MULTIPLE
- Silencio prolongado: Segmentación por pausas naturales
```

### Performance y Optimización
```python
# Optimizaciones implementadas:
- Lazy loading de modelos ML
- Processing asíncrono con thread pools
- Cache de características de audio computadas
- Fallback graceful sin dependencias de audio
```

## Error Handling y Robustez

### Estrategias de Fallback
```python
# Niveles de degradación:
1. Full Hybrid: Audio features + Text analysis
2. Audio Only: Solo clustering de características de audio  
3. Text Only: Solo patrones semánticos
4. Basic: Un segmento completo marcado como UNKNOWN

# Manejo de errores:
- SpeakerDiarizationError para errores del servicio
- Audio loading failures → fallback a texto
- Clustering failures → clasificación por patrones
- Memory issues → procesamiento en chunks
```

## Integración con Otros Servicios

### Whisper Service Integration
```python
# Datos recibidos de Whisper:
- Transcripción completa
- Segmentos con timestamps precisos
- Word-level timestamps (cuando disponible)
- Confianza por segmento

# Uso en diarización:
- Segmentos como unidades básicas de análisis
- Timestamps para características temporales
- Confidence para weighting de evidencia
```

### Vector Store Enhancement
```python
# Metadata enriquecida con información de hablantes:
{
    "speaker_distribution": "60% promotor, 40% paciente",
    "primary_speaker": "promotor",
    "interaction_type": "consulta_estructurada",
    "conversation_balance": "equilibrada"
}

# Búsquedas especializadas:
- Consultas solo de respuestas de pacientes
- Información solo de preguntas médicas
- Análisis de patrones de comunicación
```

## Casos de Uso Específicos

### Análisis de Calidad de Consulta
```python
# Métricas derivadas:
- Tiempo de escucha vs. tiempo de habla del promotor
- Frecuencia de interrupciones
- Participación del paciente en la conversación
- Calidad de la anamnesis (número de preguntas)
```

### Compliance y Auditoría
```python
# Validación de buenas prácticas:
- ¿Se presentó el profesional médico?
- ¿Se realizaron preguntas sobre alergias?
- ¿Se explicó el tratamiento claramente?
- ¿Se dio espacio para preguntas del paciente?
```

### Reportes Gerenciales
```python
# Estadísticas agregadas:
- Duración promedio de consultas por tipo
- Participación promedio de pacientes
- Patrones de comunicación efectiva
- Identificación de mejores prácticas
```

## Configuración de Producción

### Hardware Requirements
```python
# Para análisis avanzado:
- CPU: Multi-core para features de audio
- RAM: 4GB+ para modelos ML en memoria
- Storage: Temporal para archivos de audio

# Para análisis básico:
- Cualquier CPU moderna
- RAM: 1GB suficiente
- Solo procesamiento de texto
```

### Tuning de Parámetros
```python
# Optimización por contexto:
SPEAKER_CONFIDENCE_THRESHOLD = 0.7    # Balance precisión/recall
SPEAKER_MIN_SEGMENT_LENGTH = 1.0      # Evitar segmentos muy cortos
Audio/Text weight ratio: 30/70        # Más peso a análisis semántico
```

## Mejores Prácticas

### Calidad de Audio
```python
# Para mejores resultados:
1. Audio con poca reverberación
2. Micrófonos separados si es posible
3. Ambiente silencioso
4. Calidad de grabación ≥16kHz
5. Formato sin compresión (WAV preferido)
```

### Contexto Médico
```python
# Optimización para conversaciones médicas:
1. Patrones específicos del dominio médico
2. Terminología actualizada regularmente  
3. Adaptación a diferentes especialidades
4. Consideración de contextos culturales locales
```
