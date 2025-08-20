"""
Servicio de OCR y Procesamiento de Documentos para la aplicación ElSol Challenge.

Este servicio maneja el procesamiento de PDFs e imágenes usando PyPDF2 y Tesseract OCR
para extraer texto y metadata médica de documentos.

PLUS Feature 4: Subida de PDFs/Imágenes con OCR
"""

import os
import io
import time
import json
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import structlog

# PDF processing
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

# Image OCR processing
try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None
    Image = None

from app.core.config import get_settings
from app.core.schemas import OCRResult, DocumentMetadata
from app.services.openai_service import get_openai_service, OpenAIService

logger = structlog.get_logger(__name__)
settings = get_settings()


class OCRServiceError(Exception):
    """Excepción personalizada para errores del servicio OCR."""
    pass


class OCRService:
    """
    Servicio para procesamiento de documentos con OCR y extracción de texto.
    
    Maneja:
    - Extracción de texto de PDFs con PyPDF2
    - OCR de imágenes con Tesseract
    - Detección automática de tipo de archivo
    - Extracción de metadata médica con IA
    """
    
    def __init__(self):
        """Inicializar el servicio OCR."""
        self.openai_service: OpenAIService = get_openai_service()
        
        # Verificar dependencias
        self._check_dependencies()
        
        # Configurar Tesseract si está disponible
        if pytesseract:
            self._configure_tesseract()
    
    def _check_dependencies(self) -> None:
        """Verificar que las dependencias estén disponibles."""
        missing_deps = []
        
        if not PyPDF2:
            missing_deps.append("PyPDF2")
        
        if not pytesseract or not Image:
            missing_deps.append("pytesseract/Pillow")
        
        if missing_deps:
            logger.warning(
                "Missing OCR dependencies", 
                missing=missing_deps,
                message="Some document processing features may not work"
            )
    
    def _configure_tesseract(self) -> None:
        """Configurar Tesseract OCR."""
        try:
            # Verificar si Tesseract está disponible
            pytesseract.get_tesseract_version()
            logger.info("Tesseract OCR configured successfully")
        except Exception as e:
            logger.error("Tesseract configuration failed", error=str(e))
    
    def detect_file_type(self, file_path: str) -> str:
        """
        Detectar tipo de archivo basado en contenido y extensión.
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            "pdf" o "image"
            
        Raises:
            OCRServiceError: Si el tipo no es soportado
        """
        try:
            # Obtener MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            
            # Obtener extensión
            extension = Path(file_path).suffix.lower()
            
            # Clasificar por MIME type y extensión
            if mime_type == "application/pdf" or extension == ".pdf":
                return "pdf"
            elif (mime_type and mime_type.startswith("image/")) or extension in [".jpg", ".jpeg", ".png", ".tiff", ".tif"]:
                return "image"
            else:
                raise OCRServiceError(f"Tipo de archivo no soportado: {mime_type} / {extension}")
        
        except Exception as e:
            logger.error("File type detection failed", file_path=file_path, error=str(e))
            raise OCRServiceError(f"Error detectando tipo de archivo: {str(e)}")
    
    async def process_document(
        self, 
        file_path: str, 
        original_filename: str
    ) -> Tuple[OCRResult, Optional[DocumentMetadata]]:
        """
        Procesar documento completo: extracción de texto + metadata médica.
        
        Args:
            file_path: Ruta al archivo local
            original_filename: Nombre original del archivo
            
        Returns:
            Tupla con resultado OCR y metadata extraída
            
        Raises:
            OCRServiceError: Si el procesamiento falla
        """
        start_time = time.time()
        
        try:
            logger.info("Starting document processing", 
                       file_path=file_path, 
                       filename=original_filename)
            
            # Detectar tipo de archivo
            file_type = self.detect_file_type(file_path)
            
            # Extraer texto según tipo
            if file_type == "pdf":
                ocr_result = await self._process_pdf(file_path)
            elif file_type == "image":
                ocr_result = await self._process_image(file_path)
            else:
                raise OCRServiceError(f"Tipo de archivo no soportado: {file_type}")
            
            # Calcular tiempo de procesamiento
            processing_time = int((time.time() - start_time) * 1000)
            ocr_result.processing_time_ms = processing_time
            
            # Extraer metadata médica si hay texto
            metadata = None
            if ocr_result.text.strip():
                metadata = await self._extract_medical_metadata(ocr_result.text)
            
            logger.info("Document processing completed",
                       filename=original_filename,
                       text_length=len(ocr_result.text),
                       confidence=ocr_result.confidence,
                       processing_time_ms=processing_time)
            
            return ocr_result, metadata
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error("Document processing failed",
                        file_path=file_path,
                        filename=original_filename,
                        error=str(e),
                        processing_time_ms=processing_time)
            raise OCRServiceError(f"Error procesando documento: {str(e)}")
    
    async def _process_pdf(self, file_path: str) -> OCRResult:
        """
        Procesar archivo PDF para extraer texto.
        
        Args:
            file_path: Ruta al archivo PDF
            
        Returns:
            Resultado con texto extraído
        """
        if not PyPDF2:
            raise OCRServiceError("PyPDF2 no está disponible")
        
        try:
            logger.debug("Processing PDF", file_path=file_path)
            
            extracted_text = ""
            page_count = 0
            
            with open(file_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                page_count = len(pdf_reader.pages)
                
                # Limitar número de páginas
                max_pages = min(page_count, settings.PDF_MAX_PAGES)
                
                for page_num in range(max_pages):
                    try:
                        page = pdf_reader.pages[page_num]
                        text = page.extract_text()
                        
                        if text.strip():
                            extracted_text += f"\n--- Página {page_num + 1} ---\n{text}\n"
                    
                    except Exception as e:
                        logger.warning("Failed to extract text from page",
                                     page_num=page_num,
                                     error=str(e))
                        continue
            
            # Limpiar texto extraído
            cleaned_text = self._clean_extracted_text(extracted_text)
            
            # Calcular "confianza" basada en la cantidad de texto
            confidence = min(len(cleaned_text) / 100.0, 1.0)  # Heurística simple
            
            return OCRResult(
                text=cleaned_text,
                confidence=confidence,
                page_count=page_count,
                processing_time_ms=0,  # Se actualizará después
                language_detected="spa"  # Asumimos español
            )
            
        except Exception as e:
            logger.error("PDF processing failed", file_path=file_path, error=str(e))
            raise OCRServiceError(f"Error procesando PDF: {str(e)}")
    
    async def _process_image(self, file_path: str) -> OCRResult:
        """
        Procesar imagen con OCR para extraer texto.
        
        Args:
            file_path: Ruta al archivo de imagen
            
        Returns:
            Resultado con texto extraído y confianza
        """
        if not pytesseract or not Image:
            raise OCRServiceError("pytesseract/Pillow no está disponible")
        
        try:
            logger.debug("Processing image with OCR", file_path=file_path)
            
            # Abrir imagen
            with Image.open(file_path) as image:
                # Configurar parámetros de OCR
                custom_config = f'--oem 3 --psm 6 -l {settings.OCR_LANGUAGE}'
                
                # Extraer texto con OCR
                extracted_text = pytesseract.image_to_string(
                    image, 
                    config=custom_config
                )
                
                # Obtener datos de confianza
                try:
                    ocr_data = pytesseract.image_to_data(
                        image, 
                        config=custom_config,
                        output_type=pytesseract.Output.DICT
                    )
                    
                    # Calcular confianza promedio
                    confidences = [int(conf) for conf in ocr_data['conf'] if int(conf) > 0]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                    confidence = avg_confidence / 100.0
                    
                except Exception as e:
                    logger.warning("Failed to get OCR confidence", error=str(e))
                    confidence = 0.5  # Confianza por defecto
            
            # Limpiar texto extraído
            cleaned_text = self._clean_extracted_text(extracted_text)
            
            # Validar confianza mínima
            if confidence < (settings.OCR_MIN_CONFIDENCE / 100.0):
                logger.warning("OCR confidence below threshold",
                              confidence=confidence,
                              threshold=settings.OCR_MIN_CONFIDENCE / 100.0)
            
            return OCRResult(
                text=cleaned_text,
                confidence=confidence,
                page_count=1,  # Una imagen = una "página"
                processing_time_ms=0,  # Se actualizará después
                language_detected=settings.OCR_LANGUAGE
            )
            
        except Exception as e:
            logger.error("Image OCR processing failed", file_path=file_path, error=str(e))
            raise OCRServiceError(f"Error procesando imagen con OCR: {str(e)}")
    
    def _clean_extracted_text(self, text: str) -> str:
        """
        Limpiar y normalizar texto extraído.
        
        Args:
            text: Texto sin procesar
            
        Returns:
            Texto limpio y normalizado
        """
        if not text:
            return ""
        
        try:
            # Remover caracteres de control y espacios extra
            cleaned = " ".join(text.split())
            
            # Remover líneas muy cortas (probablemente ruido OCR)
            lines = cleaned.split('\n')
            meaningful_lines = [line.strip() for line in lines if len(line.strip()) > 3]
            
            # Reconstruir texto
            result = '\n'.join(meaningful_lines)
            
            # Limitar longitud total
            max_length = 50000  # 50K caracteres máximo
            if len(result) > max_length:
                result = result[:max_length] + "... [texto truncado]"
            
            return result
            
        except Exception as e:
            logger.warning("Text cleaning failed", error=str(e))
            return text  # Retornar texto original si falla limpieza
    
    async def _extract_medical_metadata(self, text: str) -> DocumentMetadata:
        """
        Extraer metadata médica usando IA.
        
        Args:
            text: Texto del documento
            
        Returns:
            Metadata médica extraída
        """
        try:
            logger.debug("Extracting medical metadata", text_length=len(text))
            
            # Prompt especializado para documentos médicos
            prompt = f"""
Analiza este documento médico en español y extrae la siguiente información:

DOCUMENTO:
{text[:4000]}  # Limitar para evitar tokens excesivos

INSTRUCCIONES:
Extrae ÚNICAMENTE la información que esté explícitamente mencionada en el documento.
Si algún campo no está presente, usa null.

FORMATO DE RESPUESTA (JSON):
{{
    "patient_name": "nombre del paciente si se menciona",
    "document_date": "fecha del documento en formato YYYY-MM-DD si se encuentra",
    "document_type": "tipo de documento (examen, receta, consulta, etc.)",
    "medical_conditions": ["lista", "de", "condiciones", "médicas", "encontradas"],
    "medications": ["lista", "de", "medicamentos", "mencionados"],
    "medical_procedures": ["lista", "de", "procedimientos", "o", "exámenes", "realizados"]
}}

Responde ÚNICAMENTE con el JSON válido, sin explicaciones adicionales.
"""
            
            # Llamar a OpenAI para extracción
            response = await self.openai_service._call_openai_api([
                {
                    "role": "system", 
                    "content": "Eres un asistente médico especializado en extraer información estructurada de documentos médicos. Responde únicamente con JSON válido."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ])
            
            # Parsear respuesta JSON
            try:
                metadata_dict = json.loads(response.strip())
                
                # Crear objeto DocumentMetadata
                metadata = DocumentMetadata(
                    patient_name=metadata_dict.get("patient_name"),
                    document_date=metadata_dict.get("document_date"),
                    document_type=metadata_dict.get("document_type"),
                    medical_conditions=metadata_dict.get("medical_conditions", []),
                    medications=metadata_dict.get("medications", []),
                    medical_procedures=metadata_dict.get("medical_procedures", [])
                )
                
                logger.info("Medical metadata extracted successfully",
                           patient_name=metadata.patient_name,
                           document_type=metadata.document_type,
                           conditions_count=len(metadata.medical_conditions))
                
                return metadata
                
            except json.JSONDecodeError as e:
                logger.error("Failed to parse AI response as JSON", 
                            response=response[:200], 
                            error=str(e))
                # Retornar metadata vacía si falla el parsing
                return DocumentMetadata()
            
        except Exception as e:
            logger.error("Medical metadata extraction failed", error=str(e))
            # Retornar metadata vacía en caso de error
            return DocumentMetadata()
    
    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Validar archivo antes de procesamiento.
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            Tupla (es_válido, mensaje_error)
        """
        try:
            # Verificar que el archivo existe
            if not os.path.exists(file_path):
                return False, "Archivo no encontrado"
            
            # Verificar tamaño
            file_size = os.path.getsize(file_path)
            max_size = settings.DOCUMENT_MAX_SIZE_MB * 1024 * 1024
            
            if file_size > max_size:
                return False, f"Archivo demasiado grande ({file_size / 1024 / 1024:.1f}MB). Máximo: {settings.DOCUMENT_MAX_SIZE_MB}MB"
            
            if file_size == 0:
                return False, "Archivo vacío"
            
            # Verificar tipo de archivo
            try:
                file_type = self.detect_file_type(file_path)
                logger.debug("File validated", file_path=file_path, type=file_type, size_mb=file_size / 1024 / 1024)
                return True, "Archivo válido"
            
            except OCRServiceError as e:
                return False, str(e)
            
        except Exception as e:
            logger.error("File validation failed", file_path=file_path, error=str(e))
            return False, f"Error validando archivo: {str(e)}"


# Singleton service instance
_ocr_service_instance: Optional[OCRService] = None


def get_ocr_service() -> OCRService:
    """Obtener instancia singleton del servicio OCR."""
    global _ocr_service_instance
    
    if _ocr_service_instance is None:
        _ocr_service_instance = OCRService()
    
    return _ocr_service_instance


# Función de conveniencia para procesamiento rápido
async def process_document_file(
    file_path: str, 
    original_filename: str
) -> Tuple[OCRResult, Optional[DocumentMetadata]]:
    """
    Función de conveniencia para procesar un documento.
    
    Args:
        file_path: Ruta al archivo
        original_filename: Nombre original del archivo
        
    Returns:
        Tupla con resultado OCR y metadata
    """
    ocr_service = get_ocr_service()
    return await ocr_service.process_document(file_path, original_filename)
