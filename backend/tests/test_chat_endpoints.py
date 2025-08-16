"""
Tests para los endpoints de Chat RAG - ElSol Challenge.

Tests para verificar el funcionamiento de los endpoints de chat médico.
Requisito 3: Chatbot vía API
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.schemas import ChatResponse, ChatSource, ChatQuery


class TestChatEndpoints:
    """Tests para endpoints del sistema de chat."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.client = TestClient(app)
    
    @patch('app.services.chat_service.get_chat_service')
    def test_chat_endpoint_success(self, mock_get_service):
        """Test endpoint principal de chat con respuesta exitosa."""
        # Mock del servicio
        mock_service = Mock()
        mock_response = ChatResponse(
            answer="Según las transcripciones médicas, Pepito Gómez presenta diabetes tipo 2.",
            sources=[
                ChatSource(
                    conversation_id="conv-123",
                    patient_name="Pepito Gómez",
                    relevance_score=0.95,
                    excerpt="Pepito Gómez presenta diabetes tipo 2...",
                    date="2024-01-15",
                    metadata={"diagnosis": "Diabetes tipo 2"}
                )
            ],
            confidence=0.87,
            intent="patient_info",
            follow_up_suggestions=[
                "¿Qué tratamiento se recomendó para Pepito?",
                "¿Cuándo fue la última consulta de Pepito?"
            ],
            processing_time_ms=1250
        )
        mock_service.process_chat_query = AsyncMock(return_value=mock_response)
        mock_get_service.return_value = mock_service
        
        # Request
        request_data = {
            "query": "¿Qué enfermedad tiene Pepito Gómez?",
            "max_results": 5,
            "include_sources": True
        }
        
        response = self.client.post("/api/v1/chat", json=request_data)
        
        # Verificaciones
        assert response.status_code == 200
        data = response.json()
        
        assert data["answer"] == "Según las transcripciones médicas, Pepito Gómez presenta diabetes tipo 2."
        assert data["confidence"] == 0.87
        assert data["intent"] == "patient_info"
        assert len(data["sources"]) == 1
        assert data["sources"][0]["patient_name"] == "Pepito Gómez"
        assert len(data["follow_up_suggestions"]) == 2
        assert data["processing_time_ms"] == 1250
    
    @patch('app.services.chat_service.get_chat_service')
    def test_chat_endpoint_diabetes_list(self, mock_get_service):
        """Test caso específico: listar pacientes con diabetes."""
        mock_service = Mock()
        mock_response = ChatResponse(
            answer="Pacientes con diabetes encontrados:\n1. Pepito Gómez - Diabetes tipo 2\n2. María García - Diabetes gestacional",
            sources=[
                ChatSource(
                    conversation_id="conv-123",
                    patient_name="Pepito Gómez",
                    relevance_score=0.9,
                    excerpt="Pepito Gómez presenta diabetes tipo 2...",
                    date="2024-01-15",
                    metadata={"diagnosis": "Diabetes tipo 2"}
                ),
                ChatSource(
                    conversation_id="conv-124",
                    patient_name="María García",
                    relevance_score=0.85,
                    excerpt="María García con diabetes gestacional...",
                    date="2024-01-16",
                    metadata={"diagnosis": "Diabetes gestacional"}
                )
            ],
            confidence=0.82,
            intent="condition_list",
            follow_up_suggestions=[
                "¿Qué tratamientos hay para diabetes?",
                "¿Cuántos pacientes nuevos con diabetes hay este mes?"
            ]
        )
        mock_service.process_chat_query = AsyncMock(return_value=mock_response)
        mock_get_service.return_value = mock_service
        
        request_data = {
            "query": "Listame los pacientes con diabetes",
            "max_results": 10
        }
        
        response = self.client.post("/api/v1/chat", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "Pepito Gómez" in data["answer"]
        assert "María García" in data["answer"]
        assert data["intent"] == "condition_list"
        assert len(data["sources"]) == 2
    
    def test_chat_endpoint_validation_error(self):
        """Test validación de parámetros inválidos."""
        # Query muy corta
        request_data = {
            "query": "a",
            "max_results": 5
        }
        
        response = self.client.post("/api/v1/chat", json=request_data)
        assert response.status_code == 400
        assert "al menos 3 caracteres" in response.json()["detail"]
    
    def test_chat_endpoint_missing_query(self):
        """Test request sin query requerido."""
        request_data = {
            "max_results": 5
        }
        
        response = self.client.post("/api/v1/chat", json=request_data)
        assert response.status_code == 422  # Validation error
    
    @patch('app.services.chat_service.get_chat_service')
    def test_chat_endpoint_service_error(self, mock_get_service):
        """Test manejo de errores del servicio de chat."""
        mock_service = Mock()
        mock_service.process_chat_query = AsyncMock(side_effect=Exception("Service error"))
        mock_get_service.return_value = mock_service
        
        request_data = {
            "query": "¿Qué enfermedad tiene Juan?",
            "max_results": 5
        }
        
        response = self.client.post("/api/v1/chat", json=request_data)
        
        assert response.status_code == 500
        assert "Error interno del servidor" in response.json()["detail"]
    
    @patch('app.services.chat_service.get_chat_service')
    def test_quick_chat_endpoint(self, mock_get_service):
        """Test endpoint de chat rápido."""
        mock_service = Mock()
        mock_response = ChatResponse(
            answer="Juan Pérez presenta hipertensión arterial.",
            sources=[],
            confidence=0.75,
            intent="patient_info",
            follow_up_suggestions=[]
        )
        mock_service.process_chat_query = AsyncMock(return_value=mock_response)
        mock_get_service.return_value = mock_service
        
        request_data = {
            "query": "¿Qué tiene Juan Pérez?",
            "max_results": 3
        }
        
        response = self.client.post("/api/v1/chat/quick", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "Juan Pérez presenta hipertensión arterial."
        assert data["confidence"] == 0.75
    
    def test_chat_examples_endpoint(self):
        """Test endpoint de ejemplos de consultas."""
        response = self.client.get("/api/v1/chat/examples")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "examples" in data
        assert "patient_info" in data["examples"]
        assert "condition_list" in data["examples"]
        assert "symptom_search" in data["examples"]
        assert "tips" in data
        assert "supported_intents" in data
        
        # Verificar ejemplos específicos
        patient_examples = data["examples"]["patient_info"]["examples"]
        assert any("Pepito Gómez" in example for example in patient_examples)
        
        condition_examples = data["examples"]["condition_list"]["examples"]
        assert any("diabetes" in example for example in condition_examples)
    
    def test_chat_stats_endpoint(self):
        """Test endpoint de estadísticas del chat."""
        response = self.client.get("/api/v1/chat/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura de estadísticas
        assert "total_queries" in data
        assert "successful_queries" in data
        assert "failed_queries" in data
        assert "avg_response_time_ms" in data
        assert "intent_distribution" in data
        assert "avg_confidence" in data
        assert "most_common_queries" in data
    
    def test_validate_chat_query_endpoint(self):
        """Test endpoint de validación de consultas."""
        # Query válida
        request_data = {"query": "¿Qué enfermedad tiene Juan Pérez?"}
        response = self.client.post("/api/v1/chat/validate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        
        # Query muy corta
        request_data = {"query": "a"}
        response = self.client.post("/api/v1/chat/validate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "demasiado corta" in data["reason"]
        
        # Query muy larga
        long_query = "a" * 1001
        request_data = {"query": long_query}
        response = self.client.post("/api/v1/chat/validate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "demasiado larga" in data["reason"]
    
    def test_chat_health_check_endpoint(self):
        """Test health check del sistema de chat."""
        response = self.client.get("/api/v1/chat/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["service"] == "chat_rag"
        assert data["status"] == "healthy"
        assert "components" in data
        assert "capabilities" in data
        assert "response_time_ms" in data
        
        # Verificar capacidades
        capabilities = data["capabilities"]
        assert "patient_info_queries" in capabilities
        assert "condition_list_queries" in capabilities
        assert "symptom_search" in capabilities


class TestChatEndpointValidation:
    """Tests específicos para validación de endpoints."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.client = TestClient(app)
    
    def test_chat_query_max_results_validation(self):
        """Test validación de max_results."""
        # Valor muy bajo
        request_data = {
            "query": "¿Qué enfermedad tiene Juan?",
            "max_results": 0
        }
        
        response = self.client.post("/api/v1/chat", json=request_data)
        assert response.status_code == 422
        
        # Valor muy alto
        request_data = {
            "query": "¿Qué enfermedad tiene Juan?",
            "max_results": 25
        }
        
        response = self.client.post("/api/v1/chat", json=request_data)
        assert response.status_code == 422
    
    def test_chat_query_length_validation(self):
        """Test validación de longitud de query."""
        # Query muy larga
        long_query = "¿" + "Qué enfermedad tiene Juan? " * 100
        request_data = {
            "query": long_query,
            "max_results": 5
        }
        
        response = self.client.post("/api/v1/chat", json=request_data)
        assert response.status_code == 422
    
    def test_chat_query_filters_optional(self):
        """Test que los filtros son opcionales."""
        request_data = {
            "query": "¿Qué enfermedad tiene Juan?",
            "max_results": 5
            # Sin filters
        }
        
        with patch('app.services.chat_service.get_chat_service') as mock_get_service:
            mock_service = Mock()
            mock_response = ChatResponse(
                answer="Test response",
                sources=[],
                confidence=0.5,
                intent="general_query",
                follow_up_suggestions=[]
            )
            mock_service.process_chat_query = AsyncMock(return_value=mock_response)
            mock_get_service.return_value = mock_service
            
            response = self.client.post("/api/v1/chat", json=request_data)
            assert response.status_code == 200


class TestChatEndpointSpecificCases:
    """Tests para casos de uso específicos del challenge."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.client = TestClient(app)
    
    @patch('app.services.chat_service.get_chat_service')
    def test_pepito_gomez_specific_case(self, mock_get_service):
        """Test caso específico requerido: 'Pepito Gómez'."""
        mock_service = Mock()
        mock_response = ChatResponse(
            answer="Según las transcripciones médicas disponibles, Pepito Gómez presenta diabetes tipo 2. El diagnóstico fue confirmado en su consulta del 15 de enero de 2024.",
            sources=[
                ChatSource(
                    conversation_id="conv-pepito-1",
                    patient_name="Pepito Gómez",
                    relevance_score=0.98,
                    excerpt="Paciente Pepito Gómez de 35 años presenta diabetes tipo 2...",
                    date="2024-01-15",
                    metadata={
                        "diagnosis": "Diabetes tipo 2",
                        "symptoms": "poliuria, polidipsia",
                        "rank": 1
                    }
                )
            ],
            confidence=0.95,
            intent="patient_info",
            follow_up_suggestions=[
                "¿Qué tratamiento se recomendó para Pepito?",
                "¿Cuándo fue la última consulta de Pepito?",
                "¿Qué síntomas reportó Pepito?"
            ],
            query_classification={
                "entities": {"patients": ["Pepito Gómez"]},
                "search_terms": ["Pepito Gómez", "enfermedad"],
                "normalized_query": "que enfermedad tiene pepito gomez"
            },
            processing_time_ms=1180
        )
        mock_service.process_chat_query = AsyncMock(return_value=mock_response)
        mock_get_service.return_value = mock_service
        
        request_data = {
            "query": "¿Qué enfermedad tiene Pepito Gómez?",
            "max_results": 5,
            "include_sources": True
        }
        
        response = self.client.post("/api/v1/chat", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificaciones específicas para el caso Pepito Gómez
        assert "Pepito Gómez" in data["answer"]
        assert "diabetes" in data["answer"].lower()
        assert data["intent"] == "patient_info"
        assert data["confidence"] >= 0.8
        assert len(data["sources"]) > 0
        assert data["sources"][0]["patient_name"] == "Pepito Gómez"
        assert "Pepito Gómez" in str(data["query_classification"]["entities"])
    
    @patch('app.services.chat_service.get_chat_service')
    def test_diabetes_patients_specific_case(self, mock_get_service):
        """Test caso específico requerido: 'Listame los pacientes con diabetes'."""
        mock_service = Mock()
        mock_response = ChatResponse(
            answer="""Pacientes con diabetes encontrados en las transcripciones:

1. **Pepito Gómez** - Diabetes tipo 2
   - Fecha de diagnóstico: 15/01/2024
   - Síntomas: poliuria, polidipsia

2. **María García** - Diabetes gestacional  
   - Fecha de consulta: 20/01/2024
   - En seguimiento prenatal

3. **Carlos López** - Diabetes tipo 1
   - Fecha de consulta: 22/01/2024
   - Tratamiento con insulina

Total: 3 pacientes con diabetes identificados.""",
            sources=[
                ChatSource(
                    conversation_id="conv-pepito-1",
                    patient_name="Pepito Gómez",
                    relevance_score=0.92,
                    excerpt="Pepito Gómez presenta diabetes tipo 2...",
                    date="2024-01-15",
                    metadata={"diagnosis": "Diabetes tipo 2", "rank": 1}
                ),
                ChatSource(
                    conversation_id="conv-maria-1",
                    patient_name="María García",
                    relevance_score=0.89,
                    excerpt="María García con diabetes gestacional...",
                    date="2024-01-20",
                    metadata={"diagnosis": "Diabetes gestacional", "rank": 2}
                ),
                ChatSource(
                    conversation_id="conv-carlos-1",
                    patient_name="Carlos López",
                    relevance_score=0.87,
                    excerpt="Carlos López requiere insulina para diabetes tipo 1...",
                    date="2024-01-22",
                    metadata={"diagnosis": "Diabetes tipo 1", "rank": 3}
                )
            ],
            confidence=0.88,
            intent="condition_list",
            follow_up_suggestions=[
                "¿Qué tratamientos hay para diabetes?",
                "¿Cuántos pacientes nuevos con diabetes hay este mes?",
                "¿Qué síntomas son más comunes en diabetes?"
            ],
            query_classification={
                "entities": {"conditions": ["diabetes"]},
                "search_terms": ["diabetes", "pacientes"],
                "normalized_query": "listame los pacientes con diabetes"
            },
            processing_time_ms=1450
        )
        mock_service.process_chat_query = AsyncMock(return_value=mock_response)
        mock_get_service.return_value = mock_service
        
        request_data = {
            "query": "Listame los pacientes con diabetes",
            "max_results": 10,
            "include_sources": True
        }
        
        response = self.client.post("/api/v1/chat", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificaciones específicas para el caso lista de diabetes
        assert "Pepito Gómez" in data["answer"]
        assert "María García" in data["answer"] 
        assert "Carlos López" in data["answer"]
        assert data["intent"] == "condition_list"
        assert data["confidence"] >= 0.8
        assert len(data["sources"]) == 3
        assert "diabetes" in str(data["query_classification"]["entities"])
        
        # Verificar que contiene múltiples pacientes
        patient_names = [source["patient_name"] for source in data["sources"]]
        assert "Pepito Gómez" in patient_names
        assert "María García" in patient_names
        assert "Carlos López" in patient_names


class TestChatEndpointErrorHandling:
    """Tests para manejo de errores en endpoints de chat."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.client = TestClient(app)
    
    @patch('app.services.chat_service.get_chat_service')
    def test_chat_service_timeout_error(self, mock_get_service):
        """Test manejo de timeout en servicio de chat."""
        mock_service = Mock()
        mock_service.process_chat_query = AsyncMock(side_effect=asyncio.TimeoutError("Timeout"))
        mock_get_service.return_value = mock_service
        
        request_data = {
            "query": "¿Qué enfermedad tiene Juan?",
            "max_results": 5
        }
        
        response = self.client.post("/api/v1/chat", json=request_data)
        
        assert response.status_code == 500
        assert "Error interno del servidor" in response.json()["detail"]
    
    def test_malformed_json_request(self):
        """Test request con JSON malformado."""
        response = self.client.post(
            "/api/v1/chat",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_missing_content_type(self):
        """Test request sin Content-Type."""
        response = self.client.post("/api/v1/chat", data='{"query": "test"}')
        
        # FastAPI debe manejar esto apropiadamente
        assert response.status_code in [422, 400]
