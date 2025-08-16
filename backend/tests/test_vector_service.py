"""
Tests para el Vector Store Service - ElSol Challenge.

Tests para verificar el funcionamiento del almacenamiento vectorial
con Chroma DB y sentence-transformers.

Requisito 2: Almacenamiento Vectorial
"""

import pytest
import asyncio
import tempfile
import shutil
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from app.services.vector_service import (
    VectorStoreService, 
    VectorStoreError, 
    get_vector_service,
    store_conversation_data
)
from app.core.schemas import VectorStoreResponse, VectorStoreStatus


class TestVectorStoreService:
    """Tests para el servicio de vector store."""
    
    @pytest.fixture
    def temp_chroma_dir(self):
        """Crear directorio temporal para Chroma DB en tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_settings(self, temp_chroma_dir):
        """Mock de configuraciones para tests."""
        with patch('app.services.vector_service.settings') as mock_settings:
            mock_settings.CHROMA_PERSIST_DIRECTORY = temp_chroma_dir
            mock_settings.CHROMA_COLLECTION_NAME = "test_conversations"
            mock_settings.EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
            mock_settings.VECTOR_EMBEDDING_DIMENSIONS = 384
            yield mock_settings
    
    @pytest.fixture
    def sample_conversation_data(self):
        """Datos de conversación de ejemplo para tests."""
        return {
            "conversation_id": "test-conv-123",
            "transcription": "Paciente Juan Pérez de 45 años presenta dolor de cabeza desde hace 3 días. Dr. González recomienda reposo.",
            "structured_data": {
                "nombre": "Juan Pérez",
                "edad": 45,
                "diagnostico": "Cefalea",
                "medico": "Dr. González"
            },
            "unstructured_data": {
                "sintomas": ["dolor de cabeza"],
                "contexto": "Consulta médica",
                "urgencia": "media"
            }
        }
    
    @pytest.mark.asyncio
    async def test_vector_service_initialization(self, mock_settings):
        """Test inicialización del servicio vectorial."""
        with patch('chromadb.PersistentClient') as mock_client:
            # Setup mocks
            mock_collection = Mock()
            mock_collection.count.return_value = 0
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            
            with patch('sentence_transformers.SentenceTransformer') as mock_transformer:
                # Inicializar servicio
                service = VectorStoreService()
                
                # Verificaciones
                assert service.client is not None
                assert service.collection is not None
                assert service.embedding_model is not None
                mock_client.assert_called_once()
                mock_transformer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_conversation_success(self, mock_settings, sample_conversation_data):
        """Test almacenamiento exitoso de conversación."""
        with patch('chromadb.PersistentClient') as mock_client:
            # Setup mocks
            mock_collection = Mock()
            mock_collection.count.return_value = 0
            mock_collection.add = Mock()
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            
            mock_embedding = [0.1] * 384  # Mock embedding de 384 dimensiones
            
            with patch('sentence_transformers.SentenceTransformer') as mock_transformer:
                mock_transformer.return_value.encode.return_value = mock_embedding
                
                # Inicializar servicio
                service = VectorStoreService()
                
                # Test almacenamiento
                response = await service.store_conversation(
                    conversation_id=sample_conversation_data["conversation_id"],
                    transcription=sample_conversation_data["transcription"],
                    structured_data=sample_conversation_data["structured_data"],
                    unstructured_data=sample_conversation_data["unstructured_data"]
                )
                
                # Verificaciones
                assert isinstance(response, VectorStoreResponse)
                assert response.stored is True
                assert response.embedding_dimensions == 384
                assert response.collection_name == "test_conversations"
                assert "conv_test-conv-123" in response.vector_id
                
                # Verificar que se llamó a Chroma
                mock_collection.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_conversation_with_metadata(self, mock_settings, sample_conversation_data):
        """Test almacenamiento con metadata adicional."""
        with patch('chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.count.return_value = 0
            mock_collection.add = Mock()
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            
            with patch('sentence_transformers.SentenceTransformer') as mock_transformer:
                mock_transformer.return_value.encode.return_value = [0.1] * 384
                
                service = VectorStoreService()
                
                # Metadata adicional
                extra_metadata = {
                    "filename": "test_audio.wav",
                    "file_size": 1024000
                }
                
                response = await service.store_conversation(
                    conversation_id=sample_conversation_data["conversation_id"],
                    transcription=sample_conversation_data["transcription"],
                    structured_data=sample_conversation_data["structured_data"],
                    unstructured_data=sample_conversation_data["unstructured_data"],
                    metadata=extra_metadata
                )
                
                # Verificar que se incluye metadata
                assert response.stored is True
                
                # Verificar que se pasó metadata a Chroma
                call_args = mock_collection.add.call_args
                metadata_passed = call_args[0][1][0]  # metadatas[0]
                
                assert metadata_passed["filename"] == "test_audio.wav"
                assert metadata_passed["file_size"] == "1024000"
                assert metadata_passed["patient_name"] == "Juan Pérez"
    
    @pytest.mark.asyncio
    async def test_get_vector_store_status(self, mock_settings):
        """Test obtener estado del vector store."""
        with patch('chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.count.return_value = 5
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            
            with patch('sentence_transformers.SentenceTransformer'):
                service = VectorStoreService()
                
                status = await service.get_vector_store_status()
                
                assert isinstance(status, VectorStoreStatus)
                assert status.status == "operational"
                assert status.total_documents == 5
                assert status.total_embeddings == 5
                assert status.collection_name == "test_conversations"
    
    @pytest.mark.asyncio
    async def test_list_stored_conversations(self, mock_settings):
        """Test listar conversaciones almacenadas."""
        with patch('chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.count.return_value = 2
            
            # Mock resultados de búsqueda
            mock_results = {
                'ids': ['conv_123_abc', 'conv_456_def'],
                'metadatas': [
                    {
                        'conversation_id': 'test-conv-123',
                        'patient_name': 'Juan Pérez',
                        'created_at': datetime.utcnow().isoformat()
                    },
                    {
                        'conversation_id': 'test-conv-456',
                        'patient_name': 'María García',
                        'created_at': datetime.utcnow().isoformat()
                    }
                ],
                'documents': [
                    'Conversación médica con Juan Pérez...',
                    'Conversación médica con María García...'
                ]
            }
            mock_collection.get.return_value = mock_results
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            
            with patch('sentence_transformers.SentenceTransformer'):
                service = VectorStoreService()
                
                conversations = await service.list_stored_conversations(limit=10)
                
                assert len(conversations) == 2
                assert conversations[0].conversation_id == 'test-conv-123'
                assert conversations[0].patient_name == 'Juan Pérez'
                assert conversations[1].conversation_id == 'test-conv-456'
    
    @pytest.mark.asyncio
    async def test_get_conversation_by_id(self, mock_settings):
        """Test obtener conversación específica por ID."""
        with patch('chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.count.return_value = 1
            
            # Mock resultado específico
            mock_results = {
                'ids': ['conv_123_abc'],
                'metadatas': [{
                    'conversation_id': 'test-conv-123',
                    'patient_name': 'Juan Pérez',
                    'created_at': datetime.utcnow().isoformat()
                }],
                'documents': ['Conversación médica completa...']
            }
            mock_collection.get.return_value = mock_results
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            
            with patch('sentence_transformers.SentenceTransformer'):
                service = VectorStoreService()
                
                conversation = await service.get_conversation_by_id('test-conv-123')
                
                assert conversation is not None
                assert conversation.conversation_id == 'test-conv-123'
                assert conversation.patient_name == 'Juan Pérez'
    
    @pytest.mark.asyncio
    async def test_get_conversation_by_id_not_found(self, mock_settings):
        """Test obtener conversación que no existe."""
        with patch('chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.count.return_value = 0
            mock_collection.get.return_value = {'ids': [], 'metadatas': [], 'documents': []}
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            
            with patch('sentence_transformers.SentenceTransformer'):
                service = VectorStoreService()
                
                conversation = await service.get_conversation_by_id('non-existent-id')
                
                assert conversation is None
    
    @pytest.mark.asyncio
    async def test_store_conversation_error_handling(self, mock_settings, sample_conversation_data):
        """Test manejo de errores en almacenamiento."""
        with patch('chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.add.side_effect = Exception("Chroma error")
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            
            with patch('sentence_transformers.SentenceTransformer') as mock_transformer:
                mock_transformer.return_value.encode.return_value = [0.1] * 384
                
                service = VectorStoreService()
                
                # Debe lanzar VectorStoreError
                with pytest.raises(VectorStoreError):
                    await service.store_conversation(
                        conversation_id=sample_conversation_data["conversation_id"],
                        transcription=sample_conversation_data["transcription"],
                        structured_data=sample_conversation_data["structured_data"],
                        unstructured_data=sample_conversation_data["unstructured_data"]
                    )
    
    def test_prepare_text_for_embedding(self, mock_settings):
        """Test preparación de texto para embedding."""
        with patch('chromadb.PersistentClient'):
            with patch('sentence_transformers.SentenceTransformer'):
                service = VectorStoreService()
                
                transcription = "Paciente reporta dolor de cabeza"
                structured_data = {"nombre": "Juan Pérez", "diagnostico": "Cefalea"}
                unstructured_data = {"sintomas": ["dolor de cabeza"], "contexto": "Consulta"}
                
                prepared_text = service._prepare_text_for_embedding(
                    transcription, structured_data, unstructured_data
                )
                
                assert "Paciente reporta dolor de cabeza" in prepared_text
                assert "Juan Pérez" in prepared_text
                assert "Cefalea" in prepared_text
                assert "dolor de cabeza" in prepared_text
    
    def test_prepare_metadata(self, mock_settings):
        """Test preparación de metadata."""
        with patch('chromadb.PersistentClient'):
            with patch('sentence_transformers.SentenceTransformer'):
                service = VectorStoreService()
                
                structured_data = {
                    "nombre": "Juan Pérez", 
                    "edad": 45,
                    "diagnostico": "Cefalea"
                }
                unstructured_data = {
                    "sintomas": ["dolor de cabeza"],
                    "urgencia": "media"
                }
                
                metadata = service._prepare_metadata(
                    "test-conv-123", structured_data, unstructured_data
                )
                
                assert metadata["conversation_id"] == "test-conv-123"
                assert metadata["patient_name"] == "Juan Pérez"
                assert metadata["diagnosis"] == "Cefalea"
                assert metadata["urgency"] == "media"
                assert metadata["symptoms"] == "dolor de cabeza"


class TestVectorServiceIntegration:
    """Tests de integración para el vector service."""
    
    @pytest.mark.asyncio
    async def test_store_conversation_data_function(self):
        """Test función de conveniencia store_conversation_data."""
        with patch('app.services.vector_service.get_vector_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_response = VectorStoreResponse(
                stored=True,
                vector_id="test-vector-id",
                embedding_dimensions=384,
                collection_name="test_conversations",
                metadata_fields=5
            )
            mock_service.store_conversation.return_value = mock_response
            mock_get_service.return_value = mock_service
            
            response = await store_conversation_data(
                conversation_id="test-123",
                transcription="Test transcription",
                structured_data={"nombre": "Test"},
                unstructured_data={"sintomas": ["test"]}
            )
            
            assert response.stored is True
            assert response.vector_id == "test-vector-id"
            mock_service.store_conversation.assert_called_once()
    
    def test_get_vector_service_singleton(self):
        """Test que get_vector_service retorna singleton."""
        with patch('app.services.vector_service.VectorStoreService') as mock_service_class:
            mock_instance = Mock()
            mock_service_class.return_value = mock_instance
            
            # Primera llamada
            service1 = get_vector_service()
            # Segunda llamada
            service2 = get_vector_service()
            
            # Debe ser la misma instancia
            assert service1 is service2
            # Solo debe crear una instancia
            mock_service_class.assert_called_once()


# Fixtures para tests de integración
@pytest.fixture
def sample_audio_data():
    """Datos de audio de ejemplo para tests de integración."""
    return {
        "filename": "test_conversation.wav",
        "file_size": 1024000,
        "transcription": "Paciente Juan Pérez de 35 años presenta fiebre y tos seca desde hace 2 días.",
        "structured_data": {
            "nombre": "Juan Pérez",
            "edad": 35,
            "diagnostico": "Síndrome gripal",
            "fecha": "2024-01-15"
        },
        "unstructured_data": {
            "sintomas": ["fiebre", "tos seca"],
            "contexto": "Consulta médica general",
            "urgencia": "baja"
        }
    }


@pytest.mark.integration
class TestVectorStoreEndToEnd:
    """Tests end-to-end para vector store."""
    
    @pytest.mark.asyncio
    async def test_full_vector_workflow(self, sample_audio_data):
        """Test flujo completo de almacenamiento vectorial."""
        # Este test requiere configuración real de Chroma
        # Se puede ejecutar con pytest -m integration
        pytest.skip("Requiere configuración real de Chroma DB")

