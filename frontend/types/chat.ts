// Chat Domain Types

export type MessageRole = 'user' | 'assistant' | 'system';
export type ChatMode = 'qa' | 'extraction' | 'sources_only';

export interface Source {
  id: string;
  filename: string;
  page: number;
  content: string;
  score?: number;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  sources?: Source[];
  timestamp: Date;
  isStreaming?: boolean;
  error?: string;
}

export interface ChatRequest {
  query: string;
  mode?: ChatMode;
  top_k?: number;
  llm_provider?: 'ollama' | 'openai';
  model?: string;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
  query: string;
  mode: ChatMode;
  cached?: boolean;
  processing_time_ms?: number;
}

export interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  mode: ChatMode;
}

// Document Types
export interface Document {
  id: string;
  filename: string;
  page_count: number;
  chunk_count: number;
  uploaded_at: string;
  status: 'pending' | 'processing' | 'indexed' | 'error';
}

export interface UploadProgress {
  filename: string;
  progress: number;
  status: 'uploading' | 'processing' | 'complete' | 'error';
  error?: string;
}
