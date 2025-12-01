// API Response/Request Types

export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

export interface ApiError {
  detail: string;
  status_code: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  has_more: boolean;
}

// Auth Types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in?: number;
}

export interface User {
  email: string;
  id?: string;
}

// Health Check
export interface HealthStatus {
  status: 'healthy' | 'unhealthy';
  qdrant: boolean;
  ollama: boolean;
  timestamp: string;
}
