import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { ChatMessage, ChatMode, Source, StructuredData } from '@/types/chat';
import { apiClient } from '@/lib/api-client';
import { API_ENDPOINTS } from '@/lib/constants';

interface ChatStore {
  // State
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  mode: ChatMode;
  
  // Actions
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void;
  clearMessages: () => void;
  setMode: (mode: ChatMode) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  
  // Async actions
  sendMessage: (query: string) => Promise<void>;
}

const generateId = () => Math.random().toString(36).substring(2, 15);

export const useChatStore = create<ChatStore>()(
  persist(
    (set, get) => ({
      // Initial state
      messages: [],
      isLoading: false,
      error: null,
      mode: 'qa',
      
      // Sync actions
      addMessage: (message) => {
        const newMessage: ChatMessage = {
          ...message,
          id: generateId(),
          timestamp: new Date(),
        };
        set((state) => ({
          messages: [...state.messages, newMessage],
        }));
      },
      
      updateMessage: (id, updates) => {
        set((state) => ({
          messages: state.messages.map((msg) =>
            msg.id === id ? { ...msg, ...updates } : msg
          ),
        }));
      },
      
      clearMessages: () => set({ messages: [], error: null }),
      
      setMode: (mode) => set({ mode }),
      
      setLoading: (isLoading) => set({ isLoading }),
      
      setError: (error) => set({ error }),
      
      // Async: Send message to backend
      sendMessage: async (query: string) => {
        const { mode, addMessage, updateMessage, setLoading, setError } = get();
        
        // Add user message immediately (optimistic update)
        addMessage({
          role: 'user',
          content: query,
        });
        
        // Add placeholder for assistant response
        const assistantId = generateId();
        const assistantMessage: ChatMessage = {
          id: assistantId,
          role: 'assistant',
          content: '',
          timestamp: new Date(),
          isStreaming: true,
        };
        set((state) => ({
          messages: [...state.messages, assistantMessage],
        }));
        
        setLoading(true);
        setError(null);
        
        try {
          // Use longer timeout for extraction mode (LLM extraction can take 2+ minutes)
          const timeout = mode === 'extraction' ? 180000 : 60000;
          
          const response = await apiClient.post(API_ENDPOINTS.CHAT, {
            message: query,  // Backend expects 'message' not 'query'
            mode,
          }, {
            timeout,
          });
          
          const data = response.data;
          
          // Map backend source fields to frontend Source type
          const sources: Source[] = data.sources?.map((src: {
            file_name: string;
            page_number: number;
            snippet: string;
            relevance_score?: number;
          }, idx: number) => ({
            id: `src-${idx}`,
            filename: src.file_name,
            page: src.page_number,
            content: src.snippet,
            score: src.relevance_score ?? 0,
          })) ?? [];
          
          // Map structured_data if present (for extraction mode)
          const structuredData: StructuredData | undefined = data.structured_data ? {
            extraction_type: data.structured_data.extraction_type,
            entries: data.structured_data.entries,
            count: data.structured_data.count,
          } : undefined;
          
          // Update assistant message with response
          updateMessage(assistantId, {
            content: data.answer,
            sources,
            structuredData,
            isStreaming: false,
          });
        } catch (err) {
          // Extract detailed error message from backend response
          let errorMessage = 'Unknown error occurred';
          let displayMessage = 'Sorry, I encountered an error.';
          
          if (err && typeof err === 'object' && 'response' in err) {
            const axiosError = err as { response?: { data?: { detail?: string }, status?: number } };
            const status = axiosError.response?.status;
            const detail = axiosError.response?.data?.detail;
            
            if (detail) {
              errorMessage = detail;
              // Create user-friendly message based on error type
              if (detail.includes('No documents') || detail.includes('no relevant')) {
                displayMessage = '📭 No documents found. Please upload a PDF first using the sidebar.';
              } else if (detail.includes('Ollama') || detail.includes('connection')) {
                displayMessage = '🔌 LLM service is unavailable. The AI model may be loading - please try again in a moment.';
              } else if (detail.includes('timeout') || detail.includes('Timeout')) {
                displayMessage = '⏱️ Request timed out. The query may be too complex - try a simpler question.';
              } else if (status === 401) {
                displayMessage = '🔐 Session expired. Please log in again.';
              } else if (status === 500) {
                displayMessage = `⚠️ Server error: ${detail}`;
              } else {
                displayMessage = `⚠️ Error: ${detail}`;
              }
            } else if (status) {
              displayMessage = `⚠️ Request failed (HTTP ${status}). Please try again.`;
            }
          } else if (err instanceof Error) {
            errorMessage = err.message;
            if (err.message.includes('Network Error')) {
              displayMessage = '🌐 Network error. Please check your connection and try again.';
            } else if (err.message.includes('timeout')) {
              displayMessage = '⏱️ Request timed out. Please try again.';
            } else {
              displayMessage = `⚠️ Error: ${err.message}`;
            }
          }
          
          updateMessage(assistantId, {
            content: displayMessage,
            error: errorMessage,
            isStreaming: false,
          });
          setError(errorMessage);
        } finally {
          setLoading(false);
        }
      },
    }),
    {
      name: 'chat-storage',
      partialize: (state) => ({
        messages: state.messages.slice(-50), // Keep last 50 messages
        mode: state.mode,
      }),
    }
  )
);

// Selector hooks for specific state
export const useMessages = () => useChatStore((state) => state.messages);
export const useIsLoading = () => useChatStore((state) => state.isLoading);
export const useChatMode = () => useChatStore((state) => state.mode);
export const useChatError = () => useChatStore((state) => state.error);
