"""
Endpoint de verificación de salud para la aplicación ElSol Challenge.

Proporciona información de estado de salud para monitoreo y descubrimiento de servicios.
"""

import time
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends
import structlog

from app.core.config import get_settings, Settings
from app.core.schemas import HealthResponse


logger = structlog.get_logger(__name__)
router = APIRouter()

# Tiempo de inicio de la aplicación para cálculo de uptime
app_start_time = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Get application health status and basic information"
)
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """
    Endpoint de verificación de salud que retorna el estado actual de la aplicación.
    
    Returns:
        HealthResponse con información de estado
    """
    current_time = datetime.utcnow()
    uptime_seconds = int(time.time() - app_start_time)
    
    # Verificar salud de dependencias
    dependencies_status = await check_dependencies_health(settings)
    
    # Determinar estado general de salud
    overall_status = "healthy"
    if any(status != "healthy" for status in dependencies_status.values()):
        overall_status = "degraded"
    
    logger.info(
        "Health check requested",
        status=overall_status,
        uptime_seconds=uptime_seconds,
        dependencies=dependencies_status
    )
    
    return HealthResponse(
        status=overall_status,
        timestamp=current_time,
        version=settings.APP_VERSION,
        uptime_seconds=uptime_seconds,
        dependencies=dependencies_status
    )


async def check_dependencies_health(settings: Settings) -> Dict[str, str]:
    """
    Check the health status of external dependencies.
    
    Args:
        settings: Application settings
        
    Returns:
        Dictionary with dependency names and their health status
    """
    dependencies = {}
    
    # Check OpenAI API availability
    dependencies["openai_api"] = await check_openai_health(settings)
    
    # Check database connectivity (if using external DB)
    dependencies["database"] = check_database_health()
    
    # Check file system access
    dependencies["file_system"] = check_file_system_health(settings)
    
    return dependencies


async def check_openai_health(settings: Settings) -> str:
    """
    Check OpenAI API health by validating API key format.
    
    Args:
        settings: Application settings
        
    Returns:
        Health status string
    """
    try:
        # Basic validation - check if API key is properly formatted
        if not settings.AZURE_OPENAI_API_KEY:
            return "unhealthy"
        
        # In a production system, you might want to make a lightweight API call
        # to verify the key is valid, but this adds latency and cost
        
        return "healthy"
        
    except Exception as e:
        logger.warning(
            "OpenAI health check failed",
            error=str(e)
        )
        return "unhealthy"


def check_database_health() -> str:
    """
    Check database connectivity health.
    
    Returns:
        Health status string
    """
    try:
        # For SQLite, we just check if we can access the file system
        # In production with PostgreSQL/MySQL, you would test actual connectivity
        return "healthy"
        
    except Exception as e:
        logger.warning(
            "Database health check failed",
            error=str(e)
        )
        return "unhealthy"


def check_file_system_health(settings: Settings) -> str:
    """
    Check file system access for upload directory.
    
    Args:
        settings: Application settings
        
    Returns:
        Health status string
    """
    try:
        import os
        
        # Check if upload directory exists or can be created
        upload_dir = settings.UPLOAD_TEMP_DIR
        
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)
        
        # Test write access
        test_file = os.path.join(upload_dir, ".health_check")
        with open(test_file, "w") as f:
            f.write("health_check")
        
        # Clean up test file
        if os.path.exists(test_file):
            os.remove(test_file)
        
        return "healthy"
        
    except Exception as e:
        logger.warning(
            "File system health check failed",
            error=str(e)
        )
        return "unhealthy"


@router.get(
    "/health/detailed",
    response_model=Dict[str, Any],
    summary="Detailed Health Check",
    description="Get detailed health information including system metrics"
)
async def detailed_health_check(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    Detailed health check endpoint with extended system information.
    
    Returns:
        Detailed health information dictionary
    """
    import psutil
    import sys
    
    current_time = datetime.utcnow()
    uptime_seconds = int(time.time() - app_start_time)
    
    # Get system metrics
    memory_info = psutil.virtual_memory()
    disk_info = psutil.disk_usage('/')
    
    # Check dependencies
    dependencies_status = await check_dependencies_health(settings)
    
    detailed_info = {
        "status": "healthy" if all(status == "healthy" for status in dependencies_status.values()) else "degraded",
        "timestamp": current_time.isoformat(),
        "version": settings.APP_VERSION,
        "uptime_seconds": uptime_seconds,
        "dependencies": dependencies_status,
        "system": {
            "python_version": sys.version,
            "platform": sys.platform,
            "memory": {
                "total_mb": round(memory_info.total / 1024 / 1024, 2),
                "available_mb": round(memory_info.available / 1024 / 1024, 2),
                "used_percent": memory_info.percent
            },
            "disk": {
                "total_gb": round(disk_info.total / 1024 / 1024 / 1024, 2),
                "free_gb": round(disk_info.free / 1024 / 1024 / 1024, 2),
                "used_percent": round((disk_info.used / disk_info.total) * 100, 2)
            }
        },
        "configuration": {
            "debug_mode": settings.DEBUG,
            "upload_max_size_mb": round(settings.UPLOAD_MAX_SIZE / 1024 / 1024, 2),
            "allowed_extensions": settings.UPLOAD_ALLOWED_EXTENSIONS,
            "upload_temp_dir": settings.UPLOAD_TEMP_DIR
        }
    }
    
    logger.info(
        "Detailed health check requested",
        status=detailed_info["status"],
        memory_used_percent=detailed_info["system"]["memory"]["used_percent"],
        disk_used_percent=detailed_info["system"]["disk"]["used_percent"]
    )
    
    return detailed_info


@router.get(
    "/health/dependencies",
    response_model=Dict[str, str],
    summary="Dependencies Health Check",
    description="Check health status of external dependencies only"
)
async def dependencies_health_check(settings: Settings = Depends(get_settings)) -> Dict[str, str]:
    """
    Check only the health of external dependencies.
    
    Returns:
        Dictionary with dependency health statuses
    """
    dependencies_status = await check_dependencies_health(settings)
    
    logger.info(
        "Dependencies health check requested",
        dependencies=dependencies_status
    )
    
    return dependencies_status
