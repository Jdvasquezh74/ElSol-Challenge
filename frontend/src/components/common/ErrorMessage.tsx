import React from 'react';
import { ExclamationTriangleIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { clsx } from 'clsx';

interface ErrorMessageProps {
  title?: string;
  message: string;
  onDismiss?: () => void;
  type?: 'error' | 'warning' | 'info';
  className?: string;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  title = 'Error',
  message,
  onDismiss,
  type = 'error',
  className,
}) => {
  const typeStyles = {
    error: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800',
  };

  const iconStyles = {
    error: 'text-red-500',
    warning: 'text-yellow-500',
    info: 'text-blue-500',
  };

  return (
    <div className={clsx(
      'border rounded-lg p-4',
      typeStyles[type],
      className
    )}>
      <div className="flex items-start">
        <ExclamationTriangleIcon className={clsx('w-5 h-5 mt-0.5 mr-3', iconStyles[type])} />
        <div className="flex-1">
          <h3 className="text-sm font-medium">{title}</h3>
          <p className="text-sm mt-1 opacity-90">{message}</p>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className={clsx(
              'ml-3 p-1 rounded-md hover:bg-black hover:bg-opacity-10 transition-colors',
              iconStyles[type]
            )}
          >
            <XMarkIcon className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};

interface ErrorBoundaryFallbackProps {
  error: Error;
  resetErrorBoundary: () => void;
}

export const ErrorBoundaryFallback: React.FC<ErrorBoundaryFallbackProps> = ({
  error,
  resetErrorBoundary,
}) => {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <div className="text-center">
            <ExclamationTriangleIcon className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-lg font-medium text-gray-900 mb-2">
              Algo salió mal
            </h2>
            <p className="text-sm text-gray-600 mb-6">
              Ha ocurrido un error inesperado en la aplicación.
            </p>
            <details className="text-left mb-6">
              <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-700">
                Detalles técnicos
              </summary>
              <pre className="mt-2 text-xs text-red-600 bg-red-50 p-2 rounded overflow-auto">
                {error.message}
              </pre>
            </details>
            <button
              onClick={resetErrorBoundary}
              className="btn-primary w-full"
            >
              Recargar aplicación
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
