"""
Tests para el servicio OCR - ElSol Challenge.

Tests para procesamiento de PDFs e imágenes con OCR.
PLUS Feature 4: Subida de PDFs/Imágenes
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from app.services.ocr_service import get_ocr_service, OCRService, OCRServiceError
from app.core.schemas import OCRResult, DocumentMetadata
from app.core.config import get_settings


class TestOCRService:
    """Tests para el servicio OCR."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.ocr_service = get_ocr_service()
        self.settings = get_settings()
    
    def test_ocr_service_singleton(self):
        """Test que el servicio sea singleton."""
        service1 = get_ocr_service()
        service2 = get_ocr_service()
        assert service1 is service2
    
    def test_detect_file_type_pdf(self):
        """Test detección de archivos PDF."""
        # Crear archivo PDF temporal
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_file = f.name
            f.write(b"fake pdf content")
        
        try:
            file_type = self.ocr_service.detect_file_type(pdf_file)
            assert file_type == "pdf"
        finally:
            os.unlink(pdf_file)
    
    def test_detect_file_type_image(self):
        """Test detección de archivos de imagen."""
        image_extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.tif']
        
        for ext in image_extensions:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                image_file = f.name
                f.write(b"fake image content")
            
            try:
                file_type = self.ocr_service.detect_file_type(image_file)
                assert file_type == "image"
            finally:
                os.unlink(image_file)
    
    def test_detect_file_type_unsupported(self):
        """Test detección de archivos no soportados."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            txt_file = f.name
            f.write(b"text content")
        
        try:
            with pytest.raises(OCRServiceError):
                self.ocr_service.detect_file_type(txt_file)
        finally:
            os.unlink(txt_file)
    
    def test_validate_file_success(self):
        """Test validación exitosa de archivo."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_file = f.name
            f.write(b"fake pdf content")
        
        try:
            is_valid, message = self.ocr_service.validate_file(pdf_file)
            assert is_valid is True
            assert "válido" in message.lower()
        finally:
            os.unlink(pdf_file)
    
    def test_validate_file_not_found(self):
        """Test validación de archivo que no existe."""
        is_valid, message = self.ocr_service.validate_file("nonexistent.pdf")
        assert is_valid is False
        assert "no encontrado" in message.lower()
    
    def test_validate_file_empty(self):
        """Test validación de archivo vacío."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            empty_file = f.name
            # Archivo vacío
        
        try:
            is_valid, message = self.ocr_service.validate_file(empty_file)
            assert is_valid is False
            assert "vacío" in message.lower()
        finally:
            os.unlink(empty_file)
    
    def test_validate_file_too_large(self):
        """Test validación de archivo demasiado grande."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            large_file = f.name
            # Crear archivo > 10MB
            large_content = b"x" * (11 * 1024 * 1024)  # 11MB
            f.write(large_content)
        
        try:
            is_valid, message = self.ocr_service.validate_file(large_file)
            assert is_valid is False
            assert "demasiado grande" in message.lower()
        finally:
            os.unlink(large_file)
    
    def test_clean_extracted_text(self):
        """Test limpieza de texto extraído."""
        # Texto con espacios extra y líneas cortas
        dirty_text = "   Texto   con   espacios   \n\na\nb\n   Línea normal   \n\n"
        
        cleaned = self.ocr_service._clean_extracted_text(dirty_text)
        
        assert "Texto con espacios" in cleaned
        assert "Línea normal" in cleaned
        # Las líneas muy cortas deberían ser removidas
        assert cleaned.count('\n') < dirty_text.count('\n')
    
    def test_clean_extracted_text_empty(self):
        """Test limpieza de texto vacío."""
        result = self.ocr_service._clean_extracted_text("")
        assert result == ""
        
        result = self.ocr_service._clean_extracted_text(None)
        assert result == ""
    
    def test_clean_extracted_text_very_long(self):
        """Test limpieza de texto muy largo."""
        # Texto > 50K caracteres
        long_text = "x" * 60000
        
        cleaned = self.ocr_service._clean_extracted_text(long_text)
        assert len(cleaned) <= 50000
        assert "truncado" in cleaned
    
    @patch('app.services.ocr_service.PyPDF2')
    @pytest.mark.asyncio
    async def test_process_pdf_success(self, mock_pypdf2):
        """Test procesamiento exitoso de PDF."""
        # Mock PyPDF2
        mock_reader = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "Contenido del PDF médico\nPaciente: Juan Pérez"
        mock_reader.pages = [mock_page]
        mock_pypdf2.PdfReader.return_value = mock_reader
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_file = f.name
            f.write(b"fake pdf content")
        
        try:
            result = await self.ocr_service._process_pdf(pdf_file)
            
            assert isinstance(result, OCRResult)
            assert "PDF médico" in result.text
            assert result.page_count == 1
            assert result.confidence > 0
            assert result.language_detected == "spa"
        finally:
            os.unlink(pdf_file)
    
    @patch('app.services.ocr_service.pytesseract')
    @patch('app.services.ocr_service.Image')
    @pytest.mark.asyncio
    async def test_process_image_success(self, mock_image, mock_tesseract):
        """Test procesamiento exitoso de imagen con OCR."""
        # Mock Tesseract
        mock_tesseract.image_to_string.return_value = "Texto extraído de imagen médica"
        mock_tesseract.image_to_data.return_value = {
            'conf': ['80', '85', '90'],
            'text': ['Texto', 'extraído', 'imagen']
        }
        mock_tesseract.Output.DICT = 'dict'
        
        # Mock PIL Image
        mock_img = Mock()
        mock_image.open.return_value.__enter__.return_value = mock_img
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            image_file = f.name
            f.write(b"fake image content")
        
        try:
            result = await self.ocr_service._process_image(image_file)
            
            assert isinstance(result, OCRResult)
            assert "imagen médica" in result.text
            assert result.page_count == 1
            assert 0 <= result.confidence <= 1
            assert result.language_detected == self.settings.OCR_LANGUAGE
        finally:
            os.unlink(image_file)
    
    @patch('app.services.ocr_service.get_openai_service')
    @pytest.mark.asyncio
    async def test_extract_medical_metadata_success(self, mock_openai):
        """Test extracción exitosa de metadata médica."""
        # Mock OpenAI service
        mock_openai_service = Mock()
        mock_openai_service._call_openai_api = AsyncMock(return_value='''
        {
            "patient_name": "Juan Pérez",
            "document_date": "2024-01-15",
            "document_type": "Examen médico",
            "medical_conditions": ["diabetes", "hipertensión"],
            "medications": ["metformina", "losartán"],
            "medical_procedures": ["glucosa en sangre", "presión arterial"]
        }
        ''')
        mock_openai.return_value = mock_openai_service
        
        text = "Examen médico de Juan Pérez. Fecha: 15/01/2024. Diagnóstico: diabetes."
        
        metadata = await self.ocr_service._extract_medical_metadata(text)
        
        assert isinstance(metadata, DocumentMetadata)
        assert metadata.patient_name == "Juan Pérez"
        assert metadata.document_date == "2024-01-15"
        assert metadata.document_type == "Examen médico"
        assert "diabetes" in metadata.medical_conditions
        assert "metformina" in metadata.medications
    
    @patch('app.services.ocr_service.get_openai_service')
    @pytest.mark.asyncio
    async def test_extract_medical_metadata_invalid_json(self, mock_openai):
        """Test manejo de JSON inválido en extracción de metadata."""
        # Mock OpenAI service con respuesta inválida
        mock_openai_service = Mock()
        mock_openai_service._call_openai_api = AsyncMock(return_value="invalid json response")
        mock_openai.return_value = mock_openai_service
        
        metadata = await self.ocr_service._extract_medical_metadata("texto médico")
        
        # Debería retornar metadata vacía en caso de error
        assert isinstance(metadata, DocumentMetadata)
        assert metadata.patient_name is None
        assert metadata.medical_conditions == []
    
    @patch('app.services.ocr_service.PyPDF2')
    @patch('app.services.ocr_service.get_openai_service')
    @pytest.mark.asyncio
    async def test_process_document_complete_workflow(self, mock_openai, mock_pypdf2):
        """Test flujo completo de procesamiento de documento."""
        # Mock PDF processing
        mock_reader = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "Informe médico completo"
        mock_reader.pages = [mock_page]
        mock_pypdf2.PdfReader.return_value = mock_reader
        
        # Mock metadata extraction
        mock_openai_service = Mock()
        mock_openai_service._call_openai_api = AsyncMock(return_value='{"patient_name": "Test Patient"}')
        mock_openai.return_value = mock_openai_service
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_file = f.name
            f.write(b"fake pdf content")
        
        try:
            ocr_result, metadata = await self.ocr_service.process_document(pdf_file, "test.pdf")
            
            # Verificar OCR result
            assert isinstance(ocr_result, OCRResult)
            assert "médico" in ocr_result.text
            assert ocr_result.processing_time_ms > 0
            
            # Verificar metadata
            assert isinstance(metadata, DocumentMetadata)
            
        finally:
            os.unlink(pdf_file)


class TestOCRServiceDependencies:
    """Tests para manejo de dependencias del servicio OCR."""
    
    @patch('app.services.ocr_service.PyPDF2', None)
    def test_missing_pypdf2_dependency(self):
        """Test comportamiento cuando falta PyPDF2."""
        # El servicio debería inicializar pero mostrar warning
        service = OCRService()
        assert service is not None
    
    @patch('app.services.ocr_service.pytesseract', None)
    def test_missing_tesseract_dependency(self):
        """Test comportamiento cuando falta Tesseract."""
        service = OCRService()
        assert service is not None
    
    @patch('app.services.ocr_service.PyPDF2', None)
    @pytest.mark.asyncio
    async def test_process_pdf_without_pypdf2(self):
        """Test procesamiento PDF sin PyPDF2."""
        service = OCRService()
        
        with tempfile.NamedTemporaryFile(suffix='.pdf') as f:
            with pytest.raises(OCRServiceError):
                await service._process_pdf(f.name)
    
    @patch('app.services.ocr_service.pytesseract', None)
    @pytest.mark.asyncio
    async def test_process_image_without_tesseract(self):
        """Test procesamiento imagen sin Tesseract."""
        service = OCRService()
        
        with tempfile.NamedTemporaryFile(suffix='.jpg') as f:
            with pytest.raises(OCRServiceError):
                await service._process_image(f.name)


class TestOCRPerformance:
    """Tests de performance para OCR."""
    
    @pytest.mark.asyncio
    async def test_processing_timeout(self):
        """Test que el procesamiento no exceda timeouts razonables."""
        import asyncio
        
        with patch('app.services.ocr_service.PyPDF2') as mock_pypdf2:
            # Mock procesamiento rápido
            mock_reader = Mock()
            mock_page = Mock()
            mock_page.extract_text.return_value = "Texto rápido"
            mock_reader.pages = [mock_page]
            mock_pypdf2.PdfReader.return_value = mock_reader
            
            service = get_ocr_service()
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                pdf_file = f.name
                f.write(b"content")
            
            try:
                start_time = asyncio.get_event_loop().time()
                await service._process_pdf(pdf_file)
                end_time = asyncio.get_event_loop().time()
                
                processing_time = end_time - start_time
                assert processing_time < 5  # Debería ser rápido con mock
            finally:
                os.unlink(pdf_file)
    
    def test_large_text_handling(self):
        """Test manejo de textos muy largos."""
        service = get_ocr_service()
        
        # Texto de 100K caracteres
        large_text = "x" * 100000
        
        cleaned = service._clean_extracted_text(large_text)
        
        # Debería estar truncado
        assert len(cleaned) <= 50000
        assert "truncado" in cleaned


# Fixtures para tests
@pytest.fixture
def temp_pdf_file():
    """Fixture para archivo PDF temporal."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(b"fake pdf content")
        temp_file = f.name
    
    yield temp_file
    
    try:
        os.unlink(temp_file)
    except FileNotFoundError:
        pass


@pytest.fixture
def temp_image_file():
    """Fixture para archivo de imagen temporal."""
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        f.write(b"fake image content")
        temp_file = f.name
    
    yield temp_file
    
    try:
        os.unlink(temp_file)
    except FileNotFoundError:
        pass


@pytest.fixture
def mock_successful_pdf_processing():
    """Fixture para mock de procesamiento PDF exitoso."""
    with patch('app.services.ocr_service.PyPDF2') as mock:
        reader = Mock()
        page = Mock()
        page.extract_text.return_value = "Contenido PDF de prueba"
        reader.pages = [page]
        mock.PdfReader.return_value = reader
        yield mock


@pytest.fixture
def mock_successful_ocr_processing():
    """Fixture para mock de OCR exitoso."""
    with patch('app.services.ocr_service.pytesseract') as mock_tesseract, \
         patch('app.services.ocr_service.Image') as mock_image:
        
        mock_tesseract.image_to_string.return_value = "Texto OCR de prueba"
        mock_tesseract.image_to_data.return_value = {'conf': ['85']}
        mock_tesseract.Output.DICT = 'dict'
        
        mock_img = Mock()
        mock_image.open.return_value.__enter__.return_value = mock_img
        
        yield mock_tesseract, mock_image


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
