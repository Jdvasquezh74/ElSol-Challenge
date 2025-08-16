import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { ErrorBoundary } from 'react-error-boundary';
import { Header } from './components/common/Header';
import { AudioUpload } from './components/AudioUpload';
import { DocumentUpload } from './components/DocumentUpload';
import { TranscriptionList } from './components/TranscriptionList';
import { ChatInterface } from './components/ChatInterface';
import { ErrorBoundaryFallback } from './components/common/ErrorMessage';
import { useChat } from './hooks/useChat';
import {
  MicrophoneIcon,
  DocumentIcon,
  QueueListIcon,
  Bars3Icon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 30, // 30 minutes
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

type Tab = 'audio' | 'documents' | 'conversations';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>('audio');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { isVisible: chatVisible, toggleVisibility: toggleChat } = useChat();

  const tabs = [
    {
      id: 'audio' as const,
      name: 'Audio Médico',
      icon: MicrophoneIcon,
      description: 'Subir y transcribir conversaciones médicas',
    },
    {
      id: 'documents' as const,
      name: 'Documentos',
      icon: DocumentIcon,
      description: 'Subir PDFs e imágenes médicas',
    },
    {
      id: 'conversations' as const,
      name: 'Conversaciones',
      icon: QueueListIcon,
      description: 'Ver historial de transcripciones',
    },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'audio':
        return <AudioUpload />;
      case 'documents':
        return <DocumentUpload />;
      case 'conversations':
        return <TranscriptionList />;
      default:
        return <AudioUpload />;
    }
  };

  return (
    <ErrorBoundary FallbackComponent={ErrorBoundaryFallback}>
      <QueryClientProvider client={queryClient}>
        <div className="min-h-screen bg-gray-50">
          {/* Header */}
          <Header onToggleChat={toggleChat} chatVisible={chatVisible} />

          <div className="flex">
            {/* Sidebar */}
            <div className={clsx(
              'fixed inset-y-0 left-0 z-40 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0',
              sidebarOpen ? 'translate-x-0' : '-translate-x-full'
            )}>
              <div className="flex flex-col h-full pt-16">
                {/* Mobile close button */}
                <div className="lg:hidden flex justify-end p-4">
                  <button
                    onClick={() => setSidebarOpen(false)}
                    className="p-2 rounded-md text-gray-400 hover:text-gray-600"
                  >
                    <XMarkIcon className="w-6 h-6" />
                  </button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 px-4 pb-4 space-y-2">
                  {tabs.map((tab) => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.id;
                    
                    return (
                      <button
                        key={tab.id}
                        onClick={() => {
                          setActiveTab(tab.id);
                          setSidebarOpen(false);
                        }}
                        className={clsx(
                          'w-full flex items-start space-x-3 px-4 py-3 text-left rounded-lg transition-colors duration-200',
                          isActive
                            ? 'bg-medical-50 text-medical-700 border border-medical-200'
                            : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                        )}
                      >
                        <Icon className={clsx(
                          'w-6 h-6 mt-0.5 flex-shrink-0',
                          isActive ? 'text-medical-600' : 'text-gray-400'
                        )} />
                        <div>
                          <div className={clsx(
                            'font-medium',
                            isActive ? 'text-medical-900' : 'text-gray-900'
                          )}>
                            {tab.name}
                          </div>
                          <div className={clsx(
                            'text-sm mt-1',
                            isActive ? 'text-medical-600' : 'text-gray-500'
                          )}>
                            {tab.description}
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </nav>

                {/* Footer */}
                <div className="p-4 border-t border-gray-200">
                  <div className="text-xs text-gray-500 text-center">
                    <p className="font-medium text-gray-700 mb-1">ElSol Medical AI</p>
                    <p>Sistema de análisis médico con IA</p>
                    <div className="mt-2 flex items-center justify-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span>Sistema operativo</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Mobile sidebar backdrop */}
            {sidebarOpen && (
              <div
                className="fixed inset-0 z-30 bg-gray-600 bg-opacity-75 lg:hidden"
                onClick={() => setSidebarOpen(false)}
              />
            )}

            {/* Main content */}
            <div className="flex-1 lg:ml-0">
              {/* Mobile menu button */}
              <div className="lg:hidden sticky top-16 z-20 bg-white border-b border-gray-200 px-4 py-3">
                <button
                  onClick={() => setSidebarOpen(true)}
                  className="flex items-center space-x-2 text-gray-600 hover:text-gray-900"
                >
                  <Bars3Icon className="w-6 h-6" />
                  <span className="font-medium">Menú</span>
                </button>
              </div>

              {/* Page content */}
              <main className="py-8 px-4 sm:px-6 lg:px-8">
                <div className="max-w-7xl mx-auto">
                  {/* Page header */}
                  <div className="mb-8">
                    <div className="sm:flex sm:items-center sm:justify-between">
                      <div>
                        <h1 className="text-3xl font-bold text-gray-900">
                          {tabs.find(t => t.id === activeTab)?.name}
                        </h1>
                        <p className="mt-2 text-gray-600">
                          {tabs.find(t => t.id === activeTab)?.description}
                        </p>
                      </div>
                      
                      {/* Quick actions */}
                      <div className="mt-4 sm:mt-0 flex space-x-3">
                        {activeTab !== 'audio' && (
                          <button
                            onClick={() => setActiveTab('audio')}
                            className="btn-secondary flex items-center space-x-2"
                          >
                            <MicrophoneIcon className="w-4 h-4" />
                            <span>Subir Audio</span>
                          </button>
                        )}
                        {activeTab !== 'documents' && (
                          <button
                            onClick={() => setActiveTab('documents')}
                            className="btn-secondary flex items-center space-x-2"
                          >
                            <DocumentIcon className="w-4 h-4" />
                            <span>Subir Documento</span>
                          </button>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Tab content */}
                  <div className="animate-fade-in">
                    {renderTabContent()}
                  </div>
                </div>
              </main>
            </div>
          </div>

          {/* Chat Interface */}
          <ChatInterface isVisible={chatVisible} onToggle={toggleChat} />

          {/* Toast notifications */}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#fff',
                color: '#374151',
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
                border: '1px solid #e5e7eb',
              },
              success: {
                iconTheme: {
                  primary: '#10b981',
                  secondary: '#fff',
                },
              },
              error: {
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#fff',
                },
              },
            }}
          />
        </div>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default App;