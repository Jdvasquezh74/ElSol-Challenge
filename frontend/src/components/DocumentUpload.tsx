import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { 
  DocumentIcon, 
  PhotoIcon,
  TrashIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClockIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';
import { useDocumentUpload } from '../hooks/useDocumentUpload';
import { LoadingSpinner } from './common/LoadingSpinner';
import { ErrorMessage } from './common/ErrorMessage';
import { clsx } from 'clsx';

export const DocumentUpload: React.FC = () => {
  const { uploadFiles, uploadProgress, removeUpload, clearCompleted, clearAll } = useDocumentUpload();
  const [dragActive, setDragActive] = useState(false);
  const [uploadMetadata, setUploadMetadata] = useState({
    patient_name: '',
    document_type: '',
    description: '',
  });

  const onDrop = useCallback((acceptedFiles: File[]) => {
    uploadFiles(acceptedFiles, uploadMetadata);
    setDragActive(false);
    // Clear metadata after upload
    setUploadMetadata({ patient_name: '', document_type: '', description: '' });
  }, [uploadFiles, uploadMetadata]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'image/tiff': ['.tiff', '.tif'],
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

  const getFileIcon = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    if (extension === 'pdf') {
      return <DocumentIcon className="w-8 h-8 text-red-500" />;
    }
    return <PhotoIcon className="w-8 h-8 text-blue-500" />;
  };

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
        return 'Procesando OCR...';
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
      {/* Metadata Form */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Información del Documento (Opcional)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nombre del Paciente
            </label>
            <input
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="ej: Juan Pérez"
              value={uploadMetadata.patient_name}
              onChange={(e) => setUploadMetadata(prev => ({ ...prev, patient_name: e.target.value }))}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tipo de Documento
            </label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={uploadMetadata.document_type}
              onChange={(e) => setUploadMetadata(prev => ({ ...prev, document_type: e.target.value }))}
            >
              <option value="">Seleccionar tipo</option>
              <option value="Examen médico">Examen médico</option>
              <option value="Receta médica">Receta médica</option>
              <option value="Radiografía">Radiografía</option>
              <option value="Laboratorio">Resultados de laboratorio</option>
              <option value="Historia clínica">Historia clínica</option>
              <option value="Informe médico">Informe médico</option>
              <option value="Otro">Otro</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Descripción
            </label>
            <input
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="ej: Resultados de glucosa"
              value={uploadMetadata.description}
              onChange={(e) => setUploadMetadata(prev => ({ ...prev, description: e.target.value }))}
            />
          </div>
        </div>
      </div>

      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={clsx(
          'border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-blue-400 transition-colors duration-200 cursor-pointer transition-all duration-200',
          (isDragActive || dragActive) && 'border-blue-500 bg-blue-50',
          hasUploads && 'border-solid border-gray-400'
        )}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center space-y-4">
          <div className={clsx(
            'w-16 h-16 rounded-full flex items-center justify-center transition-colors duration-200',
            (isDragActive || dragActive) ? 'bg-blue-100' : 'bg-gray-100'
          )}>
            <DocumentIcon className={clsx(
              'w-8 h-8 transition-colors duration-200',
              (isDragActive || dragActive) ? 'text-blue-600' : 'text-gray-500'
            )} />
          </div>
          
          <div className="text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {isDragActive || dragActive ? 'Suelta los documentos aquí' : 'Subir Documentos Médicos'}
            </h3>
            <p className="text-gray-600 mb-4">
              Arrastra PDFs o imágenes aquí o haz clic para seleccionar
            </p>
            <div className="text-sm text-gray-500">
              <p>Formatos soportados: PDF, JPG, PNG, TIFF</p>
              <p>Tamaño máximo: 10MB por archivo</p>
            </div>
          </div>

          <button className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center">
            Seleccionar Documentos
          </button>
        </div>
      </div>

      {/* Upload Progress */}
      {hasUploads && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">
              Documentos ({uploadProgress.length})
            </h3>
            <div className="flex space-x-2">
              {hasCompleted && (
                <button
                  onClick={clearCompleted}
                  className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium py-2 px-4 rounded-lg transition-colors duration-200 text-sm"
                >
                  Limpiar Completados
                </button>
              )}
              <button
                onClick={clearAll}
                className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium py-2 px-4 rounded-lg transition-colors duration-200 text-sm"
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
                  {getFileIcon(progress.file.name)}
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
                        'bg-blue-500'
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
                        Procesamiento completado
                      </div>
                      
                      {/* OCR Results - Only for DocumentResponse */}
                      {'ocr_result' in progress.result && progress.result.ocr_result && (
                        <div className="mb-3">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-medium text-gray-700">
                              Texto extraído (Confianza: {Math.round(progress.result.ocr_result.confidence * 100)}%)
                            </span>
                            <button className="text-xs text-blue-600 hover:text-blue-700 flex items-center space-x-1">
                              <EyeIcon className="w-3 h-3" />
                              <span>Ver texto</span>
                            </button>
                          </div>
                          <div className="text-xs text-gray-600 bg-white p-2 rounded border max-h-20 overflow-y-auto">
                            {progress.result.ocr_result.text.substring(0, 200)}
                            {progress.result.ocr_result.text.length > 200 && '...'}
                          </div>
                        </div>
                      )}

                      {/* Extracted Metadata - Only for DocumentResponse */}
                      {'extracted_metadata' in progress.result && progress.result.extracted_metadata && (
                        <div className="text-xs">
                          <div className="font-medium text-gray-700 mb-1">Información médica extraída:</div>
                          <div className="grid grid-cols-2 gap-2">
                            {progress.result.extracted_metadata.patient_name && (
                              <div><span className="text-gray-500">Paciente:</span> {progress.result.extracted_metadata.patient_name}</div>
                            )}
                            {progress.result.extracted_metadata.document_type && (
                              <div><span className="text-gray-500">Tipo:</span> {progress.result.extracted_metadata.document_type}</div>
                            )}
                            {progress.result.extracted_metadata.document_date && (
                              <div><span className="text-gray-500">Fecha:</span> {progress.result.extracted_metadata.document_date}</div>
                            )}
                          </div>
                          
                          {progress.result.extracted_metadata.medical_conditions.length > 0 && (
                            <div className="mt-2">
                              <span className="text-gray-500">Condiciones:</span>
                              <div className="flex flex-wrap gap-1 mt-1">
                                {progress.result.extracted_metadata.medical_conditions.slice(0, 3).map((condition, idx) => (
                                  <span key={idx} className="inline-block bg-red-100 text-red-700 text-xs px-2 py-1 rounded">
                                    {condition}
                                  </span>
                                ))}
                                {progress.result.extracted_metadata.medical_conditions.length > 3 && (
                                  <span className="text-xs text-gray-500">
                                    +{progress.result.extracted_metadata.medical_conditions.length - 3} más
                                  </span>
                                )}
                              </div>
                            </div>
                          )}

                          {progress.result.extracted_metadata.medications.length > 0 && (
                            <div className="mt-2">
                              <span className="text-gray-500">Medicamentos:</span>
                              <div className="flex flex-wrap gap-1 mt-1">
                                {progress.result.extracted_metadata.medications.slice(0, 3).map((medication, idx) => (
                                  <span key={idx} className="inline-block bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded">
                                    {medication}
                                  </span>
                                ))}
                                {progress.result.extracted_metadata.medications.length > 3 && (
                                  <span className="text-xs text-gray-500">
                                    +{progress.result.extracted_metadata.medications.length - 3} más
                                  </span>
                                )}
                              </div>
                            </div>
                          )}

                          {/* Action Button */}
                          {progress.result && 'document_id' in progress.result && (
                            <div className="mt-2 flex justify-end">
                              <button 
                                onClick={() => {
                                  // Navigate to document detail - for now just log
                                  console.log('Navigate to document:', progress.result);
                                }}
                                className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                              >
                                Ver documento completo →
                              </button>
                            </div>
                          )}
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
                  Total: {uploadProgress.length} documento(s)
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
        <div className="card bg-purple-50 border-purple-200">
          <div className="flex items-start space-x-3">
            <DocumentIcon className="w-6 h-6 text-purple-600 mt-1" />
            <div>
              <h4 className="font-medium text-purple-900 mb-2">
                ¿Cómo funciona el procesamiento de documentos?
              </h4>
              <ul className="text-sm text-purple-800 space-y-1">
                <li>• <strong>OCR automático</strong> para extraer texto de PDFs e imágenes</li>
                <li>• <strong>Análisis con IA</strong> para identificar información médica</li>
                <li>• <strong>Asociación automática</strong> con pacientes y tipos de documento</li>
                <li>• <strong>Búsqueda inteligente</strong> en el contenido extraído</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
