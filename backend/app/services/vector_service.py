"""
Servicio de Vector Store para la aplicación ElSol Challenge.

Este servicio maneja el almacenamiento vectorial de transcripciones e información 
extraída usando Chroma DB y sentence-transformers para embeddings.

Requisito 2: Almacenamiento Vectorial
"""

import os
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import structlog
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
import numpy as np

from app.core.config import get_settings
from app.core.schemas import VectorStoreMetadata, VectorStoreResponse, VectorStoreStatus, StoredConversation

logger = structlog.get_logger(__name__)
settings = get_settings()


class VectorStoreError(Exception):
    """Excepción personalizada para errores del vector store."""
    pass


class VectorStoreService:
    """
    Servicio para manejo de almacenamiento vectorial con Chroma DB.
    
    Responsabilidades:
    - Inicializar y gestionar Chroma DB
    - Generar embeddings de transcripciones
    - Almacenar información con metadata rica
    - Proporcionar funciones básicas de consulta
    """
    
    def __init__(self):
        """Inicializar el servicio de vector store."""
        self.client = None
        self.collection = None
        self.embedding_model = None
        self._initialize_chroma()
        self._initialize_embedding_model()
        
    def _initialize_chroma(self) -> None:
        """Inicializar cliente y colección de Chroma DB."""
        try:
            logger.info("Initializing Chroma DB", 
                       persist_directory=settings.CHROMA_PERSIST_DIRECTORY)
            
            # Crear directorio si no existe
            os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
            
            # Inicializar cliente con persistencia
            self.client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIRECTORY,
                settings=ChromaSettings(
                    allow_reset=True,
                    anonymized_telemetry=False
                )
            )
            
            # Crear o obtener colección
            self.collection = self.client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION_NAME,
                metadata={"description": "Medical conversations and extracted information"}
            )
            
            logger.info("Chroma DB initialized successfully",
                       collection_name=settings.CHROMA_COLLECTION_NAME,
                       collection_count=self.collection.count())
            
        except Exception as e:
            error_msg = f"Failed to initialize Chroma DB: {str(e)}"
            logger.error("Chroma DB initialization failed", error=str(e))
            raise VectorStoreError(error_msg) from e
    
    def _initialize_embedding_model(self) -> None:
        """Inicializar modelo de embeddings."""
        try:
            logger.info("Loading embedding model", 
                       model_name=settings.EMBEDDING_MODEL_NAME)
            
            # Cargar modelo en un executor para no bloquear
            self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
            
            logger.info("Embedding model loaded successfully",
                       model_name=settings.EMBEDDING_MODEL_NAME,
                       embedding_dimensions=settings.VECTOR_EMBEDDING_DIMENSIONS)
            
        except Exception as e:
            error_msg = f"Failed to load embedding model: {str(e)}"
            logger.error("Embedding model initialization failed", error=str(e))
            raise VectorStoreError(error_msg) from e
    
    async def store_conversation(
        self,
        conversation_id: str,
        transcription: str,
        structured_data: Dict[str, Any],
        unstructured_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> VectorStoreResponse:
        """
        Almacenar conversación transcrita en vector store.
        
        Args:
            conversation_id: ID único de la conversación
            transcription: Texto transcrito
            structured_data: Información estructurada extraída
            unstructured_data: Información no estructurada extraída
            metadata: Metadata adicional opcional
            
        Returns:
            VectorStoreResponse con información del almacenamiento
            
        Raises:
            VectorStoreError: Si el almacenamiento falla
        """
        logger.info("Starting conversation storage in vector store",
                   conversation_id=conversation_id,
                   text_length=len(transcription))
        
        try:
            # Generar ID único para el vector store
            vector_id = f"conv_{conversation_id}_{uuid.uuid4().hex[:8]}"
            
            # Preparar texto para embedding
            text_to_embed = self._prepare_text_for_embedding(
                transcription, structured_data, unstructured_data
            )
            
            # Generar embedding
            embedding = await self._generate_embedding(text_to_embed)
            
            # Preparar metadata
            vector_metadata = self._prepare_metadata(
                conversation_id, structured_data, unstructured_data, metadata
            )
            
            # Almacenar en Chroma
            await self._store_in_chroma(vector_id, embedding, text_to_embed, vector_metadata)
            
            logger.info("Conversation stored successfully in vector store",
                       conversation_id=conversation_id,
                       vector_id=vector_id,
                       embedding_dimensions=len(embedding))
            
            return VectorStoreResponse(
                stored=True,
                vector_id=vector_id,
                embedding_dimensions=len(embedding),
                collection_name=settings.CHROMA_COLLECTION_NAME,
                metadata_fields=len(vector_metadata)
            )
            
        except Exception as e:
            error_msg = f"Failed to store conversation in vector store: {str(e)}"
            logger.error("Vector store storage failed",
                        conversation_id=conversation_id,
                        error=str(e))
            raise VectorStoreError(error_msg) from e
    
    def _prepare_text_for_embedding(
        self,
        transcription: str,
        structured_data: Dict[str, Any],
        unstructured_data: Dict[str, Any]
    ) -> str:
        """
        Preparar texto combinado para generar embedding.
        
        Combina transcripción + datos estructurados + síntomas/contexto
        para crear un embedding rico en información médica.
        """
        text_parts = [transcription]
        
        # Agregar información estructurada relevante
        if structured_data:
            if structured_data.get('nombre'):
                text_parts.append(f"Paciente: {structured_data['nombre']}")
            if structured_data.get('diagnostico'):
                text_parts.append(f"Diagnóstico: {structured_data['diagnostico']}")
            if structured_data.get('medicamentos'):
                meds = ', '.join(structured_data['medicamentos'])
                text_parts.append(f"Medicamentos: {meds}")
        
        # Agregar información no estructurada relevante
        if unstructured_data:
            if unstructured_data.get('sintomas'):
                symptoms = ', '.join(unstructured_data['sintomas'])
                text_parts.append(f"Síntomas: {symptoms}")
            if unstructured_data.get('contexto'):
                text_parts.append(f"Contexto: {unstructured_data['contexto']}")
        
        combined_text = ' | '.join(text_parts)
        
        # Truncar si es muy largo (límite del modelo)
        if len(combined_text) > 8000:  # Límite conservador
            combined_text = combined_text[:8000] + "..."
        
        return combined_text
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generar embedding de manera asíncrona."""
        loop = asyncio.get_event_loop()
        
        # Ejecutar en thread pool para no bloquear
        embedding = await loop.run_in_executor(
            None, 
            self.embedding_model.encode, 
            text
        )
        
        return embedding.tolist()
    
    def _prepare_metadata(
        self,
        conversation_id: str,
        structured_data: Dict[str, Any],
        unstructured_data: Dict[str, Any],
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Preparar metadata rica para el vector store."""
        metadata = {
            "conversation_id": conversation_id,
            "document_type": "transcription",
            "created_at": datetime.utcnow().isoformat(),
            "has_structured_data": bool(structured_data),
            "has_unstructured_data": bool(unstructured_data)
        }
        
        # Agregar datos estructurados como metadata
        if structured_data:
            if structured_data.get('nombre'):
                metadata["patient_name"] = str(structured_data['nombre'])
            if structured_data.get('diagnostico'):
                metadata["diagnosis"] = str(structured_data['diagnostico'])
            if structured_data.get('fecha'):
                metadata["conversation_date"] = str(structured_data['fecha'])
            if structured_data.get('edad'):
                metadata["patient_age"] = str(structured_data['edad'])
        
        # Agregar datos no estructurados clave
        if unstructured_data:
            if unstructured_data.get('urgencia'):
                metadata["urgency"] = str(unstructured_data['urgencia'])
            if unstructured_data.get('sintomas'):
                # Concatenar síntomas para búsqueda
                metadata["symptoms"] = ', '.join(unstructured_data['sintomas'])
        
        # Agregar metadata adicional
        if additional_metadata:
            metadata.update({k: str(v) for k, v in additional_metadata.items()})
        
        return metadata
    
    async def _store_in_chroma(
        self,
        vector_id: str,
        embedding: List[float],
        document: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Almacenar en Chroma DB de manera asíncrona."""
        loop = asyncio.get_event_loop()
        
        # Ejecutar en thread pool para no bloquear
        await loop.run_in_executor(
            None,
            self.collection.add,
            [embedding],  # embeddings
            [metadata],   # metadatas
            [document],   # documents
            [vector_id]   # ids
        )
    
    async def get_vector_store_status(self) -> VectorStoreStatus:
        """Obtener estado actual del vector store."""
        try:
            count = self.collection.count()
            
            return VectorStoreStatus(
                status="operational",
                collection_name=settings.CHROMA_COLLECTION_NAME,
                total_documents=count,
                total_embeddings=count,
                embedding_model=settings.EMBEDDING_MODEL_NAME,
                persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error("Failed to get vector store status", error=str(e))
            return VectorStoreStatus(
                status="error",
                collection_name=settings.CHROMA_COLLECTION_NAME,
                total_documents=0,
                total_embeddings=0,
                embedding_model=settings.EMBEDDING_MODEL_NAME,
                persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
                last_updated=datetime.utcnow()
            )
    
    async def list_stored_conversations(self, limit: int = 20) -> List[StoredConversation]:
        """Listar conversaciones almacenadas en el vector store."""
        try:
            loop = asyncio.get_event_loop()
            
            # Obtener documentos recientes
            results = await loop.run_in_executor(
                None,
                self.collection.get,
                None,  # ids (None = all)
                None,  # where
                limit, # limit
                None,  # offset
                None,  # where_document
                True   # include metadata
            )
            
            conversations = []
            for i, (doc_id, metadata, document) in enumerate(
                zip(results['ids'], results['metadatas'], results['documents'])
            ):
                # Preview del texto (primeros 200 caracteres)
                text_preview = document[:200] + "..." if len(document) > 200 else document
                
                conversation = StoredConversation(
                    vector_id=doc_id,
                    conversation_id=metadata.get('conversation_id', 'unknown'),
                    patient_name=metadata.get('patient_name'),
                    stored_at=datetime.fromisoformat(metadata.get('created_at', datetime.utcnow().isoformat())),
                    text_preview=text_preview,
                    metadata=metadata
                )
                conversations.append(conversation)
            
            return conversations
            
        except Exception as e:
            logger.error("Failed to list stored conversations", error=str(e))
            return []
    
    async def get_conversation_by_id(self, conversation_id: str) -> Optional[StoredConversation]:
        """Obtener conversación específica por ID."""
        try:
            loop = asyncio.get_event_loop()
            
            # Buscar por metadata
            results = await loop.run_in_executor(
                None,
                self.collection.get,
                None,                                          # ids
                {"conversation_id": conversation_id},          # where
                1,                                             # limit
                None,                                          # offset
                None,                                          # where_document
                True                                           # include metadata
            )
            
            if not results['ids']:
                return None
            
            doc_id = results['ids'][0]
            metadata = results['metadatas'][0]
            document = results['documents'][0]
            
            return StoredConversation(
                vector_id=doc_id,
                conversation_id=conversation_id,
                patient_name=metadata.get('patient_name'),
                stored_at=datetime.fromisoformat(metadata.get('created_at', datetime.utcnow().isoformat())),
                text_preview=document,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error("Failed to get conversation by ID", 
                        conversation_id=conversation_id, 
                        error=str(e))
            return None
    
    async def semantic_search(
        self,
        query: str,
        max_results: int = 5,
        similarity_threshold: float = 0.7,
        metadata_filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Realizar búsqueda semántica avanzada para el sistema de chat.
        
        Args:
            query: Consulta en lenguaje natural
            max_results: Número máximo de resultados
            similarity_threshold: Umbral mínimo de similitud
            metadata_filters: Filtros adicionales por metadata
            
        Returns:
            Lista de resultados con contexto, metadata y puntuaciones
        """
        try:
            logger.info("Starting semantic search", 
                       query=query, 
                       max_results=max_results,
                       threshold=similarity_threshold)
            
            # Generar embedding de la consulta
            query_embedding = await self._generate_embedding(query)
            
            # Ejecutar búsqueda en Chroma
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self.collection.query,
                [query_embedding],           # query_embeddings
                max_results,                 # n_results
                metadata_filters,            # where
                None,                        # where_document
                ["documents", "metadatas", "distances"]  # include
            )
            
            # Procesar y filtrar resultados
            search_results = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0], 
                results['metadatas'][0], 
                results['distances'][0]
            )):
                # Convertir distancia a similitud (Chroma usa distancia coseno)
                similarity = 1 - distance
                
                # Filtrar por umbral de similitud
                if similarity >= similarity_threshold:
                    result = {
                        "content": doc,
                        "metadata": metadata,
                        "similarity_score": similarity,
                        "rank": i + 1,
                        "conversation_id": metadata.get("conversation_id", "unknown"),
                        "patient_name": metadata.get("patient_name"),
                        "diagnosis": metadata.get("diagnosis"),
                        "symptoms": metadata.get("symptoms"),
                        "date": metadata.get("conversation_date"),
                        "excerpt": self._create_excerpt(doc, query, max_length=200)
                    }
                    search_results.append(result)
            
            logger.info("Semantic search completed",
                       query=query,
                       results_found=len(search_results),
                       avg_similarity=sum(r['similarity_score'] for r in search_results) / len(search_results) if search_results else 0)
            
            return search_results
            
        except Exception as e:
            logger.error("Semantic search failed", 
                        query=query, 
                        error=str(e))
            return []
    
    async def search_by_patient(
        self,
        patient_name: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Buscar todas las conversaciones de un paciente específico.
        
        Args:
            patient_name: Nombre del paciente
            max_results: Número máximo de resultados
            
        Returns:
            Lista de conversaciones del paciente
        """
        try:
            logger.info("Searching by patient", patient_name=patient_name)
            
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self.collection.get,
                None,                                          # ids
                {"patient_name": {"$eq": patient_name}},       # where
                max_results,                                   # limit
                None,                                          # offset
                None,                                          # where_document
                True                                           # include metadata
            )
            
            search_results = []
            for doc, metadata in zip(results['documents'], results['metadatas']):
                result = {
                    "content": doc,
                    "metadata": metadata,
                    "similarity_score": 1.0,  # Exact match
                    "conversation_id": metadata.get("conversation_id", "unknown"),
                    "patient_name": metadata.get("patient_name"),
                    "diagnosis": metadata.get("diagnosis"),
                    "symptoms": metadata.get("symptoms"),
                    "date": metadata.get("conversation_date"),
                    "excerpt": self._create_excerpt(doc, patient_name, max_length=200)
                }
                search_results.append(result)
            
            logger.info("Patient search completed",
                       patient_name=patient_name,
                       results_found=len(search_results))
            
            return search_results
            
        except Exception as e:
            logger.error("Patient search failed", 
                        patient_name=patient_name, 
                        error=str(e))
            return []
    
    async def search_by_condition(
        self,
        condition: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Buscar pacientes por condición médica o diagnóstico.
        
        Args:
            condition: Condición médica o diagnóstico
            max_results: Número máximo de resultados
            
        Returns:
            Lista de pacientes con la condición especificada
        """
        try:
            logger.info("Searching by condition", condition=condition)
            
            # Búsqueda semántica para capturar variaciones de la condición
            search_results = await self.semantic_search(
                query=f"diagnóstico {condition} enfermedad",
                max_results=max_results * 2,  # Buscar más para luego filtrar
                similarity_threshold=0.6,
                metadata_filters=None
            )
            
            # Filtrar y agrupar por paciente
            patients_found = {}
            for result in search_results:
                patient_name = result.get("patient_name")
                if patient_name and patient_name not in patients_found:
                    # Verificar si la condición está en el diagnóstico o síntomas
                    diagnosis = (result.get("diagnosis") or "").lower()
                    symptoms = (result.get("symptoms") or "").lower()
                    content = result.get("content", "").lower()
                    condition_lower = condition.lower()
                    
                    if (condition_lower in diagnosis or 
                        condition_lower in symptoms or 
                        condition_lower in content):
                        patients_found[patient_name] = result
            
            # Convertir a lista y limitar resultados
            filtered_results = list(patients_found.values())[:max_results]
            
            logger.info("Condition search completed",
                       condition=condition,
                       unique_patients=len(filtered_results))
            
            return filtered_results
            
        except Exception as e:
            logger.error("Condition search failed", 
                        condition=condition, 
                        error=str(e))
            return []
    
    def _create_excerpt(self, text: str, query: str, max_length: int = 200) -> str:
        """
        Crear un extracto relevante del texto basado en la consulta.
        
        Args:
            text: Texto completo
            query: Consulta de búsqueda
            max_length: Longitud máxima del extracto
            
        Returns:
            Extracto relevante del texto
        """
        try:
            # Normalizar texto y consulta
            text_lower = text.lower()
            query_words = [word.lower() for word in query.split() if len(word) > 2]
            
            if not query_words:
                # Si no hay palabras válidas, retornar el inicio
                return text[:max_length] + "..." if len(text) > max_length else text
            
            # Buscar la primera aparición de cualquier palabra de la consulta
            best_start = 0
            best_score = 0
            
            for i in range(0, len(text_lower) - 50, 10):  # Buscar cada 10 caracteres
                window = text_lower[i:i + max_length]
                score = sum(1 for word in query_words if word in window)
                
                if score > best_score:
                    best_score = score
                    best_start = i
            
            # Ajustar el inicio para evitar cortar palabras
            while best_start > 0 and text[best_start] not in [' ', '.', '\n']:
                best_start -= 1
            
            # Extraer el fragmento
            excerpt = text[best_start:best_start + max_length].strip()
            
            # Agregar puntos suspensivos si es necesario
            if best_start > 0:
                excerpt = "..." + excerpt
            if len(text) > best_start + max_length:
                excerpt = excerpt + "..."
            
            return excerpt
            
        except Exception as e:
            logger.warning("Failed to create excerpt", error=str(e))
            return text[:max_length] + "..." if len(text) > max_length else text


# Singleton service instance
_vector_service_instance: Optional[VectorStoreService] = None


def get_vector_service() -> VectorStoreService:
    """Obtener instancia singleton del servicio vectorial."""
    global _vector_service_instance
    
    if _vector_service_instance is None:
        _vector_service_instance = VectorStoreService()
    
    return _vector_service_instance


async def store_conversation_data(
    conversation_id: str,
    transcription: str,
    structured_data: Dict[str, Any],
    unstructured_data: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None
) -> VectorStoreResponse:
    """
    Función de conveniencia para almacenar conversación.
    
    Args:
        conversation_id: ID único de la conversación
        transcription: Texto transcrito
        structured_data: Información estructurada extraída
        unstructured_data: Información no estructurada extraída
        metadata: Metadata adicional opcional
        
    Returns:
        VectorStoreResponse con información del almacenamiento
    """
    service = get_vector_service()
    return await service.store_conversation(
        conversation_id, transcription, structured_data, unstructured_data, metadata
    )

