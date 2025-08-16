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

from app.services.whisper_service import get_whisper_service, WhisperService, WhisperServiceError
from app.core.config import get_settings


class TestWhisperService:
    """Tests para el servicio de transcripción Whisper."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.whisper_service = get_whisper_service()
        self.settings = get_settings()
    
    def test_whisper_service_singleton(self):
        """Test que el servicio sea singleton."""
        service1 = get_whisper_service()
        service2 = get_whisper_service()
        assert service1 is service2
    
    def test_validate_audio_file_valid_formats(self):
        """Test validación de formatos de audio válidos."""
        # Crear archivos temporales para testing
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            wav_file = f.name
            f.write(b"fake audio data")
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            mp3_file = f.name
            f.write(b"fake audio data")
        
        try:
            # Test archivos válidos
            is_valid, message = self.whisper_service.validate_audio_file(wav_file)
            assert is_valid is True
            assert "válido" in message.lower()
            
            is_valid, message = self.whisper_service.validate_audio_file(mp3_file)
            assert is_valid is True
            assert "válido" in message.lower()
        
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
        assert "no encontrado" in message.lower()
    
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
    
    @patch('app.services.whisper_service.openai.Audio.transcribe')
    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self, mock_transcribe):
        """Test transcripción exitosa de audio."""
        # Mock de respuesta de Whisper
        mock_response = Mock()
        mock_response.text = "Buenos días, ¿cómo se siente hoy? Me duele la cabeza."
        mock_transcribe.return_value = mock_response
        
        # Crear archivo de audio temporal
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            audio_file = f.name
            f.write(b"fake audio data for testing")
        
        try:
            result = await self.whisper_service.transcribe_audio(audio_file, "test.wav")
            
            assert result is not None
            assert result.text == "Buenos días, ¿cómo se siente hoy? Me duele la cabeza."
            assert result.language == "spanish"
            assert result.processing_time_seconds > 0
            assert result.confidence_score > 0
            
        finally:
            os.unlink(audio_file)
    
    @patch('app.services.whisper_service.openai.Audio.transcribe')
    @pytest.mark.asyncio
    async def test_transcribe_audio_api_error(self, mock_transcribe):
        """Test manejo de error de API de Whisper."""
        # Mock error de API
        mock_transcribe.side_effect = Exception("API Error")
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            audio_file = f.name
            f.write(b"fake audio data")
        
        try:
            with pytest.raises(WhisperServiceError):
                await self.whisper_service.transcribe_audio(audio_file, "test.wav")
        
        finally:
            os.unlink(audio_file)
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_invalid_file(self):
        """Test transcripción con archivo inválido."""
        with pytest.raises(WhisperServiceError):
            await self.whisper_service.transcribe_audio("nonexistent.wav", "test.wav")
    
    def test_estimate_audio_duration(self):
        """Test estimación de duración de audio."""
        # Este test sería más completo con archivos de audio reales
        # Por ahora test el método básico
        duration = self.whisper_service._estimate_audio_duration(1024000)  # 1MB
        assert duration > 0
        assert isinstance(duration, (int, float))
    
    @pytest.mark.asyncio
    async def test_process_long_audio_file(self):
        """Test procesamiento de archivo de audio largo."""
        # Crear archivo "grande" simulado
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            large_audio_file = f.name
            # Simular archivo de 20MB
            f.write(b"fake audio data" * 1400000)  # ~20MB
        
        try:
            # Debería detectar que es un archivo grande
            file_size = os.path.getsize(large_audio_file)
            assert file_size > 10 * 1024 * 1024  # >10MB
            
            # Validación debería pasar pero advertir sobre tiempo
            is_valid, message = self.whisper_service.validate_audio_file(large_audio_file)
            # El archivo es válido pero grande
            assert is_valid is True
        
        finally:
            os.unlink(large_audio_file)


class TestTranscriptionIntegration:
    """Tests de integración para el flujo completo de transcripción."""
    
    @pytest.mark.asyncio
    async def test_full_transcription_workflow(self):
        """Test del flujo completo de transcripción (mock)."""
        with patch('app.services.whisper_service.openai.Audio.transcribe') as mock_transcribe:
            # Mock respuesta exitosa
            mock_response = Mock()
            mock_response.text = "Prueba de transcripción médica exitosa."
            mock_transcribe.return_value = mock_response
            
            whisper_service = get_whisper_service()
            
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                test_file = f.name
                f.write(b"fake audio content")
            
            try:
                # Validar archivo
                is_valid, message = whisper_service.validate_audio_file(test_file)
                assert is_valid is True
                
                # Transcribir
                result = await whisper_service.transcribe_audio(test_file, "test.wav")
                assert result is not None
                assert "transcripción médica" in result.text
                
            finally:
                os.unlink(test_file)
    
    def test_audio_format_detection(self):
        """Test detección de formatos de audio."""
        whisper_service = get_whisper_service()
        
        # Test diferentes extensiones
        test_files = [
            ("audio.wav", True),
            ("audio.mp3", True), 
            ("audio.WAV", True),  # Case insensitive
            ("audio.MP3", True),
            ("document.pdf", False),
            ("image.jpg", False),
            ("audio", False),  # Sin extensión
            ("audio.txt", False)
        ]
        
        for filename, expected_valid in test_files:
            # Crear archivo temporal con la extensión correcta
            with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix or '.tmp', delete=False) as f:
                temp_file = f.name
                f.write(b"test content")
            
            try:
                # Renombrar para tener el nombre correcto
                final_file = str(Path(temp_file).parent / filename)
                os.rename(temp_file, final_file)
                
                is_valid, _ = whisper_service.validate_audio_file(final_file)
                assert is_valid == expected_valid, f"Failed for {filename}"
                
            finally:
                try:
                    os.unlink(final_file)
                except FileNotFoundError:
                    pass


# Fixture para setup de tests
@pytest.fixture
def temp_audio_file():
    """Fixture que crea un archivo de audio temporal para tests."""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        f.write(b"fake audio data for testing purposes")
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    try:
        os.unlink(temp_file)
    except FileNotFoundError:
        pass


@pytest.fixture
def mock_openai_success():
    """Fixture que mockea una respuesta exitosa de OpenAI."""
    with patch('app.services.whisper_service.openai.Audio.transcribe') as mock:
        response = Mock()
        response.text = "Esta es una transcripción de prueba exitosa."
        mock.return_value = response
        yield mock


class TestTranscriptionPerformance:
    """Tests de performance para transcripción."""
    
    @pytest.mark.asyncio
    async def test_transcription_timeout_handling(self, temp_audio_file, mock_openai_success):
        """Test manejo de timeouts en transcripción."""
        import asyncio
        
        whisper_service = get_whisper_service()
        
        # Test transcripción normal (debería completarse rápido)
        start_time = asyncio.get_event_loop().time()
        result = await whisper_service.transcribe_audio(temp_audio_file, "test.wav")
        end_time = asyncio.get_event_loop().time()
        
        processing_time = end_time - start_time
        assert processing_time < 10  # Debería completarse en <10 segundos (con mock)
        assert result is not None
    
    def test_concurrent_validation(self):
        """Test validación concurrente de múltiples archivos."""
        whisper_service = get_whisper_service()
        
        # Crear múltiples archivos temporales
        temp_files = []
        for i in range(5):
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                f.write(f"audio content {i}".encode())
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
