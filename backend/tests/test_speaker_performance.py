"""
Tests de performance para speaker diarization - ElSol Challenge.

Tests específicos de performance y benchmarking para diferenciación de hablantes.
PLUS Feature 5: Diferenciación de Hablantes
"""

import pytest
import asyncio
import tempfile
import os
import time
import statistics
from unittest.mock import Mock, patch
import numpy as np

from app.services.speaker_service import get_speaker_service, diarize_audio_conversation
from app.core.schemas import DiarizationResult, SpeakerType


class TestSpeakerDiarizationPerformance:
    """Tests de performance para diarización de hablantes."""
    
    @pytest.mark.asyncio
    async def test_text_only_diarization_speed(self):
        """Test velocidad de diarización usando solo texto."""
        # Crear transcripción de tamaño medio
        base_conversation = """
        Buenos días, ¿cómo se encuentra hoy?
        Me siento mejor doctor, gracias por preguntar.
        ¿El medicamento le ha funcionado bien?
        Sí, mucho mejor que el anterior que me daba mareos.
        ¿Ha notado algún efecto secundario con este nuevo?
        No doctor, por ahora todo muy bien.
        """
        
        # Repetir para crear conversación más larga
        medium_conversation = base_conversation * 5  # ~30 intercambios
        
        service = get_speaker_service()
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b"medium length conversation")
            audio_file = f.name
        
        try:
            start_time = time.time()
            
            result = await service.diarize_conversation(
                audio_file, medium_conversation, whisper_segments=None
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Verificar performance
            assert processing_time < 3.0  # Debería completarse en <3 segundos
            assert isinstance(result, DiarizationResult)
            assert len(result.speaker_segments) > 5
            
            # Calcular velocidad de procesamiento
            words_per_second = len(medium_conversation.split()) / processing_time
            assert words_per_second > 50  # Al menos 50 palabras por segundo
            
        finally:
            os.unlink(audio_file)
    
    @pytest.mark.asyncio
    async def test_large_conversation_performance(self):
        """Test performance con conversaciones muy largas."""
        # Crear conversación larga (simular 10 minutos)
        conversation_parts = []
        for i in range(100):  # 100 intercambios
            conversation_parts.extend([
                f"Pregunta médica número {i} del doctor sobre síntomas específicos?",
                f"Respuesta detallada del paciente número {i} describiendo cómo se siente y los cambios que ha notado."
            ])
        
        large_conversation = " ".join(conversation_parts)
        
        service = get_speaker_service()
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b"very long conversation audio")
            audio_file = f.name
        
        try:
            start_time = time.time()
            
            result = await service.diarize_conversation(
                audio_file, large_conversation, whisper_segments=None
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Incluso conversaciones largas deberían procesarse relativamente rápido
            assert processing_time < 15.0  # <15 segundos para conversación muy larga
            assert len(result.speaker_segments) > 20
            
            # Verificar que las estadísticas son razonables
            stats = result.speaker_stats
            assert stats.total_duration > 60  # >1 minuto estimado
            assert stats.speaker_changes > 10
            
        finally:
            os.unlink(audio_file)
    
    @patch('app.services.speaker_service.librosa')
    @patch('app.services.speaker_service.KMeans')
    @pytest.mark.asyncio
    async def test_audio_processing_performance(self, mock_kmeans, mock_librosa):
        """Test performance del procesamiento de audio con características."""
        # Mock librosa para simular procesamiento de audio real
        mock_librosa.load.return_value = (np.random.random(160000), 16000)  # 10 segundos
        mock_librosa.yin.return_value = np.random.uniform(100, 300, 100)  # Pitch values
        mock_librosa.feature.rms.return_value = [np.random.uniform(0.1, 0.3, 100)]
        mock_librosa.feature.spectral_centroid.return_value = [np.random.uniform(800, 1500, 100)]
        mock_librosa.feature.zero_crossing_rate.return_value = [np.random.uniform(0.05, 0.2, 100)]
        
        # Mock clustering
        mock_kmeans_instance = Mock()
        mock_kmeans_instance.fit_predict.return_value = np.random.choice([0, 1], 10)
        mock_kmeans.return_value = mock_kmeans_instance
        
        conversation = """
        Buenos días doctor, ¿cómo está usted hoy?
        Muy bien gracias, ¿y usted cómo se siente?
        Me duele un poco la cabeza desde ayer.
        ¿Ha tomado algún analgésico para el dolor?
        """
        
        # Simular segmentos de Whisper
        whisper_segments = [
            {"start": 0.0, "end": 2.5, "text": "Buenos días doctor, ¿cómo está usted hoy?"},
            {"start": 3.0, "end": 6.0, "text": "Muy bien gracias, ¿y usted cómo se siente?"},
            {"start": 6.5, "end": 9.0, "text": "Me duele un poco la cabeza desde ayer."},
            {"start": 9.5, "end": 12.0, "text": "¿Ha tomado algún analgésico para el dolor?"}
        ]
        
        service = get_speaker_service()
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b"audio with multiple features")
            audio_file = f.name
        
        try:
            start_time = time.time()
            
            result = await service._diarize_with_audio_and_text(
                audio_file, conversation, whisper_segments
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Procesamiento con características de audio debería seguir siendo rápido
            assert processing_time < 5.0  # <5 segundos incluso con análisis de audio
            assert len(result) == 4  # Un segmento por cada entrada de Whisper
            
        finally:
            os.unlink(audio_file)
    
    @pytest.mark.asyncio
    async def test_concurrent_diarization_performance(self):
        """Test performance del procesamiento concurrente."""
        # Crear múltiples conversaciones para procesar concurrentemente
        conversations = [
            "Buenos días doctor. Me duele la cabeza. ¿Qué puedo tomar?",
            "Hola, vengo por los resultados del examen. ¿Cómo salieron?",
            "Doctor, el medicamento no me está funcionando. ¿Qué hago?",
            "Necesito renovar mi receta médica. ¿Es posible?",
            "Me siento mareado desde ayer. ¿Será algo grave?"
        ]
        
        audio_files = []
        for i, conv in enumerate(conversations):
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                f.write(f"conversation {i} audio".encode())
                audio_files.append(f.name)
        
        try:
            start_time = time.time()
            
            # Procesar todas las conversaciones concurrentemente
            tasks = []
            for audio_file, conversation in zip(audio_files, conversations):
                task = diarize_audio_conversation(audio_file, conversation, None)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Verificar que todas se procesaron exitosamente
            assert len(results) == 5
            for result in results:
                assert not isinstance(result, Exception)
                assert isinstance(result, DiarizationResult)
            
            # Procesamiento concurrente debería ser más eficiente que secuencial
            assert total_time < 10.0  # <10 segundos para 5 conversaciones concurrentes
            
            # Calcular throughput
            conversations_per_second = len(conversations) / total_time
            assert conversations_per_second > 0.5  # Al menos 0.5 conversaciones por segundo
            
        finally:
            for audio_file in audio_files:
                try:
                    os.unlink(audio_file)
                except FileNotFoundError:
                    pass
    
    @pytest.mark.asyncio
    async def test_memory_usage_with_large_inputs(self):
        """Test uso de memoria con inputs grandes."""
        import psutil
        import os as system_os
        
        # Obtener uso de memoria inicial
        process = psutil.Process(system_os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Crear conversación muy larga
        very_long_conversation = """
        Buenos días doctor, ¿cómo está usted?
        Muy bien, gracias por preguntar.
        """ * 1000  # Repetir 1000 veces
        
        service = get_speaker_service()
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b"memory test audio" * 1000)  # Archivo "grande"
            audio_file = f.name
        
        try:
            # Procesar conversación muy larga
            result = await service.diarize_conversation(
                audio_file, very_long_conversation, whisper_segments=None
            )
            
            # Verificar uso de memoria después del procesamiento
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # El aumento de memoria debería ser razonable (<100MB)
            assert memory_increase < 100  # No más de 100MB adicionales
            
            # Verificar que el resultado es válido
            assert isinstance(result, DiarizationResult)
            assert len(result.speaker_segments) > 100  # Muchos segmentos
            
        finally:
            os.unlink(audio_file)


class TestSpeakerDiarizationScalability:
    """Tests de escalabilidad para diarización."""
    
    @pytest.mark.asyncio
    async def test_scalability_with_increasing_conversation_length(self):
        """Test escalabilidad con conversaciones de longitud creciente."""
        base_conversation = "Buenos días doctor. Me duele la cabeza. ¿Qué recomienda?"
        
        conversation_lengths = [1, 5, 10, 20, 50]  # Multiplicadores
        processing_times = []
        
        service = get_speaker_service()
        
        for length_multiplier in conversation_lengths:
            conversation = base_conversation * length_multiplier
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                f.write(f"scalability test {length_multiplier}".encode())
                audio_file = f.name
            
            try:
                start_time = time.time()
                
                result = await service.diarize_conversation(
                    audio_file, conversation, whisper_segments=None
                )
                
                end_time = time.time()
                processing_time = end_time - start_time
                processing_times.append(processing_time)
                
                # Verificar que el resultado escala apropiadamente
                expected_segments = length_multiplier  # Al menos tantos segmentos
                assert len(result.speaker_segments) >= expected_segments
                
            finally:
                os.unlink(audio_file)
        
        # Verificar que el crecimiento del tiempo de procesamiento es sub-lineal
        # (idealmente O(n log n) o mejor)
        time_ratios = []
        for i in range(1, len(processing_times)):
            length_ratio = conversation_lengths[i] / conversation_lengths[i-1]
            time_ratio = processing_times[i] / processing_times[i-1]
            time_ratios.append(time_ratio / length_ratio)
        
        # Los ratios deberían ser <2.0 (crecimiento sub-cuadrático)
        avg_ratio = statistics.mean(time_ratios)
        assert avg_ratio < 2.0, f"Performance degradation too high: {avg_ratio}"
    
    @pytest.mark.asyncio
    async def test_load_testing_multiple_simultaneous_requests(self):
        """Test de carga con múltiples requests simultáneos."""
        num_concurrent_requests = 10
        
        # Crear conversaciones de prueba
        test_conversations = []
        audio_files = []
        
        for i in range(num_concurrent_requests):
            conversation = f"""
            Buenos días doctor número {i}, ¿cómo está?
            Muy bien paciente {i}, ¿qué le trae por aquí?
            Me duele la cabeza desde hace {i} días.
            Entiendo, vamos a ver qué podemos hacer.
            """
            test_conversations.append(conversation)
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                f.write(f"load test conversation {i}".encode())
                audio_files.append(f.name)
        
        try:
            start_time = time.time()
            
            # Ejecutar todas las diarizaciones concurrentemente
            tasks = []
            for audio_file, conversation in zip(audio_files, test_conversations):
                task = diarize_audio_conversation(audio_file, conversation, None)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Verificar que todas se completaron exitosamente
            successful_results = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_results) == num_concurrent_requests
            
            # Verificar throughput
            requests_per_second = num_concurrent_requests / total_time
            assert requests_per_second > 1.0  # Al menos 1 request por segundo
            
            # Verificar que no hay degradación significativa de calidad bajo carga
            for result in successful_results:
                assert isinstance(result, DiarizationResult)
                assert len(result.speaker_segments) > 0
                assert result.processing_time_ms > 0
            
        finally:
            for audio_file in audio_files:
                try:
                    os.unlink(audio_file)
                except FileNotFoundError:
                    pass


class TestSpeakerDiarizationBenchmarks:
    """Benchmarks específicos para diarización."""
    
    @pytest.mark.asyncio
    async def test_benchmark_text_analysis_speed(self):
        """Benchmark de velocidad de análisis de texto."""
        test_texts = [
            "Buenos días doctor, ¿cómo está usted hoy?",
            "Me duele mucho la cabeza desde ayer por la noche",
            "¿Ha tomado algún medicamento para el dolor?",
            "Sí doctor, tomé ibuprofeno pero no me ayudó mucho",
            "Vamos a revisar su presión arterial y temperatura",
            "Perfecto doctor, ¿necesito hacer algún examen?"
        ]
        
        service = get_speaker_service()
        
        start_time = time.time()
        
        # Analizar múltiples textos
        for _ in range(100):  # 100 iteraciones
            for text in test_texts:
                score = service._analyze_text_content(text)
                speaker_type, confidence = service._classify_speaker_by_text(text)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Calcular velocidad
        total_analyses = 100 * len(test_texts)
        analyses_per_second = total_analyses / processing_time
        
        # Debería ser muy rápido (>1000 análisis por segundo)
        assert analyses_per_second > 1000
        assert processing_time < 1.0  # <1 segundo total
    
    @pytest.mark.asyncio
    async def test_benchmark_segmentation_speed(self):
        """Benchmark de velocidad de segmentación."""
        # Crear texto largo para segmentar
        long_text = """
        Buenos días doctor, espero que esté muy bien el día de hoy.
        Muchas gracias por recibirme en su consulta.
        Me siento mucho mejor desde la última vez que nos vimos.
        El medicamento que me recetó ha funcionado de maravilla.
        ¿Cree usted que debo continuar con la misma dosis?
        O tal vez podríamos ajustar un poco el tratamiento.
        """ * 20  # Texto muy largo
        
        service = get_speaker_service()
        
        start_time = time.time()
        
        # Segmentar múltiples veces
        for _ in range(50):
            segments = service._segment_transcription(long_text)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Calcular velocidad
        segmentations_per_second = 50 / processing_time
        words_per_second = len(long_text.split()) * 50 / processing_time
        
        # Debería ser rápido
        assert segmentations_per_second > 10  # >10 segmentaciones por segundo
        assert words_per_second > 5000  # >5000 palabras por segundo
    
    @pytest.mark.asyncio
    async def test_benchmark_statistics_calculation(self):
        """Benchmark de cálculo de estadísticas."""
        from app.core.schemas import SpeakerSegment, SpeakerType
        
        # Crear muchos segmentos de prueba
        segments = []
        for i in range(1000):
            segment = SpeakerSegment(
                speaker=SpeakerType.PROMOTOR if i % 2 == 0 else SpeakerType.PACIENTE,
                text=f"Segmento de prueba número {i}",
                start_time=float(i * 2),
                end_time=float(i * 2 + 1.5),
                confidence=0.8,
                word_count=5
            )
            segments.append(segment)
        
        service = get_speaker_service()
        
        start_time = time.time()
        
        # Calcular estadísticas múltiples veces
        for _ in range(100):
            stats = service._calculate_speaker_stats(segments)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Calcular velocidad
        calculations_per_second = 100 / processing_time
        segments_per_second = len(segments) * 100 / processing_time
        
        # Debería ser muy rápido
        assert calculations_per_second > 50  # >50 cálculos por segundo
        assert segments_per_second > 50000  # >50k segmentos procesados por segundo
        assert processing_time < 2.0  # <2 segundos total


class TestSpeakerDiarizationResourceUsage:
    """Tests de uso de recursos para diarización."""
    
    @pytest.mark.asyncio
    async def test_cpu_usage_monitoring(self):
        """Test monitoreo de uso de CPU."""
        import psutil
        
        # Crear conversación para procesar
        conversation = """
        Buenos días doctor, ¿cómo se encuentra hoy?
        Muy bien gracias, ¿y usted cómo se siente?
        """ * 50  # Conversación moderadamente larga
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b"cpu monitoring test")
            audio_file = f.name
        
        try:
            # Monitorear uso de CPU durante el procesamiento
            cpu_percent_before = psutil.cpu_percent(interval=1)
            
            start_time = time.time()
            result = await diarize_audio_conversation(audio_file, conversation, None)
            end_time = time.time()
            
            cpu_percent_after = psutil.cpu_percent(interval=1)
            
            # Verificar que el procesamiento fue eficiente
            assert isinstance(result, DiarizationResult)
            processing_time = end_time - start_time
            
            # El procesamiento no debería saturar la CPU
            # (este test puede ser variable según el sistema)
            cpu_increase = cpu_percent_after - cpu_percent_before
            assert cpu_increase < 80  # No más del 80% de aumento
            
        finally:
            os.unlink(audio_file)
    
    def test_algorithm_complexity_estimation(self):
        """Test para estimar la complejidad algorítmica."""
        service = get_speaker_service()
        
        # Test con diferentes tamaños de input
        input_sizes = [10, 50, 100, 200, 500]
        processing_times = []
        
        for size in input_sizes:
            # Crear transcripción de tamaño variable
            conversation = "Buenos días doctor. Me duele la cabeza. " * size
            
            start_time = time.time()
            segments = service._segment_transcription(conversation)
            end_time = time.time()
            
            processing_time = end_time - start_time
            processing_times.append(processing_time)
        
        # Verificar que el crecimiento es sub-cuadrático
        # (tiempo debería crecer menos que O(n²))
        for i in range(1, len(input_sizes)):
            size_ratio = input_sizes[i] / input_sizes[i-1]
            time_ratio = processing_times[i] / processing_times[i-1] if processing_times[i-1] > 0 else 1
            
            # El ratio de tiempo no debería exceder el cuadrado del ratio de tamaño
            assert time_ratio < size_ratio ** 2, f"Potential O(n²) or worse complexity detected"


# Fixtures para tests de performance
@pytest.fixture
def performance_test_conversation():
    """Fixture con conversación optimizada para tests de performance."""
    return """
    Buenos días doctor, muchas gracias por recibirme el día de hoy.
    Buenos días señora García, un placer verla nuevamente por aquí.
    ¿Cómo se ha sentido desde nuestra última consulta del mes pasado?
    Mucho mejor doctor, el medicamento que me recetó ha funcionado muy bien.
    Me alegra mucho escuchar eso, ¿ha tenido algún efecto secundario?
    Al principio sentía un poco de mareo, pero ya se me pasó completamente.
    Perfecto, eso es normal durante los primeros días de tratamiento.
    ¿Debo continuar con la misma dosis que me indicó la vez anterior?
    Sí, mantengamos la misma dosis por ahora y evaluemos en la próxima cita.
    Muy bien doctor, ¿cuándo debo regresar para el siguiente control?
    """


@pytest.fixture
def large_test_dataset():
    """Fixture con dataset grande para tests de carga."""
    conversations = []
    for i in range(20):
        conversation = f"""
        Consulta médica número {i} del día de hoy.
        Buenos días doctor, vengo por mi control mensual.
        ¿Cómo se ha sentido desde la última vez?
        {['Mejor', 'Igual', 'Un poco peor'][i % 3]} que la vez anterior.
        ¿Ha tomado los medicamentos según las indicaciones?
        Sí doctor, todos los días como me indicó.
        """
        conversations.append(conversation)
    return conversations


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])
