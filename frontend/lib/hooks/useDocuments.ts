import { create } from 'zustand';
import { apiClient } from '@/lib/api-client';
import { API_ENDPOINTS } from '@/lib/constants';

export interface DocumentInfo {
  filename: string;
  pages: number;
  chunks: number;
  status: 'success' | 'error';
  time_seconds?: number;
  error?: string;
}

export interface DocumentStats {
  documents: DocumentInfo[];
  total_chunks: number;
  collection?: string;
}

interface DocumentStore {
  // State
  documents: DocumentInfo[];
  totalChunks: number;
  isUploading: boolean;
  isLoading: boolean;
  uploadProgress: number;
  error: string | null;
  
  // Actions
  setError: (error: string | null) => void;
  clearError: () => void;
  
  // Async actions
  fetchDocuments: () => Promise<void>;
  uploadDocument: (file: File) => Promise<boolean>;
  ingestAssets: () => Promise<boolean>;
  clearDocuments: () => Promise<boolean>;
}

export const useDocumentStore = create<DocumentStore>()((set) => ({
  // Initial state
  documents: [],
  totalChunks: 0,
  isUploading: false,
  isLoading: false,
  uploadProgress: 0,
  error: null,
  
  // Sync actions
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
  
  // Fetch document stats
  fetchDocuments: async () => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await apiClient.get<DocumentStats>(API_ENDPOINTS.DOCUMENTS);
      set({
        documents: response.data.documents || [],
        totalChunks: response.data.total_chunks || 0,
        isLoading: false,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch documents';
      set({ error: message, isLoading: false });
    }
  },
  
  // Upload a single document
  uploadDocument: async (file: File) => {
    set({ isUploading: true, uploadProgress: 0, error: null });
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await apiClient.post(API_ENDPOINTS.UPLOAD, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const progress = Math.round((progressEvent.loaded / progressEvent.total) * 100);
            set({ uploadProgress: progress });
          }
        },
      });
      
      const data = response.data;
      
      // Add uploaded document to state
      if (data.status === 'success') {
        set((state) => ({
          documents: [...state.documents, {
            filename: data.filename,
            pages: data.pages,
            chunks: data.chunks,
            status: 'success',
            time_seconds: data.time_seconds,
          }],
          totalChunks: state.totalChunks + data.chunks,
          isUploading: false,
          uploadProgress: 100,
        }));
        return true;
      }
      
      set({ isUploading: false, uploadProgress: 0 });
      return false;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Upload failed';
      set({ error: message, isUploading: false, uploadProgress: 0 });
      return false;
    }
  },
  
  // Ingest all documents from Assets folder
  ingestAssets: async () => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await apiClient.post(`${API_ENDPOINTS.DOCUMENTS}/ingest`);
      const data = response.data;
      
      if (data.status === 'completed') {
        set({
          documents: data.results?.map((r: DocumentInfo) => ({
            filename: r.filename,
            pages: r.pages,
            chunks: r.chunks,
            status: r.status,
            time_seconds: r.time_seconds,
            error: r.error,
          })) || [],
          totalChunks: data.total_chunks || 0,
          isLoading: false,
        });
        return true;
      }
      
      set({ isLoading: false });
      return false;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Ingestion failed';
      set({ error: message, isLoading: false });
      return false;
    }
  },
  
  // Clear all documents
  clearDocuments: async () => {
    set({ isLoading: true, error: null });
    
    try {
      await apiClient.delete(API_ENDPOINTS.DOCUMENTS);
      set({
        documents: [],
        totalChunks: 0,
        isLoading: false,
      });
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to clear documents';
      set({ error: message, isLoading: false });
      return false;
    }
  },
}));

// Selector hooks
export const useDocuments = () => useDocumentStore((state) => state.documents);
export const useTotalChunks = () => useDocumentStore((state) => state.totalChunks);
export const useIsUploading = () => useDocumentStore((state) => state.isUploading);
export const useUploadProgress = () => useDocumentStore((state) => state.uploadProgress);
export const useDocumentError = () => useDocumentStore((state) => state.error);
