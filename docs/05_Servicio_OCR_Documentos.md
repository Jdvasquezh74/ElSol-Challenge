# Servicio OCR y Procesamiento de Documentos - ElSol Challenge

## Descripción General
El OCRService maneja el procesamiento completo de documentos médicos (PDFs e imágenes) extrayendo texto mediante PyPDF2 y Tesseract OCR, seguido de extracción de metadata médica usando IA. Este servicio expande las capacidades del sistema para incluir documentos escritos además de conversaciones de audio.

## Clases Principales

### `OCRService`
Clase principal que gestiona todo el procesamiento de documentos médicos.

**Responsabilidades:**
- Detección automática de tipo de archivo (PDF vs imagen)
- Extracción de texto de PDFs usando PyPDF2
- OCR de imágenes usando Tesseract
- Limpieza y normalización de texto extraído
- Extracción de metadata médica usando OpenAI
- Validación de archivos y configuración de calidad
- Integración con vector store para búsqueda

**Atributos principales:**
```python
- openai_service: OpenAIService      # Para extracción de metadata
- tesseract_config: str             # Configuración OCR
- supported_formats: List[str]       # Formatos soportados
```

**Métodos principales:**
- `process_document()`: Procesamiento completo de documento
- `detect_file_type()`: Detección automática de formato
- `validate_file()`: Validación previa al procesamiento
- `_extract_medical_metadata()`: Extracción de información médica

## Arquitectura de Procesamiento

### Pipeline Completo
```python
# Flujo de procesamiento:
archivo → validación → detección_tipo → extracción_texto → limpieza → metadata_médica → almacenamiento

# Por tipo de archivo:
PDF: PyPDF2 → text extraction → cleaning
IMG: Tesseract OCR → confidence analysis → text cleaning
```

### Detección de Tipo de Archivo (`detect_file_type`)
```python
# Métodos de detección:
1. MIME type analysis (mimetypes.guess_type)
2. File extension validation (.pdf, .jpg, .png, .tiff, .tif)
3. Magic number verification (file headers)

# Tipos soportados:
- "pdf": application/pdf, .pdf
- "image": image/*, .jpg, .jpeg, .png, .tiff, .tif
```

## Integración con Core y Database

### Configuración (`app.core.config`)
```python
# Configuración de documentos:
DOCUMENT_UPLOAD_DIR: str = "./temp_documents"
DOCUMENT_MAX_SIZE_MB: int = 10
DOCUMENT_ALLOWED_EXTENSIONS: str = "pdf,jpg,jpeg,png,tiff,tif"

# Configuración OCR:
OCR_LANGUAGE: str = "spa"            # Español para Tesseract
OCR_MIN_CONFIDENCE: int = 60         # Confianza mínima (0-100)
PDF_MAX_PAGES: int = 50              # Límite de páginas PDF
```

### Schemas (`app.core.schemas`)
**Input Schemas:**
- `DocumentUpload`: Metadata opcional del documento
- Archivo físico cargado

**Output Schemas:**
- `OCRResult`: Resultado de extracción de texto
- `DocumentMetadata`: Metadata médica extraída
- `DocumentResponse`: Respuesta completa de procesamiento

### Database Models (`app.database.models`)
Modelo `Document` completo:
```python
# Información del archivo:
id: str                              # ID único
filename: str                        # Nombre procesado
original_filename: str               # Nombre original
file_type: str                       # "pdf" o "image"
file_size_bytes: int                 # Tamaño en bytes
file_path: str                       # Ruta de almacenamiento

# Estado de procesamiento:
status: str                          # "pending", "processing", "completed", "failed"
processed_at: datetime               # Timestamp de procesamiento
error_message: str                   # Error si falló

# Resultados OCR:
extracted_text: str                  # Texto extraído
ocr_confidence: float                # Confianza OCR (solo imágenes)
page_count: int                      # Número de páginas
language_detected: str               # Idioma detectado
processing_time_ms: int              # Tiempo de procesamiento

# Metadata médica extraída:
patient_name: str                    # Nombre del paciente
document_date: str                   # Fecha del documento
document_type: str                   # Tipo de documento médico
medical_conditions: str              # JSON array de condiciones
medications: str                     # JSON array de medicamentos
medical_procedures: str              # JSON array de procedimientos

# Vector store integration:
vector_stored: str                   # "true", "false", "failed"
vector_id: str                       # ID en ChromaDB

# Relación opcional:
conversation_id: str                 # Link a conversación relacionada
```

## Librerías Utilizadas

### PDF Processing
```python
import PyPDF2                        # Extracción de texto de PDFs
from pathlib import Path             # Manipulación de rutas
import mimetypes                     # Detección de MIME types
```

### Image OCR
```python
import pytesseract                   # Tesseract OCR engine
from PIL import Image                # Python Imaging Library
import numpy as np                   # Operaciones numéricas
```

### Text Processing
```python
import re                            # Expresiones regulares
import json                          # Parsing de metadata
from typing import Dict, Any, Optional, Tuple, List
```

## Procesamiento de PDFs

### Extracción con PyPDF2 (`_process_pdf`)
```python
# Características:
- Soporte para PDFs multipágina
- Límite configurable de páginas (PDF_MAX_PAGES)
- Extracción página por página con manejo de errores
- Marcado de páginas en texto extraído
- Cálculo heurístico de confianza basado en cantidad de texto

# Formato de salida:
"""
--- Página 1 ---
Texto de la primera página...

--- Página 2 ---
Texto de la segunda página...
"""
```

### Limitaciones y Consideraciones
```python
# Limitaciones de PyPDF2:
- PDFs con imágenes embebidas: No extrae texto de imágenes
- PDFs escaneados: Solo funciona con texto seleccionable
- PDFs protegidos: Limitaciones de acceso
- Formateo complejo: Puede perder estructura

# Soluciones:
- Combinación con OCR para PDFs escaneados (futura implementación)
- Validación de texto extraído
- Fallback a procesamiento manual
```

## Procesamiento de Imágenes

### OCR con Tesseract (`_process_image`)
```python
# Configuración OCR:
custom_config = f'--oem 3 --psm 6 -l {settings.OCR_LANGUAGE}'
# --oem 3: LSTM OCR Engine Mode
# --psm 6: Assume uniform block of text
# -l spa: Language Spanish

# Análisis de confianza:
1. Extracción con image_to_string()
2. Análisis de confianza con image_to_data()
3. Cálculo de confianza promedio por palabra
4. Validación contra OCR_MIN_CONFIDENCE
```

### Optimizaciones de Imagen
```python
# Preprocesamiento (futuras mejoras):
- Redimensionamiento para optimal OCR
- Corrección de contraste y brillo
- Detección y corrección de rotación
- Eliminación de ruido y artefactos
```

## Extracción de Metadata Médica

### Prompt Especializado (`_extract_medical_metadata`)
```python
MEDICAL_METADATA_PROMPT = """
Analiza este documento médico en español y extrae la siguiente información:

DOCUMENTO:
{text[:4000]}

INSTRUCCIONES:
Extrae ÚNICAMENTE la información que esté explícitamente mencionada en el documento.
Si algún campo no está presente, usa null.

FORMATO DE RESPUESTA (JSON):
{
    "patient_name": "nombre del paciente si se menciona",
    "document_date": "fecha del documento en formato YYYY-MM-DD si se encuentra",
    "document_type": "tipo de documento (examen, receta, consulta, etc.)",
    "medical_conditions": ["lista", "de", "condiciones", "médicas", "encontradas"],
    "medications": ["lista", "de", "medicamentos", "mencionados"],
    "medical_procedures": ["lista", "de", "procedimientos", "o", "exámenes", "realizados"]
}

Responde ÚNICAMENTE con el JSON válido, sin explicaciones adicionales.
"""
```

### Validación de Metadata
```python
# Validaciones aplicadas:
1. JSON parsing validation
2. Estructura de campos requerida
3. Tipos de datos correctos
4. Rangos válidos para fechas
5. Fallback a metadata vacía si falla parsing
```

## API Endpoints Asociados

### `/documents/upload` (POST)
**Request:**
```python
# Multipart form data:
- file: archivo PDF o imagen
- patient_name: string (opcional)
- document_type: string (opcional) 
- description: string (opcional)
```

**Response:**
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

### `/documents/{document_id}` (GET)
**Response completa:**
```json
{
    "document_id": "doc_123456",
    "filename": "examen_juan_perez.pdf",
    "status": "completed",
    "ocr_result": {
        "text": "Texto extraído completo...",
        "confidence": 0.87,
        "page_count": 3,
        "processing_time_ms": 2500,
        "language_detected": "spa"
    },
    "extracted_metadata": {
        "patient_name": "Juan Pérez",
        "document_date": "2024-01-10",
        "document_type": "examen de sangre",
        "medical_conditions": ["diabetes tipo 2"],
        "medications": ["metformina", "insulina"],
        "medical_procedures": ["análisis de glucosa"]
    },
    "vector_stored": true,
    "patient_association": "Juan Pérez"
}
```

### `/documents/search` (POST)
Búsqueda en documentos usando vector store:
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

## Validación y Error Handling

### Validación de Archivos (`validate_file`)
```python
# Validaciones realizadas:
1. Archivo existe y es accesible
2. Tamaño dentro de límites (DOCUMENT_MAX_SIZE_MB)
3. Archivo no vacío (> 0 bytes)
4. Tipo de archivo soportado
5. Headers válidos (magic numbers)

# Respuesta:
(is_valid: bool, error_message: str)
```

### Manejo de Errores
```python
- OCRServiceError: Errores específicos del servicio
- Dependency validation: PyPDF2 y pytesseract disponibles
- File format errors: Archivos corruptos o no soportados
- Processing timeouts: Límites de tiempo por documento
- Memory errors: Documentos muy grandes
```

### Dependencias Opcionales
```python
# Graceful degradation:
if not PyPDF2:
    # Solo procesamiento de imágenes
    missing_deps.append("PyPDF2")

if not pytesseract or not Image:
    # Solo procesamiento de PDFs
    missing_deps.append("pytesseract/Pillow")
```

## Integración con Vector Store

### Almacenamiento Automático
```python
# Flujo tras extracción exitosa:
1. Documento procesado → texto extraído
2. Metadata médica extraída
3. Preparación para vector store:
   - Texto combinado: extracted_text + metadata
   - Metadata rica: patient_name, document_type, etc.
4. Almacenamiento en ChromaDB
5. Actualización de document.vector_stored = "true"
```

### Búsqueda Integrada
```python
# El ChatService puede buscar en documentos:
- Búsqueda semántica en texto de documentos
- Filtrado por patient_name, document_type, fecha
- Combinación con transcripciones de audio
- Contexto unificado para respuestas RAG
```

## Configuración de Producción

### Hardware Requirements
```python
# Para OCR de imágenes:
- CPU: Multi-core recomendado
- RAM: 4GB+ para documentos grandes
- Storage: SSD para I/O rápido

# Para Tesseract:
- Tesseract 4.0+ instalado
- Language packs: spa, eng
- Fonts: Fuentes españolas para mejor reconocimiento
```

### Tesseract Configuration
```bash
# Instalación en producción:
apt-get install tesseract-ocr tesseract-ocr-spa
pip install pytesseract Pillow

# Verificación:
tesseract --version
tesseract --list-langs
```

### Monitoreo y Métricas
```python
# Métricas importantes:
- Processing time por tipo de documento
- OCR confidence distribution
- Success/failure rates
- Storage usage
- Queue length para procesamiento asíncrono
```

## Casos de Uso Específicos

### Expedientes Médicos
```python
# Documentos típicos:
- Historias clínicas en PDF
- Resultados de laboratorio
- Recetas médicas escaneadas
- Informes de especialistas
- Imágenes de radiografías con texto

# Información extraída:
- Datos del paciente
- Fechas de estudios
- Resultados numéricos
- Diagnósticos y recomendaciones
```

### Integración con Chat
```python
# Consultas combinadas:
"Muéstrame todos los exámenes de Juan Pérez"
→ Búsqueda en documentos + transcripciones

"¿Qué medicamentos aparecen en la receta de María?"
→ Búsqueda específica en documentos tipo "receta"
```

## Mejores Prácticas

### Calidad de OCR
```python
# Para mejores resultados:
1. Imágenes de alta resolución (300+ DPI)
2. Contraste adecuado entre texto y fondo
3. Texto horizontal (sin rotación)
4. Formato original mejor que escaneado
5. Idioma consistente (español)
```

### Gestión de Archivos
```python
# Organización recomendada:
temp_documents/
├── pending/           # Archivos por procesar
├── processing/        # En procesamiento
├── completed/         # Procesados exitosamente
└── failed/           # Errores de procesamiento

# Limpieza automática:
- Archivos temporales después de procesamiento
- Logs de error con rotación
- Cache de resultados OCR
```

### Performance Optimization
```python
# Optimizaciones:
1. Procesamiento asíncrono para archivos grandes
2. Cache de resultados OCR frecuentes
3. Batch processing para múltiples documentos
4. Compresión de texto extraído para storage
5. Índices de búsqueda por metadata
```
