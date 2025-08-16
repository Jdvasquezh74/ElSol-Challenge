// API Types for ElSol Challenge Frontend

export interface TranscriptionResponse {
  transcription_id: string;
  filename: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  transcription_text?: string;
  structured_data?: StructuredData;
  unstructured_data?: UnstructuredData;
  diarization_result?: DiarizationResult;
  speaker_summary?: SpeakerSummary;
  processing_time_seconds?: number;
  vector_stored?: boolean;
  created_at: string;
  processed_at?: string;
  error_message?: string;
}

export interface StructuredData {
  nombre?: string;
  edad?: string;
  diagnóstico?: string;
  fecha?: string;
  [key: string]: any;
}

export interface UnstructuredData {
  síntomas?: string[];
  contexto?: string;
  observaciones?: string;
  [key: string]: any;
}

export interface DiarizationResult {
  speaker_segments: SpeakerSegment[];
  speaker_stats: SpeakerStats;
  processing_time_ms: number;
  algorithm_version: string;
  confidence_threshold: number;
}

export interface SpeakerSegment {
  speaker: 'promotor' | 'paciente' | 'unknown' | 'multiple';
  text: string;
  start_time: number;
  end_time: number;
  confidence: number;
  word_count: number;
}

export interface SpeakerStats {
  total_speakers: number;
  promotor_time: number;
  paciente_time: number;
  unknown_time: number;
  overlap_time: number;
  total_duration: number;
  speaker_changes: number;
  average_segment_length: number;
}

export interface SpeakerSummary {
  promotor_contributions?: string[];
  paciente_contributions?: string[];
}

// Document Types
export interface DocumentResponse {
  document_id: string;
  filename: string;
  file_type: 'pdf' | 'image';
  file_size_bytes: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  ocr_result?: OCRResult;
  extracted_metadata?: DocumentMetadata;
  vector_stored: boolean;
  patient_association?: string;
  created_at: string;
  processed_at?: string;
  error_message?: string;
}

export interface OCRResult {
  text: string;
  confidence: number;
  page_count?: number;
  processing_time_ms: number;
  language_detected?: string;
}

export interface DocumentMetadata {
  patient_name?: string;
  document_date?: string;
  document_type?: string;
  medical_conditions: string[];
  medications: string[];
  medical_procedures: string[];
}

export interface DocumentSearchResult {
  document_id: string;
  filename: string;
  patient_name?: string;
  relevance_score: number;
  excerpt: string;
  highlight?: string;
  document_type: string;
  created_at: string;
}

// Chat Types
export interface ChatQuery {
  query: string;
  max_results?: number;
}

export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
  confidence: number;
  intent: string;
  follow_up_suggestions?: string[];
  processing_time_ms: number;
}

export interface ChatSource {
  conversation_id?: string;
  document_id?: string;
  patient_name?: string;
  relevance_score: number;
  excerpt: string;
  metadata?: {
    speaker_segments_used?: string[];
    total_patient_time?: number;
    document_type?: string;
    [key: string]: any;
  };
}

// Vector Store Types
export interface VectorStoreStatus {
  status: 'healthy' | 'initializing' | 'error';
  total_conversations: number;
  total_documents: number;
  total_embeddings: number;
  last_updated: string;
}

// Upload Types
export interface UploadProgress {
  file: File;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  result?: TranscriptionResponse | DocumentResponse;
  error?: string;
}

// API Error Types
export interface APIError {
  detail: string;
  status?: number;
}

// Filter and Search Types
export interface TranscriptionFilter {
  status?: string;
  patient_name?: string;
  date_from?: string;
  date_to?: string;
  skip?: number;
  limit?: number;
}

export interface DocumentFilter {
  status?: string;
  patient_name?: string;
  file_type?: string;
  skip?: number;
  limit?: number;
}

// Health Check
export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
  version?: string;
  checks?: {
    database?: string;
    vector_store?: string;
    openai_api?: string;
  };
}
