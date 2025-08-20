import React, { useState, useRef, useEffect } from 'react';
import {
  PaperAirplaneIcon,
  XMarkIcon,
  ChatBubbleLeftRightIcon,
  DocumentTextIcon,
  MicrophoneIcon,
  LightBulbIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import { useChat } from '../hooks/useChat';
import { LoadingSpinner } from './common/LoadingSpinner';
import { clsx } from 'clsx';

interface ChatInterfaceProps {
  isVisible: boolean;
  onToggle: () => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ isVisible, onToggle }) => {
  const [query, setQuery] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const {
    messages,
    isLoading,
    sendMessage,
    clearMessages,
    removeMessage,
    getSuggestedQueries,
  } = useChat();

  const suggestedQueries = getSuggestedQueries();

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;

    await sendMessage(query);
    setQuery('');
    setShowSuggestions(false);
  };

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString('es-ES', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const getSourceIcon = (source: any) => {
    if (source.conversation_id) {
      return <MicrophoneIcon className="w-4 h-4 text-blue-500" />;
    }
    if (source.document_id) {
      return <DocumentTextIcon className="w-4 h-4 text-purple-500" />;
    }
    return <ChatBubbleLeftRightIcon className="w-4 h-4 text-gray-500" />;
  };

  const getSourceType = (source: any) => {
    if (source.conversation_id) return 'Conversación';
    if (source.document_id) return 'Documento';
    return 'Fuente';
  };

  if (!isVisible) {
    return (
      <button
        onClick={onToggle}
        className="fixed bottom-6 right-6 bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-full shadow-lg transition-all duration-200 z-50"
        title="Abrir Chat RAG"
      >
        <ChatBubbleLeftRightIcon className="w-6 h-6" />
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 w-96 max-w-[calc(100vw-3rem)] bg-white rounded-xl shadow-2xl border border-gray-200 z-50 flex flex-col max-h-[80vh]">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-blue-50 rounded-t-xl">
        <div className="flex items-center space-x-2">
          <ChatBubbleLeftRightIcon className="w-5 h-5 text-blue-600" />
          <h3 className="font-medium text-gray-900">Chat RAG Médico</h3>
        </div>
        <div className="flex items-center space-x-2">
          {messages.length > 0 && (
            <button
              onClick={clearMessages}
              className="text-gray-400 hover:text-gray-600 text-sm"
              title="Limpiar conversación"
            >
              Limpiar
            </button>
          )}
          <button
            onClick={onToggle}
            className="text-gray-400 hover:text-gray-600"
            title="Cerrar chat"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
        {messages.length === 0 ? (
          <div className="text-center py-8">
            <ChatBubbleLeftRightIcon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h4 className="font-medium text-gray-700 mb-2">
              ¡Hola! Soy tu asistente médico IA
            </h4>
            <p className="text-sm text-gray-500 mb-4">
              Puedo ayudarte a buscar información en conversaciones y documentos médicos
            </p>
            
            {/* Quick Suggestions */}
            <div className="space-y-2">
              <p className="text-xs font-medium text-gray-700 mb-2">Consultas de ejemplo:</p>
              {suggestedQueries.slice(0, 3).map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="block w-full text-left text-xs bg-gray-50 hover:bg-gray-100 p-2 rounded border transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div key={message.id} className="space-y-3">
              {/* User Query */}
              <div className="flex justify-end">
                <div className="bg-blue-600 text-white p-3 rounded-lg max-w-[80%] relative group">
                  <p className="text-sm">{message.query}</p>
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-xs opacity-75">
                      {formatTimestamp(message.timestamp)}
                    </span>
                    <button
                      onClick={() => removeMessage(message.id)}
                      className="opacity-0 group-hover:opacity-100 text-white hover:text-red-200 ml-2"
                    >
                      <XMarkIcon className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>

              {/* AI Response */}
              <div className="flex justify-start">
                <div className="bg-gray-50 p-3 rounded-lg max-w-[85%]">
                  {message.isLoading ? (
                    <div className="flex items-center space-x-2">
                      <LoadingSpinner size="sm" />
                      <span className="text-sm text-gray-600">Analizando...</span>
                    </div>
                  ) : message.error ? (
                    <div className="text-red-600 text-sm">
                      <p className="font-medium">Error:</p>
                      <p>{message.error}</p>
                    </div>
                  ) : message.response ? (
                    <div className="space-y-3">
                      {/* Answer */}
                      <div className="text-sm text-gray-800">
                        {message.response.answer}
                      </div>

                      {/* Sources */}
                      {message.response.sources.length > 0 && (
                        <div className="border-t border-gray-200 pt-3">
                          <div className="flex items-center space-x-1 mb-2">
                            <LightBulbIcon className="w-4 h-4 text-yellow-500" />
                            <span className="text-xs font-medium text-gray-700">
                              Fuentes ({message.response.sources.length})
                            </span>
                          </div>
                          
                          <div className="space-y-2">
                            {message.response.sources.slice(0, 3).map((source, idx) => (
                              <div key={idx} className="bg-white p-2 rounded border text-xs">
                                <div className="flex items-center justify-between mb-1">
                                  <div className="flex items-center space-x-1">
                                    {getSourceIcon(source)}
                                    <span className="font-medium text-gray-700">
                                      {getSourceType(source)}
                                    </span>
                                  </div>
                                  <span className="text-gray-500">
                                    {Math.round(source.relevance_score * 100)}% relevante
                                  </span>
                                </div>
                                
                                {source.patient_name && (
                                  <div className="text-gray-600 mb-1">
                                    <strong>Paciente:</strong> {source.patient_name}
                                  </div>
                                )}
                                
                                <div className="text-gray-600 italic">
                                  "{source.excerpt.substring(0, 100)}..."
                                </div>

                                {/* Speaker segments if available */}
                                {source.metadata?.speaker_segments_used && (
                                  <div className="mt-1 flex flex-wrap gap-1">
                                    {source.metadata.speaker_segments_used.slice(0, 2).map((segment: string, segIdx: number) => (
                                      <span
                                        key={segIdx}
                                        className={clsx(
                                          'text-xs px-1 py-0.5 rounded',
                                          segment.includes('promotor') ? 'bg-blue-100 text-blue-700' :
                                          segment.includes('paciente') ? 'bg-green-100 text-green-700' :
                                          'bg-gray-100 text-gray-700'
                                        )}
                                      >
                                        {segment}
                                      </span>
                                    ))}
                                  </div>
                                )}
                              </div>
                            ))}
                            
                            {message.response.sources.length > 3 && (
                              <div className="text-xs text-gray-500 text-center">
                                +{message.response.sources.length - 3} fuentes más...
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Metadata */}
                      <div className="flex items-center justify-between text-xs text-gray-500 border-t border-gray-200 pt-2">
                        <div className="flex items-center space-x-1">
                          <ClockIcon className="w-3 h-3" />
                          <span>{message.response.processing_time_ms}ms</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span>Confianza: {Math.round(message.response.confidence * 100)}%</span>
                          <span>|</span>
                          <span className="capitalize">{message.response.intent}</span>
                        </div>
                      </div>

                      {/* Follow-up suggestions */}
                      {message.response.follow_up_suggestions && message.response.follow_up_suggestions.length > 0 && (
                        <div className="border-t border-gray-200 pt-2">
                          <p className="text-xs font-medium text-gray-700 mb-1">Preguntas relacionadas:</p>
                          <div className="space-y-1">
                            {message.response.follow_up_suggestions.slice(0, 2).map((suggestion, idx) => (
                              <button
                                key={idx}
                                onClick={() => handleSuggestionClick(suggestion)}
                                className="block w-full text-left text-xs bg-blue-50 hover:bg-blue-100 text-blue-700 p-1 rounded transition-colors"
                              >
                                {suggestion}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : null}
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggestions */}
      {showSuggestions && suggestedQueries.length > 0 && (
        <div className="border-t border-gray-200 p-3 bg-gray-50">
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {suggestedQueries.slice(0, 5).map((suggestion, idx) => (
              <button
                key={idx}
                onClick={() => handleSuggestionClick(suggestion)}
                className="block w-full text-left text-sm bg-white hover:bg-gray-100 p-2 rounded border transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="border-t border-gray-200 p-4 bg-white rounded-b-xl">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <div className="flex-1 relative">
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => setShowSuggestions(true)}
              onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
              placeholder="Pregunta sobre pacientes, síntomas, documentos..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              disabled={isLoading}
            />
          </div>
          <button
            type="submit"
            disabled={!query.trim() || isLoading}
                            className="flex-shrink-0 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center p-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <LoadingSpinner size="sm" />
            ) : (
              <PaperAirplaneIcon className="w-4 h-4" />
            )}
          </button>
        </form>
        
        <div className="mt-2 text-xs text-gray-500 text-center">
          Presiona Enter para enviar • 
          <button 
            onClick={() => setShowSuggestions(!showSuggestions)}
            className="ml-1 text-blue-600 hover:text-blue-700"
          >
            {showSuggestions ? 'Ocultar' : 'Ver'} sugerencias
          </button>
        </div>
      </div>
    </div>
  );
};
