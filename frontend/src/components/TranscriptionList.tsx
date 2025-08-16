import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  DocumentTextIcon,
  ClockIcon,
  UserIcon,
  TrashIcon,
  EyeIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClockIcon as PendingIcon,
} from '@heroicons/react/24/outline';
import { audioApi } from '../services/api';
import { LoadingCard, LoadingSpinner } from './common/LoadingSpinner';
import { ErrorMessage } from './common/ErrorMessage';
import { ConversationDetail } from './ConversationDetail';
import { clsx } from 'clsx';
import type { TranscriptionResponse, TranscriptionFilter } from '../types/api';

export const TranscriptionList: React.FC = () => {
  const [filters, setFilters] = useState<TranscriptionFilter>({
    skip: 0,
    limit: 20,
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTranscription, setSelectedTranscription] = useState<TranscriptionResponse | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  const { 
    data: transcriptions = [], 
    isLoading, 
    error, 
    refetch 
  } = useQuery({
    queryKey: ['transcriptions', filters],
    queryFn: () => audioApi.getTranscriptions(filters),
    refetchInterval: 5000, // Refresh every 5 seconds for status updates
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      setFilters(prev => ({ ...prev, patient_name: searchTerm, skip: 0 }));
    } else {
      setFilters(prev => ({ ...prev, patient_name: undefined, skip: 0 }));
    }
  };

  const handleFilterChange = (key: keyof TranscriptionFilter, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value, skip: 0 }));
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'processing':
        return <LoadingSpinner size="sm" />;
      case 'pending':
        return <PendingIcon className="w-5 h-5 text-yellow-500" />;
      case 'failed':
        return <ExclamationCircleIcon className="w-5 h-5 text-red-500" />;
      default:
        return <ClockIcon className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Completado';
      case 'processing':
        return 'Procesando';
      case 'pending':
        return 'Pendiente';
      case 'failed':
        return 'Error';
      default:
        return status;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-700 bg-green-100';
      case 'processing':
        return 'text-blue-700 bg-blue-100';
      case 'pending':
        return 'text-yellow-700 bg-yellow-100';
      case 'failed':
        return 'text-red-700 bg-red-100';
      default:
        return 'text-gray-700 bg-gray-100';
    }
  };

  const filteredTranscriptions = transcriptions.filter(t => 
    !searchTerm || 
    t.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.structured_data?.nombre?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (selectedTranscription) {
    return (
      <ConversationDetail
        transcription={selectedTranscription}
        onBack={() => setSelectedTranscription(null)}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Conversaciones Médicas</h2>
          <p className="text-gray-600">
            {filteredTranscriptions.length} conversación(es) encontrada(s)
          </p>
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="btn-secondary flex items-center space-x-2"
        >
          <FunnelIcon className="w-4 h-4" />
          <span>Filtros</span>
        </button>
      </div>

      {/* Search and Filters */}
      <div className="card">
        <form onSubmit={handleSearch} className="flex space-x-4">
          <div className="flex-1">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Buscar por nombre de archivo o paciente..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-medical-500"
              />
            </div>
          </div>
          <button type="submit" className="btn-primary">
            Buscar
          </button>
        </form>

        {showFilters && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Estado
                </label>
                <select
                  value={filters.status || ''}
                  onChange={(e) => handleFilterChange('status', e.target.value || undefined)}
                  className="input-field"
                >
                  <option value="">Todos los estados</option>
                  <option value="completed">Completado</option>
                  <option value="processing">Procesando</option>
                  <option value="pending">Pendiente</option>
                  <option value="failed">Error</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Fecha desde
                </label>
                <input
                  type="date"
                  value={filters.date_from || ''}
                  onChange={(e) => handleFilterChange('date_from', e.target.value || undefined)}
                  className="input-field"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Fecha hasta
                </label>
                <input
                  type="date"
                  value={filters.date_to || ''}
                  onChange={(e) => handleFilterChange('date_to', e.target.value || undefined)}
                  className="input-field"
                />
              </div>
            </div>

            <div className="mt-4 flex justify-end">
              <button
                onClick={() => {
                  setFilters({ skip: 0, limit: 20 });
                  setSearchTerm('');
                }}
                className="btn-secondary mr-2"
              >
                Limpiar Filtros
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, idx) => (
            <LoadingCard key={idx} />
          ))}
        </div>
      ) : error ? (
        <ErrorMessage
          title="Error al cargar conversaciones"
          message="No se pudieron cargar las conversaciones. Intenta nuevamente."
          onDismiss={() => refetch()}
        />
      ) : filteredTranscriptions.length === 0 ? (
        <div className="card text-center py-12">
          <DocumentTextIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No hay conversaciones
          </h3>
          <p className="text-gray-600 mb-6">
            {searchTerm || filters.status ? 
              'No se encontraron conversaciones con los filtros aplicados.' :
              'Sube tu primer archivo de audio para comenzar.'
            }
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredTranscriptions.map((transcription) => (
            <div key={transcription.transcription_id} className="card hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-4 flex-1">
                  {/* Status Icon */}
                  <div className="flex-shrink-0 mt-1">
                    {getStatusIcon(transcription.status)}
                  </div>

                  {/* Main Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-lg font-medium text-gray-900 truncate">
                        {transcription.filename}
                      </h3>
                      <span className={clsx(
                        'px-2 py-1 text-xs font-medium rounded-full',
                        getStatusColor(transcription.status)
                      )}>
                        {getStatusText(transcription.status)}
                      </span>
                    </div>

                    {/* Patient Info */}
                    {transcription.structured_data && (
                      <div className="flex flex-wrap items-center gap-4 mb-3 text-sm">
                        {transcription.structured_data.nombre && (
                          <div className="flex items-center space-x-1">
                            <UserIcon className="w-4 h-4 text-gray-500" />
                            <span className="font-medium text-gray-700">
                              {transcription.structured_data.nombre}
                            </span>
                          </div>
                        )}
                        {transcription.structured_data.diagnóstico && (
                          <div className="text-gray-600">
                            <span className="font-medium">Diagnóstico:</span> {transcription.structured_data.diagnóstico}
                          </div>
                        )}
                        {transcription.structured_data.edad && (
                          <div className="text-gray-600">
                            <span className="font-medium">Edad:</span> {transcription.structured_data.edad}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Speaker Stats */}
                    {transcription.diarization_result && (
                      <div className="grid grid-cols-4 gap-4 mb-3 text-xs bg-gray-50 p-3 rounded-lg">
                        <div className="text-center">
                          <div className="font-medium text-blue-600">
                            {formatDuration(transcription.diarization_result.speaker_stats.promotor_time)}
                          </div>
                          <div className="text-gray-500">Promotor</div>
                        </div>
                        <div className="text-center">
                          <div className="font-medium text-green-600">
                            {formatDuration(transcription.diarization_result.speaker_stats.paciente_time)}
                          </div>
                          <div className="text-gray-500">Paciente</div>
                        </div>
                        <div className="text-center">
                          <div className="font-medium text-gray-600">
                            {transcription.diarization_result.speaker_stats.speaker_changes}
                          </div>
                          <div className="text-gray-500">Cambios</div>
                        </div>
                        <div className="text-center">
                          <div className="font-medium text-gray-600">
                            {formatDuration(transcription.diarization_result.speaker_stats.total_duration)}
                          </div>
                          <div className="text-gray-500">Total</div>
                        </div>
                      </div>
                    )}

                    {/* Metadata */}
                    <div className="flex items-center justify-between text-sm text-gray-500">
                      <div className="flex items-center space-x-1">
                        <ClockIcon className="w-4 h-4" />
                        <span>{formatDate(transcription.created_at)}</span>
                      </div>
                      
                      {transcription.processing_time_seconds && (
                        <span>
                          Procesado en {transcription.processing_time_seconds}s
                        </span>
                      )}
                    </div>

                    {/* Error Message */}
                    {transcription.error_message && (
                      <div className="mt-2">
                        <ErrorMessage
                          title="Error de procesamiento"
                          message={transcription.error_message}
                          type="error"
                        />
                      </div>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center space-x-2 ml-4">
                  {transcription.status === 'completed' && (
                    <button
                      onClick={() => setSelectedTranscription(transcription)}
                      className="p-2 text-gray-400 hover:text-medical-600 transition-colors"
                      title="Ver detalles"
                    >
                      <EyeIcon className="w-5 h-5" />
                    </button>
                  )}
                  
                  <button
                    className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                    title="Eliminar"
                  >
                    <TrashIcon className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination would go here if needed */}
      {filteredTranscriptions.length >= (filters.limit || 20) && (
        <div className="flex justify-center">
          <button
            onClick={() => setFilters(prev => ({ 
              ...prev, 
              skip: (prev.skip || 0) + (prev.limit || 20) 
            }))}
            className="btn-secondary"
          >
            Cargar más conversaciones
          </button>
        </div>
      )}
    </div>
  );
};
