"""
Tests de integración para speaker diarization - ElSol Challenge.

Tests de integración para diferenciación de hablantes con transcripción.
PLUS Feature 5: Diferenciación de Hablantes
"""

import pytest
import asyncio
import tempfile
import os
import json
import time
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.speaker_service import get_speaker_service, diarize_audio_conversation
from app.services.whisper_service import get_whisper_service
from app.database.models import AudioTranscription
from app.core.schemas import SpeakerType, DiarizationResult, TranscriptionResponse


# Test client
client = TestClient(app)


class TestSpeakerTranscriptionIntegration:
    """Tests de integración entre speaker diarization y transcripción."""
    
    @patch('app.services.whisper_service.openai.Audio.transcribe')
    @pytest.mark.asyncio
    async def test_transcription_with_speaker_diarization(self, mock_whisper):
        """Test integración completa: audio → transcripción → diarización."""
        # Mock Whisper API
        mock_response = Mock()
        mock_response.text = """
        Buenos días señora García, ¿cómo se encuentra hoy?
        Buenos días doctor, me duele mucho la cabeza.
        ¿Desde cuándo tiene este dolor?
        Desde ayer por la tarde, después del trabajo.
        ¿Ha tomado algún medicamento?
        No doctor, esperé a consultarle primero.
        """
        mock_whisper.return_value = mock_response
        
        # Crear archivo de audio temporal
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b"fake medical conversation audio")
            audio_file = f.name
        
        try:
            # 1. Transcribir audio
            whisper_service = get_whisper_service()
            transcription_result = await whisper_service.transcribe_audio(audio_file, "test_conversation.wav")
            
            assert transcription_result is not None
            assert "doctor" in transcription_result.text.lower()
            assert "duele" in transcription_result.text.lower()
            
            # 2. Realizar diarización
            speaker_service = get_speaker_service()
            diarization_result = await speaker_service.diarize_conversation(
                audio_file, transcription_result.text, whisper_segments=None
            )
            
            assert isinstance(diarization_result, DiarizationResult)
            assert len(diarization_result.speaker_segments) > 0
            
            # Verificar que se identificaron ambos tipos de hablantes
            speakers = [seg.speaker for seg in diarization_result.speaker_segments]
            assert SpeakerType.PROMOTOR in speakers or SpeakerType.PACIENTE in speakers
            
            # Verificar estadísticas
            stats = diarization_result.speaker_stats
            assert stats.total_duration > 0
            assert stats.speaker_changes >= 0
            
        finally:
            os.unlink(audio_file)
    
    @patch('app.services.speaker_service.librosa')
    @patch('app.services.whisper_service.openai.Audio.transcribe')
    @pytest.mark.asyncio
    async def test_transcription_with_advanced_diarization(self, mock_whisper, mock_librosa):
        """Test integración con diarización avanzada usando características de audio."""
        # Mock Whisper con segmentos
        mock_response = Mock()
        mock_response.text = "Buenos días doctor. Me duele la cabeza."
        # Simular que Whisper también devuelve segmentos (en implementación real)
        mock_whisper.return_value = mock_response
        
        # Mock librosa para análisis de audio
        import numpy as np
        mock_librosa.load.return_value = (np.random.random(16000), 16000)
        mock_librosa.yin.return_value = np.array([150.0, 180.0])  # Diferentes pitches
        mock_librosa.feature.rms.return_value = [np.array([0.1, 0.2])]
        mock_librosa.feature.spectral_centroid.return_value = [np.array([1000, 1200])]
        mock_librosa.feature.zero_crossing_rate.return_value = [np.array([0.1, 0.15])]
        
        # Simular segmentos de Whisper
        whisper_segments = [
            {"start": 0.0, "end": 2.5, "text": "Buenos días doctor"},
            {"start": 3.0, "end": 6.0, "text": "Me duele la cabeza"}
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b"fake stereo conversation")
            audio_file = f.name
        
        try:
            transcription = "Buenos días doctor. Me duele la cabeza."
            
            # Test diarización avanzada
            diarization_result = await diarize_audio_conversation(
                audio_file, transcription, whisper_segments
            )
            
            assert isinstance(diarization_result, DiarizationResult)
            assert len(diarization_result.speaker_segments) == 2
            
            # Verificar que usó características de audio
            assert diarization_result.algorithm_version == "1.0"
            
        finally:
            os.unlink(audio_file)
    
    @pytest.mark.asyncio
    async def test_speaker_diarization_with_database_integration(self):
        """Test integración con base de datos para almacenar datos de speakers."""
        # Este test simula el flujo completo donde los datos de diarización
        # se almacenan en la base de datos junto con la transcripción
        
        transcription_text = """
        Buenos días, ¿cómo se siente hoy?
        Me siento mejor doctor, gracias.
        ¿El medicamento le ha ayudado?
        Sí, mucho mejor que antes.
        """
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b"conversation for db test")
            audio_file = f.name
        
        try:
            # Realizar diarización
            diarization_result = await diarize_audio_conversation(
                audio_file, transcription_text, whisper_segments=None
            )
            
            # Simular almacenamiento en base de datos
            # (En implementación real esto se haría en el endpoint de upload)
            speaker_data = {
                "segments": [seg.dict() for seg in diarization_result.speaker_segments],
                "stats": diarization_result.speaker_stats.dict()
            }
            
            # Verificar que los datos son serializables a JSON
            json_data = json.dumps(speaker_data, default=str)
            assert json_data is not None
            
            # Verificar que se pueden deserializar
            loaded_data = json.loads(json_data)
            assert "segments" in loaded_data
            assert "stats" in loaded_data
            assert len(loaded_data["segments"]) == len(diarization_result.speaker_segments)
            
        finally:
            os.unlink(audio_file)


class TestSpeakerChatIntegration:
    """Tests de integración entre speaker diarization y sistema de chat."""
    
    def test_speaker_aware_chat_queries_preparation(self):
        """Test preparación para consultas de chat conscientes de hablantes."""
        # Este test prepara la estructura que usaría el sistema de chat
        # para consultas específicas por hablante
        
        # Datos de ejemplo como los que generaría la diarización
        speaker_data = {
            "speaker_segments": [
                {
                    "speaker": "promotor",
                    "text": "¿Cómo se siente hoy? ¿Ha tomado el medicamento?",
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "confidence": 0.92
                },
                {
                    "speaker": "paciente",
                    "text": "Me siento mejor doctor, sí tomé las pastillas.",
                    "start_time": 5.5,
                    "end_time": 9.0,
                    "confidence": 0.88
                }
            ],
            "speaker_stats": {
                "promotor_time": 5.0,
                "paciente_time": 3.5,
                "total_duration": 9.0,
                "speaker_changes": 1
            }
        }
        
        # Verificar estructura compatible con chat
        assert "speaker_segments" in speaker_data
        
        # Simular extracción de información por hablante
        promotor_text = " ".join([
            seg["text"] for seg in speaker_data["speaker_segments"] 
            if seg["speaker"] == "promotor"
        ])
        
        paciente_text = " ".join([
            seg["text"] for seg in speaker_data["speaker_segments"] 
            if seg["speaker"] == "paciente"
        ])
        
        assert "medicamento" in promotor_text.lower()
        assert "mejor" in paciente_text.lower()
        
        # Verificar estadísticas útiles para análisis
        stats = speaker_data["speaker_stats"]
        participation_ratio = stats["paciente_time"] / stats["total_duration"]
        assert 0 <= participation_ratio <= 1
    
    def test_speaker_context_for_rag(self):
        """Test preparación de contexto de speakers para RAG."""
        # Simular datos que se usarían para enriquecer el contexto RAG
        conversation_with_speakers = {
            "transcription_id": "trans_123",
            "patient_name": "Juan Pérez",
            "transcription_text": "Conversación completa...",
            "speaker_segments": [
                {
                    "speaker": "promotor",
                    "text": "¿Qué síntomas tiene?",
                    "confidence": 0.9
                },
                {
                    "speaker": "paciente", 
                    "text": "Me duele la cabeza",
                    "confidence": 0.85
                }
            ]
        }
        
        # Simular extracción de contexto específico por hablante
        def extract_speaker_context(data, speaker_type):
            segments = [s for s in data["speaker_segments"] if s["speaker"] == speaker_type]
            return {
                "text": " ".join([s["text"] for s in segments]),
                "confidence": sum([s["confidence"] for s in segments]) / len(segments) if segments else 0
            }
        
        promotor_context = extract_speaker_context(conversation_with_speakers, "promotor")
        paciente_context = extract_speaker_context(conversation_with_speakers, "paciente")
        
        assert promotor_context["text"] != ""
        assert paciente_context["text"] != ""
        assert 0 <= promotor_context["confidence"] <= 1
        assert 0 <= paciente_context["confidence"] <= 1


class TestSpeakerUploadEndpointIntegration:
    """Tests de integración con el endpoint de upload de audio."""
    
    @patch('app.api.upload.process_transcription_task')
    def test_upload_audio_with_speaker_processing(self, mock_process):
        """Test que el upload de audio incluya procesamiento de speakers."""
        # Mock del procesamiento que incluiría diarización
        async def mock_transcription_with_speakers(transcription_id, file_path, filename, db):
            # Simular procesamiento completo con speakers
            pass
        
        mock_process.side_effect = mock_transcription_with_speakers
        
        # Crear archivo de audio temporal
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b"test audio for speaker integration")
            audio_file = f.name
        
        try:
            # Upload audio
            with open(audio_file, 'rb') as f:
                response = client.post(
                    "/api/v1/upload-audio",
                    files={"file": ("test_conversation.wav", f, "audio/wav")}
                )
            
            # Verificar respuesta exitosa
            assert response.status_code == 200
            data = response.json()
            
            assert "transcription_id" in data
            assert data["filename"] == "test_conversation.wav"
            assert data["status"] == "pending"
            
            # En implementación real, verificaríamos que se procesó con speakers
            
        finally:
            os.unlink(audio_file)


class TestSpeakerPerformanceIntegration:
    """Tests de performance para integración de speakers."""
    
    @pytest.mark.asyncio
    async def test_diarization_performance_with_transcription(self):
        """Test performance del flujo completo transcripción + diarización."""
        import time
        
        # Simular transcripción larga
        long_transcription = """
        Buenos días, ¿cómo se encuentra hoy? Me siento mejor doctor.
        ¿El medicamento le ha funcionado? Sí, mucho mejor que antes.
        ¿Ha tenido efectos secundarios? No doctor, todo bien.
        """ * 20  # Conversación larga
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b"long conversation audio")
            audio_file = f.name
        
        try:
            start_time = time.time()
            
            # Procesar diarización
            result = await diarize_audio_conversation(
                audio_file, long_transcription, whisper_segments=None
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Debería completarse en tiempo razonable
            assert processing_time < 10.0  # 10 segundos max
            assert isinstance(result, DiarizationResult)
            assert len(result.speaker_segments) > 10  # Muchos segmentos
            
        finally:
            os.unlink(audio_file)
    
    @pytest.mark.asyncio
    async def test_concurrent_speaker_processing(self):
        """Test procesamiento concurrente de múltiples diarizaciones."""
        import asyncio
        
        # Crear múltiples archivos de audio
        audio_files = []
        transcriptions = []
        
        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                f.write(f"audio content {i}".encode())
                audio_files.append(f.name)
                transcriptions.append(f"Buenos días doctor {i}. Me duele la cabeza.")
        
        try:
            start_time = time.time()
            
            # Procesar concurrentemente
            tasks = []
            for audio_file, transcription in zip(audio_files, transcriptions):
                task = diarize_audio_conversation(audio_file, transcription, None)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Verificar resultados
            assert len(results) == 3
            for result in results:
                assert not isinstance(result, Exception)
                assert isinstance(result, DiarizationResult)
            
            # Procesamiento concurrente debería ser eficiente
            assert total_time < 15.0  # 15 segundos max para 3 archivos
            
        finally:
            for audio_file in audio_files:
                try:
                    os.unlink(audio_file)
                except FileNotFoundError:
                    pass


class TestSpeakerErrorHandlingIntegration:
    """Tests de manejo de errores en integración de speakers."""
    
    @pytest.mark.asyncio
    async def test_diarization_with_empty_transcription(self):
        """Test diarización con transcripción vacía."""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b"audio content")
            audio_file = f.name
        
        try:
            # Transcripción vacía
            result = await diarize_audio_conversation(audio_file, "", None)
            
            # Debería manejar gracefully
            assert isinstance(result, DiarizationResult)
            # Puede tener segmentos vacíos o un segmento unknown
            
        finally:
            os.unlink(audio_file)
    
    @pytest.mark.asyncio
    async def test_diarization_with_very_short_audio(self):
        """Test diarización con audio muy corto."""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b"short")  # Archivo muy pequeño
            audio_file = f.name
        
        try:
            short_transcription = "Hola."
            
            result = await diarize_audio_conversation(audio_file, short_transcription, None)
            
            assert isinstance(result, DiarizationResult)
            # Debería tener al menos un segmento
            assert len(result.speaker_segments) >= 1
            
        finally:
            os.unlink(audio_file)
    
    @pytest.mark.asyncio
    async def test_diarization_with_audio_processing_error(self):
        """Test diarización cuando falla el procesamiento de audio."""
        with patch('app.services.speaker_service.librosa') as mock_librosa:
            # Mock librosa que falla
            mock_librosa.load.side_effect = Exception("Audio processing error")
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                f.write(b"problematic audio")
                audio_file = f.name
            
            try:
                transcription = "Buenos días doctor. Me duele la cabeza."
                whisper_segments = [{"start": 0, "end": 5, "text": transcription}]
                
                # Debería hacer fallback a solo texto
                result = await diarize_audio_conversation(
                    audio_file, transcription, whisper_segments
                )
                
                assert isinstance(result, DiarizationResult)
                assert len(result.speaker_segments) > 0
                
            finally:
                os.unlink(audio_file)


class TestSpeakerDataConsistency:
    """Tests de consistencia de datos para speaker diarization."""
    
    @pytest.mark.asyncio
    async def test_speaker_segment_timeline_consistency(self):
        """Test consistencia temporal de segmentos de speakers."""
        transcription = """
        Buenos días doctor, ¿cómo está?
        Muy bien, gracias. ¿Cómo se siente usted?
        Me duele un poco la cabeza.
        ¿Desde cuándo tiene este dolor?
        """
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b"conversation audio")
            audio_file = f.name
        
        try:
            result = await diarize_audio_conversation(audio_file, transcription, None)
            
            segments = result.speaker_segments
            
            # Verificar consistencia temporal
            for i in range(len(segments) - 1):
                current = segments[i]
                next_seg = segments[i + 1]
                
                # Cada segmento debe tener start < end
                assert current.start_time < current.end_time
                
                # Los segmentos deberían estar en orden cronológico
                assert current.start_time <= next_seg.start_time
            
            # Verificar que las estadísticas son consistentes
            stats = result.speaker_stats
            total_speaker_time = stats.promotor_time + stats.paciente_time + stats.unknown_time
            
            # El tiempo total debería ser razonable
            assert total_speaker_time <= stats.total_duration * 1.1  # 10% tolerance
            
        finally:
            os.unlink(audio_file)
    
    @pytest.mark.asyncio
    async def test_speaker_confidence_consistency(self):
        """Test consistencia de scores de confianza."""
        transcription = """
        Buenos días, ¿cómo se siente hoy?
        Me duele mucho la cabeza desde ayer.
        ¿Ha tomado algún medicamento?
        No doctor, esperé a consultarle.
        """
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b"clear conversation")
            audio_file = f.name
        
        try:
            result = await diarize_audio_conversation(audio_file, transcription, None)
            
            # Verificar que todas las confianzas están en rango válido
            for segment in result.speaker_segments:
                assert 0.0 <= segment.confidence <= 1.0
            
            # Segmentos con patrones médicos claros deberían tener mayor confianza
            medical_segments = [
                s for s in result.speaker_segments 
                if any(term in s.text.lower() for term in ["doctor", "medicamento", "duele"])
            ]
            
            if medical_segments:
                avg_medical_confidence = sum(s.confidence for s in medical_segments) / len(medical_segments)
                # Los segmentos médicos deberían tener confianza razonable
                assert avg_medical_confidence > 0.3
            
        finally:
            os.unlink(audio_file)


# Fixtures para tests de integración
@pytest.fixture
def sample_medical_audio_file():
    """Fixture para archivo de audio médico simulado."""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        f.write(b"simulated medical conversation audio content")
        temp_file = f.name
    
    yield temp_file
    
    try:
        os.unlink(temp_file)
    except FileNotFoundError:
        pass


@pytest.fixture
def complex_medical_transcription():
    """Fixture con transcripción médica compleja."""
    return """
    Buenos días señora Rodríguez, ¿cómo se ha sentido desde la última consulta?
    Buenos días doctor, mucho mejor gracias. El medicamento me ha ayudado bastante.
    Me alegra escucharlo. ¿Ha tenido algún efecto secundario con el nuevo tratamiento?
    Al principio me daba un poco de mareo, pero ya se me pasó. 
    ¿Y el dolor de espalda que mencionó la vez anterior?
    Ese sí ha mejorado mucho doctor. Ya puedo caminar sin problemas.
    Excelente. Vamos a continuar con la misma dosis entonces.
    Perfecto doctor. ¿Necesito volver el próximo mes?
    Sí, programe su cita para dentro de cuatro semanas.
    Muy bien, muchas gracias doctor.
    """


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
