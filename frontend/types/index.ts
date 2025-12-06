// Re-export all types
export * from './api';
// Export extraction types first (canonical definitions)
export * from './extraction';
// Then chat types (which re-exports WageEntry and DoorScheduleEntry)
export type {
  MessageRole,
  ChatMode,
  Source,
  StructuredData,
  ChatMessage,
  ChatRequest,
  ChatResponse,
  ChatState,
  Document,
  UploadProgress
} from './chat';
