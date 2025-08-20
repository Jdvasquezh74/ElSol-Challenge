"""
Tests para el servicio de transcripción de audio - ElSol Challenge.

Tests básicos para validar funcionalidad de transcripción con Whisper API.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import os
from pathlib import Path

#from app.services.whisper_service import get_whisper_service, WhisperService, WhisperServiceError
from app.services.whisper_service import get_whisper_service, LocalWhisperService, WhisperTranscriptionError
from app.core.config import get_settings


class TestWhisperService:
    """Tests para el servicio de transcripción Whisper."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.whisper_service = get_whisper_service()
        self.settings = get_settings()
    
    def test_whisper_service_creation(self):
        """Test que el servicio se puede crear correctamente."""
        service1 = get_whisper_service()
        service2 = get_whisper_service()
        # No es singleton, cada llamada crea una nueva instancia
        assert isinstance(service1, LocalWhisperService)
        assert isinstance(service2, LocalWhisperService)
    
    def test_validate_audio_file_valid_formats(self):
        """Test validación de formatos de audio válidos."""
        # Crear archivo WAV válido con header correcto
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            wav_file = f.name
            # Header WAV válido: RIFF + tamaño + WAVE
            f.write(b'RIFF' + b'\x24\x00\x00\x00' + b'WAVE' + b'fmt ' + b'\x10\x00\x00\x00')
        
        # Crear archivo MP3 válido con header ID3
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            mp3_file = f.name
            # Header MP3 válido: ID3 tag
            f.write(b'ID3' + b'\x03\x00\x00\x00' + b'extra_content')
        
        try:
            # Test archivos válidos
            is_valid, message = self.whisper_service.validate_audio_file(wav_file)
            assert is_valid is True
            assert message is None
            
            is_valid, message = self.whisper_service.validate_audio_file(mp3_file)
            assert is_valid is True
            assert message is None
        
        finally:
            # Cleanup
            os.unlink(wav_file)
            os.unlink(mp3_file)
    
    def test_validate_audio_file_invalid_format(self):
        """Test validación de formatos inválidos."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            txt_file = f.name
            f.write(b"not audio data")
        
        try:
            is_valid, message = self.whisper_service.validate_audio_file(txt_file)
            assert is_valid is False
            assert "no permitida" in message.lower()
        
        finally:
            os.unlink(txt_file)
    
    def test_validate_audio_file_nonexistent(self):
        """Test validación de archivo que no existe."""
        is_valid, message = self.whisper_service.validate_audio_file("nonexistent.wav")
        assert is_valid is False
        assert "no existe" in message.lower()
    
    def test_validate_audio_file_empty(self):
        """Test validación de archivo vacío."""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            empty_file = f.name
            # No escribir nada = archivo vacío
        
        try:
            is_valid, message = self.whisper_service.validate_audio_file(empty_file)
            assert is_valid is False
            assert "vacío" in message.lower()
        
        finally:
            os.unlink(empty_file)
    
    @patch.object(LocalWhisperService, '_perform_local_transcription')
    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self, mock_transcription):
        """Test transcripción exitosa de audio."""
        # Mock de respuesta local de Whisper
        mock_transcription.return_value = {
            "text": "Buenos días, ¿cómo se siente hoy? Me duele la cabeza.",
            "language": "es",
            "segments": [{"start": 0, "end": 5, "avg_logprob": -0.1}]
        }
        
        # Crear archivo WAV válido
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            audio_file = f.name
            f.write(b'RIFF' + b'\x24\x00\x00\x00' + b'WAVE' + b'fmt ' + b'\x10\x00\x00\x00')
        
        try:
            result = await self.whisper_service.transcribe_audio(audio_file)
            
            assert result is not None
            assert "Buenos días" in result["text"]
            assert result["language"] == "es"
            assert "processing_time_seconds" in result
            assert "confidence_score" in result
            
        finally:
            os.unlink(audio_file)
    
    @patch.object(LocalWhisperService, '_perform_local_transcription')
    @pytest.mark.asyncio
    async def test_transcribe_audio_api_error(self, mock_transcription):
        """Test manejo de error de transcripción local."""
        # Mock error de transcripción
        mock_transcription.side_effect = Exception("Transcription Error")
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            audio_file = f.name
            f.write(b'RIFF' + b'\x24\x00\x00\x00' + b'WAVE' + b'fmt ' + b'\x10\x00\x00\x00')
        
        try:
            with pytest.raises(WhisperTranscriptionError):
                await self.whisper_service.transcribe_audio(audio_file)
        
        finally:
            os.unlink(audio_file)
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_invalid_file(self):
        """Test transcripción con archivo inválido."""
        with pytest.raises(WhisperTranscriptionError):
            await self.whisper_service.transcribe_audio("nonexistent.wav")
    
    def test_get_model_info(self):
        """Test obtención de información del modelo."""
        info = self.whisper_service.get_model_info()
        assert "model_name" in info
        assert "device" in info
        assert "is_loaded" in info
        assert info["model_name"] == self.settings.WHISPER_MODEL
        assert isinstance(info["cuda_available"], bool)
    
    @pytest.mark.asyncio
    async def test_process_long_audio_file(self):
        """Test procesamiento de archivo de audio largo."""
        # Crear archivo "grande" simulado con header válido
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            large_audio_file = f.name
            # Header WAV válido + contenido grande
            header = b'RIFF' + b'\x24\x00\x00\x00' + b'WAVE' + b'fmt ' + b'\x10\x00\x00\x00'
            f.write(header + b"fake audio data" * 2000000)  # ~30MB
        
        try:
            # Debería detectar que es un archivo grande
            file_size = os.path.getsize(large_audio_file)
            assert file_size > 10 * 1024 * 1024  # >10MB
            
            # Validación debería fallar por exceder tamaño máximo
            is_valid, message = self.whisper_service.validate_audio_file(large_audio_file)
            # El archivo excede el límite máximo
            assert is_valid is False
            assert "excede el límite máximo" in message
        
        finally:
            os.unlink(large_audio_file)


class TestTranscriptionIntegration:
    """Tests de integración para el flujo completo de transcripción."""
    
    @patch.object(LocalWhisperService, '_perform_local_transcription')
    @pytest.mark.asyncio
    async def test_full_transcription_workflow(self, mock_transcription):
        """Test del flujo completo de transcripción (mock)."""
        # Mock respuesta exitosa
        mock_transcription.return_value = {
            "text": "Prueba de transcripción médica exitosa.",
            "language": "es",
            "segments": [{"start": 0, "end": 3, "avg_logprob": -0.1}]
        }
        
        whisper_service = get_whisper_service()
        
        # Crear archivo WAV válido
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            test_file = f.name
            f.write(b'RIFF' + b'\x24\x00\x00\x00' + b'WAVE' + b'fmt ' + b'\x10\x00\x00\x00')
        
        try:
            # Validar archivo
            is_valid, message = whisper_service.validate_audio_file(test_file)
            assert is_valid is True
            assert message is None
            
            # Transcribir
            result = await whisper_service.transcribe_audio(test_file)
            assert result is not None
            assert "transcripción médica" in result["text"]
            
        finally:
            os.unlink(test_file)
    
    def test_audio_format_detection(self):
        """Test detección de formatos de audio."""
        whisper_service = get_whisper_service()
        
        test_cases = [
            # (filename, content, expected_valid)
            ("audio.wav", b'RIFF\x24\x00\x00\x00WAVE', True),
            ("audio.mp3", b'ID3\x03\x00\x00\x00', True),
            ("audio.mp3", b'\xff\xfb\x90\x00', True),  # MP3 frame header
            ("audio.WAV", b'RIFF\x24\x00\x00\x00WAVE', True),  # Case insensitive
            ("document.pdf", b'%PDF-1.4', False),
            ("image.jpg", b'\xff\xd8\xff\xe0', False),
            ("audio.txt", b'plain text', False),
        ]
        
        for filename, content, expected_valid in test_cases:
            with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as f:
                f.write(content)
                temp_file = f.name
            
            try:
                is_valid, _ = whisper_service.validate_audio_file(temp_file)
                assert is_valid == expected_valid, f"Failed for {filename} with content {content[:10]}"
            finally:
                os.unlink(temp_file)


# Fixture para setup de tests
@pytest.fixture
def temp_audio_file():
    """Fixture que crea un archivo de audio temporal para tests."""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        # Crear archivo WAV válido con header
        f.write(b'RIFF' + b'\x24\x00\x00\x00' + b'WAVE' + b'fmt ' + b'\x10\x00\x00\x00')
        f.write(b"fake audio data for testing purposes")
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    try:
        os.unlink(temp_file)
    except FileNotFoundError:
        pass


@pytest.fixture
def mock_whisper_success():
    """Fixture que mockea una respuesta exitosa de Whisper local."""
    with patch.object(LocalWhisperService, '_perform_local_transcription') as mock:
        mock.return_value = {
            "text": "Esta es una transcripción de prueba exitosa.",
            "language": "es",
            "segments": [{"start": 0, "end": 3, "avg_logprob": -0.1}]
        }
        yield mock


class TestTranscriptionPerformance:
    """Tests de performance para transcripción."""
    
    @pytest.mark.asyncio
    async def test_transcription_timeout_handling(self, temp_audio_file, mock_whisper_success):
        """Test manejo de timeouts en transcripción."""
        import asyncio
        
        whisper_service = get_whisper_service()
        
        # Test transcripción normal (debería completarse rápido)
        start_time = asyncio.get_event_loop().time()
        result = await whisper_service.transcribe_audio(temp_audio_file)
        end_time = asyncio.get_event_loop().time()
        
        processing_time = end_time - start_time
        assert processing_time < 10  # Debería completarse en <10 segundos (con mock)
        assert result is not None
        assert "text" in result
    
    def test_concurrent_validation(self):
        """Test validación concurrente de múltiples archivos."""
        whisper_service = get_whisper_service()
        
        # Crear múltiples archivos temporales con headers válidos
        temp_files = []
        for i in range(5):
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                # Header WAV válido + contenido único
                header = b'RIFF' + b'\x24\x00\x00\x00' + b'WAVE' + b'fmt ' + b'\x10\x00\x00\x00'
                f.write(header + f"audio content {i}".encode())
                temp_files.append(f.name)
        
        try:
            # Validar todos concurrentemente
            results = []
            for file_path in temp_files:
                is_valid, message = whisper_service.validate_audio_file(file_path)
                results.append(is_valid)
            
            # Todos deberían ser válidos
            assert all(results)
            assert len(results) == 5
        
        finally:
            # Cleanup
            for file_path in temp_files:
                try:
                    os.unlink(file_path)
                except FileNotFoundError:
                    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
