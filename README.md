# Sprint 2 - 6. Cliente React Simple (funcionalidad PLUS)
---

## 📱 Descripción del Frontend

Interfaz web React moderna y profesional para interactuar con todas las funcionalidades del sistema ElSol Medical AI. Proporciona una experiencia de usuario intuitiva para subir archivos, consultar el chatbot RAG y visualizar transcripciones con diferenciación de hablantes.

## 🎯 Decisiones Técnicas del Frontend

### **Stack Tecnológico Elegido**
- **React 19** con **TypeScript**: Type safety y componentes modernos
- **Vite**: Build tool ultrarrápido para desarrollo
- **Tailwind CSS**: Styling utility-first para UI consistente
- **React Query**: Gestión de estado del servidor optimizada
- **React Dropzone**: Upload de archivos intuitivo
- **React Hot Toast**: Notificaciones elegantes
- **React Error Boundary**: Manejo robusto de errores

### **¿Por qué esta Stack?**
- **Performance**: Vite + React 19 ofrecen desarrollo ultrarrápido
- **Type Safety**: TypeScript elimina bugs en tiempo de compilación
- **UI Profesional**: Tailwind + Heroicons crean interfaz médica consistente
- **UX Optimizada**: React Query maneja cache y sincronización automáticamente
- **Escalabilidad**: Arquitectura modular con hooks personalizados

---

## 🖥️ Endpoints Frontend que Consume

### **Vista Audio Upload**
- `POST /api/v1/upload-audio` - Subida archivos WAV/MP3
- `GET /api/v1/transcriptions` - Lista transcripciones
- `GET /api/v1/transcriptions/{id}` - Detalle transcripción

**Dónde se muestra la información:**
- **Upload Area**: Drag & drop con progress tracking
- **Progress Cards**: Estado en tiempo real (uploading → transcribing → completed)
- **Preview Cards**: Estadísticas de speakers + información extraída
- **Lista Principal**: Grid de transcripciones con filtros

### **Vista Document Upload**
- `POST /api/v1/upload-document` - Subida PDFs/imágenes
- `GET /api/v1/documents` - Lista documentos
- `GET /api/v1/documents/search` - Búsqueda en documentos

**Dónde se muestra la información:**
- **Metadata Form**: Campos para paciente/tipo/descripción
- **Upload Area**: Drag & drop específico para documentos
- **OCR Preview**: Texto extraído con confianza
- **Metadata Cards**: Información médica estructurada (condiciones, medicamentos)

### **Vista Conversaciones**
- `GET /api/v1/transcriptions` - Lista con filtros avanzados
- `GET /api/v1/transcriptions/{id}` - Detalle conversación completa

**Dónde se muestra la información:**
- **Lista Filtrable**: Cards con información resumida
- **Detalle Completo**: Timeline con speakers diferenciados
- **Análisis**: Información estructurada y no estructurada
- **Estadísticas**: Tiempo por hablante, cambios de speaker

### **Chat RAG Interface**
- `POST /api/v1/chat` - Consultas inteligentes
- `GET /api/v1/chat/examples` - Ejemplos de consultas
- `POST /api/v1/chat/quick` - Chat rápido

**Dónde se muestra la información:**
- **Chat Flotante**: Interface fija en esquina inferior derecha
- **Respuestas Contextuales**: Con fuentes y relevancia
- **Sugerencias**: Queries ejemplo basadas en contenido
- **Fuentes**: Referencias a conversaciones y documentos

### **Vector Store Status**
- `GET /api/v1/vector-store/status` - Estado del sistema
- `GET /health` - Health check general

**Dónde se muestra la información:**
- **Header**: Indicador de estado del sistema
- **Footer**: Información de conectividad

---

## 🧪 Cómo Testear la Funcionalidad

### **Instalación y Setup**
```bash
# 1. Navegar al directorio frontend
cd frontend

# 2. Instalar dependencias
npm install

# 3. Configurar variables de entorno (opcional)
# crear archivo .env con:
# VITE_API_URL=http://localhost:8000

# 4. Iniciar servidor de desarrollo
npm run dev
```

### **Scripts Disponibles**
```bash
npm run dev          # Servidor desarrollo (puerto 3000)
npm run build        # Build producción
npm run preview      # Preview del build
npm run type-check   # Verificación TypeScript
npm run lint         # ESLint
```

### **Pruebas de Funcionalidad**

#### **1. Upload de Audio**
- Acceder a http://localhost:3000
- Arrastrar archivo WAV/MP3 al área de upload
- Verificar progress bar y estados
- Confirmar preview con estadísticas de speakers
- Revisar información estructurada extraída

#### **2. Upload de Documentos**
- Cambiar a pestaña "Documentos"
- Completar metadata opcional
- Subir PDF o imagen médica
- Verificar OCR en tiempo real
- Confirmar extracción de información médica

#### **3. Lista de Conversaciones**
- Navegar a pestaña "Conversaciones"
- Usar filtros por estado/paciente/fecha
- Hacer clic en conversación para ver detalle
- Revisar timeline con speakers diferenciados
- Explorar análisis de información

#### **4. Chat RAG**
- Hacer clic en botón de chat (esquina inferior derecha)
- Probar consultas ejemplo:
  - "¿Qué síntomas reportó el paciente?"
  - "¿Qué documentos médicos tengo disponibles?"
  - "Listame pacientes con diabetes"
- Verificar respuestas con fuentes
- Probar sugerencias de seguimiento

#### **5. Responsive Design**
- Probar en móvil (< 640px)
- Verificar sidebar colapsable
- Confirmar chat interface adaptada
- Revisar upload areas responsivas

---

## 🤔 Supuestos Hechos

### **Arquitectura**
- **Backend ya operativo**: El frontend asume que todas las APIs del backend están funcionando
- **CORS configurado**: Se espera que el backend permita requests desde http://localhost:3000
- **Formato de respuestas**: Se asume que las APIs responden con los tipos definidos en `types/api.ts`

### **Datos**
- **IDs únicos**: Cada transcripción y documento tiene un ID único para tracking
- **Estados predefinidos**: `pending`, `processing`, `completed`, `failed` como estados posibles
- **Formatos de fecha**: ISO 8601 para timestamps desde el backend
- **Embeddings automáticos**: El backend maneja almacenamiento vectorial automáticamente

### **Usuario**
- **Conexión estable**: Se asume conexión a internet para APIs y CDNs
- **Navegadores modernos**: Compatible con Chrome/Firefox/Safari/Edge últimas versiones
- **JavaScript habilitado**: No hay fallback para usuarios sin JS
- **Archivos válidos**: El usuario selecciona archivos de los tipos permitidos

### **UX/UI**
- **Feedback inmediato**: Progress bars y toasts para todas las acciones
- **Estados de loading**: Skeletons y spinners durante cargas
- **Error recovery**: Boundaries para manejar crashes gracefully
- **Mobile-first**: Diseño responsive desde móvil hacia desktop

---

## ✅ Buenas Prácticas Aplicadas

### **Desarrollo**
- **TypeScript estricto**: Type safety completo para prevenir errores
- **Componentes modulares**: Separación clara de responsabilidades
- **Custom hooks**: Lógica reutilizable para upload, chat, y API
- **Error boundaries**: Manejo graceful de errores inesperados
- **Lazy loading**: Code splitting para componentes pesados

### **Performance**
- **React Query**: Cache inteligente y sincronización automática
- **Optimistic updates**: UI responsive sin esperar respuestas del servidor
- **Debounced search**: Evita requests excesivos durante búsquedas
- **Image optimization**: Lazy loading para previews de documentos
- **Bundle optimization**: Vite optimiza bundles automáticamente

### **UX/UI**
- **Design System**: Paleta médica consistente (azules + verdes)
- **Accessibility**: Labels, ARIA attributes, y navegación por teclado
- **Loading states**: Feedback visual durante todas las operaciones
- **Progressive disclosure**: Información detallada on-demand
- **Micro-interactions**: Hover states y transiciones suaves

### **Seguridad**
- **Input sanitization**: Validación de tipos de archivo y tamaños
- **HTTPS enforcement**: Configurado para producción
- **Error messages**: Sin exposición de información sensible del backend
- **CORS compliance**: Requests apropiados al backend

### **Código**
- **ESLint + Prettier**: Código consistente y sin errores
- **Import organization**: Imports agrupados y ordenados
- **Component composition**: Favor de composición sobre herencia
- **Memoization apropiada**: React.memo y useMemo donde corresponde
- **Clean components**: Single responsibility principle

### **Testing Ready**
- **Estructura testeable**: Componentes puros y lógica separada
- **Mock-friendly**: APIs abstraídas para fácil testing
- **Error scenarios**: Manejo explícito de casos de error
- **Type coverage**: 100% TypeScript para testing robusto

---

## 🚀 Instrucciones de Despliegue

### **Desarrollo**
```bash
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload

# Terminal 2: Frontend  
cd frontend
npm run dev
```

### **Producción**
```bash
# Build frontend
cd frontend
npm run build

# Servir archivos estáticos
# Los archivos están en ./dist/
# Usar nginx, vercel, netlify, etc.
```

### **Docker (Opcional)**
```dockerfile
# Dockerfile para frontend
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

---

# Sprint 1 - 1. Transcripción de audio (requisito mínimo)
---

## Descripción del Proyecto

Esta es la primera parte del primer sprint del proyecto **ElSol-Challenge**, enfocado en implementar la funcionalidad básica de **transcripción de audio**. El sistema permite subir archivos de audio (.wav, .mp3) y obtener tanto la transcripción completa como información estructurada extraída del contenido.

## Decisión Técnica: OpenAI Whisper API

###  **¿Por qué OpenAI Whisper?**
- **Alta precisión**: Excelente rendimiento en conversaciones médicas y técnicas
- **Soporte multiidioma**: Maneja español e inglés nativamente
- **API estable**: Servicio confiable con buena documentación
- **Simplicidad de integración**: SDK oficial de Python bien mantenido
- **Formato agnóstico**: Acepta múltiples formatos de audio sin conversión previa

### **Para Producción Recomendaría:**
**Azure Speech-to-Text** por:
- Mejor escalabilidad horizontal
- Costos más predecibles en volúmenes altos
- SLA empresarial más robusto
- Integración nativa con ecosistemas Microsoft

---

## Endpoints Disponibles

### **POST /upload-audio**
Subir y procesar archivo de audio para transcripción.

**Request:**
```bash
curl -X POST "http://localhost:8000/upload-audio" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@conversation.wav"
```

**Response:**
```json
{
  "id": "uuid-123",
  "filename": "conversation.wav",
  "status": "processing",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### **GET /transcriptions/{id}**
Obtener resultado de transcripción procesada.

**Request:**
```bash
curl -X GET "http://localhost:8000/transcriptions/uuid-123"
```

**Response:**
```json
{
  "id": "uuid-123",
  "status": "completed",
  "transcription": {
    "raw_text": "Paciente Juan Pérez, 45 años...",
    "structured_data": {
      "nombre": "Juan Pérez",
      "edad": 45,
      "fecha": "2024-01-15",
      "diagnostico": "Hipertensión arterial"
    },
    "unstructured_data": {
      "sintomas": ["dolor de cabeza", "mareos"],
      "contexto": "Consulta de seguimiento",
      "observaciones": "Paciente cooperativo"
    }
  },
  "processed_at": "2024-01-15T10:32:15Z"
}
```

### **GET /transcriptions**
Listar todas las transcripciones disponibles.

**Request:**
```bash
curl -X GET "http://localhost:8000/transcriptions?limit=10&offset=0"
```

### **GET /health**
Health check del servicio.

**Request:**
```bash
curl -X GET "http://localhost:8000/health"
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

---

## Cómo Testear la Funcionalidad

### 1. **Setup del Entorno**
```bash
# Clonar y navegar al proyecto
cd backend

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tu OPENAI_API_KEY

# Ejecutar la aplicación
uvicorn app.main:app --reload
```

### 2. **Pruebas Manuales**

**Subir un archivo de audio:**
```bash
# Preparar archivo de prueba
curl -X POST "http://localhost:8000/upload-audio" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_audio.wav"
```

**Verificar transcripción:**
```bash
# Usar el ID retornado en el paso anterior
curl -X GET "http://localhost:8000/transcriptions/{id}"
```

### 3. **Pruebas Automatizadas**
```bash
# Ejecutar test suite
cd backend
python -m pytest tests/ -v

# Coverage report
python -m pytest tests/ --cov=app --cov-report=html
```

### 4. **Archivos de Prueba Sugeridos**
- Audio médico: Conversación doctor-paciente de 2-3 minutos
- Formatos: `.wav` (preferido) y `.mp3`
- Duración: Entre 30 segundos y 10 minutos
- Calidad: Audio claro sin ruido excesivo

---

## Supuestos Hechos

### **Técnicos:**
- Archivos de audio ≤ 25MB (límite de Whisper API)
- Formatos soportados: `.wav`, `.mp3`
- Conversaciones principalmente en español/inglés
- Base de datos SQLite para desarrollo
- Almacenamiento temporal de archivos (no persistente)

### **De Negocio:**
- Conversaciones son del ámbito médico/clínico
- No se requiere autenticación en MVP
- Los datos extraídos siguen formato médico estándar
- Información sensible no se almacena permanentemente

### **De Infraestructura:**
- Servidor con acceso a internet (para API de OpenAI)
- Python 3.9+ disponible
- Espacio en disco para archivos temporales
- Rate limits de OpenAI respetados (50 requests/min)

---

## Buenas Prácticas Aplicadas

### **Arquitectura:**
-  **Separación de responsabilidades**: Services pattern para lógica de negocio
-  **Dependency Injection**: Configuración centralizada y testeable
-  **API-First Design**: Endpoints RESTful bien definidos
-  **Error Handling**: Manejo robusto de excepciones con códigos HTTP apropiados

### **Código:**
-  **Type Hints**: Tipado estático completo con Pydantic
-  **Async/Await**: Operaciones no bloqueantes para mejor performance
-  **Logging estructurado**: Trazabilidad completa de requests
-  **Validación de entrada**: Sanitización y validación de archivos

### **Seguridad:**
-  **Validación de archivos**: Verificación de tipo MIME y extensiones
-  **Rate limiting**: Protección contra abuse de API
-  **Environment variables**: Secrets no hardcodeados
-  **Temporary storage**: Limpieza automática de archivos

### **Testing:**
-  **Unit tests**: Cobertura >80% en servicios críticos
-  **Integration tests**: Verificación end-to-end de endpoints
-  **Mocking**: APIs externas simuladas para tests determinísticos
-  **Test fixtures**: Datos de prueba reutilizables

### **DevOps:**
-  **Docker ready**: Containerización preparada
-  **Health checks**: Monitoreo de servicio
-  **Configuration management**: Variables de entorno centralizadas
-  **Logging**: Structured logging para observabilidad

---

## Variables de Entorno Requeridas

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here

# Database
DATABASE_URL=sqlite:///./conversations.db

# Application
UPLOAD_MAX_SIZE=26214400  # 25MB in bytes
UPLOAD_ALLOWED_EXTENSIONS=wav,mp3
LOG_LEVEL=INFO

# Optional
DEBUG=False
API_V1_STR=/api/v1
```

---

## Próximos Pasos (Sprint 2)

1. **Diarización de speakers** - Identificar quién habla cuándo
2. **Base de datos vectorial** - Implementar Chroma para embeddings
3. **Sistema RAG** - Chat inteligente sobre conversaciones
4. **Frontend React** - Interfaz de usuario
5. **Containerización** - Docker Compose para orquestación

## 🧪 Cómo Testear la Transcripción de Audio

### **Setup del Entorno de Testing**

**Instalar dependencias de testing:**
```bash
pip install pytest pytest-asyncio pytest-cov
```

### **Tests Básicos del Servicio Whisper**

**Tests de validación de archivos:**
```bash
# Test validación de formatos válidos
python -m pytest tests/test_transcription_service.py::TestWhisperService::test_validate_audio_file_valid_formats -v

# Test validación de formatos inválidos 
python -m pytest tests/test_transcription_service.py::TestWhisperService::test_validate_audio_file_invalid_format -v

# Test validación de archivos vacíos
python -m pytest tests/test_transcription_service.py::TestWhisperService::test_validate_audio_file_empty -v
```

**Tests de transcripción:**
```bash
# Test transcripción exitosa (con mock)
python -m pytest tests/test_transcription_service.py::TestWhisperService::test_transcribe_audio_success -v

# Test manejo de errores de API
python -m pytest tests/test_transcription_service.py::TestWhisperService::test_transcribe_audio_api_error -v

# Test integración completa
python -m pytest tests/test_transcription_service.py::TestTranscriptionIntegration::test_full_transcription_workflow -v
```

**Tests de performance:**
```bash
# Test manejo de timeouts
python -m pytest tests/test_transcription_service.py::TestTranscriptionPerformance::test_transcription_timeout_handling -v

# Test validación concurrente
python -m pytest tests/test_transcription_service.py::TestTranscriptionPerformance::test_concurrent_validation -v
```

### **Suite Completa de Tests de Transcripción**

```bash
# Ejecutar todos los tests de transcripción
python -m pytest tests/test_transcription_service.py -v

# Tests con coverage detallado
python -m pytest tests/test_transcription_service.py --cov=app.services.whisper_service --cov-report=html

# Tests específicos de detección de formatos
python -m pytest tests/test_transcription_service.py::TestTranscriptionIntegration::test_audio_format_detection -v
```

## ✅ **Supuestos de Testing para Transcripción**

### **Técnicos:**
- **Mock de OpenAI API**: Tests usan mocks para evitar llamadas reales a la API
- **Archivos temporales**: Tests crean archivos temporales que se limpian automáticamente
- **Formatos soportados**: Tests validan .wav y .mp3 principalmente
- **Timeouts**: Tests verifican manejo de timeouts en transcripciones largas

### **De Validación:**
- **Tamaño de archivos**: Tests incluyen validación de archivos grandes (>25MB)
- **Formatos inválidos**: Tests verifican rechazo de .txt, .pdf, etc.
- **Archivos corruptos**: Tests manejan archivos con contenido inválido
- **Casos edge**: Tests cubren archivos vacíos y muy pequeños

### **De Performance:**
- **Concurrencia**: Tests verifican procesamiento de múltiples archivos
- **Timeout handling**: Tests validan manejo de transcripciones largas
- **Memory usage**: Tests monitorizan uso de memoria en archivos grandes
- **Error recovery**: Tests verifican recuperación graceful de errores

---

# Sprint 1 - 2. Almacenamiento Vectorial (requisito mínimo)

---

## Descripción del Almacenamiento Vectorial

Esta es la segunda parte del primer sprint del proyecto **ElSol-Challenge**, enfocado en implementar la funcionalidad de **almacenamiento vectorial**. El sistema almacena automáticamente cada conversación transcrita en una base de datos vectorial para permitir búsquedas semánticas futuras.

## Decisión Técnica: Chroma DB

###  **¿Por qué Chroma DB?**
- **Setup simple**: Sin dependencias externas complejas como Docker
- **Persistencia local**: Compatible con SQLite, ideal para MVP
- **Python nativo**: Integración directa sin APIs REST adicionales
- **Embeddings incluidos**: sentence-transformers integrado nativamente
- **Metadata filtering**: Búsquedas híbridas vector + metadata
- **Migración futura**: Path claro hacia Qdrant para producción

### **Para Producción Recomendaría:**
**Qdrant** por:
- Escalabilidad horizontal superior
- Performance optimizada para búsquedas complejas
- Clustering y replicación nativa
- API REST robusta para arquitecturas distribuidas

---

## Endpoints Disponibles

### **GET /api/v1/vector-store/status**
Obtener estado actual del vector store y estadísticas.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/vector-store/status"
```

**Response:**
```json
{
  "status": "operational",
  "collection_name": "medical_conversations",
  "total_documents": 15,
  "total_embeddings": 15,
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "persist_directory": "./chroma_db",
  "last_updated": "2024-01-15T10:30:00Z"
}
```

### **GET /api/v1/vector-store/conversations**
Listar conversaciones almacenadas en el vector store.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/vector-store/conversations?limit=10"
```

**Response:**
```json
[
  {
    "vector_id": "conv_uuid-123_abc12345",
    "conversation_id": "uuid-123",
    "patient_name": "Juan Pérez",
    "stored_at": "2024-01-15T10:30:00Z",
    "text_preview": "Paciente Juan Pérez de 45 años presenta dolor de cabeza...",
    "metadata": {
      "diagnosis": "Cefalea",
      "urgency": "media",
      "symptoms": "dolor de cabeza, mareos"
    }
  }
]
```

### **GET /api/v1/vector-store/conversations/{id}**
Obtener conversación específica almacenada en vector store.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/vector-store/conversations/uuid-123"
```

**Response:**
```json
{
  "vector_id": "conv_uuid-123_abc12345",
  "conversation_id": "uuid-123",
  "patient_name": "Juan Pérez",
  "stored_at": "2024-01-15T10:30:00Z",
  "text_preview": "Conversación médica completa con Juan Pérez...",
  "metadata": {
    "diagnosis": "Cefalea",
    "urgency": "media",
    "symptoms": "dolor de cabeza, mareos",
    "patient_age": "45",
    "filename": "conversation_20240115.wav"
  }
}
```

### **GET /api/v1/vector-store/health**
Health check específico del vector store.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/vector-store/health"
```

**Response:**
```json
{
  "service": "vector_store",
  "status": "operational",
  "chroma_accessible": true,
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "total_documents": 15,
  "collection_name": "medical_conversations"
}
```

---

## Cómo Testear la Funcionalidad

### 1. **Setup del Entorno**
```bash
# Navegar al proyecto
cd backend

# Instalar nuevas dependencias vectoriales
pip install -r requirements.txt

# Ejecutar la aplicación
uvicorn app.main:app --reload
```

### 2. **Pruebas Manuales del Flujo Completo**

**Paso 1: Subir audio (debe almacenar en vector store automáticamente)**
```bash
curl -X POST "http://localhost:8000/api/v1/upload-audio" -F "file=@test_audio.wav"

# Response incluirá el ID de transcripción
# {"id": "uuid-123", "status": "processing", ...}
```

**Paso 2: Verificar que se almacenó en vector store**
```bash
# Verificar estado general
curl -X GET "http://localhost:8000/api/v1/vector-store/status"

# Listar conversaciones almacenadas
curl -X GET "http://localhost:8000/api/v1/vector-store/conversations"

# Obtener conversación específica
curl -X GET "http://localhost:8000/api/v1/vector-store/conversations/uuid-123"
```

**Paso 3: Verificar en base de datos SQLite**
```bash
sqlite3 conversations.db
.tables
SELECT id, filename, vector_stored, vector_id FROM audio_transcriptions;
```

### 3. **Pruebas Automatizadas**
```bash
# Ejecutar tests del vector store
python -m pytest tests/test_vector_service.py -v

# Tests de integración
python -m pytest tests/test_vector_integration.py -v
```

### 4. **Archivos de Prueba Sugeridos**
- Audio médico con información estructurada clara
- Conversaciones de 2-5 minutos de duración
- Formato `.wav` preferido para mejor calidad de transcripción
- Audio con nombres de pacientes y diagnósticos explícitos

---

## Supuestos Hechos

### **Técnicos:**
- Modelo de embeddings: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensiones)
- Almacenamiento local en `./chroma_db` para MVP
- Persistencia SQLite para metadatos de Chroma
- Máximo 8000 caracteres por texto para embedding
- Chunking automático para transcripciones largas

### **De Almacenamiento:**
- Una colección única: "medical_conversations"
- Metadata rica incluye: paciente, diagnóstico, síntomas, urgencia
- Vector IDs formato: `conv_{conversation_id}_{random_hash}`
- Backup automático a través de persistencia de Chroma
- No elimina embeddings antiguos (solo crecimiento)

### **De Integración:**
- Vector store se ejecuta **después** de transcripción exitosa
- Fallo en vector store **no falla** el proceso de transcripción
- Campo `vector_stored` en SQLite: "true", "false", "failed"
- Vector store es **no crítico** para funcionalidad básica

### **De Performance:**
- Embedding generation: <2 segundos por conversación
- Almacenamiento: <1 segundo por documento
- Máximo 1000 conversaciones recomendadas para MVP local
- Búsquedas: preparación para <3 segundos en el futuro (Requisito 3)

---

## Buenas Prácticas Aplicadas

### **Arquitectura Vectorial:**
-  **Separación de responsabilidades**: Vector store como servicio independiente
-  **Fault tolerance**: Fallo vectorial no afecta transcripción principal
-  **Metadata rica**: Información estructurada + no estructurada combinada
-  **Preparación para RAG**: Embeddings optimizados para búsqueda semántica

### **Gestión de Embeddings:**
-  **Modelo optimizado**: sentence-transformers para español médico
-  **Texto combinado**: Transcripción + datos estructurados + síntomas
-  **Dimensiones eficientes**: 384d balance entre calidad y performance
-  **Chunking inteligente**: Límite 8000 caracteres con truncado seguro

### **Persistencia y Reliability:**
-  **Persistencia local**: Chroma DB con SQLite backend
-  **Trazabilidad**: Vector ID almacenado en transcripción original
-  **Estado tracking**: vector_stored field para monitoreo
-  **Graceful degradation**: Sistema funciona sin vector store

### **Testing Comprehensivo:**
-  **Unit tests**: Servicios vectoriales aislados con mocks
-  **Integration tests**: Flujo completo upload → vector store
-  **Error handling**: Cobertura de fallos de Chroma y embeddings
-  **Performance tests**: Validación de tiempos de respuesta

### **Observabilidad:**
-  **Logging estructurado**: Todos los eventos vectoriales loggeados
-  **Health checks**: Endpoint específico para vector store
-  **Métricas**: Conteo de documentos, estado de colección
-  **Error tracking**: Fallos vectoriales no críticos loggeados

---

## Variables de Entorno para Vector Store

```env
# Vector Store Configuration (Requisito 2)
CHROMA_PERSIST_DIRECTORY=./chroma_db
CHROMA_COLLECTION_NAME=medical_conversations
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
VECTOR_EMBEDDING_DIMENSIONS=384
```

---

## Flujo de Datos Actualizado

```
1. Upload Audio → Whisper Transcription → OpenAI Extraction
                                               ↓
2. Store in SQLite ← Vector Storage ← Embedding Generation
                                               ↓
3. Chroma DB Storage ← Metadata Preparation ← Text Combination
                                               ↓
4. Response with vector_id → Ready for RAG (Requisito 3)
```

---

## Próximos Pasos (Requisito 3)

Con el almacenamiento vectorial implementado, el sistema está **listo para**:

1. **Sistema RAG** - Búsqueda semántica + generación de respuestas
2. **Endpoint /chat** - Consultas como "¿Qué enfermedad tiene Juan?"
3. **Context retrieval** - Recuperación de conversaciones relevantes
4. **Cross-patient search** - Búsquedas por síntomas o diagnósticos

El vector store actual proporciona la **base sólida** para todas estas funcionalidades avanzadas.

---

# Sprint 1 - 3. Chatbot vía API (requisito mínimo)

---

## Descripción del Chatbot vía API

Esta es la tercera y última parte del primer sprint del proyecto **ElSol-Challenge**, enfocado en implementar el **sistema de chat médico con RAG**. El sistema permite hacer consultas en lenguaje natural sobre las conversaciones médicas almacenadas, utilizando un pipeline completo de Retrieval-Augmented Generation.

## Decisión Técnica: RAG con Azure OpenAI GPT-4

###  **¿Por qué RAG (Retrieval-Augmented Generation)?**
- **Precisión médica**: Respuestas basadas únicamente en datos reales del sistema
- **No alucinaciones**: El modelo no inventa información médica
- **Contexto específico**: Búsqueda semántica en conversaciones almacenadas
- **Trazabilidad**: Cada respuesta incluye fuentes verificables
- **Escalabilidad**: Funciona con cualquier cantidad de conversaciones

###  **¿Por qué Azure OpenAI GPT-4?**
- **Comprensión médica avanzada**: Excelente manejo de terminología médica
- **Respuestas estructuradas**: Capacidad de generar respuestas organizadas
- **Integración existente**: Aprovecha la configuración ya implementada
- **Confiabilidad empresarial**: SLA y soporte de Microsoft Azure

---

## Endpoints Disponibles

### **POST /api/v1/chat**
Endpoint principal para consultas médicas en lenguaje natural.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿Qué enfermedad tiene Pepito Gómez?",
    "max_results": 5,
    "include_sources": true,
    "filters": {
      "patient_name": "Pepito Gómez"
    }
  }'
```

**Response:**
```json
{
  "answer": "Según las transcripciones médicas disponibles, Pepito Gómez presenta diabetes tipo 2. El diagnóstico fue confirmado en su consulta del 15 de enero de 2024. Se le recetó metformina para el control de la glucosa.",
  "sources": [
    {
      "conversation_id": "conv-pepito-1",
      "patient_name": "Pepito Gómez",
      "relevance_score": 0.95,
      "excerpt": "Paciente Pepito Gómez de 35 años presenta diabetes tipo 2...",
      "date": "2024-01-15",
      "metadata": {
        "diagnosis": "Diabetes tipo 2",
        "symptoms": "poliuria, polidipsia",
        "rank": 1
      }
    }
  ],
  "confidence": 0.87,
  "intent": "patient_info",
  "follow_up_suggestions": [
    "¿Qué tratamiento se recomendó para Pepito?",
    "¿Cuándo fue la última consulta de Pepito?",
    "¿Qué síntomas reportó Pepito?"
  ],
  "query_classification": {
    "entities": {
      "patients": ["Pepito Gómez"],
      "conditions": [],
      "symptoms": []
    },
    "search_terms": ["Pepito Gómez", "enfermedad"],
    "normalized_query": "que enfermedad tiene pepito gomez"
  },
  "processing_time_ms": 1250
}
```

### **POST /api/v1/chat/quick**
Versión simplificada para consultas rápidas.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/chat/quick" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Listame los pacientes con diabetes",
    "max_results": 3
  }'
```

**Response:**
```json
{
  "answer": "Pacientes con diabetes encontrados:\n1. Pepito Gómez - Diabetes tipo 2\n2. María García - Diabetes gestacional\n3. Carlos López - Diabetes tipo 1",
  "sources": [...],
  "confidence": 0.82,
  "intent": "condition_list",
  "follow_up_suggestions": [...]
}
```

### **GET /api/v1/chat/examples**
Obtener ejemplos de consultas que el sistema puede manejar.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/chat/examples"
```

**Response:**
```json
{
  "examples": {
    "patient_info": {
      "description": "Consultas sobre información específica de pacientes",
      "examples": [
        "¿Qué enfermedad tiene Pepito Gómez?",
        "¿Cuál es el diagnóstico de María García?",
        "Información del paciente Carlos López"
      ]
    },
    "condition_list": {
      "description": "Listas de pacientes por condición médica",
      "examples": [
        "Listame los pacientes con diabetes",
        "¿Quiénes tienen hipertensión?",
        "Pacientes con asma"
      ]
    }
  },
  "tips": [
    "Usa nombres específicos para mejores resultados",
    "Incluye términos médicos cuando sea posible"
  ]
}
```

### **POST /api/v1/chat/validate**
Validar consulta antes de procesarla.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/chat/validate" \
  -H "Content-Type: application/json" \
  -d '{"query": "¿Qué enfermedad tiene Juan?"}'
```

### **GET /api/v1/chat/stats**
Estadísticas de uso del sistema de chat.

### **GET /api/v1/chat/health**
Health check del sistema de chat.

---

## Cómo Testear la Funcionalidad

### 1. **Setup del Entorno**
```bash
# Asegurar que todos los servicios estén funcionando
cd backend

# Verificar que ChromaDB y vector store funcionan
curl -X GET "http://localhost:8000/api/v1/vector-store/status"

# Ejecutar la aplicación si no está corriendo
uvicorn app.main:app --reload
```

### 2. **Casos de Uso Obligatorios del Challenge**

**Caso 1: "¿Qué enfermedad tiene Pepito Gómez?"**
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿Qué enfermedad tiene Pepito Gómez?",
    "max_results": 5
  }'
```

**Caso 2: "Listame los pacientes con diabetes"**
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Listame los pacientes con diabetes",
    "max_results": 10
  }'
```

### 3. **Casos de Uso Adicionales**

**Búsqueda por síntomas:**
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿Quién tiene dolor de cabeza?",
    "max_results": 5
  }'
```

**Consultas temporales:**
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿Qué pacientes vinieron ayer?",
    "max_results": 5
  }'
```

**Información de medicamentos:**
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿Qué medicamentos toma Ana García?",
    "max_results": 3
  }'
```

### 4. **Flujo de Testing Completo**

**Paso 1: Subir audio médico**
```bash
curl -X POST "http://localhost:8000/api/v1/upload-audio" \
  -F "file=@conversation_pepito_gomez.wav"
```

**Paso 2: Verificar almacenamiento en vector store**
```bash
curl -X GET "http://localhost:8000/api/v1/vector-store/conversations"
```

**Paso 3: Realizar consulta de chat**
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "¿Qué enfermedad tiene Pepito Gómez?"}'
```

### 5. **Pruebas Automatizadas**
```bash
# Ejecutar tests del sistema de chat
python -m pytest tests/test_chat_service.py -v

# Tests de endpoints
python -m pytest tests/test_chat_endpoints.py -v

# Tests de integración completa
python -m pytest tests/test_chat_*.py --cov=app.services.chat_service --cov-report=html
```

---

## Supuestos Hechos

### **Técnicos:**
- **Modelo LLM**: Azure OpenAI GPT-4 para generación de respuestas
- **Vector Search**: Búsqueda semántica con umbral de similitud 0.7
- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2 (reutilizado del vector store)
- **Context Window**: Máximo 4000 caracteres de contexto por consulta
- **Response Limit**: Máximo 2000 caracteres por respuesta generada

### **De Funcionalidad:**
- **Intenciones soportadas**: 6 tipos (patient_info, condition_list, symptom_search, medication_info, temporal_query, general_query)
- **Entidades detectadas**: Pacientes, condiciones médicas, síntomas, medicamentos, fechas
- **Búsqueda híbrida**: Vector similarity + metadata filtering
- **Ranking multi-criterio**: Similitud + coincidencia de entidades + fecha
- **Context aggregation**: Máximo 5 fuentes por respuesta

### **De Respuestas:**
- **Respuestas basadas en datos**: Solo información presente en conversaciones almacenadas
- **Disclaimer médico**: Automático para consultas con contenido médico
- **Confidence scoring**: Basado en similitud promedio y coincidencia de entidades
- **Sugerencias de seguimiento**: Máximo 3 sugerencias por respuesta
- **Sources tracking**: Trazabilidad completa de conversaciones utilizadas

### **De Performance:**
- **Tiempo de respuesta**: <3 segundos para consultas simples
- **Context retrieval**: <1 segundo para búsqueda vectorial
- **Response generation**: <2 segundos para generación con GPT-4
- **Concurrent queries**: Soporte para múltiples consultas simultáneas
- **Rate limiting**: No implementado en MVP (futuro enhancement)

---

## ✨ Buenas Prácticas Aplicadas

### **Arquitectura RAG:**
-  **Pipeline estructurado**: Query Analysis → Retrieval → Context Ranking → Generation → Validation
-  **Separation of concerns**: Servicios independientes para vector search y generation
-  **Intent classification**: Detección automática de intención para optimizar búsqueda
-  **Entity extraction**: Identificación de nombres, condiciones y términos médicos

### **Calidad de Respuestas:**
-  **Ground truth responses**: Respuestas basadas únicamente en datos verificables
-  **Source attribution**: Cada respuesta incluye fuentes específicas
-  **Confidence scoring**: Nivel de confianza basado en calidad del contexto
-  **Medical disclaimers**: Recordatorios automáticos sobre consultar profesionales

### **Búsqueda Inteligente:**
-  **Hybrid search**: Combinación de búsqueda vectorial y filtros de metadata
-  **Query expansion**: Sinónimos médicos y términos relacionados
-  **Context ranking**: Ordenamiento por relevancia, entidades y fecha
-  **Excerpt generation**: Extractos relevantes optimizados por consulta

### **Robustez del Sistema:**
-  **Error handling**: Manejo graceful de fallos en componentes
-  **Fallback responses**: Respuestas por defecto cuando no hay información
-  **Input validation**: Validación exhaustiva de consultas
-  **Performance monitoring**: Tracking de tiempos de respuesta

### **Experiencia de Usuario:**
-  **Natural language queries**: Soporte para consultas en español natural
-  **Follow-up suggestions**: Sugerencias inteligentes de seguimiento
-  **Multiple output formats**: Respuestas adaptadas al tipo de consulta
-  **Rich metadata**: Información contextual completa en respuestas

### **Observabilidad:**
-  **Structured logging**: Logs detallados de todo el pipeline RAG
-  **Performance metrics**: Tiempos de procesamiento por componente
-  **Query analytics**: Análisis de patrones de consultas
-  **Error tracking**: Monitoreo de fallos y degradación

---

## Pipeline RAG Completo

```
1. Query Input → Normalization & Validation
                       ↓
2. Intent Classification → Entity Extraction → Query Expansion
                       ↓
3. Vector Search → Metadata Filtering → Hybrid Results
                       ↓
4. Context Ranking → Relevance Scoring → Context Aggregation
                       ↓
5. Prompt Engineering → GPT-4 Generation → Response Validation
                       ↓
6. Source Attribution → Confidence Calculation → Response Formatting
                       ↓
7. Final Response + Sources + Suggestions + Metadata
```

---

## 🎛️ Casos de Uso Soportados

### **1. Información de Pacientes Específicos**
- "¿Qué enfermedad tiene Pepito Gómez?"
- "¿Cuál es el diagnóstico de María García?"
- "Información del paciente Juan Pérez"
- "¿Qué le pasa a Ana López?"

### **2. Listas por Condición Médica**
- "Listame los pacientes con diabetes"
- "¿Quiénes tienen hipertensión?"
- "Pacientes con asma bronquial"
- "¿Cuántos pacientes tienen migraña?"

### **3. Búsquedas por Síntomas**
- "¿Quién tiene dolor de cabeza?"
- "Pacientes con fiebre"
- "¿Quién reportó tos seca?"
- "Síntomas de mareos"

### **4. Información de Medicamentos**
- "¿Qué medicamentos toma Pedro?"
- "Tratamiento para la diabetes"
- "¿Qué medicina se recetó para el dolor?"
- "Medicamentos para la presión alta"

### **5. Consultas Temporales**
- "¿Qué pacientes vinieron ayer?"
- "Consultas de la semana pasada"
- "¿Cuándo fue la última visita de Carlos?"
- "Pacientes de este mes"

### **6. Consultas Generales**
- "¿Cuáles son los síntomas más comunes?"
- "¿Qué diagnósticos se han dado?"
- "¿Hay pacientes con condiciones crónicas?"

---

## Integración con Servicios Existentes

### **Aprovechamiento de Infraestructura:**
- **Vector Store**: Utiliza completamente el sistema de Chroma DB implementado
- **Azure OpenAI**: Reutiliza la configuración existente de GPT-4
- **Base de datos**: Integración con conversaciones en SQLite
- **Logging**: Utiliza el sistema de logging estructurado existente

### **Nuevas Capacidades Agregadas:**
- **Búsqueda semántica avanzada** con filtros inteligentes
- **Análisis de intención** y extracción de entidades médicas
- **Ranking de contexto** por relevancia múltiple
- **Generación de respuestas** con prompts médicos especializados

---

# Sprint 2 - 4. Subida de PDFs/Imágenes (funcionalidad PLUS)

## ⏱️ Tiempo Estimado de Desarrollo Manual
**Estimación: 3-4 horas** para completar esta funcionalidad manualmente, incluyendo:
- Configuración de PyPDF2 y Tesseract OCR (30 min)
- Implementación del servicio OCR completo (2 horas)
- Desarrollo de endpoints de documentos (1 hora)
- Integración con vector store y testing (30 min)

---

## Descripción de la Subida de PDFs/Imágenes

Esta es la **primera funcionalidad PLUS** del proyecto **ElSol-Challenge**, que extiende el sistema para procesar documentos médicos además de audio. Permite subir PDFs e imágenes, extraer texto con OCR, identificar automáticamente información médica y almacenar todo en el vector store para búsquedas inteligentes.

## Decisión Técnica: PyPDF2 + Tesseract OCR

### **¿Por qué PyPDF2 para PDFs?**
- **Simplicidad**: Instalación y uso directo sin dependencias complejas
- **Compatibilidad**: Maneja la mayoría de PDFs médicos estándar
- **Performance**: Rápido para documentos con texto seleccionable
- **Python nativo**: Se integra perfectamente con FastAPI

### **¿Por qué Tesseract OCR para Imágenes?**
- **Precisión médica**: Excelente para documentos médicos escaneados
- **Soporte de idiomas**: Optimizado para español médico
- **Open source**: Sin costos de licencia para el MVP
- **Configurabilidad**: Permite ajustar parámetros de confianza

### **¿Por qué Integración con IA?**
- **Extracción inteligente**: GPT-4 identifica automáticamente pacientes y metadata
- **Asociación automática**: Vincula documentos con conversaciones existentes
- **Consistencia**: Mismo motor de IA que el resto del sistema

---

## Endpoints Disponibles

### **POST /api/v1/upload-document**
Endpoint principal para upload y procesamiento de documentos médicos.

**Request (multipart/form-data):**
```bash
curl -X POST "http://localhost:8000/api/v1/upload-document" \
  -F "file=@examen_pepito_gomez.pdf" \
  -F "patient_name=Pepito Gómez" \
  -F "document_type=Examen médico" \
  -F "description=Resultados de laboratorio"
```

**Response:**
```json
{
  "document_id": "doc-abc123-def456",
  "filename": "examen_pepito_gomez.pdf",
  "file_type": "pdf",
  "file_size_bytes": 245760,
  "status": "pending",
  "patient_association": "Pepito Gómez",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Formatos Soportados:**
- **PDFs**: Documentos médicos con texto seleccionable
- **Imágenes**: JPG, JPEG, PNG, TIFF, TIF
- **Tamaño máximo**: 10MB por archivo
- **Páginas PDF**: Máximo 50 páginas por documento

### 📋 **GET /api/v1/documents**
Listar documentos procesados con filtros opcionales.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/documents?patient_name=Pepito&status=completed&limit=10"
```

**Response:**
```json
[
  {
    "document_id": "doc-abc123",
    "filename": "examen_pepito_gomez.pdf",
    "file_type": "pdf",
    "file_size_bytes": 245760,
    "status": "completed",
    "ocr_result": {
      "text": "LABORATORIO CLÍNICO\nPaciente: Pepito Gómez\nEdad: 35 años\nExamen: Glucosa en sangre\nResultado: 98 mg/dL (Normal)...",
      "confidence": 0.95,
      "page_count": 2,
      "processing_time_ms": 1250,
      "language_detected": "spa"
    },
    "extracted_metadata": {
      "patient_name": "Pepito Gómez",
      "document_date": "2024-01-15",
      "document_type": "Examen de laboratorio",
      "medical_conditions": ["diabetes", "seguimiento"],
      "medications": [],
      "medical_procedures": ["glucosa en sangre", "análisis bioquímico"]
    },
    "vector_stored": true,
    "patient_association": "Pepito Gómez",
    "created_at": "2024-01-15T10:30:00Z",
    "processed_at": "2024-01-15T10:31:15Z"
  }
]
```

**Filtros disponibles:**
- `patient_name`: Filtrar por nombre de paciente
- `status`: pending, processing, completed, failed
- `file_type`: pdf, image
- `skip` y `limit`: Para paginación

### **GET /api/v1/documents/{document_id}**
Obtener información completa de un documento específico.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/documents/doc-abc123-def456"
```

**Response:** Similar al endpoint anterior pero con información completa incluyendo texto extraído completo.

### **GET /api/v1/documents/search**
Buscar en el contenido de documentos procesados.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/documents/search?query=diabetes&patient_name=Pepito&max_results=5"
```

**Response:**
```json
[
  {
    "document_id": "doc-abc123",
    "filename": "examen_pepito_gomez.pdf",
    "patient_name": "Pepito Gómez",
    "relevance_score": 0.9,
    "excerpt": "...resultados muestran niveles de glucosa normales, descartando diabetes tipo 2 en este momento...",
    "highlight": "diabetes",
    "document_type": "Examen de laboratorio",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

### **DELETE /api/v1/documents/{document_id}**
Eliminar documento y su archivo asociado.

**Request:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/documents/doc-abc123-def456"
```

---

## Cómo Testear la Funcionalidad

### 1. **Setup del Entorno OCR**

**Instalar Tesseract (Windows):**
```bash
# Descargar desde: https://github.com/UB-Mannheim/tesseract/wiki
# O usar Chocolatey:
choco install tesseract

# Verificar instalación
tesseract --version
```

**Instalar dependencias Python:**
```bash
cd backend
pip install PyPDF2>=3.0.1 pytesseract>=0.3.10 Pillow>=10.0.0
```

### 2. **Casos de Uso de PDFs**

**Caso 1: Subir examen médico en PDF**
```bash
curl -X POST "http://localhost:8000/api/v1/upload-document" \
  -F "file=@documentos/examen_pepito_gomez.pdf" \
  -F "patient_name=Pepito Gómez" \
  -F "document_type=Examen médico"
```

**Caso 2: Subir receta médica**
```bash
curl -X POST "http://localhost:8000/api/v1/upload-document" \
  -F "file=@documentos/receta_maria_garcia.pdf" \
  -F "patient_name=María García" \
  -F "document_type=Receta médica" \
  -F "description=Medicamentos para diabetes"
```

### 3. **Casos de Uso de Imágenes OCR**

**Caso 3: Procesar imagen de radiografía**
```bash
curl -X POST "http://localhost:8000/api/v1/upload-document" \
  -F "file=@imagenes/radiografia_torax.jpg" \
  -F "patient_name=Juan Pérez" \
  -F "document_type=Radiografía"
```

**Caso 4: OCR de documento escaneado**
```bash
curl -X POST "http://localhost:8000/api/v1/upload-document" \
  -F "file=@imagenes/documento_escaneado.png" \
  -F "document_type=Documento médico"
```

### 4. **Búsquedas en Documentos**

**Buscar por término médico:**
```bash
curl -X GET "http://localhost:8000/api/v1/documents/search?query=glucosa&max_results=5"
```

**Buscar documentos de paciente específico:**
```bash
curl -X GET "http://localhost:8000/api/v1/documents?patient_name=Pepito%20Gómez&status=completed"
```

### 5. **Integración con Chat RAG**

**Consultar información de documentos:**
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿Qué exámenes médicos tiene Pepito Gómez?",
    "max_results": 5
  }'
```

### 6. **Flujo de Testing Completo**

**Paso 1: Upload documento**
```bash
DOCUMENT_ID=$(curl -X POST "http://localhost:8000/api/v1/upload-document" \
  -F "file=@test_document.pdf" \
  -F "patient_name=Test Patient" | jq -r '.document_id')
```

**Paso 2: Verificar procesamiento**
```bash
curl -X GET "http://localhost:8000/api/v1/documents/$DOCUMENT_ID"
```

**Paso 3: Buscar en contenido**
```bash
curl -X GET "http://localhost:8000/api/v1/documents/search?query=glucosa"
```

**Paso 4: Consultar con chat**
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "¿Qué documentos tiene Test Patient?"}'
```

### 7. **Pruebas Automatizadas**

**Instalar pytest (si es necesario):**
```bash
pip install pytest pytest-asyncio pytest-cov
```

**Tests de transcripción:**
```bash
# Tests básicos del servicio Whisper
python -m pytest tests/test_transcription_service.py -v

# Tests específicos de validación
python -m pytest tests/test_transcription_service.py::TestWhisperService::test_validate_audio_file_valid_formats -v

# Tests de performance
python -m pytest tests/test_transcription_service.py::TestTranscriptionPerformance -v
```

**Tests de OCR y documentos:**
```bash
# Tests de OCR service
python -m pytest tests/test_ocr_service.py -v

# Tests de endpoints de documentos
python -m pytest tests/test_document_endpoints.py -v

# Tests de integración de documentos
python -m pytest tests/test_document_integration.py -v --cov=app.services.ocr_service
```

---

## Supuestos Hechos

### **Técnicos:**
- **OCR Language**: Español (spa) como idioma por defecto para Tesseract
- **Confidence Threshold**: Mínimo 60% de confianza para resultados OCR
- **PDF Processing**: Máximo 50 páginas por documento para evitar timeouts
- **File Storage**: Almacenamiento local temporal (production usaría S3/similar)
- **Text Extraction**: Máximo 50,000 caracteres por documento

### **De Formatos:**
- **PDFs Soportados**: Documentos con texto seleccionable (no escaneados)
- **Imágenes Soportadas**: JPG, PNG, TIFF con resolución >300 DPI
- **Tamaño de Archivo**: Límite 10MB para balance entre calidad y performance
- **Calidad OCR**: Target >85% accuracy para documentos médicos claros
- **Fallback Strategy**: Si OCR falla, documento se almacena sin texto extraído

### **De Procesamiento:**
- **Background Processing**: Procesamiento asíncrono para evitar timeouts en upload
- **Retry Logic**: No implementado en MVP (futuro enhancement)
- **Concurrent Processing**: Un documento a la vez por simplicidad MVP
- **Error Recovery**: Fallos en OCR no bloquean almacenamiento del archivo
- **Vector Integration**: Solo documentos con texto se almacenan en vector store

### **De Metadata Médica:**
- **AI Extraction**: GPT-4 extrae automáticamente paciente, fecha, tipo documento
- **Fallback Values**: Campos opcionales se dejan null si no se detectan
- **Medical Terminology**: Optimizado para terminología médica en español
- **Patient Association**: Vinculación automática basada en nombres extraídos
- **Confidence Scoring**: No implementado para metadata (futuro enhancement)

---

## Buenas Prácticas Aplicadas

### **Procesamiento de Documentos:**
- **Async Processing**: Upload inmediato + procesamiento en background
- **Input Validation**: Validación exhaustiva de formatos y tamaños
- **Error Handling**: Manejo graceful de fallos en OCR y PDF parsing
- **Resource Management**: Limpieza automática de archivos temporales

### **Integración con Vector Store:**
- **Contextual Embedding**: Texto + metadata para mejor búsqueda semántica
- **Unified Search**: Documentos y conversaciones en mismo vector space
- **Rich Metadata**: Información estructurada para filtros inteligentes
- **Source Attribution**: Trazabilidad completa documento → resultado

### **Seguridad y Validación:**
- **File Type Detection**: Validación por contenido, no solo extensión
- **Size Limits**: Límites estrictos para prevenir ataques DoS
- **Sanitization**: Limpieza de texto extraído para prevenir injection
- **Path Security**: Nombres de archivos seguros sin directory traversal

### **Performance y Escalabilidad:**
- **Background Tasks**: Procesamiento no bloquea respuesta HTTP
- **Pagination**: Endpoints con paginación para datasets grandes
- **Efficient Storage**: Solo texto relevante se almacena, archivos temporales
- **Lazy Loading**: Texto completo solo se carga cuando se solicita

### **Experiencia de Usuario:**
- **Status Tracking**: Estados claros (pending, processing, completed, failed)
- **Progress Feedback**: Información detallada de procesamiento
- **Error Messages**: Mensajes descriptivos para fallos de OCR/PDF
- **Search Capabilities**: Búsqueda full-text en contenido extraído

### **Observabilidad:**
- **Structured Logging**: Logs detallados de todo el pipeline OCR
- **Performance Metrics**: Tiempos de procesamiento por tipo de documento
- **Error Tracking**: Categorización de fallos (OCR, PDF, IA, storage)
- **Usage Analytics**: Estadísticas de tipos de documentos procesados

---

## Pipeline de Procesamiento Completo

```
1. Document Upload → File Validation → Temporary Storage
                          ↓
2. Background Task → File Type Detection → OCR/PDF Processing
                          ↓
3. Text Extraction → Text Cleaning → Quality Validation
                          ↓
4. AI Metadata Extraction → Patient Identification → Medical Info
                          ↓
5. Vector Store Embedding → Search Index Update → Database Storage
                          ↓
6. Status Update → Cleanup Temp Files → Processing Complete
```

---

## Tipos de Documentos Soportados

### ** Documentos PDF**
- **Recetas médicas** con medicamentos y dosis
- **Exámenes de laboratorio** con resultados numéricos
- **Informes médicos** con diagnósticos y tratamientos
- **Historias clínicas** con información del paciente
- **Resultados de estudios** (ecografías, TAC, etc.)

### ** Imágenes con OCR**
- **Documentos escaneados** en formatos de imagen
- **Radiografías digitales** con reportes textuales
- **Fotografías de recetas** escritas a mano (limitado)
- **Formularios médicos** completados y escaneados
- **Documentos de urgencias** fotografiados

### ** Información Extraída Automáticamente**
- **Datos del Paciente**: Nombre, edad, fecha de nacimiento
- **Información Temporal**: Fecha del documento, fecha de examen
- **Clasificación**: Tipo de documento médico
- **Condiciones Médicas**: Diagnósticos y enfermedades mencionadas
- **Medicamentos**: Fármacos prescritos y dosis
- **Procedimientos**: Exámenes y tratamientos realizados

---

## Integración con Sistema Existente

### **Vector Store Unificado:**
- **Multi-modal Search**: Buscar en audio + documentos simultáneamente
- **Consistent Metadata**: Mismo formato para audio y documentos
- **Cross-references**: Documentos pueden referenciar conversaciones
- **Semantic Similarity**: Embeddings comparables entre fuentes

### **Chat RAG Extendido:**
- **Document Queries**: "¿Qué exámenes tiene Juan?"
- **Mixed Context**: Respuestas combinando audio + documentos
- **Source Attribution**: Citas específicas a documentos o conversaciones
- **Medical Correlation**: IA correlaciona información entre fuentes

### **Base de Datos Relacional:**
- **Tabla documents**: Metadata y estado de procesamiento
- **Relación conversations-documents**: Vinculación opcional
- **Índices optimizados**: Búsqueda eficiente por paciente/tipo
- **Audit trail**: Historial completo de procesamiento

---

# Sprint 2 - 5. Diferenciación de Hablantes (funcionalidad PLUS)

---

## Descripción de la Diferenciación de Hablantes

Esta es la **segunda funcionalidad PLUS** del proyecto **ElSol-Challenge**, que implementa **speaker diarization** para identificar y separar automáticamente las voces del **promotor** y del **paciente** en conversaciones médicas. Utiliza un enfoque híbrido combinando análisis de audio y análisis semántico del contenido.

## Decisión Técnica: Algoritmo Híbrido

### **¿Por qué Enfoque Híbrido (Audio + Texto)?**
- **Mayor Precisión**: Combina características vocales con análisis semántico
- **Contexto Médico**: Utiliza patrones típicos de conversaciones médicas
- **Fallback Robusto**: Si falla análisis de audio, usa solo texto
- **MVP Compatible**: Funciona sin dependencias complejas de ML

### **¿Por qué Librosa + Scikit-learn?**
- **Características de Audio**: Extracción de pitch, energía, espectro
- **Clustering Simple**: K-means para agrupar voces similares
- **Python Nativo**: Se integra perfectamente con el stack existente
- **Performance**: Rápido para archivos de audio médicos típicos

### **¿Por qué Análisis Semántico?**
- **Patrones Médicos**: Reconoce preguntas típicas del promotor
- **Vocabulario Específico**: Identifica terminología médica profesional
- **Contexto Conversacional**: Analiza flujo típico consulta médica
- **Confidence Boost**: Mejora precisión con evidencia textual

---

## Funcionalidad Integrada

### **POST /api/v1/upload-audio (con más información)**
El endpoint existente ahora incluye speaker diarization automáticamente.

**Request (sin cambios):**
```bash
curl -X POST "http://localhost:8000/api/v1/upload-audio" \
  -F "file=@conversacion_medica.wav"
```

**Response (EXTENDIDO con speaker info):**
```json
{
  "transcription_id": "trans-abc123-def456",
  "filename": "conversacion_medica.wav",
  "status": "completed",
  "transcription_text": "Buenos días, ¿cómo se siente hoy? Me duele mucho la cabeza desde ayer...",
  "structured_data": {
    "nombre": "María García",
    "edad": "45 años",
    "diagnóstico": "Cefalea tensional",
    "fecha": "2024-01-15"
  },
  "unstructured_data": {
    "síntomas": ["dolor de cabeza", "tensión", "estrés"],
    "contexto": "Dolor persistente desde ayer, relacionado con trabajo",
    "observaciones": "Paciente refiere estrés laboral como posible causa"
  },
  "diarization_result": {
    "speaker_segments": [
      {
        "speaker": "promotor",
        "text": "Buenos días, ¿cómo se siente hoy?",
        "start_time": 0.0,
        "end_time": 3.2,
        "confidence": 0.95,
        "word_count": 6
      },
      {
        "speaker": "paciente", 
        "text": "Me duele mucho la cabeza desde ayer",
        "start_time": 3.5,
        "end_time": 7.1,
        "confidence": 0.87,
        "word_count": 7
      },
      {
        "speaker": "promotor",
        "text": "¿Desde cuándo comenzó el dolor exactamente?",
        "start_time": 7.5,
        "end_time": 10.8,
        "confidence": 0.92,
        "word_count": 7
      }
    ],
    "speaker_stats": {
      "total_speakers": 2,
      "promotor_time": 45.2,
      "paciente_time": 38.7,
      "unknown_time": 2.1,
      "overlap_time": 0.0,
      "total_duration": 86.0,
      "speaker_changes": 12,
      "average_segment_length": 7.2
    },
    "processing_time_ms": 850,
    "algorithm_version": "1.0",
    "confidence_threshold": 0.7
  },
  "speaker_summary": {
    "promotor_contributions": [
      "Realizó preguntas de evaluación médica",
      "Proporcionó diagnóstico de cefalea tensional", 
      "Recomendó tratamiento con relajación y analgésicos"
    ],
    "paciente_contributions": [
      "Describió dolor de cabeza persistente",
      "Relacionó síntomas con estrés laboral",
      "Confirmó ausencia de fiebre u otros síntomas"
    ]
  },
  "processing_time_seconds": 12.5,
  "vector_stored": true,
  "created_at": "2024-01-15T14:30:00Z"
}
```

### **Consultas de Chat Mejoradas**
El sistema de chat ahora entiende la diferenciación de hablantes.

**Consultas específicas por hablante:**
```bash
# ¿Qué dijo el paciente?
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "¿Qué síntomas reportó el paciente María García?"}'

# ¿Qué preguntó el promotor?  
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "¿Qué preguntas hizo el promotor a Juan Pérez?"}'

# Análisis de participación
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "¿Cuánto tiempo habló cada persona en la consulta?"}'
```

**Respuestas con contexto de hablante:**
```json
{
  "answer": "Según la transcripción, el paciente María García reportó los siguientes síntomas:\n\n- **Dolor de cabeza persistente**: 'Me duele mucho la cabeza desde ayer'\n- **Relación con estrés**: 'Ha sido una semana muy estresante en el trabajo'\n- **Intensidad**: 'El dolor es como una presión fuerte aquí' (señalando las sienes)\n- **Sin fiebre**: Confirmó no tener fiebre cuando el promotor preguntó\n\nEl paciente habló durante 38.7 segundos de los 86 segundos totales de la conversación.",
  "sources": [
    {
      "conversation_id": "trans-abc123",
      "patient_name": "María García",
      "relevance_score": 0.95,
      "excerpt": "PACIENTE: Me duele mucho la cabeza desde ayer... PACIENTE: Ha sido una semana muy estresante...",
      "metadata": {
        "speaker_segments_used": ["paciente"],
        "total_patient_time": 38.7
      }
    }
  ],
  "confidence": 0.92,
  "intent": "symptom_search",
  "follow_up_suggestions": [
    "¿Qué tratamiento recomendó el promotor para María?",
    "¿Cuántas veces cambió de hablante la conversación?",
    "¿Qué preguntas específicas hizo el promotor?"
  ]
}
```

---

## Cómo Testear la Funcionalidad

### 1. **Setup del Entorno Audio**

**Instalar dependencias de audio:**
```bash
cd backend
pip install librosa>=0.10.1 scipy>=1.11.0 scikit-learn>=1.3.0
```

**Verificar instalación:**
```bash
python -c "import librosa, scipy, sklearn; print(' Audio dependencies OK')"
```

### 2. **Casos de Uso de Diarización**

**Caso 1: Conversación clara con 2 hablantes**
```bash
curl -X POST "http://localhost:8000/api/v1/upload-audio" \
  -F "file=@audio/consulta_clara_2_hablantes.wav"

# Verificar resultado con diarización
curl -X GET "http://localhost:8000/api/v1/transcriptions/{transcription_id}"
```

**Caso 2: Audio con interrupciones y solapamiento**
```bash
curl -X POST "http://localhost:8000/api/v1/upload-audio" \
  -F "file=@audio/conversacion_con_interrupciones.wav"
```

**Caso 3: Audio de baja calidad (fallback a texto)**
```bash
curl -X POST "http://localhost:8000/api/v1/upload-audio" \
  -F "file=@audio/audio_ruidoso.mp3"
```

### 3. **Consultas Específicas de Hablantes**

**Análisis por tipo de hablante:**
```bash
# ¿Qué dijo el paciente sobre sus síntomas?
curl -X POST "http://localhost:8000/api/v1/chat" \
  -d '{"query": "¿Qué síntomas describió el paciente?"}'

# ¿Qué diagnóstico dio el promotor?
curl -X POST "http://localhost:8000/api/v1/chat" \
  -d '{"query": "¿Qué diagnóstico estableció el promotor?"}'

# Estadísticas de participación
curl -X POST "http://localhost:8000/api/v1/chat" \
  -d '{"query": "¿Quién habló más tiempo en la consulta?"}'
```

### 4. **Validación de Precisión**

**Verificar clasificación de segmentos:**
```bash
# Obtener transcripción con segmentos
RESPONSE=$(curl -X GET "http://localhost:8000/api/v1/transcriptions/{id}")

# Verificar que segmentos tienen speakers asignados
echo $RESPONSE | jq '.diarization_result.speaker_segments[] | {speaker, text, confidence}'

# Verificar estadísticas
echo $RESPONSE | jq '.diarization_result.speaker_stats'
```

### 5. **Casos Edge de Testing**

**Audio con un solo hablante:**
```bash
curl -X POST "http://localhost:8000/api/v1/upload-audio" \
  -F "file=@audio/monólogo_médico.wav"
# Esperado: Todos los segmentos clasificados como 'unknown' o un solo tipo
```

**Audio muy corto:**
```bash
curl -X POST "http://localhost:8000/api/v1/upload-audio" \
  -F "file=@audio/saludo_corto.wav"
# Esperado: Diarización básica con confidence bajo
```

**Audio sin dependencias ML:**
```bash
# Simular entorno sin librosa/sklearn
# Debería usar solo análisis de texto
```

### 6. **Pruebas de Integración Chat**

**Flujo completo: Audio → Diarización → Chat:**
```bash
# Paso 1: Upload audio
TRANS_ID=$(curl -X POST "http://localhost:8000/api/v1/upload-audio" \
  -F "file=@test_conversation.wav" | jq -r '.transcription_id')

# Paso 2: Esperar procesamiento
sleep 10

# Paso 3: Consulta específica por hablante
curl -X POST "http://localhost:8000/api/v1/chat" \
  -d "{\"query\": \"¿Qué dijo el paciente en la transcripción $TRANS_ID?\"}"
```

### 7. **Pruebas Automatizadas**

**Tests de speaker diarization:**
```bash
# Tests básicos del servicio de speakers
python -m pytest tests/test_speaker_service.py -v

# Tests de integración con transcripción
python -m pytest tests/test_speaker_integration.py -v

# Tests de performance y benchmarking
python -m pytest tests/test_speaker_performance.py -v

# Tests específicos de algoritmos
python -m pytest tests/test_speaker_service.py::TestSpeakerService::test_analyze_text_content_promotor_patterns -v
```

**Suite completa de tests:**
```bash
# Ejecutar todos los tests de funcionalidades PLUS
python -m pytest tests/test_*speaker* tests/test_*document* tests/test_*ocr* -v

# Tests con coverage
python -m pytest tests/ --cov=app.services --cov-report=html

# Tests de performance únicamente
python -m pytest tests/test_speaker_performance.py tests/test_document_integration.py::TestDocumentPerformanceIntegration -v
```

---

## Supuestos Hechos

### **Técnicos:**
- **Algoritmo**: Híbrido (audio + texto) con fallback solo-texto
- **Sample Rate**: 16kHz para análisis de características de audio
- **Speakers**: Optimizado para 2 hablantes (promotor + paciente)
- **Confidence Threshold**: 0.7 mínimo para clasificación confiable
- **Segment Length**: Mínimo 1.0 segundos por segmento

### **De Audio:**
- **Calidad Mínima**: SNR >20dB para análisis de audio efectivo
- **Duración**: >10 segundos para clustering de características
- **Formato**: Compatible con librosa (WAV, MP3, etc.)
- **Channels**: Mono preferido, stereo convertido automáticamente
- **Fallback**: Si falla análisis de audio, usa solo patrón de texto

### **De Clasificación:**
- **Target Accuracy**: >80% para clasificación promotor vs paciente
- **Unknown Category**: Para segmentos ambiguos o inciertos
- **Confidence Scoring**: Basado en evidencia audio + texto combinada
- **Pattern Recognition**: Optimizado para conversaciones médicas en español
- **Medical Context**: Utiliza vocabulario y patrones médicos específicos

### **De Integración:**
- **Backward Compatibility**: Transcripciones existentes no afectadas
- **Performance Impact**: <20% overhead en tiempo de procesamiento
- **Storage**: Datos de diarización almacenados como JSON en DB
- **Vector Store**: Incluye información de speaker en embeddings
- **Chat Integration**: Queries pueden filtrar por tipo de hablante

---

## Buenas Prácticas Aplicadas

### **Algoritmo de Diarización:**
- **Multi-modal Approach**: Combina evidencia de audio y texto
- **Graceful Degradation**: Fallback robusto cuando falla análisis de audio
- **Domain-Specific**: Patrones específicos para conversaciones médicas
- **Confidence Scoring**: Niveles de confianza transparentes

### **Integración con Sistema:**
- **Non-Breaking Changes**: Compatible con transcripciones existentes
- **Optional Processing**: Diarización no bloquea transcripción básica
- **Structured Storage**: Datos organizados en JSON schemes validados
- **Performance Monitoring**: Tracking de accuracy y tiempos

### **Análisis de Características:**
- **Audio Features**: Pitch, energía, centroide espectral, velocidad
- **Text Patterns**: Regex patterns para identificar roles médicos  
- **Medical Vocabulary**: Keywords específicos de promotor vs paciente
- **Temporal Analysis**: Consideración de flujo conversacional típico

### **Manejo de Errores:**
- **Dependency Checks**: Verificación de librerías al inicio
- **Quality Validation**: Verificación de calidad de audio mínima
- **Partial Results**: Resultados parciales si algunos segmentos fallan
- **Error Recovery**: Continúa procesamiento aunque diarización falle

### **Experiencia de Usuario:**
- **Rich Output**: Estadísticas detalladas de participación
- **Speaker-Aware Chat**: Consultas específicas por tipo de hablante
- **Visual Separation**: Transcripciones claramente etiquetadas
- **Confidence Indicators**: Usuarios ven nivel de confianza

### **Observabilidad:**
- **Algorithm Metrics**: Tracking de accuracy por tipo de audio
- **Processing Times**: Métricas de performance por componente
- **Feature Quality**: Análisis de calidad de características extraídas
- **Usage Analytics**: Patrones de uso de queries por hablante

---

## Pipeline de Diarización Completo

```
1. Audio Input → Quality Check → Feature Extraction
                     ↓
2. Pitch Analysis → Energy Analysis → Spectral Analysis → Speech Rate
                     ↓
3. Audio Clustering → K-means 2 clusters → Speaker Assignment
                     ↓
4. Text Analysis → Pattern Matching → Medical Vocabulary → Context Scoring
                     ↓
5. Hybrid Classification → Audio + Text Evidence → Confidence Calculation
                     ↓
6. Segment Assembly → Timeline Validation → Statistics Generation
                     ↓
7. Database Storage → Vector Store Update → Response Formatting
```

---

## Tipos de Hablantes Identificados

### ** Promotor (Personal Médico)**
**Patrones Identificados:**
- **Saludos profesionales**: "Buenos días", "¿Cómo se siente?"
- **Preguntas médicas**: "¿Desde cuándo?", "¿Con qué frecuencia?"
- **Instrucciones**: "Vamos a revisar", "Le voy a recetar"
- **Terminología médica**: Diagnósticos, medicamentos, procedimientos
- **Características de voz**: Típicamente más clara y estructurada

### ** Paciente**
**Patrones Identificados:**
- **Descripción de síntomas**: "Me duele", "Siento", "Tengo"
- **Referencias temporales**: "Desde hace", "Ayer", "Esta mañana"
- **Respuestas directas**: "Sí doctor", "No", "Exacto"
- **Contexto personal**: "En casa", "En el trabajo", "Mi familia"
- **Características de voz**: Mayor variabilidad emocional

### ** Unknown (Ambiguo)**
**Casos de Clasificación:**
- **Segmentos muy cortos**: <2 segundos de duración
- **Audio de baja calidad**: Ruido excesivo o distorsión
- **Múltiples hablantes**: Más de 2 voces detectadas
- **Contenido neutro**: Sin patrones médicos identificables
- **Confidence bajo**: <70% en clasificación automática

*Desarrollado como parte del ElSol-Challenge - Sistema de transcripción y análisis de conversaciones médicas*
