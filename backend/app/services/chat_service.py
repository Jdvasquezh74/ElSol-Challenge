"""
Servicio de Chat RAG para la aplicación ElSol Challenge.

Este servicio implementa el sistema completo RAG (Retrieval-Augmented Generation)
para responder consultas médicas basadas en conversaciones almacenadas.

Requisito 3: Chatbot vía API
"""

import re
import time
import asyncio
from typing import Dict, Any, List, Optional, Tuple
import structlog

from app.core.config import get_settings
from app.core.schemas import (
    ChatQuery, ChatResponse, ChatSource, ChatIntent, 
    QueryAnalysis, RAGContext
)
from app.services.vector_service import get_vector_service, VectorStoreService
from app.services.openai_service import get_openai_service, OpenAIService

logger = structlog.get_logger(__name__)
settings = get_settings()


class ChatServiceError(Exception):
    """Excepción personalizada para errores del servicio de chat."""
    pass


class ChatService:
    """
    Servicio principal para el sistema de chat médico con RAG.
    
    Implementa el pipeline completo:
    Query → Intent Classification → Vector Search → Context Ranking → GPT-4 → Response
    """
    
    def __init__(self):
        """Inicializar el servicio de chat con dependencias."""
        self.vector_service: VectorStoreService = get_vector_service()
        self.openai_service: OpenAIService = get_openai_service()
        
        # Patrones para detección de intención
        self._intent_patterns = {
            ChatIntent.PATIENT_INFO: [
                r"qu[eé].*(enfermedad|tiene|diagn[oó]stico).*([\w\s]+)",
                r"informaci[oó]n.*(paciente|de).*([\w\s]+)",
                r"qu[eé].*(le pasa|padece).*([\w\s]+)",
                r"([\w\s]+).*(qu[eé].*(tiene|enfermedad|diagn[oó]stico))"
            ],
            ChatIntent.CONDITION_LIST: [
                r"lista.*pacientes.*(con|que tienen).*([\w\s]+)",
                r"qui[eé]nes.*(tienen|padecen).*([\w\s]+)",
                r"pacientes.*(diabetes|hipertensi[oó]n|cancer|asma|[\w\s]+)",
                r"cu[aá]ntos.*pacientes.*([\w\s]+)"
            ],
            ChatIntent.SYMPTOM_SEARCH: [
                r"qui[eé]n.*tiene.*(dolor|s[ií]ntoma|molestia).*([\w\s]+)",
                r"pacientes.*con.*(dolor|s[ií]ntoma|molestia).*([\w\s]+)",
                r"(fiebre|tos|dolor de cabeza|mareos|[\w\s]+).*pacientes"
            ],
            ChatIntent.MEDICATION_INFO: [
                r"qu[eé].*(medicamento|medicina|tratamiento).*toma.*([\w\s]+)",
                r"medicamentos.*para.*([\w\s]+)",
                r"tratamiento.*de.*([\w\s]+)"
            ],
            ChatIntent.TEMPORAL_QUERY: [
                r"(ayer|hoy|semana pasada|mes pasado|[\w\s]+).*paciente",
                r"[uú]ltima.*consulta.*([\w\s]+)",
                r"cu[aá]ndo.*fue.*([\w\s]+)"
            ]
        }
        
        # Términos médicos comunes para expansión de consultas
        self._medical_terms = {
            "diabetes": ["diabetes", "diabético", "glucosa", "azúcar", "insulina"],
            "hipertensión": ["hipertensión", "presión alta", "presión arterial", "hipertenso"],
            "asma": ["asma", "asmático", "bronquial", "respiratorio"],
            "migraña": ["migraña", "jaqueca", "dolor de cabeza", "cefalea"],
            "covid": ["covid", "coronavirus", "sars-cov-2", "pandemia"],
            "gripe": ["gripe", "influenza", "resfriado", "catarro"]
        }
    
    async def process_chat_query(self, query: ChatQuery) -> ChatResponse:
        """
        Procesar consulta de chat completa usando pipeline RAG.
        
        Args:
            query: Consulta del usuario
            
        Returns:
            Respuesta estructurada con contexto y fuentes
            
        Raises:
            ChatServiceError: Si el procesamiento falla
        """
        start_time = time.time()
        
        try:
            logger.info("Processing chat query", 
                       query=query.query, 
                       max_results=query.max_results)
            
            # 1. Analizar consulta y detectar intención
            query_analysis = await self._analyze_query(query.query)
            
            # 2. Recuperar contexto relevante
            retrieved_contexts = await self._retrieve_context(
                query_analysis, query.max_results, query.filters
            )
            
            # 3. Ordenar y preparar contexto final
            ranked_contexts = self._rank_contexts(retrieved_contexts, query_analysis)
            final_context = self._prepare_final_context(ranked_contexts)
            
            # 4. Generar respuesta usando GPT-4
            answer = await self._generate_answer(query_analysis, final_context)
            
            # 5. Preparar fuentes y respuesta final
            sources = self._prepare_sources(ranked_contexts)
            confidence = self._calculate_confidence(ranked_contexts, query_analysis)
            follow_ups = self._generate_follow_up_suggestions(query_analysis)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            response = ChatResponse(
                answer=answer,
                sources=sources,
                confidence=confidence,
                intent=query_analysis.intent.value,
                follow_up_suggestions=follow_ups,
                query_classification={
                    "entities": query_analysis.entities,
                    "search_terms": query_analysis.search_terms,
                    "normalized_query": query_analysis.normalized_query
                },
                processing_time_ms=processing_time
            )
            
            logger.info("Chat query processed successfully",
                       query=query.query,
                       intent=query_analysis.intent.value,
                       sources_count=len(sources),
                       confidence=confidence,
                       processing_time_ms=processing_time)
            
            return response
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            error_msg = f"Chat query processing failed: {str(e)}"
            
            logger.error("Chat query processing failed",
                        query=query.query,
                        error=str(e),
                        processing_time_ms=processing_time)
            
            raise ChatServiceError(error_msg) from e
    
    async def _analyze_query(self, query: str) -> QueryAnalysis:
        """Analizar consulta y detectar intención y entidades."""
        try:
            logger.debug("Analyzing query", query=query)
            
            # Normalizar consulta
            normalized_query = self._normalize_query(query)
            
            # Detectar intención
            intent = self._detect_intent(normalized_query)
            
            # Extraer entidades
            entities = self._extract_entities(normalized_query, intent)
            
            # Generar términos de búsqueda optimizados
            search_terms = self._generate_search_terms(normalized_query, entities)
            
            # Generar filtros automáticos
            filters = self._generate_filters(entities, intent)
            
            analysis = QueryAnalysis(
                original_query=query,
                intent=intent,
                entities=entities,
                normalized_query=normalized_query,
                search_terms=search_terms,
                filters=filters
            )
            
            logger.debug("Query analysis completed",
                        intent=intent.value,
                        entities_count=sum(len(v) for v in entities.values()),
                        search_terms_count=len(search_terms))
            
            return analysis
            
        except Exception as e:
            logger.error("Query analysis failed", query=query, error=str(e))
            # Retornar análisis básico en caso de error
            return QueryAnalysis(
                original_query=query,
                intent=ChatIntent.GENERAL_QUERY,
                entities={},
                normalized_query=query.lower(),
                search_terms=[query],
                filters={}
            )
    
    def _normalize_query(self, query: str) -> str:
        """Normalizar consulta para mejor procesamiento."""
        # Convertir a minúsculas
        normalized = query.lower().strip()
        
        # Remover acentos y caracteres especiales
        accents = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', '¿': '', '¡': '', '?': '', '!': ''
        }
        for accented, normal in accents.items():
            normalized = normalized.replace(accented, normal)
        
        # Limpiar espacios extra
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    def _detect_intent(self, query: str) -> ChatIntent:
        """Detectar intención de la consulta usando patrones."""
        for intent, patterns in self._intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return intent
        
        # Intención por defecto
        return ChatIntent.GENERAL_QUERY
    
    def _extract_entities(self, query: str, intent: ChatIntent) -> Dict[str, List[str]]:
        """Extraer entidades de la consulta según la intención."""
        entities = {
            "patients": [],
            "conditions": [],
            "symptoms": [],
            "medications": [],
            "dates": []
        }
        
        try:
            # Extraer nombres de pacientes (palabras capitalizadas)
            patient_patterns = [
                r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b",
                r"(?:paciente|de|tiene)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            ]
            
            for pattern in patient_patterns:
                matches = re.findall(pattern, query)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0] if match else ""
                    if match and len(match) > 2 and match not in entities["patients"]:
                        entities["patients"].append(match)
            
            # Extraer condiciones médicas
            for condition, synonyms in self._medical_terms.items():
                for synonym in synonyms:
                    if synonym.lower() in query.lower():
                        if condition not in entities["conditions"]:
                            entities["conditions"].append(condition)
            
            # Extraer síntomas comunes
            symptom_keywords = [
                "dolor", "fiebre", "tos", "mareos", "nausea", "vomito",
                "diarrea", "estreñimiento", "fatiga", "cansancio", "debilidad"
            ]
            
            for symptom in symptom_keywords:
                if symptom in query.lower():
                    if symptom not in entities["symptoms"]:
                        entities["symptoms"].append(symptom)
            
            # Extraer fechas/tiempo
            time_patterns = [
                r"(ayer|hoy|mañana)",
                r"(semana|mes|año)\s+(pasada?|anterior|ultimo)",
                r"\d{1,2}/\d{1,2}/\d{4}",
                r"\d{4}-\d{2}-\d{2}"
            ]
            
            for pattern in time_patterns:
                matches = re.findall(pattern, query.lower())
                for match in matches:
                    if isinstance(match, tuple):
                        match = ' '.join(match).strip()
                    if match and match not in entities["dates"]:
                        entities["dates"].append(match)
            
        except Exception as e:
            logger.warning("Entity extraction failed", error=str(e))
        
        return entities
    
    def _generate_search_terms(self, query: str, entities: Dict[str, List[str]]) -> List[str]:
        """Generar términos de búsqueda optimizados."""
        search_terms = []
        
        # Agregar consulta original
        search_terms.append(query)
        
        # Agregar entidades encontradas
        for entity_type, entity_list in entities.items():
            search_terms.extend(entity_list)
        
        # Expandir con sinónimos médicos
        for condition, synonyms in self._medical_terms.items():
            if any(synonym in query.lower() for synonym in synonyms):
                search_terms.extend(synonyms[:3])  # Top 3 sinónimos
        
        # Remover duplicados y términos muy cortos
        search_terms = list(set([term for term in search_terms if len(term) > 2]))
        
        return search_terms[:10]  # Limitar a 10 términos
    
    def _generate_filters(self, entities: Dict[str, List[str]], intent: ChatIntent) -> Dict[str, Any]:
        """Generar filtros automáticos basados en entidades e intención."""
        filters = {}
        
        # Filtros por paciente
        if entities.get("patients"):
            # Para búsquedas de paciente específico, usar filtro exacto
            if intent == ChatIntent.PATIENT_INFO and len(entities["patients"]) == 1:
                filters["patient_name"] = {"$eq": entities["patients"][0]}
        
        # Filtros por condición médica
        if entities.get("conditions") and intent == ChatIntent.CONDITION_LIST:
            # Para listas por condición, buscar en diagnóstico
            filters["diagnosis"] = {"$contains": entities["conditions"][0]}
        
        return filters
    
    async def _retrieve_context(
        self, 
        analysis: QueryAnalysis, 
        max_results: int,
        user_filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Recuperar contexto relevante del vector store."""
        try:
            # Combinar filtros automáticos con filtros del usuario
            combined_filters = {**analysis.filters}
            if user_filters:
                combined_filters.update(user_filters)
            
            # Estrategia de búsqueda según intención
            if analysis.intent == ChatIntent.PATIENT_INFO and analysis.entities.get("patients"):
                # Búsqueda específica por paciente
                patient_name = analysis.entities["patients"][0]
                results = await self.vector_service.search_by_patient(
                    patient_name=patient_name,
                    max_results=max_results
                )
            elif analysis.intent == ChatIntent.CONDITION_LIST and analysis.entities.get("conditions"):
                # Búsqueda por condición médica
                condition = analysis.entities["conditions"][0]
                results = await self.vector_service.search_by_condition(
                    condition=condition,
                    max_results=max_results
                )
            else:
                # Búsqueda semántica general
                search_query = " ".join(analysis.search_terms[:3])  # Top 3 términos
                results = await self.vector_service.semantic_search(
                    query=search_query,
                    max_results=max_results,
                    similarity_threshold=0.6,
                    metadata_filters=combined_filters if combined_filters else None
                )
            
            logger.debug("Context retrieval completed",
                        intent=analysis.intent.value,
                        results_count=len(results))
            
            return results
            
        except Exception as e:
            logger.error("Context retrieval failed", error=str(e))
            return []
    
    def _rank_contexts(
        self, 
        contexts: List[Dict[str, Any]], 
        analysis: QueryAnalysis
    ) -> List[Dict[str, Any]]:
        """Ordenar contextos por relevancia múltiple."""
        try:
            # Agregar puntuaciones adicionales
            for context in contexts:
                base_score = context.get("similarity_score", 0.0)
                
                # Bonus por coincidencia exacta de entidades
                entity_bonus = 0.0
                content = context.get("content", "").lower()
                
                # Bonus por nombres de pacientes
                for patient in analysis.entities.get("patients", []):
                    if patient.lower() in content:
                        entity_bonus += 0.1
                
                # Bonus por condiciones médicas
                for condition in analysis.entities.get("conditions", []):
                    if condition.lower() in content:
                        entity_bonus += 0.15
                
                # Bonus por síntomas
                for symptom in analysis.entities.get("symptoms", []):
                    if symptom.lower() in content:
                        entity_bonus += 0.05
                
                # Bonus por fecha reciente (placeholder)
                date_bonus = 0.0
                if context.get("date"):
                    # TODO: Implementar lógica de fechas
                    date_bonus = 0.02
                
                # Puntuación final
                final_score = base_score + entity_bonus + date_bonus
                context["final_score"] = min(final_score, 1.0)  # Cap at 1.0
            
            # Ordenar por puntuación final
            ranked = sorted(contexts, key=lambda x: x.get("final_score", 0), reverse=True)
            
            logger.debug("Context ranking completed",
                        contexts_count=len(ranked),
                        top_score=ranked[0].get("final_score", 0) if ranked else 0)
            
            return ranked
            
        except Exception as e:
            logger.warning("Context ranking failed", error=str(e))
            return contexts
    
    def _prepare_final_context(self, ranked_contexts: List[Dict[str, Any]]) -> str:
        """Preparar contexto final para generación de respuesta."""
        if not ranked_contexts:
            return "No se encontró información relevante en las conversaciones médicas."
        
        context_parts = []
        
        for i, context in enumerate(ranked_contexts[:5]):  # Top 5 contextos
            patient_name = context.get("patient_name", "Paciente no identificado")
            date = context.get("date", "Fecha no disponible")
            content = context.get("content", "")
            
            context_part = f"""
CONVERSACIÓN {i + 1}:
Paciente: {patient_name}
Fecha: {date}
Relevancia: {context.get('final_score', 0):.2f}
Contenido: {content[:500]}{'...' if len(content) > 500 else ''}
"""
            context_parts.append(context_part)
        
        final_context = "\n".join(context_parts)
        
        # Limitar tamaño total del contexto
        if len(final_context) > 4000:
            final_context = final_context[:4000] + "\n\n[Contexto truncado...]"
        
        return final_context
    
    async def _generate_answer(self, analysis: QueryAnalysis, context: str) -> str:
        """Generar respuesta usando GPT-4 con contexto médico."""
        try:
            # Seleccionar prompt según intención
            prompt_template = self._get_prompt_template(analysis.intent)
            
            # Preparar prompt final
            full_prompt = prompt_template.format(
                query=analysis.original_query,
                context=context,
                intent=analysis.intent.value,
                entities=", ".join([
                    f"{k}: {', '.join(v)}" for k, v in analysis.entities.items() if v
                ])
            )
            
            # Generar respuesta usando OpenAI
            response = await self.openai_service._call_openai_api([
                {"role": "system", "content": "Eres un asistente médico especializado en consultar información de expedientes médicos."},
                {"role": "user", "content": full_prompt}
            ])
            
            # Validar y limpiar respuesta
            validated_response = self._validate_response(response, analysis)
            
            return validated_response
            
        except Exception as e:
            logger.error("Answer generation failed", error=str(e))
            return "Lo siento, no pude procesar tu consulta en este momento. Por favor, intenta reformular tu pregunta o consulta directamente con el personal médico."
    
    def _get_prompt_template(self, intent: ChatIntent) -> str:
        """Obtener template de prompt específico según intención."""
        
        if intent == ChatIntent.PATIENT_INFO:
            return """
Basándote ÚNICAMENTE en la información médica proporcionada, responde la siguiente consulta sobre un paciente específico.

INFORMACIÓN MÉDICA DISPONIBLE:
{context}

CONSULTA: {query}

INSTRUCCIONES CRÍTICAS:
- Responde SOLO con información que esté explícitamente en el contexto
- Si no hay información suficiente, indícalo claramente
- Usa terminología médica apropiada pero accesible
- NUNCA inventes información médica
- Incluye fechas y detalles relevantes cuando estén disponibles
- Sugiere consultar al médico para decisiones críticas

RESPUESTA:
"""
        
        elif intent == ChatIntent.CONDITION_LIST:
            return """
Basándote en la información médica proporcionada, genera una lista de pacientes que cumplen con el criterio solicitado.

INFORMACIÓN MÉDICA DISPONIBLE:
{context}

CONSULTA: {query}

INSTRUCCIONES:
- Lista SOLO pacientes que aparezcan en la información proporcionada
- Incluye información relevante de cada paciente (diagnóstico, fecha, síntomas)
- Organiza la lista de manera clara y estructurada
- Indica el número total de pacientes encontrados
- Si no hay pacientes que cumplan el criterio, indícalo claramente

RESPUESTA:
"""
        
        else:
            return """
Basándote en la información médica proporcionada, responde la consulta médica de manera precisa y responsable.

INFORMACIÓN MÉDICA DISPONIBLE:
{context}

CONSULTA: {query}
ENTIDADES DETECTADAS: {entities}

INSTRUCCIONES:
- Responde basándote ÚNICAMENTE en la información proporcionada
- Mantén un enfoque médico profesional pero accesible
- Si la información es insuficiente, sugiere consultar al médico
- NUNCA inventes datos médicos
- Proporciona respuestas estructuradas y claras

RESPUESTA:
"""
    
    def _validate_response(self, response: str, analysis: QueryAnalysis) -> str:
        """Validar y limpiar respuesta generada."""
        try:
            # Limpieza básica
            cleaned = response.strip()
            
            # Agregar disclaimer médico si es necesario
            medical_keywords = ["diagnóstico", "medicamento", "tratamiento", "enfermedad"]
            if any(keyword in cleaned.lower() for keyword in medical_keywords):
                disclaimer = "\n\n⚠️ Esta información proviene de conversaciones registradas. Para decisiones médicas, consulte siempre con un profesional de la salud."
                cleaned += disclaimer
            
            # Limitar longitud
            if len(cleaned) > 2000:
                cleaned = cleaned[:2000] + "..."
            
            return cleaned
            
        except Exception as e:
            logger.warning("Response validation failed", error=str(e))
            return response
    
    def _prepare_sources(self, contexts: List[Dict[str, Any]]) -> List[ChatSource]:
        """Preparar fuentes para la respuesta."""
        sources = []
        
        for context in contexts[:5]:  # Top 5 fuentes
            source = ChatSource(
                conversation_id=context.get("conversation_id", "unknown"),
                patient_name=context.get("patient_name"),
                relevance_score=context.get("final_score", context.get("similarity_score", 0.0)),
                excerpt=context.get("excerpt", context.get("content", "")[:200]),
                date=context.get("date"),
                metadata={
                    "diagnosis": context.get("diagnosis"),
                    "symptoms": context.get("symptoms"),
                    "rank": context.get("rank", 0)
                }
            )
            sources.append(source)
        
        return sources
    
    def _calculate_confidence(
        self, 
        contexts: List[Dict[str, Any]], 
        analysis: QueryAnalysis
    ) -> float:
        """Calcular nivel de confianza de la respuesta."""
        if not contexts:
            return 0.1
        
        # Factores de confianza
        avg_similarity = sum(c.get("final_score", 0) for c in contexts[:3]) / min(len(contexts), 3)
        
        # Bonus por coincidencia de entidades
        entity_bonus = 0.0
        if analysis.entities.get("patients") or analysis.entities.get("conditions"):
            entity_bonus = 0.1
        
        # Bonus por número de fuentes
        source_bonus = min(len(contexts) * 0.05, 0.2)
        
        confidence = min(avg_similarity + entity_bonus + source_bonus, 0.95)
        
        return round(confidence, 2)
    
    def _generate_follow_up_suggestions(self, analysis: QueryAnalysis) -> List[str]:
        """Generar sugerencias de seguimiento."""
        suggestions = []
        
        try:
            if analysis.intent == ChatIntent.PATIENT_INFO and analysis.entities.get("patients"):
                patient = analysis.entities["patients"][0]
                suggestions = [
                    f"¿Qué tratamiento se recomendó para {patient}?",
                    f"¿Cuándo fue la última consulta de {patient}?",
                    f"¿Qué síntomas reportó {patient}?"
                ]
            
            elif analysis.intent == ChatIntent.CONDITION_LIST and analysis.entities.get("conditions"):
                condition = analysis.entities["conditions"][0]
                suggestions = [
                    f"¿Qué tratamientos hay para {condition}?",
                    f"¿Cuántos pacientes nuevos con {condition} hay este mes?",
                    f"¿Qué síntomas son más comunes en {condition}?"
                ]
            
            else:
                suggestions = [
                    "¿Puedes mostrarme información de un paciente específico?",
                    "¿Qué pacientes tienen una condición particular?",
                    "¿Cuáles son los síntomas más reportados?"
                ]
        
        except Exception as e:
            logger.warning("Failed to generate follow-up suggestions", error=str(e))
        
        return suggestions[:3]  # Máximo 3 sugerencias


# Singleton service instance
_chat_service_instance: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """Obtener instancia singleton del servicio de chat."""
    global _chat_service_instance
    
    if _chat_service_instance is None:
        _chat_service_instance = ChatService()
    
    return _chat_service_instance


async def process_medical_query(
    query: str,
    max_results: int = 5,
    filters: Optional[Dict[str, Any]] = None
) -> ChatResponse:
    """
    Función de conveniencia para procesar consultas médicas.
    
    Args:
        query: Consulta en lenguaje natural
        max_results: Número máximo de resultados
        filters: Filtros opcionales
        
    Returns:
        Respuesta estructurada del sistema de chat
    """
    chat_service = get_chat_service()
    chat_query = ChatQuery(
        query=query,
        max_results=max_results,
        filters=filters
    )
    
    return await chat_service.process_chat_query(chat_query)
