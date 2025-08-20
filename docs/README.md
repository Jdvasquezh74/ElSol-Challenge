# Documentación ElSol Challenge

Esta carpeta contiene la documentación completa del proyecto ElSol Challenge.

## Archivos Principales

### 📄 Documento Unificado
- `ElSol_Challenge_Documentacion_Completa.pdf` - Documentación completa en PDF

### 📋 Documentos Individuales
- `00_Indice_Documentacion_ElSol.md` - Índice general
- `01_Servicio_Whisper_Transcripcion.md` - Servicio de transcripción
- `02_Servicio_OpenAI_Extraccion.md` - Servicio de extracción
- `03_Servicio_Vector_Store.md` - Almacenamiento vectorial
- `04_Servicio_Chat_RAG.md` - Sistema de chat RAG
- `05_Servicio_OCR_Documentos.md` - Procesamiento de documentos
- `06_Servicio_Speaker_Diarization.md` - Diferenciación de hablantes
- `07_Endpoints_API_Documentacion.md` - Documentación de API
- `08_Schemas_Base_Datos.md` - Esquemas de base de datos
- `09_Arquitectura_General_ElSol.md` - Arquitectura general
- `10_Decisiones_Arquitectonicas_Migracion.md` - Decisiones arquitectónicas

### 🖼️ Diagramas
- `images/` - Diagramas Mermaid como imágenes PNG

### 🛠️ Scripts de Construcción
- `build_documentation.py` - Script principal
- `generate_mermaid_images.py` - Generador de imágenes
- `generate_pdf.py` - Generador de PDF

## Cómo Regenerar la Documentación

```bash
# Instalar dependencias opcionales
npm install -g @mermaid-js/mermaid-cli
pip install weasyprint markdown

# Ejecutar script principal
python docs/build_documentation.py
```

## Dependencias

### Para imágenes de diagramas:
- Node.js + mermaid-cli: `npm install -g @mermaid-js/mermaid-cli`

### Para PDF:
- **Opción 1**: Pandoc + wkhtmltopdf
- **Opción 2**: Python weasyprint: `pip install weasyprint markdown`

---

**Generado automáticamente el:** 2025-08-20 08:47
**Proyecto:** ElSol Challenge
**Versión:** 1.0.0
