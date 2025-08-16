import axios from 'axios';
import type {
  TranscriptionResponse,
  DocumentResponse,
  DocumentSearchResult,
  ChatQuery,
  ChatResponse,
  VectorStoreStatus,
  HealthResponse,
  TranscriptionFilter,
  DocumentFilter,
} from '../types/api';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error(`❌ API Error:`, error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Audio/Transcription API
export const audioApi = {
  // Upload audio file
  uploadAudio: async (file: File): Promise<TranscriptionResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/api/v1/upload-audio', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Get transcription by ID
  getTranscription: async (id: string): Promise<TranscriptionResponse> => {
    const response = await api.get(`/api/v1/transcriptions/${id}`);
    return response.data;
  },

  // List transcriptions with filters
  getTranscriptions: async (filters: TranscriptionFilter = {}): Promise<TranscriptionResponse[]> => {
    const response = await api.get('/api/v1/transcriptions', { params: filters });
    return response.data;
  },

  // Delete transcription
  deleteTranscription: async (id: string): Promise<void> => {
    await api.delete(`/api/v1/transcriptions/${id}`);
  },
};

// Document API
export const documentApi = {
  // Upload document (PDF/Image)
  uploadDocument: async (
    file: File, 
    metadata?: { patient_name?: string; document_type?: string; description?: string }
  ): Promise<DocumentResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    if (metadata?.patient_name) {
      formData.append('patient_name', metadata.patient_name);
    }
    if (metadata?.document_type) {
      formData.append('document_type', metadata.document_type);
    }
    if (metadata?.description) {
      formData.append('description', metadata.description);
    }
    
    const response = await api.post('/api/v1/upload-document', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Get document by ID
  getDocument: async (id: string): Promise<DocumentResponse> => {
    const response = await api.get(`/api/v1/documents/${id}`);
    return response.data;
  },

  // List documents with filters
  getDocuments: async (filters: DocumentFilter = {}): Promise<DocumentResponse[]> => {
    const response = await api.get('/api/v1/documents', { params: filters });
    return response.data;
  },

  // Search documents
  searchDocuments: async (
    query: string,
    filters: { patient_name?: string; document_type?: string; max_results?: number } = {}
  ): Promise<DocumentSearchResult[]> => {
    const response = await api.get('/api/v1/documents/search', {
      params: { query, ...filters },
    });
    return response.data;
  },

  // Delete document
  deleteDocument: async (id: string): Promise<void> => {
    await api.delete(`/api/v1/documents/${id}`);
  },
};

// Chat API
export const chatApi = {
  // Send chat query
  chat: async (query: ChatQuery): Promise<ChatResponse> => {
    const response = await api.post('/api/v1/chat', query);
    return response.data;
  },

  // Quick chat (simplified)
  quickChat: async (query: string): Promise<ChatResponse> => {
    const response = await api.post('/api/v1/chat/quick', { query });
    return response.data;
  },

  // Get chat examples
  getChatExamples: async (): Promise<string[]> => {
    const response = await api.get('/api/v1/chat/examples');
    return response.data;
  },

  // Get chat statistics
  getChatStats: async () => {
    const response = await api.get('/api/v1/chat/stats');
    return response.data;
  },
};

// Vector Store API
export const vectorApi = {
  // Get vector store status
  getStatus: async (): Promise<VectorStoreStatus> => {
    const response = await api.get('/api/v1/vector-store/status');
    return response.data;
  },

  // Get stored conversations
  getConversations: async (filters: { skip?: number; limit?: number } = {}) => {
    const response = await api.get('/api/v1/vector-store/conversations', { params: filters });
    return response.data;
  },

  // Search in vector store
  search: async (query: string, filters: { max_results?: number; min_score?: number } = {}) => {
    const response = await api.post('/api/v1/vector-store/search', { query, ...filters });
    return response.data;
  },
};

// Health API
export const healthApi = {
  // Health check
  getHealth: async (): Promise<HealthResponse> => {
    const response = await api.get('/health');
    return response.data;
  },
};

// Utility functions
export const uploadWithProgress = (
  file: File,
  _uploadFn: (file: File) => Promise<unknown>,
  onProgress?: (progress: number) => void
) => {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    
    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable && onProgress) {
        const progress = (event.loaded / event.total) * 100;
        onProgress(progress);
      }
    });
    
    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText);
          resolve(response);
        } catch (e) {
          reject(new Error('Invalid JSON response'));
        }
      } else {
        reject(new Error(`Upload failed with status ${xhr.status}`));
      }
    });
    
    xhr.addEventListener('error', () => {
      reject(new Error('Upload failed'));
    });
    
    const formData = new FormData();
    formData.append('file', file);
    
    xhr.open('POST', `${API_BASE_URL}/api/v1/upload-audio`);
    xhr.send(formData);
  });
};

// Error handling utilities
export const handleApiError = (error: any): string => {
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }
  
  if (error.message) {
    return error.message;
  }
  
  return 'Ha ocurrido un error inesperado';
};

export const isNetworkError = (error: any): boolean => {
  return !error.response && error.request;
};

export default api;
