"""
Endpoints de API para Chat RAG - ElSol Challenge.

Endpoints para el sistema de chat médico con retrieval-augmented generation.
Requisito 3: Chatbot vía API
"""

import time
from typing import Dict, Any
import structlog
from fastapi import APIRouter, HTTPException, Depends, Body, Query
from fastapi.responses import JSONResponse

from app.core.schemas import ChatQuery, ChatResponse, ErrorResponse, ChatStats
from app.services.chat_service import get_chat_service, ChatService, ChatServiceError

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat Médico con RAG",
    description="""
    Endpoint principal para consultas médicas en lenguaje natural.
    
    Utiliza un sistema RAG completo que:
    1. Analiza la consulta y detecta intención
    2. Busca información relevante en conversaciones almacenadas  
    3. Genera respuesta usando Azure OpenAI GPT-4
    4. Proporciona fuentes y nivel de confianza
    
    ## Casos de uso específicos:
    - "¿Qué enfermedad tiene Pepito Gómez?"
    - "Listame los pacientes con diabetes"
    - "¿Qué síntomas reportó María ayer?"
    - "¿Cuántos pacientes tienen hipertensión?"
    """
)
async def chat_query(
    query_data: ChatQuery = Body(...),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Procesar consulta médica usando sistema RAG.
    
    Args:
        query_data: Datos de la consulta (query, max_results, filters, etc.)
        chat_service: Servicio de chat inyectado
        
    Returns:
        Respuesta estructurada con answer, sources, confidence, etc.
        
    Raises:
        HTTPException: Si la consulta falla
    """
    request_start = time.time()
    
    try:
        logger.info("Processing chat query",
                   query=query_data.query,
                   max_results=query_data.max_results,
                   has_filters=bool(query_data.filters))
        
        # Validaciones adicionales
        if len(query_data.query.strip()) < 3:
            raise HTTPException(
                status_code=400,
                detail="La consulta debe tener al menos 3 caracteres"
            )
        
        # Procesar consulta con el servicio RAG
        response = await chat_service.process_chat_query(query_data)
        
        # Log de respuesta exitosa
        logger.info("Chat query processed successfully",
                   query=query_data.query,
                   intent=response.intent,
                   confidence=response.confidence,
                   sources_count=len(response.sources),
                   processing_time_ms=response.processing_time_ms)
        
        return response
        
    except ChatServiceError as e:
        logger.error("Chat service error",
                    query=query_data.query,
                    error=str(e))
        
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando consulta médica: {str(e)}"
        )
        
    except ValueError as e:
        logger.warning("Invalid query parameters",
                      query=query_data.query,
                      error=str(e))
        
        raise HTTPException(
            status_code=400,
            detail=f"Parámetros de consulta inválidos: {str(e)}"
        )
        
    except Exception as e:
        request_time = int((time.time() - request_start) * 1000)
        logger.error("Unexpected error in chat endpoint",
                    query=query_data.query,
                    error=str(e),
                    request_time_ms=request_time)
        
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor. Por favor intenta de nuevo."
        )


@router.post(
    "/chat/quick",
    response_model=ChatResponse,
    summary="Chat Rápido",
    description="Versión simplificada del endpoint de chat para consultas rápidas"
)
async def quick_chat(
    query: str = Body(..., embed=True, min_length=3, max_length=500),
    max_results: int = Body(3, embed=True, ge=1, le=10),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Endpoint simplificado para consultas rápidas.
    
    Args:
        query: Consulta médica en texto plano
        max_results: Número máximo de resultados (1-10)
        chat_service: Servicio de chat inyectado
        
    Returns:
        Respuesta del chat con información médica
    """
    try:
        logger.info("Processing quick chat query", query=query)
        
        # Crear objeto ChatQuery
        query_data = ChatQuery(
            query=query,
            max_results=max_results,
            include_sources=True
        )
        
        response = await chat_service.process_chat_query(query_data)
        
        logger.info("Quick chat query processed", 
                   query=query,
                   intent=response.intent)
        
        return response
        
    except Exception as e:
        logger.error("Quick chat error", query=query, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error en consulta rápida: {str(e)}"
        )


@router.get(
    "/chat/examples",
    summary="Ejemplos de Consultas",
    description="Obtener ejemplos de consultas que el sistema puede manejar"
)
async def get_chat_examples():
    """
    Obtener ejemplos de consultas médicas que el sistema puede procesar.
    
    Returns:
        Diccionario con ejemplos organizados por tipo de consulta
    """
    examples = {
        "patient_info": {
            "description": "Consultas sobre información específica de pacientes",
            "examples": [
                "¿Qué enfermedad tiene Pepito Gómez?",
                "¿Cuál es el diagnóstico de María García?",
                "¿Qué le pasa a Juan Pérez?",
                "Información del paciente Carlos López"
            ]
        },
        "condition_list": {
            "description": "Listas de pacientes por condición médica",
            "examples": [
                "Listame los pacientes con diabetes",
                "¿Quiénes tienen hipertensión?",
                "Pacientes con asma",
                "¿Cuántos pacientes tienen migraña?"
            ]
        },
        "symptom_search": {
            "description": "Búsquedas por síntomas específicos",
            "examples": [
                "¿Quién tiene dolor de cabeza?",
                "Pacientes con fiebre",
                "¿Quién reportó tos?",
                "Síntomas de mareos"
            ]
        },
        "medication_info": {
            "description": "Información sobre medicamentos y tratamientos",
            "examples": [
                "¿Qué medicamentos toma Ana?",
                "Tratamiento para la diabetes",
                "¿Qué medicina se recetó para el dolor?",
                "Medicamentos para la presión"
            ]
        },
        "temporal_queries": {
            "description": "Consultas con componente temporal",
            "examples": [
                "¿Qué pacientes vinieron ayer?",
                "Consultas de la semana pasada",
                "¿Cuándo fue la última visita de Pedro?",
                "Pacientes de este mes"
            ]
        }
    }
    
    return {
        "examples": examples,
        "tips": [
            "Usa nombres específicos para mejores resultados",
            "Incluye términos médicos cuando sea posible",
            "Las consultas más específicas obtienen respuestas más precisas",
            "Puedes preguntar por síntomas, diagnósticos o tratamientos"
        ],
        "supported_intents": [
            "patient_info",
            "condition_list", 
            "symptom_search",
            "medication_info",
            "temporal_query",
            "general_query"
        ]
    }


@router.get(
    "/chat/stats",
    response_model=ChatStats,
    summary="Estadísticas del Chat",
    description="Obtener estadísticas de uso del sistema de chat"
)
async def get_chat_stats():
    """
    Obtener estadísticas del sistema de chat.
    
    Returns:
        Estadísticas de uso, performance y distribución de consultas
    """
    # TODO: Implementar almacenamiento real de estadísticas
    # Por ahora retornamos estadísticas de ejemplo
    
    stats = ChatStats(
        total_queries=0,
        successful_queries=0,
        failed_queries=0,
        avg_response_time_ms=0.0,
        intent_distribution={},
        avg_confidence=0.0,
        most_common_queries=[]
    )
    
    logger.info("Chat stats requested")
    
    return stats


@router.post(
    "/chat/validate",
    summary="Validar Consulta",
    description="Validar que una consulta puede ser procesada por el sistema"
)
async def validate_chat_query(
    query: str = Body(..., embed=True),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Validar consulta antes de procesarla completamente.
    
    Args:
        query: Consulta a validar
        chat_service: Servicio de chat
        
    Returns:
        Información sobre la validez y análisis preliminar de la consulta
    """
    try:
        logger.info("Validating chat query", query=query)
        
        # Validaciones básicas
        if len(query.strip()) < 3:
            return {
                "valid": False,
                "reason": "Consulta demasiado corta (mínimo 3 caracteres)",
                "suggestions": ["Intenta ser más específico en tu consulta"]
            }
        
        if len(query) > 1000:
            return {
                "valid": False,
                "reason": "Consulta demasiado larga (máximo 1000 caracteres)",
                "suggestions": ["Intenta ser más conciso en tu consulta"]
            }
        
        # Análisis preliminar usando el servicio de chat
        # TODO: Implementar método de análisis rápido en ChatService
        
        return {
            "valid": True,
            "confidence": "high",
            "estimated_intent": "general_query",
            "suggestions": [
                "Tu consulta parece válida",
                "Puedes proceder con la consulta completa"
            ]
        }
        
    except Exception as e:
        logger.error("Query validation error", query=query, error=str(e))
        return {
            "valid": False,
            "reason": f"Error en validación: {str(e)}",
            "suggestions": ["Intenta reformular tu consulta"]
        }


@router.get(
    "/chat/health",
    summary="Health Check del Chat",
    description="Verificar estado del sistema de chat y dependencias"
)
async def chat_health_check(
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Health check específico para el sistema de chat.
    
    Returns:
        Estado del chat y sus dependencias
    """
    try:
        start_time = time.time()
        
        # Verificar componentes del chat
        health_data = {
            "service": "chat_rag",
            "status": "healthy",
            "components": {
                "chat_service": "operational",
                "vector_store": "unknown",  # TODO: Verificar vector store
                "openai_service": "unknown"  # TODO: Verificar OpenAI
            },
            "capabilities": [
                "patient_info_queries",
                "condition_list_queries", 
                "symptom_search",
                "medication_info",
                "temporal_queries"
            ],
            "response_time_ms": 0
        }
        
        # TODO: Agregar verificaciones reales de dependencias
        
        response_time = int((time.time() - start_time) * 1000)
        health_data["response_time_ms"] = response_time
        
        logger.info("Chat health check completed", response_time_ms=response_time)
        
        return JSONResponse(
            status_code=200,
            content=health_data
        )
        
    except Exception as e:
        logger.error("Chat health check failed", error=str(e))
        
        return JSONResponse(
            status_code=503,
            content={
                "service": "chat_rag",
                "status": "unhealthy",
                "error": str(e),
                "components": {
                    "chat_service": "error",
                    "vector_store": "unknown",
                    "openai_service": "unknown"
                }
            }
        )
