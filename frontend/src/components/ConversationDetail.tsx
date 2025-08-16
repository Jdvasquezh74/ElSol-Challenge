import React, { useState } from 'react';
import {
  ArrowLeftIcon,
  UserIcon,
  DocumentTextIcon,
  ShareIcon,
  ArrowDownTrayIcon,
  TagIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';
import type { TranscriptionResponse } from '../types/api';

interface ConversationDetailProps {
  transcription: TranscriptionResponse;
  onBack: () => void;
}

export const ConversationDetail: React.FC<ConversationDetailProps> = ({ 
  transcription, 
  onBack 
}) => {
  const [activeTab, setActiveTab] = useState<'transcript' | 'analysis' | 'export'>('transcript');

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('es-ES', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getSpeakerColor = (speaker: string) => {
    switch (speaker) {
      case 'promotor':
        return 'speaker-promotor';
      case 'paciente':
        return 'speaker-paciente';
      default:
        return 'speaker-unknown';
    }
  };

  const getSpeakerIcon = (speaker: string) => {
    switch (speaker) {
      case 'promotor':
        return '👨‍⚕️';
      case 'paciente':
        return '👤';
      default:
        return '❓';
    }
  };

  const handleExport = (format: 'json' | 'txt' | 'pdf') => {
    // Implementation would depend on backend support or client-side generation
    console.log(`Exporting as ${format}`);
  };

  const segments = transcription.diarization_result?.speaker_segments || [];
  const stats = transcription.diarization_result?.speaker_stats;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={onBack}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Volver a la lista"
          >
            <ArrowLeftIcon className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {transcription.filename}
            </h1>
            <p className="text-gray-600">
              {formatDate(transcription.created_at)}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => handleExport('txt')}
            className="btn-secondary flex items-center space-x-2"
          >
            <ArrowDownTrayIcon className="w-4 h-4" />
            <span>Exportar</span>
          </button>
          <button className="btn-secondary p-2" title="Compartir">
            <ShareIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Patient Info Card */}
      {transcription.structured_data && (
        <div className="card bg-blue-50 border-blue-200">
          <div className="flex items-start space-x-4">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <UserIcon className="w-6 h-6 text-blue-600" />
            </div>
            <div className="flex-1">
              <h3 className="font-medium text-blue-900 mb-2">Información del Paciente</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                {transcription.structured_data.nombre && (
                  <div>
                    <span className="text-blue-700 font-medium">Nombre:</span>
                    <p className="text-blue-800">{transcription.structured_data.nombre}</p>
                  </div>
                )}
                {transcription.structured_data.edad && (
                  <div>
                    <span className="text-blue-700 font-medium">Edad:</span>
                    <p className="text-blue-800">{transcription.structured_data.edad}</p>
                  </div>
                )}
                {transcription.structured_data.diagnóstico && (
                  <div>
                    <span className="text-blue-700 font-medium">Diagnóstico:</span>
                    <p className="text-blue-800">{transcription.structured_data.diagnóstico}</p>
                  </div>
                )}
                {transcription.structured_data.fecha && (
                  <div>
                    <span className="text-blue-700 font-medium">Fecha consulta:</span>
                    <p className="text-blue-800">{transcription.structured_data.fecha}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('transcript')}
            className={clsx(
              'py-2 px-1 border-b-2 font-medium text-sm',
              activeTab === 'transcript'
                ? 'border-medical-500 text-medical-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            )}
          >
            <div className="flex items-center space-x-2">
              <DocumentTextIcon className="w-4 h-4" />
              <span>Transcripción</span>
            </div>
          </button>
          
          <button
            onClick={() => setActiveTab('analysis')}
            className={clsx(
              'py-2 px-1 border-b-2 font-medium text-sm',
              activeTab === 'analysis'
                ? 'border-medical-500 text-medical-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            )}
          >
            <div className="flex items-center space-x-2">
              <ChartBarIcon className="w-4 h-4" />
              <span>Análisis</span>
            </div>
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'transcript' && (
        <div className="space-y-6">
          {/* Speaker Statistics Summary */}
          {stats && (
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Estadísticas de Participación
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {formatTime(stats.promotor_time)}
                  </div>
                  <div className="text-sm text-blue-700">👨‍⚕️ Promotor</div>
                  <div className="text-xs text-blue-600 mt-1">
                    {Math.round((stats.promotor_time / stats.total_duration) * 100)}%
                  </div>
                </div>
                
                <div className="bg-green-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {formatTime(stats.paciente_time)}
                  </div>
                  <div className="text-sm text-green-700">👤 Paciente</div>
                  <div className="text-xs text-green-600 mt-1">
                    {Math.round((stats.paciente_time / stats.total_duration) * 100)}%
                  </div>
                </div>
                
                <div className="bg-gray-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-gray-600">
                    {stats.speaker_changes}
                  </div>
                  <div className="text-sm text-gray-700">Cambios de hablante</div>
                </div>
                
                <div className="bg-purple-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {formatTime(stats.total_duration)}
                  </div>
                  <div className="text-sm text-purple-700">Duración total</div>
                </div>
              </div>
            </div>
          )}

          {/* Transcript */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                Transcripción con Hablantes
              </h3>
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                <div className="flex items-center space-x-1">
                  <div className="w-3 h-3 bg-blue-500 rounded"></div>
                  <span>Promotor</span>
                </div>
                <div className="flex items-center space-x-1">
                  <div className="w-3 h-3 bg-green-500 rounded"></div>
                  <span>Paciente</span>
                </div>
              </div>
            </div>
            
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {segments.length > 0 ? (
                segments.map((segment, index) => (
                  <div key={index} className={clsx('p-4 rounded-lg', getSpeakerColor(segment.speaker))}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="text-lg">{getSpeakerIcon(segment.speaker)}</span>
                        <span className="font-medium capitalize">
                          {segment.speaker}
                        </span>
                        <span className="text-xs text-gray-500">
                          {Math.round(segment.confidence * 100)}% confianza
                        </span>
                      </div>
                      <div className="text-xs text-gray-500">
                        {formatTime(segment.start_time)} - {formatTime(segment.end_time)}
                      </div>
                    </div>
                    <p className="text-gray-800 leading-relaxed">
                      {segment.text}
                    </p>
                    <div className="mt-2 text-xs text-gray-500">
                      {segment.word_count} palabras • {formatTime(segment.end_time - segment.start_time)} duración
                    </div>
                  </div>
                ))
              ) : transcription.transcription_text ? (
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-gray-800 leading-relaxed">
                    {transcription.transcription_text}
                  </p>
                  <div className="mt-2 text-xs text-gray-500">
                    Transcripción sin diferenciación de hablantes
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <DocumentTextIcon className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>No hay transcripción disponible</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'analysis' && (
        <div className="space-y-6">
          {/* Unstructured Information */}
          {transcription.unstructured_data && (
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Información No Estructurada
              </h3>
              
              <div className="grid gap-6">
                {transcription.unstructured_data.síntomas && (
                  <div>
                    <h4 className="font-medium text-gray-700 mb-2 flex items-center">
                      <TagIcon className="w-4 h-4 mr-2" />
                      Síntomas Reportados
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {Array.isArray(transcription.unstructured_data.síntomas) ? 
                        transcription.unstructured_data.síntomas.map((symptom, idx) => (
                          <span key={idx} className="bg-red-100 text-red-700 px-3 py-1 rounded-full text-sm">
                            {symptom}
                          </span>
                        )) : (
                          <p className="text-gray-600">{transcription.unstructured_data.síntomas}</p>
                        )
                      }
                    </div>
                  </div>
                )}

                {transcription.unstructured_data.contexto && (
                  <div>
                    <h4 className="font-medium text-gray-700 mb-2">Contexto Conversacional</h4>
                    <p className="text-gray-600 bg-gray-50 p-3 rounded-lg">
                      {transcription.unstructured_data.contexto}
                    </p>
                  </div>
                )}

                {transcription.unstructured_data.observaciones && (
                  <div>
                    <h4 className="font-medium text-gray-700 mb-2">Observaciones del Promotor</h4>
                    <p className="text-gray-600 bg-blue-50 p-3 rounded-lg">
                      {transcription.unstructured_data.observaciones}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Speaker Summary */}
          {transcription.speaker_summary && (
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Resumen por Hablante
              </h3>
              
              <div className="grid md:grid-cols-2 gap-6">
                {transcription.speaker_summary.promotor_contributions && (
                  <div>
                    <h4 className="font-medium text-blue-700 mb-3 flex items-center">
                      👨‍⚕️ Contribuciones del Promotor
                    </h4>
                    <ul className="space-y-2">
                      {transcription.speaker_summary.promotor_contributions.map((contribution, idx) => (
                        <li key={idx} className="text-sm text-gray-600 bg-blue-50 p-2 rounded">
                          • {contribution}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {transcription.speaker_summary.paciente_contributions && (
                  <div>
                    <h4 className="font-medium text-green-700 mb-3 flex items-center">
                      👤 Contribuciones del Paciente
                    </h4>
                    <ul className="space-y-2">
                      {transcription.speaker_summary.paciente_contributions.map((contribution, idx) => (
                        <li key={idx} className="text-sm text-gray-600 bg-green-50 p-2 rounded">
                          • {contribution}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Processing Information */}
          <div className="card bg-gray-50">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Información Técnica
            </h3>
            
            <div className="grid md:grid-cols-2 gap-6 text-sm">
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Procesamiento</h4>
                <div className="space-y-1 text-gray-600">
                  <div>
                    <span className="font-medium">Estado:</span> {transcription.status}
                  </div>
                  {transcription.processing_time_seconds && (
                    <div>
                      <span className="font-medium">Tiempo de procesamiento:</span> {transcription.processing_time_seconds}s
                    </div>
                  )}
                  <div>
                    <span className="font-medium">Almacenado en vector DB:</span> {transcription.vector_stored ? '✅ Sí' : '❌ No'}
                  </div>
                </div>
              </div>

              {transcription.diarization_result && (
                <div>
                  <h4 className="font-medium text-gray-700 mb-2">Diarización</h4>
                  <div className="space-y-1 text-gray-600">
                    <div>
                      <span className="font-medium">Algoritmo:</span> {transcription.diarization_result.algorithm_version}
                    </div>
                    <div>
                      <span className="font-medium">Umbral de confianza:</span> {Math.round(transcription.diarization_result.confidence_threshold * 100)}%
                    </div>
                    <div>
                      <span className="font-medium">Tiempo de procesamiento:</span> {transcription.diarization_result.processing_time_ms}ms
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
