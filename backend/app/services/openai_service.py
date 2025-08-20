"""
Servicio de Extracción de Información OpenAI para la aplicación ElSol Challenge.

Este servicio maneja la extracción de información estructurada y no estructurada
de texto transcrito usando los modelos GPT de OpenAI.
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, Tuple
import structlog
from openai import AzureOpenAI
from openai.types.chat import ChatCompletion
from dotenv import load_dotenv

from app.core.config import get_settings

# Cargar variables de entorno
load_dotenv()#override=True)


logger = structlog.get_logger(__name__)
settings = get_settings()


class OpenAIExtractionError(Exception):
    """Excepción personalizada para errores de extracción de información de OpenAI."""
    pass


class OpenAIService:
    """
    Clase de servicio para extraer información estructurada y no estructurada
    de texto transcrito usando los modelos GPT de OpenAI.
    """
    
    def __init__(self):
        """Inicializar el servicio Azure OpenAI con configuración del cliente."""
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_API_ENDPOINT")
        )
        self.model = os.getenv("AZURE_OPENAI_DEPLOYMENT")  # Modelo configurado en Azure
        self.max_tokens = 1500
        self.temperature = 0.2  # Temperatura baja para extracción consistente
        
    async def extract_information(
        self, 
        transcription_text: str,
        context: Optional[str] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Extraer información estructurada y no estructurada de la transcripción.
        
        Args:
            transcription_text: El texto transcrito a analizar
            context: Contexto opcional sobre la conversación
            
        Returns:
            Tupla de diccionarios (structured_data, unstructured_data)
            
        Raises:
            OpenAIExtractionError: Si la extracción falla
        """
        logger.info(
            "Starting information extraction",
            text_length=len(transcription_text),
            context=context
        )
        
        try:
            # Extract structured information
            structured_data = await self._extract_structured_data(transcription_text, context)
            
            # Extract unstructured information
            unstructured_data = await self._extract_unstructured_data(transcription_text, context)
            
            logger.info(
                "Information extraction completed successfully",
                structured_fields=len(structured_data),
                unstructured_fields=len(unstructured_data)
            )
            
            return structured_data, unstructured_data
            
        except Exception as e:
            error_msg = f"Information extraction failed: {str(e)}"
            logger.error(
                "Information extraction failed",
                error=str(e),
                text_length=len(transcription_text)
            )
            raise OpenAIExtractionError(error_msg) from e
    
    async def _extract_structured_data(
        self, 
        text: str, 
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract structured information using OpenAI GPT.
        
        Args:
            text: Transcribed text
            context: Optional context
            
        Returns:
            Dictionary with structured data fields
        """
        system_prompt = self._get_structured_extraction_prompt()
        user_prompt = self._format_user_prompt(text, context, "structured")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self._call_openai_api(messages)
        
        try:
            # Parse JSON response
            extracted_data = json.loads(response)
            
            # Validate and clean the extracted data
            validated_data = self._validate_structured_data(extracted_data)
            
            return validated_data
            
        except json.JSONDecodeError as e:
            logger.warning(
                "Failed to parse structured data JSON",
                response=response,
                error=str(e)
            )
            return {}
    
    async def _extract_unstructured_data(
        self, 
        text: str, 
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract unstructured information using OpenAI GPT.
        
        Args:
            text: Transcribed text
            context: Optional context
            
        Returns:
            Dictionary with unstructured data fields
        """
        system_prompt = self._get_unstructured_extraction_prompt()
        user_prompt = self._format_user_prompt(text, context, "unstructured")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self._call_openai_api(messages)
        
        try:
            # Parse JSON response
            extracted_data = json.loads(response)
            
            # Validate and clean the extracted data
            validated_data = self._validate_unstructured_data(extracted_data)
            
            return validated_data
            
        except json.JSONDecodeError as e:
            logger.warning(
                "Failed to parse unstructured data JSON",
                response=response,
                error=str(e)
            )
            return {}
    
    async def _call_openai_api(self, messages: list) -> str:
        """
        Make API call to OpenAI with error handling and retries.
        Configured for JSON extraction tasks.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Response content from OpenAI
        """
        try:
            loop = asyncio.get_event_loop()
            
            response: ChatCompletion = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    response_format={"type": "json_object"}
                )
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            logger.error(
                "OpenAI API call failed",
                error=str(e),
                model=self.model
            )
            raise OpenAIExtractionError(f"API call failed: {str(e)}")
    
    async def _call_openai_chat_api(self, messages: list) -> str:
        """
        Make API call to OpenAI for chat responses (text format).
        Configured for natural language responses without JSON forcing.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Response content from OpenAI in natural language
        """
        try:
            loop = asyncio.get_event_loop()
            
            response: ChatCompletion = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=2000,  # Más tokens para respuestas de chat
                    temperature=0.3,  # Ligeramente más creativo para chat
                    # NO incluir response_format para permitir texto plano
                )
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            logger.error(
                "OpenAI Chat API call failed",
                error=str(e),
                model=self.model
            )
            raise OpenAIExtractionError(f"Chat API call failed: {str(e)}")
    
    def _get_structured_extraction_prompt(self) -> str:
        """Get system prompt for structured data extraction."""
        return """
Eres un asistente médico especializado en extraer información estructurada de conversaciones médicas.

Tu tarea es analizar una transcripción de conversación médica y extraer ÚNICAMENTE la información estructurada que esté explícitamente mencionada en el texto.

IMPORTANTE: 
- Solo incluye información que esté claramente mencionada en la transcripción
- Si un campo no se menciona, déjalo como null
- No inventes ni deduzcas información que no esté explícita
- Mantén la precisión sobre la creatividad

Debes responder ÚNICAMENTE con un objeto JSON válido que contenga estos campos:

{
  "nombre": "string o null - Nombre del paciente mencionado",
  "edad": "number o null - Edad en años si se menciona",
  "fecha": "string o null - Fecha mencionada en formato YYYY-MM-DD si es posible",
  "diagnostico": "string o null - Diagnóstico médico específico mencionado",
  "medico": "string o null - Nombre del médico o doctor mencionado",
  "medicamentos": "array de strings o null - Lista de medicamentos mencionados",
  "telefono": "string o null - Número de teléfono mencionado",
  "email": "string o null - Dirección de email mencionada"
}

Responde SOLO con el JSON, sin explicaciones adicionales.
"""
    
    def _get_unstructured_extraction_prompt(self) -> str:
        """Get system prompt for unstructured data extraction."""
        return """
Eres un asistente médico especializado en extraer información no estructurada de conversaciones médicas.

Tu tarea es analizar una transcripción de conversación médica y extraer información contextual, emocional y observacional.

Extrae información sobre:
- Síntomas mencionados (lista)
- Contexto de la conversación (string descriptivo)
- Observaciones del médico o paciente (string)
- Emociones detectadas en la conversación (lista)
- Nivel de urgencia percibido (string: "baja", "media", "alta")
- Recomendaciones dadas (lista)
- Preguntas importantes realizadas (lista)
- Respuestas clave proporcionadas (lista)

IMPORTANTE:
- Basa toda la información en lo que realmente se dice en la transcripción
- Para emociones, considera el tono y las palabras usadas
- Para urgencia, evalúa la gravedad de los síntomas mencionados

Debes responder ÚNICAMENTE con un objeto JSON válido:

{
  "sintomas": "array de strings o null - Lista de síntomas mencionados",
  "contexto": "string o null - Descripción del contexto de la conversación",
  "observaciones": "string o null - Observaciones relevantes",
  "emociones": "array de strings o null - Emociones detectadas",
  "urgencia": "string o null - Nivel de urgencia: 'baja', 'media', 'alta'",
  "recomendaciones": "array de strings o null - Recomendaciones dadas",
  "preguntas": "array de strings o null - Preguntas importantes",
  "respuestas": "array de strings o null - Respuestas clave"
}

Responde SOLO con el JSON, sin explicaciones adicionales.
"""
    
    def _format_user_prompt(self, text: str, context: Optional[str], extraction_type: str) -> str:
        """Format user prompt with transcription text and context."""
        prompt_parts = []
        
        if context:
            prompt_parts.append(f"CONTEXTO: {context}\n")
        
        prompt_parts.append(f"TRANSCRIPCIÓN A ANALIZAR:\n{text}")
        
        if extraction_type == "structured":
            prompt_parts.append("\nExtrae la información estructurada en formato JSON:")
        else:
            prompt_parts.append("\nExtrae la información no estructurada en formato JSON:")
        
        return "\n".join(prompt_parts)
    
    def _validate_structured_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean structured data extraction."""
        validated = {}
        
        # Define field validations
        field_validators = {
            "nombre": lambda x: str(x) if x and isinstance(x, str) else None,
            "edad": lambda x: int(x) if x is not None and str(x).isdigit() and 0 <= int(x) <= 150 else None,
            "fecha": lambda x: str(x) if x and isinstance(x, str) else None,
            "diagnostico": lambda x: str(x) if x and isinstance(x, str) else None,
            "medico": lambda x: str(x) if x and isinstance(x, str) else None,
            "medicamentos": lambda x: list(x) if x and isinstance(x, list) else None,
            "telefono": lambda x: str(x) if x and isinstance(x, str) else None,
            "email": lambda x: str(x) if x and isinstance(x, str) and "@" in str(x) else None
        }
        
        for field, validator in field_validators.items():
            try:
                validated[field] = validator(data.get(field))
            except (ValueError, TypeError):
                validated[field] = None
        
        return validated
    
    def _validate_unstructured_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean unstructured data extraction."""
        validated = {}
        
        # Define field validations
        field_validators = {
            "sintomas": lambda x: list(x) if x and isinstance(x, list) else None,
            "contexto": lambda x: str(x) if x and isinstance(x, str) else None,
            "observaciones": lambda x: str(x) if x and isinstance(x, str) else None,
            "emociones": lambda x: list(x) if x and isinstance(x, list) else None,
            "urgencia": lambda x: str(x).lower() if x and str(x).lower() in ["baja", "media", "alta"] else None,
            "recomendaciones": lambda x: list(x) if x and isinstance(x, list) else None,
            "preguntas": lambda x: list(x) if x and isinstance(x, list) else None,
            "respuestas": lambda x: list(x) if x and isinstance(x, list) else None
        }
        
        for field, validator in field_validators.items():
            try:
                validated[field] = validator(data.get(field))
            except (ValueError, TypeError):
                validated[field] = None
        
        return validated


# Service instantiation utilities
def get_openai_service() -> OpenAIService:
    """Get an instance of the OpenAI service."""
    return OpenAIService()


async def extract_conversation_information(
    transcription_text: str,
    context: Optional[str] = None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Convenience function to extract information from transcription.
    
    Args:
        transcription_text: The transcribed text
        context: Optional context about the conversation
        
    Returns:
        Tuple of (structured_data, unstructured_data)
    """
    service = get_openai_service()
    return await service.extract_information(transcription_text, context)


# Medical context prompts for different scenarios
MEDICAL_CONTEXTS = {
    "consultation": "Esta es una consulta médica general entre doctor y paciente",
    "emergency": "Esta es una conversación de emergencia médica",
    "follow_up": "Esta es una consulta de seguimiento médico",
    "diagnosis": "Esta es una conversación enfocada en diagnóstico médico",
    "treatment": "Esta es una conversación sobre tratamiento médico"
}
