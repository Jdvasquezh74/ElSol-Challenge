# ElSol Medical AI - Frontend

Frontend React para el sistema de transcripción y análisis médico con IA.

## 🚀 Características

- **Upload de Audio**: Subir archivos WAV/MP3 con transcripción automática
- **Upload de Documentos**: Subir PDFs e imágenes con OCR
- **Chat RAG**: Consultas inteligentes sobre contenido médico
- **Diferenciación de Hablantes**: Visualización de promotor vs paciente
- **Interfaz Responsive**: Diseño mobile-first con Tailwind CSS
- **TypeScript**: Type safety completo
- **React Query**: Gestión de estado del servidor optimizada

## 🛠️ Stack Tecnológico

- **React 19** con TypeScript
- **Vite** para build y desarrollo
- **Tailwind CSS** para styling
- **React Query** para estado del servidor
- **React Dropzone** para uploads
- **Heroicons** para iconografía
- **React Hot Toast** para notificaciones

## 📦 Instalación

```bash
# Instalar dependencias
npm install

# Desarrollo
npm run dev

# Build de producción
npm run build

# Previsualizar build
npm run preview

# Verificar tipos
npm run type-check
```

## Estructura del Proyecto

```
src/
├── components/              # Componentes React
│   ├── common/             # Componentes reutilizables
│   ├── AudioUpload.tsx     # Upload de audio
│   ├── DocumentUpload.tsx  # Upload de documentos
│   ├── ChatInterface.tsx   # Chat RAG
│   ├── TranscriptionList.tsx # Lista conversaciones
│   └── ConversationDetail.tsx # Detalle conversación
├── hooks/                  # Custom hooks
│   ├── useAudioUpload.ts   # Upload audio
│   ├── useDocumentUpload.ts # Upload documentos
│   └── useChat.ts          # Chat functionality
├── services/               # API services
│   └── api.ts              # Cliente HTTP
├── types/                  # TypeScript definitions
│   └── api.ts              # API types
└── App.tsx                 # Componente principal
```

## Componentes Principales

### AudioUpload
- Drag & drop para archivos WAV/MP3
- Progress tracking en tiempo real
- Preview de transcripción con speakers
- Estadísticas de participación

### DocumentUpload  
- Support para PDFs e imágenes
- Metadata configurable
- Preview de OCR
- Extracción de información médica

### ChatInterface
- Chat RAG flotante
- Sugerencias inteligentes
- Fuentes con referencias
- Contexto multi-modal

### TranscriptionList
- Lista paginada de conversaciones
- Filtros por estado/paciente/fecha
- Cards con información resumida
- Navegación a detalles

### ConversationDetail
- Transcript segmentado por speaker
- Análisis de información estructurada
- Estadísticas de participación
- Opciones de exportación

## 🔗 Integración con Backend

### Endpoints Consumidos

**Audio/Transcripción:**
- `POST /api/v1/upload-audio` - Upload archivo audio
- `GET /api/v1/transcriptions` - Lista transcripciones
- `GET /api/v1/transcriptions/{id}` - Detalle transcripción

**Documentos:**
- `POST /api/v1/upload-document` - Upload documento
- `GET /api/v1/documents` - Lista documentos  
- `GET /api/v1/documents/search` - Búsqueda en documentos

**Chat RAG:**
- `POST /api/v1/chat` - Consulta chat
- `GET /api/v1/chat/examples` - Ejemplos de consultas

**Vector Store:**
- `GET /api/v1/vector-store/status` - Estado del sistema

## Features UX/UI

### Diseño
- **Paleta médica**: Azules profesionales + acentos verdes
- **Typography**: Inter font para legibilidad
- **Iconografía**: Heroicons consistente
- **Responsive**: Mobile-first approach

### Interacciones
- **Drag & drop** intuitivo para uploads
- **Real-time updates** con polling
- **Optimistic updates** para mejor UX
- **Loading skeletons** durante cargas
- **Toast notifications** para feedback

### Estados
- **Loading states** granulares por componente
- **Error boundaries** para recuperación graceful  
- **Empty states** informativos
- **Progress tracking** visual para uploads

## Manejo de Estados

### React Query
- Cache inteligente de datos del servidor
- Invalidación automática en mutations
- Retry logic configurable
- Background refetching

### Local State
- useState para UI state
- Custom hooks para lógica compleja
- Context API para estado global mínimo

## Responsive Design

### Breakpoints
- **Mobile**: < 640px - UI simplificada
- **Tablet**: 640px - 1024px - Layout híbrido  
- **Desktop**: > 1024px - Sidebar + contenido

### Adaptaciones Mobile
- Sidebar colapsable con overlay
- Chat interface optimizada
- Upload areas adaptativas
- Typography escalable

## Desarrollo

### Scripts Disponibles
```bash
npm run dev          # Servidor desarrollo (puerto 3000)
npm run build        # Build producción
npm run preview      # Preview del build
npm run type-check   # Verificación TypeScript
npm run lint         # ESLint
```

### Hot Reload
- Vite HMR para desarrollo rápido
- TypeScript compilation en tiempo real
- CSS hot reloading con Tailwind

## Debugging

### React DevTools
- Extensión recomendada para debugging
- React Query DevTools incluidos en desarrollo

### Network
- Axios interceptors para logging
- Request/response logging en desarrollo
- Error handling centralizado

## Performance

### Optimizaciones
- Code splitting por rutas
- Lazy loading de componentes pesados
- Image optimization automática
- Bundle analysis con Rollup

### Métricas Target
- **First Load**: < 2s
- **Route Changes**: < 300ms  
- **Upload Feedback**: < 100ms
- **Chat Response**: < 50ms UI feedback

## Seguridad

### Best Practices
- Sanitización de inputs
- HTTPS enforcement en producción
- Content Security Policy headers
- XSS protection

### API Security
- CORS configurado en backend
- Request timeouts configurados
- Error messages no exponen internals

## Deployment

### Build de Producción
```bash
npm run build
# Genera ./dist/ para deploy
```

```

### Opciones de despliegue (a futuro)
- **Vercel/Netlify**: Deploy automático desde Git
- **Docker**: Dockerfile incluido
- **Static Hosting**: Compatible con cualquier CDN