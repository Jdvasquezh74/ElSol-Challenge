"""
Tests de integración para Vector Store - ElSol Challenge.

Tests que verifican la integración del vector store con el flujo 
completo de transcripción y almacenamiento.

Requisito 2: Almacenamiento Vectorial
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.vector_service import VectorStoreResponse
from app.core.schemas import VectorStoreStatus, StoredConversation


class TestVectorStoreEndpoints:
    """Tests para endpoints del vector store."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.client = TestClient(app)
    
    @patch('app.services.vector_service.get_vector_service')
    def test_get_vector_store_status_endpoint(self, mock_get_service):
        """Test endpoint de estado del vector store."""
        # Mock del servicio
        mock_service = Mock()
        mock_status = VectorStoreStatus(
            status="operational",
            collection_name="test_conversations",
            total_documents=10,
            total_embeddings=10,
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            persist_directory="./test_chroma_db"
        )
        mock_service.get_vector_store_status = AsyncMock(return_value=mock_status)
        mock_get_service.return_value = mock_service
        
        # Hacer request
        response = self.client.get("/api/v1/vector-store/status")
        
        # Verificaciones
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert data["total_documents"] == 10
        assert data["collection_name"] == "test_conversations"
    
    @patch('app.services.vector_service.get_vector_service')
    def test_list_stored_conversations_endpoint(self, mock_get_service):
        """Test endpoint para listar conversaciones almacenadas."""
        # Mock del servicio
        mock_service = Mock()
        mock_conversations = [
            StoredConversation(
                vector_id="conv_123_abc",
                conversation_id="test-conv-123",
                patient_name="Juan Pérez",
                stored_at="2024-01-15T10:00:00",
                text_preview="Paciente reporta dolor...",
                metadata={"diagnosis": "Cefalea"}
            ),
            StoredConversation(
                vector_id="conv_456_def",
                conversation_id="test-conv-456",
                patient_name="María García",
                stored_at="2024-01-15T11:00:00",
                text_preview="Paciente presenta fiebre...",
                metadata={"diagnosis": "Gripe"}
            )
        ]
        mock_service.list_stored_conversations = AsyncMock(return_value=mock_conversations)
        mock_get_service.return_value = mock_service
        
        # Hacer request
        response = self.client.get("/api/v1/vector-store/conversations?limit=10")
        
        # Verificaciones
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["patient_name"] == "Juan Pérez"
        assert data[1]["patient_name"] == "María García"
    
    @patch('app.services.vector_service.get_vector_service')
    def test_get_stored_conversation_endpoint(self, mock_get_service):
        """Test endpoint para obtener conversación específica."""
        # Mock del servicio
        mock_service = Mock()
        mock_conversation = StoredConversation(
            vector_id="conv_123_abc",
            conversation_id="test-conv-123",
            patient_name="Juan Pérez",
            stored_at="2024-01-15T10:00:00",
            text_preview="Conversación médica completa...",
            metadata={"diagnosis": "Cefalea", "urgency": "media"}
        )
        mock_service.get_conversation_by_id = AsyncMock(return_value=mock_conversation)
        mock_get_service.return_value = mock_service
        
        # Hacer request
        response = self.client.get("/api/v1/vector-store/conversations/test-conv-123")
        
        # Verificaciones
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == "test-conv-123"
        assert data["patient_name"] == "Juan Pérez"
        assert data["metadata"]["diagnosis"] == "Cefalea"
    
    @patch('app.services.vector_service.get_vector_service')
    def test_get_stored_conversation_not_found(self, mock_get_service):
        """Test endpoint cuando conversación no existe."""
        # Mock del servicio
        mock_service = Mock()
        mock_service.get_conversation_by_id = AsyncMock(return_value=None)
        mock_get_service.return_value = mock_service
        
        # Hacer request
        response = self.client.get("/api/v1/vector-store/conversations/non-existent")
        
        # Verificaciones
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    @patch('app.services.vector_service.get_vector_service')
    def test_vector_store_health_check(self, mock_get_service):
        """Test health check del vector store."""
        # Mock del servicio
        mock_service = Mock()
        mock_status = VectorStoreStatus(
            status="operational",
            collection_name="test_conversations",
            total_documents=5,
            total_embeddings=5,
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            persist_directory="./test_chroma_db"
        )
        mock_service.get_vector_store_status = AsyncMock(return_value=mock_status)
        mock_get_service.return_value = mock_service
        
        # Hacer request
        response = self.client.get("/api/v1/vector-store/health")
        
        # Verificaciones
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "vector_store"
        assert data["status"] == "operational"
        assert data["chroma_accessible"] is True
        assert data["total_documents"] == 5


class TestUploadVectorIntegration:
    """Tests de integración entre upload y vector store."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.client = TestClient(app)
    
    @patch('app.api.upload.process_transcription_pipeline')
    @patch('app.services.vector_service.store_conversation_data')
    def test_upload_triggers_vector_storage(self, mock_store_conversation, mock_process_pipeline):
        """Test que el upload desencadena almacenamiento vectorial."""
        # Mock del pipeline de transcripción
        mock_process_pipeline.return_value = None
        
        # Mock del almacenamiento vectorial
        mock_vector_response = VectorStoreResponse(
            stored=True,
            vector_id="conv_test_123",
            embedding_dimensions=384,
            collection_name="medical_conversations",
            metadata_fields=5
        )
        mock_store_conversation.return_value = mock_vector_response
        
        # Preparar archivo de prueba
        test_file_content = b"fake audio content"
        files = {"file": ("test_audio.wav", test_file_content, "audio/wav")}
        
        # Hacer upload
        with patch('app.api.upload.validate_audio_file') as mock_validate:
            mock_validate.return_value = True
            with patch('app.database.models.create_transcription') as mock_create:
                mock_transcription = Mock()
                mock_transcription.id = "test-transcription-123"
                mock_create.return_value = mock_transcription
                
                response = self.client.post("/api/v1/upload-audio", files=files)
        
        # Verificaciones básicas
        assert response.status_code == 202  # Accepted for background processing
        
        # El pipeline debe haberse llamado con el ID correcto
        mock_process_pipeline.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_vector_storage_in_pipeline(self):
        """Test que el vector storage se ejecuta en el pipeline."""
        from app.api.upload import process_transcription_pipeline
        from app.core.config import get_settings
        
        # Mock de dependencias
        with patch('app.services.whisper_service.get_whisper_service') as mock_whisper:
            with patch('app.services.openai_service.get_openai_service') as mock_openai:
                with patch('app.services.vector_service.store_conversation_data') as mock_vector:
                    with patch('app.database.models.get_transcription_by_id') as mock_get_transcription:
                        with patch('app.database.models.update_transcription') as mock_update:
                            
                            # Setup mocks
                            mock_transcription = Mock()
                            mock_transcription.id = "test-123"
                            mock_transcription.filename = "test.wav"
                            mock_transcription.file_size = 1024
                            mock_transcription.mark_processing = Mock()
                            mock_transcription.mark_completed = Mock()
                            mock_transcription.mark_vector_stored = Mock()
                            mock_get_transcription.return_value = mock_transcription
                            
                            # Mock Whisper response
                            mock_whisper_service = Mock()
                            mock_whisper_service.transcribe_audio = AsyncMock(return_value={
                                "text": "Paciente reporta dolor de cabeza",
                                "confidence_score": "0.95",
                                "language": "es",
                                "duration": 120
                            })
                            mock_whisper.return_value = mock_whisper_service
                            
                            # Mock OpenAI response
                            mock_openai_service = Mock()
                            mock_openai_service.extract_information = AsyncMock(return_value=(
                                {"nombre": "Juan Pérez", "diagnostico": "Cefalea"},
                                {"sintomas": ["dolor de cabeza"], "urgencia": "media"}
                            ))
                            mock_openai.return_value = mock_openai_service
                            
                            # Mock Vector store response
                            mock_vector_response = VectorStoreResponse(
                                stored=True,
                                vector_id="conv_test_123",
                                embedding_dimensions=384,
                                collection_name="medical_conversations",
                                metadata_fields=5
                            )
                            mock_vector.return_value = mock_vector_response
                            
                            # Mock file path
                            with patch('os.path.exists', return_value=True):
                                with patch('os.remove'):
                                    # Ejecutar pipeline
                                    await process_transcription_pipeline(
                                        transcription_id="test-123",
                                        file_path="/fake/path/test.wav",
                                        settings=get_settings()
                                    )
                            
                            # Verificaciones
                            mock_vector.assert_called_once()
                            mock_transcription.mark_vector_stored.assert_called_once_with("conv_test_123")
    
    @pytest.mark.asyncio
    async def test_vector_storage_failure_handling(self):
        """Test manejo de errores en almacenamiento vectorial."""
        from app.api.upload import process_transcription_pipeline
        from app.core.config import get_settings
        
        # Mock de dependencias
        with patch('app.services.whisper_service.get_whisper_service') as mock_whisper:
            with patch('app.services.openai_service.get_openai_service') as mock_openai:
                with patch('app.services.vector_service.store_conversation_data') as mock_vector:
                    with patch('app.database.models.get_transcription_by_id') as mock_get_transcription:
                        with patch('app.database.models.update_transcription') as mock_update:
                            
                            # Setup mocks
                            mock_transcription = Mock()
                            mock_transcription.id = "test-123"
                            mock_transcription.filename = "test.wav"
                            mock_transcription.file_size = 1024
                            mock_transcription.mark_processing = Mock()
                            mock_transcription.mark_completed = Mock()
                            mock_transcription.mark_vector_failed = Mock()
                            mock_get_transcription.return_value = mock_transcription
                            
                            # Mock servicios exitosos
                            mock_whisper_service = Mock()
                            mock_whisper_service.transcribe_audio = AsyncMock(return_value={
                                "text": "Test transcription",
                                "confidence_score": "0.95"
                            })
                            mock_whisper.return_value = mock_whisper_service
                            
                            mock_openai_service = Mock()
                            mock_openai_service.extract_information = AsyncMock(return_value=(
                                {"nombre": "Test"}, {"sintomas": ["test"]}
                            ))
                            mock_openai.return_value = mock_openai_service
                            
                            # Mock vector store failure
                            mock_vector.side_effect = Exception("Vector store error")
                            
                            # Mock file system
                            with patch('os.path.exists', return_value=True):
                                with patch('os.remove'):
                                    # Ejecutar pipeline
                                    await process_transcription_pipeline(
                                        transcription_id="test-123",
                                        file_path="/fake/path/test.wav",
                                        settings=get_settings()
                                    )
                            
                            # Verificaciones: el pipeline no debe fallar por vector store
                            mock_transcription.mark_completed.assert_called_once()
                            mock_transcription.mark_vector_failed.assert_called_once()
                            # La transcripción debe completarse a pesar del error vectorial
                            assert mock_update.call_count >= 2  # Una para completed, otra para vector failed


class TestVectorStoreErrorHandling:
    """Tests para manejo de errores del vector store."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.client = TestClient(app)
    
    @patch('app.services.vector_service.get_vector_service')
    def test_vector_store_service_error(self, mock_get_service):
        """Test manejo de errores del servicio vectorial."""
        # Mock del servicio que falla
        mock_service = Mock()
        mock_service.get_vector_store_status = AsyncMock(side_effect=Exception("Chroma DB error"))
        mock_get_service.return_value = mock_service
        
        # Hacer request
        response = self.client.get("/api/v1/vector-store/status")
        
        # Verificaciones
        assert response.status_code == 500
        data = response.json()
        assert "error" in data["detail"].lower()
    
    @patch('app.services.vector_service.get_vector_service')
    def test_vector_store_health_check_unhealthy(self, mock_get_service):
        """Test health check cuando vector store no está operativo."""
        # Mock del servicio con estado error
        mock_service = Mock()
        mock_status = VectorStoreStatus(
            status="error",
            collection_name="test_conversations",
            total_documents=0,
            total_embeddings=0,
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            persist_directory="./test_chroma_db"
        )
        mock_service.get_vector_store_status = AsyncMock(return_value=mock_status)
        mock_get_service.return_value = mock_service
        
        # Hacer request
        response = self.client.get("/api/v1/vector-store/health")
        
        # Verificaciones
        assert response.status_code == 503  # Service Unavailable
        data = response.json()
        assert data["service"] == "vector_store"
        assert data["status"] == "error"
        assert data["chroma_accessible"] is False


# Tests para configuración y validación
class TestVectorStoreConfiguration:
    """Tests para configuración del vector store."""
    
    def test_vector_store_configuration_validation(self):
        """Test validación de configuración del vector store."""
        from app.core.config import get_settings
        
        settings = get_settings()
        
        # Verificar que las configuraciones vectoriales existen
        assert hasattr(settings, 'CHROMA_PERSIST_DIRECTORY')
        assert hasattr(settings, 'CHROMA_COLLECTION_NAME')
        assert hasattr(settings, 'EMBEDDING_MODEL_NAME')
        assert hasattr(settings, 'VECTOR_EMBEDDING_DIMENSIONS')
        
        # Verificar valores por defecto
        assert settings.CHROMA_COLLECTION_NAME == "medical_conversations"
        assert settings.EMBEDDING_MODEL_NAME == "sentence-transformers/all-MiniLM-L6-v2"
        assert settings.VECTOR_EMBEDDING_DIMENSIONS == 384
    
    @patch('app.core.config.os.makedirs')
    def test_chroma_directory_creation(self, mock_makedirs):
        """Test creación del directorio de Chroma."""
        from app.core.config import create_chroma_dir
        
        create_chroma_dir()
        
        mock_makedirs.assert_called_once()
        args, kwargs = mock_makedirs.call_args
        assert kwargs.get('exist_ok') is True

