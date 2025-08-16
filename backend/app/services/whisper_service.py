"""
Servicio de Transcripción Whisper para la aplicación ElSol Challenge.

Este servicio maneja la transcripción de audio usando Whisper local (offline).
Proporciona funcionalidad para transcribir archivos de audio y extraer metadatos.
"""

import os
import time
import asyncio
import logging
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
import structlog
import whisper
import torch

from app.core.config import get_settings


logger = structlog.get_logger(__name__)
settings = get_settings()


class WhisperTranscriptionError(Exception):
    """Excepción personalizada para errores de transcripción de Whisper."""
    pass


class LocalWhisperService:
    """
    Clase de servicio para manejar transcripción de audio usando Whisper local.
    
    Este servicio utiliza el modelo Whisper de OpenAI ejecutado localmente,
    sin necesidad de conexión a internet o API keys.
    """
    
    def __init__(self):
        """Inicializar el servicio Whisper local."""
        self.model_name = settings.WHISPER_MODEL
        self.device = settings.WHISPER_DEVICE
        self.model = None
        self.timeout = settings.TRANSCRIPTION_TIMEOUT
        
        # Configurar logging de whisper para evitar ruido
        logging.getLogger("whisper").setLevel(logging.WARNING)
        
    def _load_model(self):
        """
        Cargar el modelo Whisper de forma lazy (solo cuando se necesite).
        
        Raises:
            WhisperTranscriptionError: Si el modelo no se puede cargar
        """
        if self.model is None:
            try:
                logger.info(
                    "Cargando modelo Whisper local",
                    model=self.model_name,
                    device=self.device
                )
                
                # Verificar si CUDA está disponible
                if self.device == "cuda" and not torch.cuda.is_available():
                    logger.warning("CUDA no disponible, usando CPU")
                    self.device = "cpu"
                
                # Cargar modelo
                self.model = whisper.load_model(
                    self.model_name, 
                    device=self.device
                )
                
                logger.info(
                    "Modelo Whisper cargado exitosamente",
                    model=self.model_name,
                    device=self.device
                )
                
            except Exception as e:
                error_msg = f"Error cargando modelo Whisper: {str(e)}"
                logger.error(error_msg)
                raise WhisperTranscriptionError(error_msg) from e
    
    async def transcribe_audio(
        self, 
        file_path: str,
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribir un archivo de audio usando Whisper local.
        
        Args:
            file_path: Ruta al archivo de audio a transcribir
            language: Código de idioma opcional (ej., 'es', 'en')
            prompt: Prompt de contexto opcional para mejorar la precisión de transcripción
            
        Returns:
            Diccionario conteniendo resultados de transcripción y metadatos
            
        Raises:
            WhisperTranscriptionError: Si la transcripción falla
        """
        start_time = time.time()
        
        logger.info(
            "Iniciando transcripción de audio local",
            file_path=file_path,
            language=language,
            model=self.model_name
        )
        
        try:
            # Validar archivo existe y es legible
            if not os.path.exists(file_path):
                raise WhisperTranscriptionError(f"Archivo de audio no encontrado: {file_path}")
            
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                raise WhisperTranscriptionError("El archivo de audio está vacío")
            
            if file_size > settings.UPLOAD_MAX_SIZE:
                raise WhisperTranscriptionError(
                    f"Tamaño del archivo ({file_size}) excede el límite máximo ({settings.UPLOAD_MAX_SIZE})"
                )
            
            # Cargar modelo si no está cargado
            self._load_model()
            
            # Realizar transcripción
            transcription_result = await self._perform_local_transcription(
                file_path, language, prompt
            )
            
            processing_time = int(time.time() - start_time)
            
            # Calcular duración del audio
            audio_duration = transcription_result.get("segments", [])
            if audio_duration:
                duration_seconds = int(audio_duration[-1]["end"]) if audio_duration else None
            else:
                duration_seconds = None
            
            logger.info(
                "Transcripción de audio completada exitosamente",
                file_path=file_path,
                processing_time_seconds=processing_time,
                text_length=len(transcription_result["text"]),
                audio_duration_seconds=duration_seconds
            )
            
            return {
                "text": transcription_result["text"],
                "language": transcription_result.get("language", language),
                "duration": duration_seconds,
                "processing_time_seconds": processing_time,
                "model_used": self.model_name,
                "confidence_score": self._calculate_confidence_score(
                    transcription_result["text"], 
                    transcription_result.get("segments", [])
                ),
                "segments": transcription_result.get("segments", [])  # Para futura diarización
            }
            
        except Exception as e:
            processing_time = int(time.time() - start_time)
            error_msg = f"Transcripción falló: {str(e)}"
            
            logger.error(
                "Transcripción de audio falló",
                file_path=file_path,
                error=str(e),
                processing_time_seconds=processing_time
            )
            
            raise WhisperTranscriptionError(error_msg) from e
    
    async def _perform_local_transcription(
        self,
        file_path: str,
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Realizar la transcripción local usando Whisper.
        
        Args:
            file_path: Ruta al archivo de audio
            language: Código de idioma opcional
            prompt: Prompt de contexto opcional
            
        Returns:
            Resultado de transcripción de Whisper
        """
        # Preparar parámetros de transcripción
        transcription_params = {
            "verbose": False,  # Menos output verboso
            "word_timestamps": True,  # Para futura diarización
        }
        
        # Agregar parámetros opcionales
        if language:
            transcription_params["language"] = language
            
        if prompt:
            transcription_params["initial_prompt"] = prompt
        
        # Ejecutar en thread pool para evitar bloqueo
        loop = asyncio.get_event_loop()
        
        def transcribe_sync():
            return self.model.transcribe(file_path, **transcription_params)
        
        transcription = await loop.run_in_executor(None, transcribe_sync)
        
        return transcription
    
    def _calculate_confidence_score(
        self, 
        text: str, 
        segments: list = None
    ) -> str:
        """
        Calcular un puntaje de confianza basado en características del texto y segmentos.
        
        Args:
            text: Texto transcrito
            segments: Segmentos de Whisper con timestamps y probabilidades
            
        Returns:
            Puntaje de confianza como string ("high", "medium", "low")
        """
        if not text or len(text.strip()) < 10:
            return "low"
        
        # Usar probabilidades de segmentos si están disponibles
        if segments:
            try:
                # Calcular promedio de probabilidades de los segmentos
                probabilities = []
                for segment in segments:
                    if "avg_logprob" in segment:
                        # Convertir log probability a probability
                        prob = min(1.0, max(0.0, 2 ** segment["avg_logprob"]))
                        probabilities.append(prob)
                
                if probabilities:
                    avg_prob = sum(probabilities) / len(probabilities)
                    if avg_prob > 0.8:
                        return "high"
                    elif avg_prob > 0.6:
                        return "medium"
                    else:
                        return "low"
            except Exception:
                # Fallback a heurísticas simples si hay error
                pass
        
        # Heurísticas simples para estimación de confianza
        word_count = len(text.split())
        avg_word_length = sum(len(word) for word in text.split()) / word_count if word_count > 0 else 0
        
        # Contar posibles problemas de transcripción
        issues = 0
        if "[inaudible]" in text.lower() or "[inaudible]" in text.lower():
            issues += 1
        if "..." in text:
            issues += 1
        if len([c for c in text if c == "?"]) > word_count * 0.1:  # Demasiados signos de pregunta
            issues += 1
        
        # Puntuación básica
        if issues == 0 and word_count > 20 and avg_word_length > 3:
            return "high"
        elif issues <= 1 and word_count > 10:
            return "medium"
        else:
            return "low"
    
    def validate_audio_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validar archivo de audio antes de la transcripción.
        
        Args:
            file_path: Ruta al archivo de audio
            
        Returns:
            Tupla de (es_válido, mensaje_error)
        """
        try:
            # Verificar que el archivo existe
            if not os.path.exists(file_path):
                return False, "El archivo no existe"
            
            # Verificar tamaño del archivo
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False, "El archivo está vacío"
            
            if file_size > settings.UPLOAD_MAX_SIZE:
                return False, f"El tamaño del archivo excede el límite máximo de {settings.UPLOAD_MAX_SIZE} bytes"
            
            # Verificar extensión del archivo
            file_extension = Path(file_path).suffix.lower().lstrip('.')
            if file_extension not in settings.extensions_list:
                return False, f"Extensión de archivo '{file_extension}' no permitida"
            
            # Validación básica de encabezado de archivo (números mágicos)
            if not self._validate_audio_format(file_path):
                return False, "Formato de archivo de audio inválido"
            
            return True, None
            
        except Exception as e:
            return False, f"Error de validación: {str(e)}"
    
    def _validate_audio_format(self, file_path: str) -> bool:
        """
        Validar formato de archivo de audio verificando números mágicos.
        
        Args:
            file_path: Ruta al archivo de audio
            
        Returns:
            True si es formato de audio válido, False en caso contrario
        """
        try:
            with open(file_path, 'rb') as f:
                header = f.read(12)
            
            # Validación de formato WAV
            if header[:4] == b'RIFF' and header[8:12] == b'WAVE':
                return True
            
            # Validación de formato MP3 (ID3v2 o frame de audio)
            if header[:3] == b'ID3' or header[:2] == b'\xff\xfb':
                return True
            
            # Otros formatos de audio se pueden agregar aquí
            
            return False
            
        except Exception:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Obtener información sobre el modelo Whisper cargado.
        
        Returns:
            Diccionario con información del modelo
        """
        return {
            "model_name": self.model_name,
            "device": self.device,
            "is_loaded": self.model is not None,
            "cuda_available": torch.cuda.is_available(),
            "current_device": str(self.device)
        }


# Funciones de utilidad para instanciación del servicio
def get_whisper_service() -> LocalWhisperService:
    """Obtener una instancia del servicio Whisper."""
    return LocalWhisperService()


async def transcribe_audio_file(
    file_path: str,
    language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Función de conveniencia para transcribir un archivo de audio.
    
    Args:
        file_path: Ruta al archivo de audio
        language: Código de idioma opcional
        
    Returns:
        Resultados de transcripción
    """
    service = get_whisper_service()
    return await service.transcribe_audio(file_path, language)


# Prompt de conversación médica para mejorar precisión
MEDICAL_CONVERSATION_PROMPT = """
Esta es una transcripción de una conversación médica entre un doctor y un paciente. 
El diálogo puede incluir información como nombres, edades, síntomas, diagnósticos, 
medicamentos, y recomendaciones médicas. Por favor transcribe con precisión todos 
los términos médicos y datos personales mencionados.
"""

# Configuración de modelos Whisper disponibles
WHISPER_MODELS_INFO = {
    "tiny": {"size": "~39 MB", "speed": "~32x", "accuracy": "Básica"},
    "base": {"size": "~74 MB", "speed": "~16x", "accuracy": "Buena"},
    "small": {"size": "~244 MB", "speed": "~6x", "accuracy": "Muy buena"},
    "medium": {"size": "~769 MB", "speed": "~2x", "accuracy": "Excelente"},
    "large": {"size": "~1550 MB", "speed": "~1x", "accuracy": "Máxima"},
    "large-v2": {"size": "~1550 MB", "speed": "~1x", "accuracy": "Máxima mejorada"},
    "large-v3": {"size": "~1550 MB", "speed": "~1x", "accuracy": "Máxima última versión"}
}