"""
Tests para el servicio de diarización de hablantes - ElSol Challenge.

Tests para diferenciación de hablantes (promotor vs paciente).
PLUS Feature 5: Diferenciación de Hablantes
"""

import pytest
import asyncio
import tempfile
import os
import json
import numpy as np
from unittest.mock import Mock, patch, AsyncMock

from app.services.speaker_service import (
    get_speaker_service, SpeakerService, SpeakerDiarizationError,
    diarize_audio_conversation
)
from app.core.schemas import (
    SpeakerSegment, SpeakerStats, DiarizationResult, 
    SpeakerType, TranscriptionResponse
)
from app.core.config import get_settings


class TestSpeakerService:
    """Tests para el servicio de diarización de hablantes."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.speaker_service = get_speaker_service()
        self.settings = get_settings()
    
    def test_speaker_service_singleton(self):
        """Test que el servicio sea singleton."""
        service1 = get_speaker_service()
        service2 = get_speaker_service()
        assert service1 is service2
    
    def test_analyze_text_content_promotor_patterns(self):
        """Test análisis de patrones de texto del promotor."""
        promotor_texts = [
            "Buenos días, ¿cómo se siente hoy?",
            "¿Desde cuándo tiene estos síntomas?",
            "Vamos a revisar su presión arterial",
            "Le voy a recetar este medicamento",
            "¿Tiene alguna alergia conocida?"
        ]
        
        for text in promotor_texts:
            score = self.speaker_service._analyze_text_content(text)
            assert score > 0, f"Text '{text}' should indicate promotor"
    
    def test_analyze_text_content_paciente_patterns(self):
        """Test análisis de patrones de texto del paciente."""
        paciente_texts = [
            "Me duele mucho la cabeza desde ayer",
            "Sí doctor, tomo estas pastillas",
            "No puedo dormir bien por las noches",
            "En mi familia hay antecedentes de diabetes",
            "Hace como una semana que me siento mal"
        ]
        
        for text in paciente_texts:
            score = self.speaker_service._analyze_text_content(text)
            assert score < 0, f"Text '{text}' should indicate paciente"
    
    def test_analyze_text_content_neutral(self):
        """Test análisis de texto neutro."""
        neutral_texts = [
            "El clima está muy bueno hoy",
            "Los números son importantes",
            "Esta es una oración neutral",
            ""
        ]
        
        for text in neutral_texts:
            score = self.speaker_service._analyze_text_content(text)
            assert abs(score) < 0.3, f"Text '{text}' should be neutral"
    
    def test_classify_speaker_by_text_promotor(self):
        """Test clasificación basada solo en texto - promotor."""
        promotor_text = "Buenos días. ¿Cómo se siente hoy? ¿Desde cuándo tiene estos síntomas?"
        
        speaker_type, confidence = self.speaker_service._classify_speaker_by_text(promotor_text)
        
        assert speaker_type == SpeakerType.PROMOTOR
        assert confidence > 0.5
    
    def test_classify_speaker_by_text_paciente(self):
        """Test clasificación basada solo en texto - paciente."""
        paciente_text = "Me duele mucho la cabeza desde ayer. No puedo dormir bien."
        
        speaker_type, confidence = self.speaker_service._classify_speaker_by_text(paciente_text)
        
        assert speaker_type == SpeakerType.PACIENTE
        assert confidence > 0.5
    
    def test_classify_speaker_by_text_unknown(self):
        """Test clasificación basada solo en texto - desconocido."""
        neutral_text = "El tiempo está muy bueno hoy en la ciudad."
        
        speaker_type, confidence = self.speaker_service._classify_speaker_by_text(neutral_text)
        
        assert speaker_type == SpeakerType.UNKNOWN
        assert confidence < 0.5
    
    def test_segment_transcription_basic(self):
        """Test segmentación básica de transcripción."""
        transcription = """
        Buenos días, ¿cómo se siente hoy? Me duele mucho la cabeza desde ayer.
        ¿Desde cuándo comenzó este dolor? Bueno, comenzó ayer en la tarde.
        ¿Ha tomado algún medicamento? Sí doctor, tomé un ibuprofeno.
        """
        
        segments = self.speaker_service._segment_transcription(transcription)
        
        assert len(segments) > 1  # Debería dividirse en múltiples segmentos
        assert all(len(segment.strip()) > 10 for segment in segments)  # Todos deberían ser significativos
    
    def test_segment_transcription_empty(self):
        """Test segmentación de transcripción vacía."""
        segments = self.speaker_service._segment_transcription("")
        assert segments == []
        
        segments = self.speaker_service._segment_transcription(None)
        assert segments == []
    
    def test_segment_transcription_short(self):
        """Test segmentación de transcripción muy corta."""
        short_text = "Hola doctor."
        segments = self.speaker_service._segment_transcription(short_text)
        
        assert len(segments) == 1
        assert segments[0].strip() == short_text
    
    def test_calculate_speaker_stats_basic(self):
        """Test cálculo de estadísticas básicas."""
        segments = [
            SpeakerSegment(
                speaker=SpeakerType.PROMOTOR,
                text="¿Cómo se siente?",
                start_time=0.0,
                end_time=3.0,
                confidence=0.9,
                word_count=3
            ),
            SpeakerSegment(
                speaker=SpeakerType.PACIENTE,
                text="Me duele la cabeza",
                start_time=3.5,
                end_time=8.0,
                confidence=0.8,
                word_count=4
            ),
            SpeakerSegment(
                speaker=SpeakerType.PROMOTOR,
                text="¿Desde cuándo?",
                start_time=8.5,
                end_time=10.0,
                confidence=0.85,
                word_count=2
            )
        ]
        
        stats = self.speaker_service._calculate_speaker_stats(segments)
        
        assert isinstance(stats, SpeakerStats)
        assert stats.total_speakers == 2
        assert stats.promotor_time == 4.5  # 3.0 + 1.5
        assert stats.paciente_time == 4.5   # 8.0 - 3.5
        assert stats.speaker_changes == 2
        assert stats.total_duration == 10.0
        assert stats.average_segment_length > 0
    
    def test_calculate_speaker_stats_empty(self):
        """Test cálculo de estadísticas con lista vacía."""
        stats = self.speaker_service._calculate_speaker_stats([])
        
        assert stats.total_speakers == 0
        assert stats.total_duration == 0.0
        assert stats.speaker_changes == 0
    
    @pytest.mark.asyncio
    async def test_diarize_text_only_basic(self):
        """Test diarización usando solo texto."""
        transcription = """
        Buenos días, ¿cómo se siente hoy?
        Me duele mucho la cabeza desde ayer.
        ¿Desde cuándo comenzó exactamente?
        Comenzó ayer por la tarde después del trabajo.
        Le voy a recetar un analgésico.
        Gracias doctor.
        """
        
        segments = await self.speaker_service._diarize_text_only(transcription)
        
        assert len(segments) > 0
        assert all(isinstance(seg, SpeakerSegment) for seg in segments)
        assert all(seg.start_time < seg.end_time for seg in segments)
        
        # Debería haber identificado algunos promotor y paciente
        speakers = [seg.speaker for seg in segments]
        assert SpeakerType.PROMOTOR in speakers or SpeakerType.PACIENTE in speakers
    
    @pytest.mark.asyncio
    async def test_diarize_text_only_medical_conversation(self):
        """Test diarización con conversación médica realista."""
        medical_conversation = """
        Buenos días señora García, ¿cómo se encuentra hoy?
        Buenos días doctor, me siento un poco mejor pero todavía me duele.
        ¿El medicamento que le receté la última vez le ha ayudado?
        Sí doctor, el ibuprofeno me quita el dolor pero vuelve después de unas horas.
        Entiendo. ¿Ha notado si el dolor empeora con alguna actividad específica?
        Sí, cuando estoy mucho tiempo frente a la computadora en el trabajo.
        Vamos a ajustar el tratamiento entonces. Le voy a recetar un relajante muscular.
        Perfecto doctor, ¿hay algo más que deba evitar?
        """
        
        segments = await self.speaker_service._diarize_text_only(medical_conversation)
        
        # Verificar que se identificaron roles correctamente
        promotor_segments = [s for s in segments if s.speaker == SpeakerType.PROMOTOR]
        paciente_segments = [s for s in segments if s.speaker == SpeakerType.PACIENTE]
        
        assert len(promotor_segments) > 0
        assert len(paciente_segments) > 0
        
        # Verificar patrones típicos
        promotor_text = " ".join([s.text for s in promotor_segments])
        paciente_text = " ".join([s.text for s in paciente_segments])
        
        assert "recetar" in promotor_text.lower() or "medicamento" in promotor_text.lower()
        assert "duele" in paciente_text.lower() or "dolor" in paciente_text.lower()
    
    @patch('app.services.speaker_service.librosa')
    @patch('app.services.speaker_service.KMeans')
    @patch('app.services.speaker_service.StandardScaler')
    @pytest.mark.asyncio
    async def test_diarize_with_audio_and_text_success(self, mock_scaler, mock_kmeans, mock_librosa):
        """Test diarización híbrida exitosa con audio y texto."""
        # Mock librosa
        mock_librosa.load.return_value = (np.random.random(16000), 16000)  # 1 segundo de audio
        mock_librosa.yin.return_value = np.array([150.0, 155.0, 160.0])  # Pitch values
        mock_librosa.feature.rms.return_value = [np.array([0.1, 0.15, 0.12])]
        mock_librosa.feature.spectral_centroid.return_value = [np.array([1000, 1100, 1050])]
        mock_librosa.feature.zero_crossing_rate.return_value = [np.array([0.1, 0.12, 0.11])]
        
        # Mock clustering
        mock_kmeans_instance = Mock()
        mock_kmeans_instance.fit_predict.return_value = np.array([0, 1, 0])  # 3 clusters alternados
        mock_kmeans.return_value = mock_kmeans_instance
        
        # Mock scaler
        mock_scaler_instance = Mock()
        mock_scaler_instance.fit_transform.return_value = np.array([[0.1, 0.2], [0.3, 0.4], [0.1, 0.2]])
        mock_scaler.return_value = mock_scaler_instance
        
        # Mock Whisper segments
        whisper_segments = [
            {"start": 0.0, "end": 3.0, "text": "Buenos días, ¿cómo se siente?"},
            {"start": 3.5, "end": 7.0, "text": "Me duele la cabeza doctor"},
            {"start": 7.5, "end": 10.0, "text": "¿Desde cuándo tiene este dolor?"}
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b"fake audio content")
            audio_file = f.name
        
        try:
            transcription = "Buenos días, ¿cómo se siente? Me duele la cabeza doctor. ¿Desde cuándo tiene este dolor?"
            
            segments = await self.speaker_service._diarize_with_audio_and_text(
                audio_file, transcription, whisper_segments
            )
            
            assert len(segments) == 3
            assert all(isinstance(seg, SpeakerSegment) for seg in segments)
            assert all(0 <= seg.confidence <= 1 for seg in segments)
            
        finally:
            os.unlink(audio_file)
    
    @pytest.mark.asyncio
    async def test_diarize_conversation_full_workflow(self):
        """Test flujo completo de diarización."""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b"fake audio content")
            audio_file = f.name
        
        try:
            transcription = """
            Buenos días, ¿cómo se encuentra hoy?
            Me duele mucho la cabeza desde ayer.
            ¿Ha tomado algún medicamento?
            No doctor, esperé a venir a consultarle.
            """
            
            # Sin segmentos de Whisper (fallback a solo texto)
            result = await self.speaker_service.diarize_conversation(
                audio_file, transcription, whisper_segments=None
            )
            
            assert isinstance(result, DiarizationResult)
            assert len(result.speaker_segments) > 0
            assert isinstance(result.speaker_stats, SpeakerStats)
            assert result.processing_time_ms > 0
            assert result.algorithm_version == "1.0"
            
        finally:
            os.unlink(audio_file)
    
    @pytest.mark.asyncio
    async def test_diarize_conversation_error_handling(self):
        """Test manejo de errores en diarización."""
        # Archivo que no existe
        with pytest.raises(SpeakerDiarizationError):
            await self.speaker_service.diarize_conversation(
                "nonexistent_file.wav", "transcription", None
            )
    
    def test_classify_speaker_hybrid_promotor_strong(self):
        """Test clasificación híbrida con evidencia fuerte de promotor."""
        audio_cluster = 1  # Cluster típico de promotor
        text_score = 0.8   # Score fuerte de promotor
        text = "Buenos días, ¿cómo se siente hoy? Le voy a tomar la presión arterial."
        
        speaker_type, confidence = self.speaker_service._classify_speaker_hybrid(
            audio_cluster, text_score, text
        )
        
        assert speaker_type == SpeakerType.PROMOTOR
        assert confidence > 0.8
    
    def test_classify_speaker_hybrid_paciente_strong(self):
        """Test clasificación híbrida con evidencia fuerte de paciente."""
        audio_cluster = 0  # Cluster típico de paciente
        text_score = -0.8  # Score fuerte de paciente
        text = "Me duele mucho la cabeza desde hace tres días. No puedo dormir bien."
        
        speaker_type, confidence = self.speaker_service._classify_speaker_hybrid(
            audio_cluster, text_score, text
        )
        
        assert speaker_type == SpeakerType.PACIENTE
        assert confidence > 0.8
    
    def test_classify_speaker_hybrid_conflicting_evidence(self):
        """Test clasificación híbrida con evidencia conflictiva."""
        audio_cluster = 1  # Sugiere promotor
        text_score = -0.5  # Sugiere paciente
        text = "Me duele pero el doctor dice que está bien."
        
        speaker_type, confidence = self.speaker_service._classify_speaker_hybrid(
            audio_cluster, text_score, text
        )
        
        # Debería ser menos confiable o unknown
        assert confidence < 0.7 or speaker_type == SpeakerType.UNKNOWN


class TestSpeakerServiceDependencies:
    """Tests para manejo de dependencias del servicio."""
    
    @patch('app.services.speaker_service.librosa', None)
    @patch('app.services.speaker_service.KMeans', None)
    def test_missing_audio_dependencies(self):
        """Test comportamiento sin dependencias de audio."""
        service = SpeakerService()
        assert service is not None
        # Debería funcionar con solo análisis de texto
    
    @patch('app.services.speaker_service.librosa', None)
    @pytest.mark.asyncio
    async def test_diarization_fallback_to_text_only(self):
        """Test fallback a solo texto cuando faltan dependencias de audio."""
        service = SpeakerService()
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b"audio content")
            audio_file = f.name
        
        try:
            transcription = "Buenos días doctor. Me duele la cabeza."
            whisper_segments = [{"start": 0, "end": 5, "text": transcription}]
            
            # Debería usar solo texto cuando faltan dependencias
            result = await service.diarize_conversation(audio_file, transcription, whisper_segments)
            
            assert isinstance(result, DiarizationResult)
            assert len(result.speaker_segments) > 0
            
        finally:
            os.unlink(audio_file)


class TestSpeakerServicePerformance:
    """Tests de performance para diarización."""
    
    @pytest.mark.asyncio
    async def test_diarization_performance_text_only(self):
        """Test performance de diarización solo con texto."""
        import time
        
        # Transcripción larga
        long_transcription = """
        Buenos días, ¿cómo se encuentra hoy? Me siento mejor doctor, gracias.
        ¿El medicamento le ha ayudado? Sí, mucho mejor que antes.
        ¿Ha tenido efectos secundarios? No doctor, ninguno.
        ¿Qué tal el dolor de cabeza? Ya casi no me duele.
        """ * 10  # Repetir para hacer más largo
        
        service = get_speaker_service()
        
        start_time = time.time()
        segments = await service._diarize_text_only(long_transcription)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Debería ser rápido incluso con texto largo
        assert processing_time < 5.0  # 5 segundos max
        assert len(segments) > 0
    
    @pytest.mark.asyncio
    async def test_large_conversation_handling(self):
        """Test manejo de conversaciones muy largas."""
        # Crear conversación de ~50 intercambios
        conversation_parts = []
        for i in range(25):
            conversation_parts.extend([
                f"Pregunta médica número {i} del promotor?",
                f"Respuesta del paciente número {i} sobre síntomas."
            ])
        
        long_conversation = " ".join(conversation_parts)
        
        service = get_speaker_service()
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b"long audio content")
            audio_file = f.name
        
        try:
            result = await service.diarize_conversation(audio_file, long_conversation, None)
            
            assert isinstance(result, DiarizationResult)
            assert len(result.speaker_segments) > 10  # Debería tener muchos segmentos
            assert result.speaker_stats.speaker_changes > 5
            
        finally:
            os.unlink(audio_file)


class TestSpeakerServiceAccuracy:
    """Tests de precisión para diarización."""
    
    @pytest.mark.asyncio
    async def test_medical_conversation_accuracy(self):
        """Test precisión con conversación médica típica."""
        medical_conversation = """
        Buenos días señora Martínez, tome asiento por favor.
        Gracias doctor, buenos días.
        ¿Cómo se ha sentido desde la última consulta?
        Mucho mejor doctor, el medicamento me ha ayudado bastante.
        Me alegra escuchar eso. ¿Ha tenido algún efecto secundario?
        No doctor, todo muy bien. Solo que a veces me da un poco de sueño.
        Eso es normal con este medicamento. ¿El dolor de espalda ha mejorado?
        Sí doctor, ya casi no me duele. Solo cuando hago mucho esfuerzo.
        Perfecto. Vamos a continuar con el mismo tratamiento entonces.
        Muy bien doctor, ¿necesito volver en un mes?
        """
        
        service = get_speaker_service()
        segments = await service._diarize_text_only(medical_conversation)
        
        # Analizar precisión
        promotor_segments = [s for s in segments if s.speaker == SpeakerType.PROMOTOR]
        paciente_segments = [s for s in segments if s.speaker == SpeakerType.PACIENTE]
        
        # Debería haber identificado ambos tipos
        assert len(promotor_segments) > 0
        assert len(paciente_segments) > 0
        
        # Verificar que los patrones son correctos
        promotor_text = " ".join([s.text for s in promotor_segments]).lower()
        paciente_text = " ".join([s.text for s in paciente_segments]).lower()
        
        # Promotor debería tener lenguaje médico
        medical_terms_in_promotor = any(term in promotor_text for term in 
                                      ["medicamento", "tratamiento", "consulta", "efecto"])
        
        # Paciente debería describir síntomas/sensaciones
        patient_terms_in_paciente = any(term in paciente_text for term in 
                                      ["me duele", "me siento", "dolor", "mejor"])
        
        # Al menos una de estas condiciones debería cumplirse para buena precisión
        assert medical_terms_in_promotor or patient_terms_in_paciente


# Fixtures para tests
@pytest.fixture
def sample_medical_conversation():
    """Fixture con conversación médica para tests."""
    return """
    Buenos días, ¿cómo se encuentra hoy?
    Buenos días doctor, me siento un poco mejor.
    ¿El medicamento le ha ayudado?
    Sí doctor, el dolor ya no es tan fuerte.
    ¿Ha notado algún efecto secundario?
    No doctor, todo bien por ahora.
    Perfecto, continuemos con el tratamiento.
    """


@pytest.fixture
def sample_whisper_segments():
    """Fixture con segmentos de Whisper para tests."""
    return [
        {"start": 0.0, "end": 3.5, "text": "Buenos días, ¿cómo se encuentra hoy?"},
        {"start": 4.0, "end": 8.0, "text": "Buenos días doctor, me siento un poco mejor."},
        {"start": 8.5, "end": 11.0, "text": "¿El medicamento le ha ayudado?"},
        {"start": 11.5, "end": 15.0, "text": "Sí doctor, el dolor ya no es tan fuerte."},
    ]


@pytest.fixture
def temp_audio_file():
    """Fixture para archivo de audio temporal."""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        f.write(b"fake audio content for speaker diarization tests")
        temp_file = f.name
    
    yield temp_file
    
    try:
        os.unlink(temp_file)
    except FileNotFoundError:
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
