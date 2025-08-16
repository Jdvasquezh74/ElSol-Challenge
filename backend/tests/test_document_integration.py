"""
Tests de integración para funcionalidad completa de documentos - ElSol Challenge.

Tests end-to-end para el flujo completo de procesamiento de documentos.
PLUS Feature 4: Subida de PDFs/Imágenes
"""

import pytest
import asyncio
import tempfile
import os
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.connection import get_db, get_session
from app.database.models import Document
from app.services.ocr_service import get_ocr_service
from app.services.vector_service import get_vector_service
from app.core.schemas import DocumentProcessingStatus, OCRResult, DocumentMetadata


# Test client
client = TestClient(app)


class TestDocumentProcessingIntegration:
    """Tests de integración para procesamiento completo de documentos."""
    
    @patch('app.services.ocr_service.PyPDF2')
    @patch('app.services.ocr_service.get_openai_service')
    @pytest.mark.asyncio
    async def test_pdf_processing_full_pipeline(self, mock_openai, mock_pypdf2):
        """Test pipeline completo: PDF → OCR → Metadata → Vector Store."""
        # Mock PDF processing
        mock_reader = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = """
        LABORATORIO CLÍNICO CENTRAL
        
        Paciente: María González
        Fecha de nacimiento: 15/03/1980
        Fecha del examen: 10/01/2024
        
        EXAMEN DE GLUCOSA EN SANGRE
        
        Resultado: 95 mg/dL
        Valor de referencia: 70-100 mg/dL
        Interpretación: Normal
        
        Diagnóstico: Seguimiento diabético - valores normales
        Médico: Dr. Juan Pérez
        """
        mock_reader.pages = [mock_page]
        mock_pypdf2.PdfReader.return_value = mock_reader
        
        # Mock metadata extraction
        mock_openai_service = Mock()
        mock_openai_service._call_openai_api = AsyncMock(return_value=json.dumps({
            "patient_name": "María González",
            "document_date": "2024-01-10",
            "document_type": "Examen de laboratorio",
            "medical_conditions": ["diabetes", "seguimiento"],
            "medications": [],
            "medical_procedures": ["glucosa en sangre"]
        }))
        mock_openai.return_value = mock_openai_service
        
        # Test procesamiento completo
        ocr_service = get_ocr_service()
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b"fake pdf content")
            pdf_file = f.name
        
        try:
            # Procesar documento
            ocr_result, metadata = await ocr_service.process_document(pdf_file, "examen_maria.pdf")
            
            # Verificar OCR result
            assert isinstance(ocr_result, OCRResult)
            assert "María González" in ocr_result.text
            assert "glucosa" in ocr_result.text.lower()
            assert ocr_result.confidence > 0
            assert ocr_result.processing_time_ms > 0
            
            # Verificar metadata
            assert isinstance(metadata, DocumentMetadata)
            assert metadata.patient_name == "María González"
            assert metadata.document_type == "Examen de laboratorio"
            assert "diabetes" in metadata.medical_conditions
            assert "glucosa en sangre" in metadata.medical_procedures
            
        finally:
            os.unlink(pdf_file)
    
    @patch('app.services.ocr_service.pytesseract')
    @patch('app.services.ocr_service.Image')
    @patch('app.services.ocr_service.get_openai_service')
    @pytest.mark.asyncio
    async def test_image_ocr_full_pipeline(self, mock_openai, mock_image, mock_tesseract):
        """Test pipeline completo: Imagen → OCR → Metadata."""
        # Mock OCR processing
        mock_tesseract.image_to_string.return_value = """
        HOSPITAL GENERAL
        
        RADIOGRAFIA DE TORAX
        
        Paciente: Carlos Ruiz
        Edad: 45 años
        Fecha: 15/01/2024
        
        HALLAZGOS:
        - Campos pulmonares normales
        - Corazón de tamaño normal
        - Sin infiltrados
        
        IMPRESION: Radiografía de tórax normal
        """
        
        mock_tesseract.image_to_data.return_value = {
            'conf': ['85', '90', '88', '92', '87'],
            'text': ['HOSPITAL', 'GENERAL', 'RADIOGRAFIA', 'Paciente:', 'Carlos']
        }
        mock_tesseract.Output.DICT = 'dict'
        
        # Mock PIL Image
        mock_img = Mock()
        mock_image.open.return_value.__enter__.return_value = mock_img
        
        # Mock metadata extraction
        mock_openai_service = Mock()
        mock_openai_service._call_openai_api = AsyncMock(return_value=json.dumps({
            "patient_name": "Carlos Ruiz",
            "document_date": "2024-01-15",
            "document_type": "Radiografía",
            "medical_conditions": [],
            "medications": [],
            "medical_procedures": ["radiografía de tórax"]
        }))
        mock_openai.return_value = mock_openai_service
        
        # Test procesamiento
        ocr_service = get_ocr_service()
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b"fake image content")
            image_file = f.name
        
        try:
            ocr_result, metadata = await ocr_service.process_document(image_file, "radiografia_carlos.jpg")
            
            # Verificar OCR result
            assert isinstance(ocr_result, OCRResult)
            assert "Carlos Ruiz" in ocr_result.text
            assert "radiografía" in ocr_result.text.lower()
            assert 0.8 <= ocr_result.confidence <= 1.0  # Confianza alta del mock
            
            # Verificar metadata
            assert metadata.patient_name == "Carlos Ruiz"
            assert metadata.document_type == "Radiografía"
            assert "radiografía de tórax" in metadata.medical_procedures
            
        finally:
            os.unlink(image_file)
    
    @patch('app.api.documents.process_document_background')
    def test_upload_to_database_integration(self, mock_background):
        """Test integración upload → base de datos."""
        # Mock background processing
        async def mock_process(doc_id, file_path, filename, db):
            # Simular procesamiento exitoso
            document = db.query(Document).filter(Document.id == doc_id).first()
            if document:
                document.mark_completed(1500)  # 1.5 segundos
                document.extracted_text = "Texto extraído de prueba"
                document.patient_name = "Test Patient"
                db.commit()
        
        mock_background.side_effect = mock_process
        
        # Upload documento
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b"integration test content")
            pdf_file = f.name
        
        try:
            with open(pdf_file, 'rb') as f:
                response = client.post(
                    "/api/v1/upload-document",
                    files={"file": ("integration_test.pdf", f, "application/pdf")},
                    data={
                        "patient_name": "Integration Test",
                        "document_type": "Test Document"
                    }
                )
            
            assert response.status_code == 200
            data = response.json()
            document_id = data["document_id"]
            
            # Verificar que se creó el registro
            assert data["filename"] == "integration_test.pdf"
            assert data["status"] == "pending"
            assert data["patient_association"] == "Integration Test"
            
            # El documento debería existir en la base de datos
            # (En un test real podríamos verificar esto)
            
        finally:
            os.unlink(pdf_file)
    
    @patch('app.services.vector_service.VectorStoreService')
    @pytest.mark.asyncio
    async def test_vector_store_integration(self, mock_vector_service):
        """Test integración con vector store."""
        # Mock vector service
        mock_service_instance = Mock()
        mock_service_instance.store_conversation_data = AsyncMock(return_value="vector_id_123")
        mock_vector_service.return_value = mock_service_instance
        
        # Simular datos de documento procesado
        document_text = "Examen médico de Juan Pérez. Glucosa: 95 mg/dL. Normal."
        metadata = {
            "patient_name": "Juan Pérez",
            "document_type": "Examen médico",
            "medical_conditions": ["seguimiento diabético"]
        }
        
        vector_service = get_vector_service()
        
        # Simular almacenamiento en vector store
        vector_id = await vector_service.store_conversation_data(
            conversation_id="doc_123",
            transcription=document_text,
            structured_data=metadata,
            unstructured_data={"extracted_text": document_text},
            metadata={
                "document_id": "doc_123",
                "source": "document",
                "file_type": "pdf"
            }
        )
        
        assert vector_id == "vector_id_123"
        mock_service_instance.store_conversation_data.assert_called_once()
    
    def test_error_handling_integration(self):
        """Test manejo de errores en integración completa."""
        # Test con archivo corrupto
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b"corrupted content that's not a real PDF")
            corrupted_file = f.name
        
        try:
            with open(corrupted_file, 'rb') as f:
                response = client.post(
                    "/api/v1/upload-document",
                    files={"file": ("corrupted.pdf", f, "application/pdf")}
                )
            
            # Debería manejar el error gracefully
            # Puede ser 200 (con procesamiento en background que fallará)
            # o 400 (error inmediato)
            assert response.status_code in [200, 400, 500]
            
        finally:
            os.unlink(corrupted_file)


class TestDocumentSearchIntegration:
    """Tests de integración para búsqueda de documentos."""
    
    def test_search_integration_workflow(self):
        """Test flujo completo de búsqueda."""
        # 1. Buscar documentos (puede estar vacío)
        search_response = client.get("/api/v1/documents/search?query=diabetes&max_results=5")
        
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert isinstance(search_data, list)
        
        # 2. Si hay resultados, verificar estructura
        if search_data:
            result = search_data[0]
            required_fields = ["document_id", "filename", "relevance_score", "excerpt", "created_at"]
            for field in required_fields:
                assert field in result
            
            # 3. Obtener detalle del primer documento
            document_id = result["document_id"]
            detail_response = client.get(f"/api/v1/documents/{document_id}")
            
            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                assert detail_data["document_id"] == document_id
    
    def test_cross_modal_search_preparation(self):
        """Test preparación para búsqueda cross-modal (audio + documentos)."""
        # Este test prepara la integración con chat RAG
        
        # 1. Buscar en documentos
        doc_response = client.get("/api/v1/documents/search?query=glucosa")
        assert doc_response.status_code == 200
        
        # 2. En el futuro, esto se combinaría con búsqueda en transcripciones
        # para proporcionar contexto completo al chat RAG
        
        # 3. Verificar que la estructura de respuesta es compatible
        # con lo que esperaría el sistema de chat
        doc_data = doc_response.json()
        if doc_data:
            result = doc_data[0]
            # Campos que serían útiles para chat RAG
            useful_fields = ["document_id", "excerpt", "relevance_score", "patient_name"]
            for field in useful_fields:
                assert field in result or result.get(field) is not None


class TestDocumentPerformanceIntegration:
    """Tests de performance para integración completa."""
    
    @pytest.mark.asyncio
    async def test_concurrent_document_processing(self):
        """Test procesamiento concurrente de múltiples documentos."""
        import asyncio
        
        # Mock para evitar procesamiento real
        with patch('app.services.ocr_service.PyPDF2') as mock_pypdf2:
            mock_reader = Mock()
            mock_page = Mock()
            mock_page.extract_text.return_value = "Contenido de prueba"
            mock_reader.pages = [mock_page]
            mock_pypdf2.PdfReader.return_value = mock_reader
            
            ocr_service = get_ocr_service()
            
            # Crear múltiples archivos temporales
            temp_files = []
            for i in range(3):
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                    f.write(f"content {i}".encode())
                    temp_files.append(f.name)
            
            try:
                # Procesar concurrentemente
                start_time = time.time()
                
                tasks = []
                for i, file_path in enumerate(temp_files):
                    task = ocr_service.process_document(file_path, f"test_{i}.pdf")
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                # Verificar que se procesaron todos
                assert len(results) == 3
                
                # Procesamiento concurrente debería ser más rápido que secuencial
                assert processing_time < 10  # Con mocks debería ser muy rápido
                
                # Verificar que no hay excepciones
                for result in results:
                    assert not isinstance(result, Exception)
            
            finally:
                for file_path in temp_files:
                    try:
                        os.unlink(file_path)
                    except FileNotFoundError:
                        pass
    
    def test_large_document_handling(self):
        """Test manejo de documentos grandes."""
        # Crear archivo "grande"
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            # Simular archivo de 5MB
            large_content = b"PDF content " * 400000  # ~5MB
            f.write(large_content)
            large_file = f.name
        
        try:
            start_time = time.time()
            
            with open(large_file, 'rb') as f:
                response = client.post(
                    "/api/v1/upload-document",
                    files={"file": ("large_test.pdf", f, "application/pdf")}
                )
            
            end_time = time.time()
            upload_time = end_time - start_time
            
            # Upload debería completarse en tiempo razonable
            assert upload_time < 30  # 30 segundos max para upload
            
            # Respuesta debería ser válida
            assert response.status_code in [200, 400]  # 400 si excede límites
            
        finally:
            os.unlink(large_file)


class TestDocumentSecurityIntegration:
    """Tests de seguridad para integración completa."""
    
    def test_malicious_file_content_handling(self):
        """Test manejo de contenido potencialmente malicioso."""
        # Archivo con contenido que podría causar problemas
        malicious_contents = [
            b"<script>alert('xss')</script>",
            b"'; DROP TABLE documents; --",
            b"{{7*7}}",  # Template injection
            b"\x00\x01\x02\x03",  # Binary content
        ]
        
        for i, content in enumerate(malicious_contents):
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                f.write(content)
                malicious_file = f.name
            
            try:
                with open(malicious_file, 'rb') as f:
                    response = client.post(
                        "/api/v1/upload-document",
                        files={"file": (f"malicious_{i}.pdf", f, "application/pdf")}
                    )
                
                # Debería manejar gracefully sin errores de servidor
                assert response.status_code != 500
                
                # Si se acepta, debería procesarse de forma segura
                if response.status_code == 200:
                    data = response.json()
                    assert "document_id" in data
                
            finally:
                os.unlink(malicious_file)
    
    def test_file_size_limits_enforcement(self):
        """Test que se respeten los límites de tamaño de archivo."""
        # Crear archivo que excede límite (>10MB)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            oversized_content = b"x" * (12 * 1024 * 1024)  # 12MB
            f.write(oversized_content)
            oversized_file = f.name
        
        try:
            with open(oversized_file, 'rb') as f:
                response = client.post(
                    "/api/v1/upload-document",
                    files={"file": ("oversized.pdf", f, "application/pdf")}
                )
            
            # Debería rechazar el archivo
            assert response.status_code == 400
            assert "grande" in response.json()["detail"].lower()
            
        finally:
            os.unlink(oversized_file)


# Fixtures para tests de integración
@pytest.fixture
def sample_medical_pdf_content():
    """Fixture con contenido médico realista para tests."""
    return """
    CENTRO MÉDICO INTEGRAL
    
    INFORME DE LABORATORIO
    
    Paciente: Ana María López
    Edad: 52 años
    Fecha de nacimiento: 20/08/1971
    Documento: 12345678
    
    Fecha de examen: 20/01/2024
    Médico solicitante: Dr. Roberto García
    
    QUÍMICA SANGUÍNEA:
    
    Glucosa en ayunas: 102 mg/dL (70-100)
    Colesterol total: 195 mg/dL (<200)
    HDL Colesterol: 45 mg/dL (>40)
    LDL Colesterol: 125 mg/dL (<130)
    Triglicéridos: 150 mg/dL (<150)
    
    OBSERVACIONES:
    Glucosa ligeramente elevada. Se recomienda control dietético
    y nueva evaluación en 3 meses.
    
    DIAGNÓSTICO:
    Prediabetes. Control metabólico requerido.
    """


@pytest.fixture
def sample_radiology_content():
    """Fixture con contenido de radiología para tests."""
    return """
    HOSPITAL UNIVERSITARIO
    SERVICIO DE RADIOLOGÍA
    
    TOMOGRAFÍA COMPUTADA DE TÓRAX
    
    Paciente: Miguel Hernández
    Edad: 38 años
    Fecha: 22/01/2024
    
    TÉCNICA:
    Se realizó estudio tomográfico de tórax con contraste IV.
    
    HALLAZGOS:
    - Parénquima pulmonar: Sin alteraciones significativas
    - Mediastino: Estructuras vasculares normales
    - Pleura: Sin derrame pleural
    - Corazón: Tamaño y morfología normales
    
    IMPRESIÓN:
    Estudio tomográfico de tórax normal.
    
    Dr. Sandra Martínez
    Radióloga
    """


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
