import React from 'react';
import { HeartIcon, BeakerIcon } from '@heroicons/react/24/outline';

interface HeaderProps {
  onToggleChat?: () => void;
  chatVisible?: boolean;
}

export const Header: React.FC<HeaderProps> = ({ onToggleChat, chatVisible }) => {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo and Title */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600">
              <HeartIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">ElSol Medical AI</h1>
              <p className="text-sm text-gray-500">Sistema de Transcripción y Análisis Médico</p>
            </div>
          </div>

          {/* Navigation and Actions */}
          <div className="flex items-center space-x-4">
            {/* Health Status Indicator */}
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-gray-600">Sistema Activo</span>
            </div>

            {/* Chat Toggle Button */}
            {onToggleChat && (
              <button
                onClick={onToggleChat}
                className={`p-2 rounded-lg transition-colors duration-200 ${
                  chatVisible
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
                title={chatVisible ? 'Ocultar Chat' : 'Mostrar Chat RAG'}
              >
                <BeakerIcon className="w-5 h-5" />
              </button>
            )}

            {/* Version Badge */}
            <div className="hidden sm:flex items-center px-3 py-1 bg-gray-100 rounded-full">
              <span className="text-xs font-medium text-gray-600">v1.0</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
