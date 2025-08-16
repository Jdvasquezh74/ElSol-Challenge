import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { 
  MicrophoneIcon, 
  DocumentTextIcon, 
  TrashIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import { useAudioUpload } from '../hooks/useAudioUpload';
import { LoadingSpinner } from './common/LoadingSpinner';
import { ErrorMessage } from './common/ErrorMessage';
import { clsx } from 'clsx';

export const AudioUpload: React.FC = () => {
  const { uploadFiles, uploadProgress, removeUpload, clearCompleted, clearAll } = useAudioUpload();
  const [dragActive, setDragActive] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    uploadFiles(acceptedFiles);
    setDragActive(false);
  }, [uploadFiles]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/wav': ['.wav'],
      'audio/mpeg': ['.mp3'],
      'audio/mp3': ['.mp3'],
    },
    multiple: true,
    onDragEnter: () => setDragActive(true),
    onDragLeave: () => setDragActive(false),
  });

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Utility function for duration formatting (currently unused but may be needed)
  // const formatDuration = (seconds: number) => {
  //   const mins = Math.floor(seconds / 60);
  //   const secs = Math.floor(seconds % 60);
  //   return `${mins}:${secs.toString().padStart(2, '0')}`;
  // };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'uploading':
        return <ClockIcon className="w-5 h-5 text-blue-500" />;
      case 'processing':
        return <LoadingSpinner size="sm" />;
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'error':
        return <ExclamationCircleIcon className="w-5 h-5 text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'uploading':
        return 'Subiendo...';
      case 'processing':
        return 'Transcribiendo...';
      case 'completed':
        return 'Completado';
      case 'error':
        return 'Error';
      default:
        return status;
    }
  };

  const hasUploads = uploadProgress.length > 0;
  const hasCompleted = uploadProgress.some(p => p.status === 'completed');
  const hasErrors = uploadProgress.some(p => p.status === 'error');

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={clsx(
          'upload-area cursor-pointer transition-all duration-200',
          (isDragActive || dragActive) && 'dragover',
          hasUploads && 'border-solid border-gray-400'
        )}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center space-y-4">
          <div className={clsx(
            'w-16 h-16 rounded-full flex items-center justify-center transition-colors duration-200',
            (isDragActive || dragActive) ? 'bg-medical-100' : 'bg-gray-100'
          )}>
            <MicrophoneIcon className={clsx(
              'w-8 h-8 transition-colors duration-200',
              (isDragActive || dragActive) ? 'text-medical-600' : 'text-gray-500'
            )} />
          </div>
          
          <div className="text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {isDragActive || dragActive ? 'Suelta los archivos aquí' : 'Subir Audio Médico'}
            </h3>
            <p className="text-gray-600 mb-4">
              Arrastra archivos de audio aquí o haz clic para seleccionar
            </p>
            <div className="text-sm text-gray-500">
              <p>Formatos soportados: WAV, MP3</p>
              <p>Tamaño máximo: 25MB por archivo</p>
            </div>
          </div>

          <button className="btn-primary">
            Seleccionar Archivos
          </button>
        </div>
      </div>

      {/* Upload Progress */}
      {hasUploads && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">
              Archivos de Audio ({uploadProgress.length})
            </h3>
            <div className="flex space-x-2">
              {hasCompleted && (
                <button
                  onClick={clearCompleted}
                  className="btn-secondary text-sm"
                >
                  Limpiar Completados
                </button>
              )}
              <button
                onClick={clearAll}
                className="btn-secondary text-sm"
              >
                Limpiar Todo
              </button>
            </div>
          </div>

          <div className="space-y-3">
            {uploadProgress.map((progress) => (
              <div
                key={progress.key}
                className="flex items-center space-x-4 p-4 border border-gray-200 rounded-lg"
              >
                {/* File Icon and Info */}
                <div className="flex-shrink-0">
                  <DocumentTextIcon className="w-8 h-8 text-gray-400" />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {progress.file.name}
                    </p>
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(progress.status)}
                      <span className="text-sm text-gray-600">
                        {getStatusText(progress.status)}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>{formatFileSize(progress.file.size)}</span>
                    <span>{progress.progress}%</span>
                  </div>

                  {/* Progress Bar */}
                  <div className="mt-2 w-full bg-gray-200 rounded-full h-1.5">
                    <div
                      className={clsx(
                        'h-1.5 rounded-full transition-all duration-300',
                        progress.status === 'completed' ? 'bg-green-500' :
                        progress.status === 'error' ? 'bg-red-500' :
                        'bg-medical-500'
                      )}
                      style={{ width: `${progress.progress}%` }}
                    />
                  </div>

                  {/* Error Message */}
                  {progress.error && (
                    <div className="mt-2">
                      <ErrorMessage
                        title="Error de procesamiento"
                        message={progress.error}
                        type="error"
                        className="text-xs"
                      />
                    </div>
                  )}

                  {/* Success Result Preview */}
                  {progress.status === 'completed' && progress.result && (
                    <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                      <div className="text-xs text-gray-600 mb-2">
                        Transcripción completada
                      </div>
                      
                      {/* Speaker Statistics - Only for TranscriptionResponse */}
                      {'diarization_result' in progress.result && progress.result.diarization_result && (
                        <div className="grid grid-cols-3 gap-2 text-xs">
                          <div className="text-center">
                            <div className="font-medium text-blue-600">
                              {Math.round(progress.result.diarization_result.speaker_stats.promotor_time)}s
                            </div>
                            <div className="text-gray-500">Promotor</div>
                          </div>
                          <div className="text-center">
                            <div className="font-medium text-green-600">
                              {Math.round(progress.result.diarization_result.speaker_stats.paciente_time)}s
                            </div>
                            <div className="text-gray-500">Paciente</div>
                          </div>
                          <div className="text-center">
                            <div className="font-medium text-gray-600">
                              {progress.result.diarization_result.speaker_stats.speaker_changes}
                            </div>
                            <div className="text-gray-500">Cambios</div>
                          </div>
                        </div>
                      )}

                      {/* Structured Data Preview - Only for TranscriptionResponse */}
                      {'structured_data' in progress.result && progress.result.structured_data && (
                        <div className="mt-2 text-xs">
                          <div className="font-medium text-gray-700 mb-1">Información extraída:</div>
                          <div className="space-y-1">
                            {progress.result.structured_data.nombre && (
                              <div><span className="text-gray-500">Paciente:</span> {progress.result.structured_data.nombre}</div>
                            )}
                            {progress.result.structured_data.diagnóstico && (
                              <div><span className="text-gray-500">Diagnóstico:</span> {progress.result.structured_data.diagnóstico}</div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Remove Button */}
                <button
                  onClick={() => removeUpload(progress.key)}
                  className="flex-shrink-0 p-2 text-gray-400 hover:text-red-500 transition-colors"
                  title="Eliminar"
                >
                  <TrashIcon className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>

          {/* Summary */}
          {hasUploads && (
            <div className="mt-4 p-3 bg-gray-50 rounded-lg">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">
                  Total: {uploadProgress.length} archivo(s)
                </span>
                <div className="space-x-4">
                  <span className="text-green-600">
                    ✓ {uploadProgress.filter(p => p.status === 'completed').length} completados
                  </span>
                  {hasErrors && (
                    <span className="text-red-600">
                      ✗ {uploadProgress.filter(p => p.status === 'error').length} con error
                    </span>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Instructions */}
      {!hasUploads && (
        <div className="card bg-blue-50 border-blue-200">
          <div className="flex items-start space-x-3">
            <MicrophoneIcon className="w-6 h-6 text-blue-600 mt-1" />
            <div>
              <h4 className="font-medium text-blue-900 mb-2">
                ¿Cómo funciona la transcripción médica?
              </h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• <strong>Transcripción automática</strong> con OpenAI Whisper</li>
                <li>• <strong>Diferenciación de hablantes</strong> (promotor vs paciente)</li>
                <li>• <strong>Extracción de información médica</strong> estructurada</li>
                <li>• <strong>Almacenamiento inteligente</strong> para consultas posteriores</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
