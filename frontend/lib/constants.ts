// API Endpoints and Constants

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  // Auth
  LOGIN: '/api/v1/auth/token',
  ME: '/api/v1/auth/me',
  
  // Documents
  DOCUMENTS: '/api/v1/documents',
  UPLOAD: '/api/v1/documents/upload',
  SMART_INGEST: '/api/v1/documents/smart-ingest',
  CLEAR_DOCUMENTS: '/api/v1/documents', // DELETE method
  
  // Chat
  CHAT: '/api/v1/chat',
  
  // Health
  HEALTH: '/api/v1/health',
} as const;

// Animation timings (in seconds for Framer Motion)
export const ANIMATION = {
  FAST: 0.15,
  MEDIUM: 0.3,
  SLOW: 0.5,
  VERY_SLOW: 0.8,
  // Nested structure for components expecting duration.fast pattern
  duration: {
    fast: 0.15,
    medium: 0.3,
    slow: 0.5,
    verySlow: 0.8,
  },
} as const;

// Animation easing curves
export const EASING = {
  ENTRANCE: [0.0, 0.0, 0.2, 1.0],
  EXIT: [0.4, 0.0, 1.0, 1.0],
  INTERACTIVE: [0.34, 1.56, 0.64, 1.0],
  SCROLL: [0.16, 1.0, 0.3, 1.0],
  // camelCase aliases
  entrance: [0.0, 0.0, 0.2, 1.0],
  exit: [0.4, 0.0, 1.0, 1.0],
  easeOut: [0.0, 0.0, 0.2, 1.0],
  easeIn: [0.4, 0.0, 1.0, 1.0],
  spring: [0.34, 1.56, 0.64, 1.0],
} as const;

// Test credentials
export const TEST_CREDENTIALS = {
  email: 'testingcheckuser1234@gmail.com',
  password: 'constructure2024',
} as const;
