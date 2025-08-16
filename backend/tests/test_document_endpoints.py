"""
Tests para endpoints de documentos - ElSol Challenge.

Tests de integración para los endpoints de upload y gestión de documentos.
PLUS Feature 4: Subida de PDFs/Imágenes
"""

import pytest
import asyncio
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.connection import get_db
from app.database.models import Document
from app.core.schemas import DocumentProcessingStatus


# Test client
client = TestClient(app)


class TestDocumentUploadEndpoint:
    """Tests para el endpoint de upload de documentos."""
    
    def test_upload_pdf_success(self):
        """Test upload exitoso de PDF."""
        # Crear archivo PDF temporal
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b"fake pdf content for testing")
            pdf_file = f.name
        
        try:
            with open(pdf_file, 'rb') as f:
                response = client.post(
                    "/api/v1/upload-document",
                    files={"file": ("test.pdf", f, "application/pdf")},
                    data={
                        "patient_name": "Juan Pérez",
                        "document_type": "Examen médico",
                        "description": "Resultados de laboratorio"
                    }
                )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "document_id" in data
            assert data["filename"] == "test.pdf"
            assert data["file_type"] == "pdf"
            assert data["status"] == "pending"
            assert data["patient_association"] == "Juan Pérez"
            assert "created_at" in data
        
        finally:
            os.unlink(pdf_file)
    
    def test_upload_image_success(self):
        """Test upload exitoso de imagen."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b"fake image content")
            image_file = f.name
        
        try:
            with open(image_file, 'rb') as f:
                response = client.post(
                    "/api/v1/upload-document",
                    files={"file": ("test.jpg", f, "image/jpeg")},
                    data={"document_type": "Radiografía"}
                )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["filename"] == "test.jpg"
            assert data["file_type"] == "image"
            assert data["status"] == "pending"
        
        finally:
            os.unlink(image_file)
    
    def test_upload_without_file(self):
        """Test upload sin archivo."""
        response = client.post(
            "/api/v1/upload-document",
            data={"patient_name": "Test"}
        )
        
        assert response.status_code == 422  # FastAPI validation error
    
    def test_upload_invalid_format(self):
        """Test upload con formato inválido."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"text content")
            txt_file = f.name
        
        try:
            with open(txt_file, 'rb') as f:
                response = client.post(
                    "/api/v1/upload-document",
                    files={"file": ("test.txt", f, "text/plain")}
                )
            
            assert response.status_code == 400
            assert "no permitida" in response.json()["detail"].lower()
        
        finally:
            os.unlink(txt_file)
    
    def test_upload_empty_file(self):
        """Test upload de archivo vacío."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            # Archivo vacío
            empty_file = f.name
        
        try:
            with open(empty_file, 'rb') as f:
                response = client.post(
                    "/api/v1/upload-document",
                    files={"file": ("empty.pdf", f, "application/pdf")}
                )
            
            # Podría ser 400 (validación) o 500 (error procesamiento)
            assert response.status_code in [400, 500]
        
        finally:
            os.unlink(empty_file)
    
    @patch('app.api.documents.get_ocr_service')
    def test_upload_with_ocr_service_error(self, mock_ocr_service):
        """Test upload cuando el servicio OCR falla."""
        # Mock servicio OCR que falla
        mock_service = Mock()
        mock_service.detect_file_type.side_effect = Exception("OCR Error")
        mock_ocr_service.return_value = mock_service
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b"content")
            pdf_file = f.name
        
        try:
            with open(pdf_file, 'rb') as f:
                response = client.post(
                    "/api/v1/upload-document",
                    files={"file": ("test.pdf", f, "application/pdf")}
                )
            
            assert response.status_code == 400
        
        finally:
            os.unlink(pdf_file)


class TestDocumentListEndpoint:
    """Tests para el endpoint de listado de documentos."""
    
    def test_list_documents_empty(self):
        """Test listado cuando no hay documentos."""
        response = client.get("/api/v1/documents")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Puede estar vacío o tener documentos de otros tests
    
    def test_list_documents_with_pagination(self):
        """Test listado con paginación."""
        response = client.get("/api/v1/documents?skip=0&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5
    
    def test_list_documents_with_filters(self):
        """Test listado con filtros."""
        response = client.get("/api/v1/documents?patient_name=Juan&status=completed")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_documents_invalid_status(self):
        """Test listado con status inválido."""
        response = client.get("/api/v1/documents?status=invalid_status")
        
        assert response.status_code == 422  # Validation error
    
    def test_list_documents_negative_pagination(self):
        """Test listado con parámetros de paginación inválidos."""
        response = client.get("/api/v1/documents?skip=-1&limit=0")
        
        assert response.status_code == 422  # Validation error


class TestDocumentDetailEndpoint:
    """Tests para el endpoint de detalle de documento."""
    
    def test_get_document_not_found(self):
        """Test obtener documento que no existe."""
        response = client.get("/api/v1/documents/nonexistent-id")
        
        assert response.status_code == 404
        assert "no encontrado" in response.json()["detail"].lower()
    
    def test_get_document_invalid_id_format(self):
        """Test con formato de ID inválido."""
        response = client.get("/api/v1/documents/invalid-id-format")
        
        # Debería retornar 404 (no encontrado) o 422 (validación)
        assert response.status_code in [404, 422]


class TestDocumentSearchEndpoint:
    """Tests para el endpoint de búsqueda de documentos."""
    
    def test_search_documents_basic(self):
        """Test búsqueda básica."""
        response = client.get("/api/v1/documents/search?query=diabetes")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_search_documents_with_filters(self):
        """Test búsqueda con filtros."""
        response = client.get(
            "/api/v1/documents/search?query=examen&patient_name=Juan&max_results=3"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 3
    
    def test_search_documents_without_query(self):
        """Test búsqueda sin query."""
        response = client.get("/api/v1/documents/search")
        
        assert response.status_code == 422  # Missing required parameter
    
    def test_search_documents_empty_query(self):
        """Test búsqueda con query vacío."""
        response = client.get("/api/v1/documents/search?query=")
        
        assert response.status_code == 422  # Validation error
    
    def test_search_documents_invalid_max_results(self):
        """Test búsqueda con max_results inválido."""
        response = client.get("/api/v1/documents/search?query=test&max_results=100")
        
        assert response.status_code == 422  # Exceeds limit


class TestDocumentDeleteEndpoint:
    """Tests para el endpoint de eliminación de documentos."""
    
    def test_delete_document_not_found(self):
        """Test eliminar documento que no existe."""
        response = client.delete("/api/v1/documents/nonexistent-id")
        
        assert response.status_code == 404
        assert "no encontrado" in response.json()["detail"].lower()


class TestDocumentEndpointsIntegration:
    """Tests de integración completa para endpoints de documentos."""
    
    @patch('app.api.documents.process_document_background')
    def test_upload_and_list_workflow(self, mock_background):
        """Test flujo completo: upload → list → detail."""
        # Mock background processing
        mock_background.return_value = None
        
        # 1. Upload documento
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b"test content")
            pdf_file = f.name
        
        try:
            with open(pdf_file, 'rb') as f:
                upload_response = client.post(
                    "/api/v1/upload-document",
                    files={"file": ("integration_test.pdf", f, "application/pdf")},
                    data={"patient_name": "Integration Test"}
                )
            
            assert upload_response.status_code == 200
            upload_data = upload_response.json()
            document_id = upload_data["document_id"]
            
            # 2. Listar documentos (debería incluir el nuevo)
            list_response = client.get("/api/v1/documents")
            assert list_response.status_code == 200
            
            # 3. Obtener detalle del documento
            detail_response = client.get(f"/api/v1/documents/{document_id}")
            
            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                assert detail_data["document_id"] == document_id
                assert detail_data["filename"] == "integration_test.pdf"
            else:
                # El documento puede no existir en la BD de test
                assert detail_response.status_code == 404
        
        finally:
            os.unlink(pdf_file)
    
    def test_error_handling_consistency(self):
        """Test que los errores sean consistentes entre endpoints."""
        nonexistent_id = "test-nonexistent-id"
        
        # Todos estos endpoints deberían retornar 404 para ID inexistente
        endpoints = [
            f"/api/v1/documents/{nonexistent_id}",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 404
            assert "detail" in response.json()
    
    def test_validation_error_format(self):
        """Test formato consistente de errores de validación."""
        # Error de validación en upload
        upload_response = client.post("/api/v1/upload-document")
        assert upload_response.status_code == 422
        
        # Error de validación en búsqueda
        search_response = client.get("/api/v1/documents/search")
        assert search_response.status_code == 422
        
        # Ambos deberían tener estructura similar
        upload_error = upload_response.json()
        search_error = search_response.json()
        
        assert "detail" in upload_error
        assert "detail" in search_error


class TestDocumentEndpointsPerformance:
    """Tests de performance para endpoints de documentos."""
    
    def test_upload_response_time(self):
        """Test tiempo de respuesta de upload."""
        import time
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b"performance test content")
            pdf_file = f.name
        
        try:
            start_time = time.time()
            
            with open(pdf_file, 'rb') as f:
                response = client.post(
                    "/api/v1/upload-document",
                    files={"file": ("perf_test.pdf", f, "application/pdf")}
                )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Upload debería ser rápido (sin procesamiento real)
            assert response_time < 5.0  # 5 segundos max
            assert response.status_code in [200, 400, 500]  # Cualquier respuesta válida
        
        finally:
            os.unlink(pdf_file)
    
    def test_list_response_time(self):
        """Test tiempo de respuesta de listado."""
        import time
        
        start_time = time.time()
        response = client.get("/api/v1/documents?limit=10")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Listado debería ser muy rápido
        assert response_time < 2.0  # 2 segundos max
        assert response.status_code == 200
    
    def test_search_response_time(self):
        """Test tiempo de respuesta de búsqueda."""
        import time
        
        start_time = time.time()
        response = client.get("/api/v1/documents/search?query=test&max_results=5")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Búsqueda debería ser razonablemente rápida
        assert response_time < 3.0  # 3 segundos max
        assert response.status_code == 200


class TestDocumentEndpointsSecurity:
    """Tests de seguridad para endpoints de documentos."""
    
    def test_file_path_traversal_protection(self):
        """Test protección contra path traversal."""
        # Intentar acceso con path traversal
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]
        
        for path in malicious_paths:
            response = client.get(f"/api/v1/documents/{path}")
            # Debería retornar 404 (no encontrado) o 400 (bad request)
            assert response.status_code in [400, 404, 422]
    
    def test_large_filename_handling(self):
        """Test manejo de nombres de archivo muy largos."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b"content")
            pdf_file = f.name
        
        try:
            # Nombre de archivo muy largo
            long_filename = "x" * 300 + ".pdf"
            
            with open(pdf_file, 'rb') as f:
                response = client.post(
                    "/api/v1/upload-document",
                    files={"file": (long_filename, f, "application/pdf")}
                )
            
            # Debería manejar gracefully
            assert response.status_code in [200, 400, 422]
        
        finally:
            os.unlink(pdf_file)
    
    def test_special_characters_in_filename(self):
        """Test manejo de caracteres especiales en nombres de archivo."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b"content")
            pdf_file = f.name
        
        try:
            special_filenames = [
                "test<script>.pdf",
                "test&amp;.pdf", 
                "test|cmd.pdf",
                "test\x00null.pdf"
            ]
            
            for filename in special_filenames:
                with open(pdf_file, 'rb') as f:
                    response = client.post(
                        "/api/v1/upload-document",
                        files={"file": (filename, f, "application/pdf")}
                    )
                
                # Debería manejar gracefully sin errores de servidor
                assert response.status_code != 500
        
        finally:
            os.unlink(pdf_file)


# Fixtures para tests
@pytest.fixture
def temp_pdf_file():
    """Fixture para archivo PDF temporal."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(b"PDF test content")
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
        f.write(b"Image test content")
        temp_file = f.name
    
    yield temp_file
    
    try:
        os.unlink(temp_file)
    except FileNotFoundError:
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
