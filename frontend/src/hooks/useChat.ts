import { useState, useCallback } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { chatApi, handleApiError } from '../services/api';
import type { ChatResponse } from '../types/api';
import toast from 'react-hot-toast';

interface ChatMessage {
  id: string;
  query: string;
  response?: ChatResponse;
  timestamp: Date;
  isLoading: boolean;
  error?: string;
}

export const useChat = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isVisible, setIsVisible] = useState(false);

  // Get chat examples
  const { data: chatExamples } = useQuery({
    queryKey: ['chat-examples'],
    queryFn: chatApi.getChatExamples,
    staleTime: 1000 * 60 * 30, // 30 minutes
  });

  const chatMutation = useMutation({
    mutationFn: chatApi.chat,
    onSuccess: (response, variables) => {
      setMessages(prev => 
        prev.map(msg => 
          msg.query === variables.query && msg.isLoading
            ? { ...msg, response, isLoading: false }
            : msg
        )
      );
    },
    onError: (error, variables) => {
      const errorMessage = handleApiError(error);
      
      setMessages(prev => 
        prev.map(msg => 
          msg.query === variables.query && msg.isLoading
            ? { ...msg, error: errorMessage, isLoading: false }
            : msg
        )
      );
      
      toast.error(`Error en consulta: ${errorMessage}`);
    },
  });

  const sendMessage = useCallback(async (query: string, maxResults?: number) => {
    if (!query.trim()) return;

    const messageId = Date.now().toString();
    const newMessage: ChatMessage = {
      id: messageId,
      query: query.trim(),
      timestamp: new Date(),
      isLoading: true,
    };

    setMessages(prev => [...prev, newMessage]);
    setIsVisible(true);

    try {
      await chatMutation.mutateAsync({ query: query.trim(), max_results: maxResults });
    } catch (error) {
      // Error handling is done in the mutation's onError
      console.error('Chat error:', error);
    }
  }, [chatMutation]);

  const quickChat = useCallback(async (query: string) => {
    try {
      const response = await chatApi.quickChat(query);
      
      const messageId = Date.now().toString();
      const newMessage: ChatMessage = {
        id: messageId,
        query,
        response,
        timestamp: new Date(),
        isLoading: false,
      };

      setMessages(prev => [...prev, newMessage]);
      setIsVisible(true);
      
      return response;
    } catch (error) {
      const errorMessage = handleApiError(error);
      toast.error(`Error en consulta rápida: ${errorMessage}`);
      throw error;
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const removeMessage = useCallback((messageId: string) => {
    setMessages(prev => prev.filter(msg => msg.id !== messageId));
  }, []);

  const toggleVisibility = useCallback(() => {
    setIsVisible(prev => !prev);
  }, []);

  const getSuggestedQueries = useCallback(() => {
    const suggestions = chatExamples || [
      "¿Qué síntomas reportó el paciente?",
      "¿Qué diagnóstico estableció el promotor?",
      "Listame los pacientes con diabetes",
      "¿Qué documentos médicos tengo disponibles?",
      "¿Cuánto tiempo habló cada persona en la consulta?",
    ];

    // Add dynamic suggestions based on recent messages
    const recentPatients = messages
      .flatMap(msg => msg.response?.sources || [])
      .map(source => source.patient_name)
      .filter((name, index, arr) => name && arr.indexOf(name) === index)
      .slice(0, 3);

    if (recentPatients.length > 0) {
      const patientSuggestions = recentPatients.map(
        patient => `¿Qué información completa tiene ${patient}?`
      );
      return [...patientSuggestions, ...suggestions];
    }

    return suggestions;
  }, [chatExamples, messages]);

  return {
    messages,
    isVisible,
    isLoading: chatMutation.isPending,
    sendMessage,
    quickChat,
    clearMessages,
    removeMessage,
    toggleVisibility,
    setIsVisible,
    chatExamples,
    getSuggestedQueries,
  };
};
