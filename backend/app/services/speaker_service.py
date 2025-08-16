"""
Servicio de Diferenciación de Hablantes para la aplicación ElSol Challenge.

Este servicio implementa speaker diarization para identificar y separar
hablantes en conversaciones médicas (promotor vs paciente).

PLUS Feature 5: Diferenciación de Hablantes
"""

import re
import time
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import structlog

# Audio processing libraries
try:
    import librosa
    import scipy.signal
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
except ImportError:
    librosa = None
    scipy = None
    KMeans = None
    StandardScaler = None

from app.core.config import get_settings
from app.core.schemas import (
    SpeakerSegment, SpeakerStats, DiarizationResult, 
    SpeakerType, TranscriptionResponse
)

logger = structlog.get_logger(__name__)
settings = get_settings()


class SpeakerDiarizationError(Exception):
    """Excepción personalizada para errores de diarización."""
    pass


class SpeakerService:
    """
    Servicio para diferenciación de hablantes en conversaciones médicas.
    
    Implementa un algoritmo híbrido que combina:
    - Análisis de características de audio (tono, velocidad, pausas)
    - Análisis semántico del contenido transcrito
    - Patrones típicos de conversaciones médicas
    """
    
    def __init__(self):
        """Inicializar el servicio de speaker diarization."""
        self._check_dependencies()
        
        # Patrones para identificar rol de hablante
        self._promotor_patterns = [
            r"buenos días|buenas tardes|hola",
            r"¿cómo se siente|¿cómo está|¿qué le pasa",
            r"vamos a revisar|le voy a|necesito que",
            r"¿desde cuándo|¿cuánto tiempo|¿con qué frecuencia",
            r"voy a recetarle|le recomiendo|debe tomar",
            r"¿tiene alguna alergia|¿toma algún medicamento",
            r"doctor|doctora|médico|enfermero|enfermera"
        ]
        
        self._paciente_patterns = [
            r"me duele|me siento|tengo dolor",
            r"desde hace|hace como|hace unos",
            r"no puedo|no me deja|me impide",
            r"sí doctor|no doctor|gracias doctor",
            r"tomo|estoy tomando|me tomo",
            r"mi familia|mi trabajo|en casa"
        ]
        
        # Palabras clave médicas del promotor
        self._medical_professional_keywords = [
            "diagnóstico", "tratamiento", "medicamento", "receta", 
            "examen", "análisis", "síntoma", "presión", "temperatura",
            "auscultar", "palpar", "revisar", "prescribir", "recetar"
        ]
        
        # Palabras clave del paciente
        self._patient_keywords = [
            "dolor", "malestar", "molestia", "síntoma", "siento",
            "familia", "trabajo", "casa", "dormir", "comer"
        ]
    
    def _check_dependencies(self) -> None:
        """Verificar que las dependencias estén disponibles."""
        missing_deps = []
        
        if not librosa:
            missing_deps.append("librosa")
        if not scipy:
            missing_deps.append("scipy")
        if not KMeans or not StandardScaler:
            missing_deps.append("scikit-learn")
        
        if missing_deps:
            logger.warning(
                "Missing speaker diarization dependencies",
                missing=missing_deps,
                message="Speaker diarization will use text-only approach"
            )
    
    async def diarize_conversation(
        self,
        audio_file_path: str,
        transcription: str,
        whisper_segments: Optional[List[Dict]] = None
    ) -> DiarizationResult:
        """
        Realizar diarización completa de una conversación.
        
        Args:
            audio_file_path: Ruta al archivo de audio
            transcription: Transcripción completa
            whisper_segments: Segmentos de Whisper con timestamps (opcional)
            
        Returns:
            Resultado completo de diarización con segmentos y estadísticas
        """
        start_time = time.time()
        
        try:
            logger.info("Starting speaker diarization",
                       audio_file=audio_file_path,
                       transcription_length=len(transcription))
            
            # Estrategia híbrida de diarización
            if whisper_segments and librosa:
                # Método avanzado: audio + texto
                segments = await self._diarize_with_audio_and_text(
                    audio_file_path, transcription, whisper_segments
                )
            else:
                # Método básico: solo texto
                segments = await self._diarize_text_only(transcription)
            
            # Calcular estadísticas
            stats = self._calculate_speaker_stats(segments)
            
            # Calcular tiempo de procesamiento
            processing_time = int((time.time() - start_time) * 1000)
            
            result = DiarizationResult(
                speaker_segments=segments,
                speaker_stats=stats,
                processing_time_ms=processing_time,
                algorithm_version="1.0",
                confidence_threshold=settings.SPEAKER_CONFIDENCE_THRESHOLD
            )
            
            logger.info("Speaker diarization completed",
                       segments_count=len(segments),
                       promotor_segments=len([s for s in segments if s.speaker == SpeakerType.PROMOTOR]),
                       paciente_segments=len([s for s in segments if s.speaker == SpeakerType.PACIENTE]),
                       processing_time_ms=processing_time)
            
            return result
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error("Speaker diarization failed",
                        audio_file=audio_file_path,
                        error=str(e),
                        processing_time_ms=processing_time)
            raise SpeakerDiarizationError(f"Error en diarización: {str(e)}")
    
    async def _diarize_with_audio_and_text(
        self,
        audio_file_path: str,
        transcription: str,
        whisper_segments: List[Dict]
    ) -> List[SpeakerSegment]:
        """
        Diarización avanzada usando características de audio y análisis de texto.
        
        Args:
            audio_file_path: Ruta al archivo de audio
            transcription: Transcripción completa
            whisper_segments: Segmentos de Whisper
            
        Returns:
            Lista de segmentos con hablantes identificados
        """
        try:
            logger.debug("Using advanced audio+text diarization")
            
            # Cargar audio
            audio, sr = librosa.load(audio_file_path, sr=settings.DIARIZATION_SAMPLE_RATE)
            
            # Extraer características de audio para cada segmento
            audio_features = []
            text_features = []
            
            for segment in whisper_segments:
                start_sample = int(segment.get('start', 0) * sr)
                end_sample = int(segment.get('end', 0) * sr)
                
                # Extraer características de audio
                audio_segment = audio[start_sample:end_sample]
                features = self._extract_audio_features(audio_segment, sr)
                audio_features.append(features)
                
                # Analizar contenido textual
                text = segment.get('text', '')
                text_score = self._analyze_text_content(text)
                text_features.append(text_score)
            
            # Clustering de características de audio
            speaker_clusters = self._cluster_speakers(audio_features)
            
            # Crear segmentos con clasificación híbrida
            segments = []
            for i, segment in enumerate(whisper_segments):
                # Combinar evidencia de audio y texto
                audio_cluster = speaker_clusters[i]
                text_score = text_features[i]
                
                # Decidir tipo de hablante
                speaker_type, confidence = self._classify_speaker_hybrid(
                    audio_cluster, text_score, segment.get('text', '')
                )
                
                speaker_segment = SpeakerSegment(
                    speaker=speaker_type,
                    text=segment.get('text', ''),
                    start_time=float(segment.get('start', 0)),
                    end_time=float(segment.get('end', 0)),
                    confidence=confidence,
                    word_count=len(segment.get('text', '').split())
                )
                
                segments.append(speaker_segment)
            
            return segments
            
        except Exception as e:
            logger.error("Advanced diarization failed", error=str(e))
            # Fallback a método básico
            return await self._diarize_text_only(transcription)
    
    async def _diarize_text_only(self, transcription: str) -> List[SpeakerSegment]:
        """
        Diarización básica usando solo análisis de texto.
        
        Args:
            transcription: Transcripción completa
            
        Returns:
            Lista de segmentos con hablantes identificados
        """
        try:
            logger.debug("Using text-only diarization")
            
            # Dividir transcripción en segmentos lógicos
            segments = self._segment_transcription(transcription)
            
            # Clasificar cada segmento
            speaker_segments = []
            current_time = 0.0
            
            for segment_text in segments:
                # Estimar duración del segmento (aproximación)
                word_count = len(segment_text.split())
                duration = word_count * 0.6  # ~0.6 segundos por palabra
                
                # Clasificar hablante
                speaker_type, confidence = self._classify_speaker_by_text(segment_text)
                
                speaker_segment = SpeakerSegment(
                    speaker=speaker_type,
                    text=segment_text.strip(),
                    start_time=current_time,
                    end_time=current_time + duration,
                    confidence=confidence,
                    word_count=word_count
                )
                
                speaker_segments.append(speaker_segment)
                current_time += duration
            
            return speaker_segments
            
        except Exception as e:
            logger.error("Text-only diarization failed", error=str(e))
            # Crear segmento único si todo falla
            return [SpeakerSegment(
                speaker=SpeakerType.UNKNOWN,
                text=transcription,
                start_time=0.0,
                end_time=60.0,  # Estimación por defecto
                confidence=0.1,
                word_count=len(transcription.split())
            )]
    
    def _extract_audio_features(self, audio_segment: np.ndarray, sr: int) -> np.ndarray:
        """
        Extraer características de audio relevantes para identificar hablantes.
        
        Args:
            audio_segment: Segmento de audio
            sr: Sample rate
            
        Returns:
            Vector de características
        """
        try:
            if len(audio_segment) < sr * 0.1:  # Menos de 100ms
                return np.zeros(6)  # Retornar características vacías
            
            # Características fundamentales para diferenciación de hablantes
            
            # 1. Pitch (frecuencia fundamental)
            f0 = librosa.yin(audio_segment, fmin=50, fmax=400, sr=sr)
            pitch_mean = np.nanmean(f0)
            pitch_std = np.nanstd(f0)
            
            # 2. Intensidad (RMS energy)
            rms = librosa.feature.rms(y=audio_segment)[0]
            energy_mean = np.mean(rms)
            
            # 3. Espectro (MFCC centroide)
            spectral_centroid = librosa.feature.spectral_centroid(y=audio_segment, sr=sr)[0]
            spectrum_mean = np.mean(spectral_centroid)
            
            # 4. Velocidad de habla (zero crossing rate)
            zcr = librosa.feature.zero_crossing_rate(audio_segment)[0]
            speech_rate = np.mean(zcr)
            
            # 5. Variabilidad tonal
            pitch_range = np.nanmax(f0) - np.nanmin(f0) if not np.all(np.isnan(f0)) else 0
            
            features = np.array([
                pitch_mean if not np.isnan(pitch_mean) else 150,  # Valor por defecto
                pitch_std if not np.isnan(pitch_std) else 20,
                energy_mean,
                spectrum_mean,
                speech_rate,
                pitch_range
            ])
            
            return features
            
        except Exception as e:
            logger.warning("Audio feature extraction failed", error=str(e))
            return np.zeros(6)  # Características por defecto
    
    def _cluster_speakers(self, audio_features: List[np.ndarray]) -> List[int]:
        """
        Agrupar características de audio en clusters de hablantes.
        
        Args:
            audio_features: Lista de vectores de características
            
        Returns:
            Lista de cluster IDs (0 o 1 para 2 hablantes)
        """
        try:
            if not audio_features or len(audio_features) < 2:
                return [0] * len(audio_features)
            
            # Preparar datos para clustering
            features_matrix = np.array(audio_features)
            
            # Normalizar características
            if StandardScaler:
                scaler = StandardScaler()
                features_matrix = scaler.fit_transform(features_matrix)
            
            # K-means con 2 clusters (promotor y paciente)
            if KMeans:
                kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
                clusters = kmeans.fit_predict(features_matrix)
                return clusters.tolist()
            else:
                # Clustering simple basado en pitch si no hay scikit-learn
                pitches = [f[0] for f in audio_features]  # Primer feature es pitch
                median_pitch = np.median(pitches)
                return [0 if pitch < median_pitch else 1 for pitch in pitches]
            
        except Exception as e:
            logger.warning("Audio clustering failed", error=str(e))
            return [0] * len(audio_features)
    
    def _analyze_text_content(self, text: str) -> float:
        """
        Analizar contenido de texto para determinar tipo de hablante.
        
        Args:
            text: Texto del segmento
            
        Returns:
            Score: -1.0 (paciente) a +1.0 (promotor)
        """
        if not text:
            return 0.0
        
        text_lower = text.lower()
        promotor_score = 0
        paciente_score = 0
        
        # Buscar patrones de promotor
        for pattern in self._promotor_patterns:
            if re.search(pattern, text_lower):
                promotor_score += 1
        
        # Buscar patrones de paciente
        for pattern in self._paciente_patterns:
            if re.search(pattern, text_lower):
                paciente_score += 1
        
        # Contar palabras clave médicas (típicas del promotor)
        for keyword in self._medical_professional_keywords:
            if keyword in text_lower:
                promotor_score += 0.5
        
        # Contar palabras clave del paciente
        for keyword in self._patient_keywords:
            if keyword in text_lower:
                paciente_score += 0.5
        
        # Calcular score normalizado
        total_score = promotor_score + paciente_score
        if total_score == 0:
            return 0.0
        
        return (promotor_score - paciente_score) / total_score
    
    def _classify_speaker_hybrid(
        self, 
        audio_cluster: int, 
        text_score: float, 
        text: str
    ) -> Tuple[SpeakerType, float]:
        """
        Clasificar hablante usando evidencia híbrida (audio + texto).
        
        Args:
            audio_cluster: Cluster de audio (0 o 1)
            text_score: Score de análisis de texto (-1 a +1)
            text: Texto del segmento
            
        Returns:
            Tupla (tipo_hablante, confianza)
        """
        # Pesos para evidencia
        audio_weight = 0.3
        text_weight = 0.7
        
        # Convertir cluster de audio a score (-1 a +1)
        # Asumimos que cluster 0 = paciente, cluster 1 = promotor
        audio_score = 1.0 if audio_cluster == 1 else -1.0
        
        # Score combinado
        combined_score = (audio_weight * audio_score) + (text_weight * text_score)
        
        # Clasificar basado en score combinado
        if combined_score > 0.2:
            speaker_type = SpeakerType.PROMOTOR
            confidence = min(0.9, 0.6 + abs(combined_score) * 0.3)
        elif combined_score < -0.2:
            speaker_type = SpeakerType.PACIENTE
            confidence = min(0.9, 0.6 + abs(combined_score) * 0.3)
        else:
            speaker_type = SpeakerType.UNKNOWN
            confidence = 0.4
        
        # Boost de confianza para patrones muy claros
        if any(re.search(pattern, text.lower()) for pattern in self._promotor_patterns[:3]):
            if speaker_type == SpeakerType.PROMOTOR:
                confidence = min(0.95, confidence + 0.2)
        
        if any(re.search(pattern, text.lower()) for pattern in self._paciente_patterns[:3]):
            if speaker_type == SpeakerType.PACIENTE:
                confidence = min(0.95, confidence + 0.2)
        
        return speaker_type, confidence
    
    def _classify_speaker_by_text(self, text: str) -> Tuple[SpeakerType, float]:
        """
        Clasificar hablante usando solo análisis de texto.
        
        Args:
            text: Texto del segmento
            
        Returns:
            Tupla (tipo_hablante, confianza)
        """
        text_score = self._analyze_text_content(text)
        
        if text_score > 0.3:
            return SpeakerType.PROMOTOR, min(0.8, 0.5 + text_score * 0.3)
        elif text_score < -0.3:
            return SpeakerType.PACIENTE, min(0.8, 0.5 + abs(text_score) * 0.3)
        else:
            return SpeakerType.UNKNOWN, 0.3
    
    def _segment_transcription(self, transcription: str) -> List[str]:
        """
        Dividir transcripción en segmentos lógicos.
        
        Args:
            transcription: Transcripción completa
            
        Returns:
            Lista de segmentos de texto
        """
        if not transcription:
            return []
        
        # Dividir por patrones de cambio de hablante
        # Buscar preguntas, saludos, y cambios de tema
        
        # Patrones que típicamente indican cambio de hablante
        split_patterns = [
            r'\?\s+[A-ZÁÉÍÓÚ]',  # Pregunta seguida de mayúscula
            r'\.\s+[A-ZÁÉÍÓÚ][a-z]+\s+(días?|tardes?|noches?)',  # Saludos
            r'\.\s+[A-ZÁÉÍÓÚ][a-z]+\s+(doctor|doctora)',  # Dirigirse al doctor
            r'\.\s+[A-ZÁÉÍÓÚ][a-z]+\s+(me|mi|yo)',  # Cambio a primera persona
            r'\.\s+[A-ZÁÉÍÓÚ][a-z]+\s+(le voy|vamos|necesito)'  # Acciones médicas
        ]
        
        segments = [transcription]
        
        for pattern in split_patterns:
            new_segments = []
            for segment in segments:
                # Dividir por patrón manteniendo el separador
                parts = re.split(f'({pattern})', segment)
                current_segment = ""
                
                for i, part in enumerate(parts):
                    if re.match(pattern, part) and current_segment:
                        # Guardar segmento actual y comenzar nuevo
                        new_segments.append(current_segment.strip())
                        current_segment = part
                    else:
                        current_segment += part
                
                if current_segment.strip():
                    new_segments.append(current_segment.strip())
            
            segments = [s for s in new_segments if len(s.strip()) > 10]  # Filtrar muy cortos
        
        # Si no se encontraron divisiones claras, dividir por oraciones largas
        if len(segments) == 1 and len(transcription) > 200:
            sentences = re.split(r'[.!?]+\s+', transcription)
            segments = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        return segments if segments else [transcription]
    
    def _calculate_speaker_stats(self, segments: List[SpeakerSegment]) -> SpeakerStats:
        """
        Calcular estadísticas de participación por hablante.
        
        Args:
            segments: Lista de segmentos con hablantes
            
        Returns:
            Estadísticas detalladas
        """
        if not segments:
            return SpeakerStats(
                total_speakers=0,
                total_duration=0.0,
                speaker_changes=0,
                average_segment_length=0.0
            )
        
        # Calcular tiempos por hablante
        promotor_time = sum(
            seg.end_time - seg.start_time 
            for seg in segments 
            if seg.speaker == SpeakerType.PROMOTOR
        )
        
        paciente_time = sum(
            seg.end_time - seg.start_time 
            for seg in segments 
            if seg.speaker == SpeakerType.PACIENTE
        )
        
        unknown_time = sum(
            seg.end_time - seg.start_time 
            for seg in segments 
            if seg.speaker == SpeakerType.UNKNOWN
        )
        
        # Calcular tiempo total
        total_duration = max(seg.end_time for seg in segments) if segments else 0.0
        
        # Contar cambios de hablante
        speaker_changes = 0
        prev_speaker = None
        for segment in segments:
            if prev_speaker and prev_speaker != segment.speaker:
                speaker_changes += 1
            prev_speaker = segment.speaker
        
        # Duración promedio de segmentos
        segment_durations = [seg.end_time - seg.start_time for seg in segments]
        avg_segment_length = sum(segment_durations) / len(segment_durations) if segment_durations else 0.0
        
        # Número de hablantes únicos
        unique_speakers = len(set(seg.speaker for seg in segments if seg.speaker != SpeakerType.UNKNOWN))
        
        return SpeakerStats(
            total_speakers=unique_speakers,
            promotor_time=promotor_time,
            paciente_time=paciente_time,
            unknown_time=unknown_time,
            overlap_time=0.0,  # No detectamos overlap en esta versión
            total_duration=total_duration,
            speaker_changes=speaker_changes,
            average_segment_length=avg_segment_length
        )


# Singleton service instance
_speaker_service_instance: Optional[SpeakerService] = None


def get_speaker_service() -> SpeakerService:
    """Obtener instancia singleton del servicio de speaker diarization."""
    global _speaker_service_instance
    
    if _speaker_service_instance is None:
        _speaker_service_instance = SpeakerService()
    
    return _speaker_service_instance


# Función de conveniencia
async def diarize_audio_conversation(
    audio_file_path: str,
    transcription: str,
    whisper_segments: Optional[List[Dict]] = None
) -> DiarizationResult:
    """
    Función de conveniencia para diarizar una conversación.
    
    Args:
        audio_file_path: Ruta al archivo de audio
        transcription: Transcripción completa
        whisper_segments: Segmentos de Whisper (opcional)
        
    Returns:
        Resultado completo de diarización
    """
    speaker_service = get_speaker_service()
    return await speaker_service.diarize_conversation(
        audio_file_path, transcription, whisper_segments
    )
