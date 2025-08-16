"""
Endpoints de API para Vector Store - ElSol Challenge.

Endpoints para verificación y gestión básica del almacenamiento vectorial.
Requisito 2: Almacenamiento Vectorial
"""

from typing import List
import structlog
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

from app.core.schemas import VectorStoreStatus, StoredConversation, ErrorResponse
from app.services.vector_service import get_vector_service, VectorStoreService, VectorStoreError

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get(
    "/vector-store/status",
    response_model=VectorStoreStatus,
    summary="Vector Store Status",
    description="Obtener estado actual del vector store y estadísticas básicas"
)
async def get_vector_store_status(
    vector_service: VectorStoreService = Depends(get_vector_service)
):
    """
    Endpoint para verificar el estado del vector store.
    
    Retorna información sobre:
    - Estado de conexión con Chroma DB
    - Número de documentos almacenados
    - Configuración del modelo de embeddings
    - Directorio de persistencia
    """
    try:
        logger.info("Getting vector store status")
        
        status = await vector_service.get_vector_store_status()
        
        logger.info("Vector store status retrieved successfully",
                   total_documents=status.total_documents,
                   status=status.status)
        
        return status
        
    except VectorStoreError as e:
        logger.error("Vector store error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Vector store error: {str(e)}"
        )
    except Exception as e:
        logger.error("Unexpected error getting vector store status", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting vector store status"
        )


@router.get(
    "/vector-store/conversations",
    response_model=List[StoredConversation],
    summary="List Stored Conversations",
    description="Listar conversaciones almacenadas en el vector store"
)
async def list_stored_conversations(
    limit: int = Query(20, ge=1, le=100, description="Número máximo de conversaciones a retornar"),
    vector_service: VectorStoreService = Depends(get_vector_service)
):
    """
    Endpoint para listar conversaciones almacenadas en el vector store.
    
    Parámetros:
    - limit: Número máximo de conversaciones a retornar (1-100, default 20)
    
    Retorna lista de conversaciones con:
    - ID en vector store
    - ID de conversación original
    - Nombre del paciente (si disponible)
    - Preview del texto almacenado
    - Metadata asociada
    """
    try:
        logger.info("Listing stored conversations", limit=limit)
        
        conversations = await vector_service.list_stored_conversations(limit=limit)
        
        logger.info("Stored conversations retrieved successfully",
                   count=len(conversations))
        
        return conversations
        
    except VectorStoreError as e:
        logger.error("Vector store error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Vector store error: {str(e)}"
        )
    except Exception as e:
        logger.error("Unexpected error listing conversations", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Internal server error while listing conversations"
        )


@router.get(
    "/vector-store/conversations/{conversation_id}",
    response_model=StoredConversation,
    summary="Get Conversation by ID",
    description="Obtener conversación específica almacenada en vector store"
)
async def get_stored_conversation(
    conversation_id: str,
    vector_service: VectorStoreService = Depends(get_vector_service)
):
    """
    Endpoint para obtener una conversación específica del vector store.
    
    Parámetros:
    - conversation_id: ID único de la conversación
    
    Retorna:
    - Datos completos de la conversación almacenada
    - Metadata completa
    - Texto completo almacenado
    """
    try:
        logger.info("Getting stored conversation", conversation_id=conversation_id)
        
        conversation = await vector_service.get_conversation_by_id(conversation_id)
        
        if not conversation:
            logger.warning("Conversation not found in vector store", 
                          conversation_id=conversation_id)
            raise HTTPException(
                status_code=404,
                detail=f"Conversation with ID {conversation_id} not found in vector store"
            )
        
        logger.info("Stored conversation retrieved successfully",
                   conversation_id=conversation_id,
                   patient_name=conversation.patient_name)
        
        return conversation
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except VectorStoreError as e:
        logger.error("Vector store error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Vector store error: {str(e)}"
        )
    except Exception as e:
        logger.error("Unexpected error getting conversation", 
                    conversation_id=conversation_id, 
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting conversation"
        )


@router.get(
    "/vector-store/health",
    summary="Vector Store Health Check",
    description="Health check específico para el vector store"
)
async def vector_store_health_check(
    vector_service: VectorStoreService = Depends(get_vector_service)
):
    """
    Health check específico para el vector store.
    
    Verifica:
    - Conexión con Chroma DB
    - Disponibilidad del modelo de embeddings
    - Acceso al directorio de persistencia
    """
    try:
        logger.info("Performing vector store health check")
        
        # Verificar estado básico
        status = await vector_service.get_vector_store_status()
        
        health_data = {
            "service": "vector_store",
            "status": status.status,
            "chroma_accessible": status.status == "operational",
            "embedding_model": status.embedding_model,
            "total_documents": status.total_documents,
            "collection_name": status.collection_name
        }
        
        if status.status == "operational":
            logger.info("Vector store health check passed")
            return JSONResponse(
                status_code=200,
                content=health_data
            )
        else:
            logger.warning("Vector store health check failed", status=status.status)
            return JSONResponse(
                status_code=503,
                content={**health_data, "message": "Vector store not operational"}
            )
        
    except Exception as e:
        logger.error("Vector store health check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "service": "vector_store",
                "status": "unhealthy",
                "error": str(e),
                "chroma_accessible": False
            }
        )

