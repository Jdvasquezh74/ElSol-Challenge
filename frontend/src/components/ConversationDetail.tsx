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

  const handleExport = (format: 'json' | 'txt' | 'pdf') => {
    // Implementation would depend on backend support or client-side generation
    console.log(`Exporting as ${format}`);
  };

  // For now, we'll work with the basic transcription data
  // Speaker diarization functionality will be added later
  const transcriptText = transcription.transcription?.raw_text || '';
  const structuredData = transcription.transcription?.structured_data;
  const unstructuredData = transcription.transcription?.unstructured_data;

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
            className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium py-2 px-4 rounded-lg transition-colors duration-200 flex items-center space-x-2"
          >
            <ArrowDownTrayIcon className="w-4 h-4" />
            <span>Exportar</span>
          </button>
          <button className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium py-2 px-4 rounded-lg transition-colors duration-200 p-2" title="Compartir">
            <ShareIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Patient Info Card */}
      {structuredData && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 bg-blue-50 border-blue-200">
          <div className="flex items-start space-x-4">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <UserIcon className="w-6 h-6 text-blue-600" />
            </div>
            <div className="flex-1">
              <h3 className="font-medium text-blue-900 mb-2">Información del Paciente</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                {structuredData.nombre && (
                  <div>
                    <span className="text-blue-700 font-medium">Nombre:</span>
                    <p className="text-blue-800">{structuredData.nombre}</p>
                  </div>
                )}
                {structuredData.edad && (
                  <div>
                    <span className="text-blue-700 font-medium">Edad:</span>
                    <p className="text-blue-800">{structuredData.edad} años</p>
                  </div>
                )}
                {structuredData.diagnostico && (
                  <div>
                    <span className="text-blue-700 font-medium">Diagnóstico:</span>
                    <p className="text-blue-800">{structuredData.diagnostico}</p>
                  </div>
                )}
                {structuredData.fecha && (
                  <div>
                    <span className="text-blue-700 font-medium">Fecha consulta:</span>
                    <p className="text-blue-800">{structuredData.fecha}</p>
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
                ? 'border-blue-500 text-blue-600'
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
                ? 'border-blue-500 text-blue-600'
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
          {/* Transcription Information Summary */}
          {transcription.transcription && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Información de Transcripción
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {transcription.transcription.confidence_score ? 
                      `${Math.round(transcription.transcription.confidence_score * 100)}%` : 
                      'N/A'
                    }
                  </div>
                  <div className="text-sm text-blue-700">Confianza</div>
                </div>
                
                <div className="bg-green-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {transcription.transcription.audio_duration_seconds ? 
                      formatTime(transcription.transcription.audio_duration_seconds) : 
                      'N/A'
                    }
                  </div>
                  <div className="text-sm text-green-700">Duración</div>
                </div>
                
                <div className="bg-gray-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-gray-600">
                    {transcription.transcription.language_detected || 'N/A'}
                  </div>
                  <div className="text-sm text-gray-700">Idioma</div>
                </div>
                
                <div className="bg-purple-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {transcription.transcription.processing_time_seconds ? 
                      `${transcription.transcription.processing_time_seconds}s` : 
                      'N/A'
                    }
                  </div>
                  <div className="text-sm text-purple-700">Procesamiento</div>
                </div>
              </div>
            </div>
          )}

          {/* Transcript */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                Transcripción Completa
              </h3>
            </div>
            
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {transcriptText ? (
                <div className="bg-gray-50 border-l-4 border-gray-400 pl-4 py-3 rounded-r-lg">
                  <div className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                    {transcriptText}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <DocumentTextIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>No hay transcripción disponible</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'analysis' && (
        <div className="space-y-6">
          {/* Structured Data */}
          {structuredData && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center space-x-2">
                <TagIcon className="w-5 h-5" />
                <span>Información Estructurada</span>
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {structuredData.nombre && (
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <div className="text-sm font-medium text-blue-700 mb-1">Paciente</div>
                    <div className="text-blue-900">{structuredData.nombre}</div>
                  </div>
                )}
                {structuredData.edad && (
                  <div className="bg-green-50 p-4 rounded-lg">
                    <div className="text-sm font-medium text-green-700 mb-1">Edad</div>
                    <div className="text-green-900">{structuredData.edad} años</div>
                  </div>
                )}
                {structuredData.diagnostico && (
                  <div className="bg-red-50 p-4 rounded-lg">
                    <div className="text-sm font-medium text-red-700 mb-1">Diagnóstico</div>
                    <div className="text-red-900">{structuredData.diagnostico}</div>
                  </div>
                )}
                {structuredData.fecha && (
                  <div className="bg-yellow-50 p-4 rounded-lg">
                    <div className="text-sm font-medium text-yellow-700 mb-1">Fecha</div>
                    <div className="text-yellow-900">{structuredData.fecha}</div>
                  </div>
                )}
                {structuredData.medico && (
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <div className="text-sm font-medium text-purple-700 mb-1">Médico</div>
                    <div className="text-purple-900">{structuredData.medico}</div>
                  </div>
                )}
                {structuredData.medicamentos && structuredData.medicamentos.length > 0 && (
                  <div className="bg-indigo-50 p-4 rounded-lg md:col-span-2">
                    <div className="text-sm font-medium text-indigo-700 mb-2">Medicamentos</div>
                    <div className="flex flex-wrap gap-2">
                      {structuredData.medicamentos.map((med, idx) => (
                        <span key={idx} className="bg-indigo-100 text-indigo-800 text-xs px-2 py-1 rounded">
                          {med}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Unstructured Data */}
          {unstructuredData && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center space-x-2">
                <ChartBarIcon className="w-5 h-5" />
                <span>Análisis Contextual</span>
              </h3>
              <div className="space-y-4">
                {unstructuredData.sintomas && unstructuredData.sintomas.length > 0 && (
                  <div>
                    <div className="text-sm font-medium text-gray-700 mb-2">Síntomas</div>
                    <div className="flex flex-wrap gap-2">
                      {unstructuredData.sintomas.map((sintoma, idx) => (
                        <span key={idx} className="bg-red-100 text-red-800 text-sm px-3 py-1 rounded-full">
                          {sintoma}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {unstructuredData.contexto && (
                  <div>
                    <div className="text-sm font-medium text-gray-700 mb-2">Contexto</div>
                    <div className="text-gray-600 bg-gray-50 p-3 rounded-lg">
                      {unstructuredData.contexto}
                    </div>
                  </div>
                )}
                {unstructuredData.observaciones && (
                  <div>
                    <div className="text-sm font-medium text-gray-700 mb-2">Observaciones</div>
                    <div className="text-gray-600 bg-gray-50 p-3 rounded-lg">
                      {unstructuredData.observaciones}
                    </div>
                  </div>
                )}
                {unstructuredData.recomendaciones && unstructuredData.recomendaciones.length > 0 && (
                  <div>
                    <div className="text-sm font-medium text-gray-700 mb-2">Recomendaciones</div>
                    <ul className="list-disc list-inside space-y-1 text-gray-600">
                      {unstructuredData.recomendaciones.map((rec, idx) => (
                        <li key={idx}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'export' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Exportar Conversación
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <button
              onClick={() => handleExport('txt')}
              className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-center"
            >
              <DocumentTextIcon className="w-8 h-8 mx-auto mb-2 text-gray-600" />
              <div className="font-medium">Texto (.txt)</div>
              <div className="text-sm text-gray-500">Transcripción en texto plano</div>
            </button>
            
            <button
              onClick={() => handleExport('json')}
              className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-center"
            >
              <DocumentTextIcon className="w-8 h-8 mx-auto mb-2 text-gray-600" />
              <div className="font-medium">JSON (.json)</div>
              <div className="text-sm text-gray-500">Datos estructurados completos</div>
            </button>
            
            <button
              onClick={() => handleExport('pdf')}
              className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-center"
            >
              <DocumentTextIcon className="w-8 h-8 mx-auto mb-2 text-gray-600" />
              <div className="font-medium">PDF (.pdf)</div>
              <div className="text-sm text-gray-500">Reporte formateado</div>
            </button>
          </div>
          
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center space-x-2 text-yellow-800">
              <span className="text-lg">ℹ️</span>
              <span className="font-medium">Nota:</span>
            </div>
            <p className="text-yellow-700 mt-1 text-sm">
              La funcionalidad de exportación estará disponible próximamente. 
              Los archivos incluirán toda la información de transcripción y análisis.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};