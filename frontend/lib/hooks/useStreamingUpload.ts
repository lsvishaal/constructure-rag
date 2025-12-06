"use client";

import { useState, useCallback, useRef } from 'react';
import { API_BASE_URL, API_ENDPOINTS } from '@/lib/constants';
import { getAuthToken } from '@/lib/api-client';
import type { UploadProgressData, UploadStep } from '@/components/upload';

interface UseStreamingUploadOptions {
  onComplete?: (data: UploadProgressData) => void;
  onError?: (error: string) => void;
}

export function useStreamingUpload(options: UseStreamingUploadOptions = {}) {
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState<UploadProgressData>({
    step: 'idle',
    progress: 0,
    detail: '',
  });
  const abortControllerRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    setProgress({
      step: 'idle',
      progress: 0,
      detail: '',
    });
  }, []);

  const uploadWithStreaming = useCallback(async (file: File): Promise<boolean> => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setProgress({
        step: 'error',
        progress: 0,
        detail: 'Only PDF files are supported',
        error: 'Only PDF files are supported',
      });
      return false;
    }

    setIsUploading(true);
    setProgress({
      step: 'saving',
      progress: 0,
      detail: 'Preparing upload...',
      filename: file.name,
    });

    abortControllerRef.current = new AbortController();

    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error('Not authenticated');
      }

      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(
        API_BASE_URL + API_ENDPOINTS.UPLOAD_STREAM,
        {
          method: 'POST',
          headers: {
            'Authorization': 'Bearer ' + token,
          },
          body: formData,
          signal: abortControllerRef.current.signal,
        }
      );

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || 'HTTP ' + response.status);
      }

      if (!response.body) {
        throw new Error('No response body');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              const progressData: UploadProgressData = {
                step: data.step as UploadStep,
                progress: data.progress || 0,
                detail: data.detail || '',
                filename: file.name,
                pages: data.pages,
                text_pages: data.text_pages,
                chunks: data.chunks,
                time_seconds: data.time_seconds,
                pages_per_second: data.pages_per_second,
                error: data.error,
              };

              setProgress(progressData);

              if (data.step === 'complete') {
                options.onComplete?.(progressData);
                setIsUploading(false);
                return true;
              }

              if (data.step === 'error') {
                options.onError?.(data.error || 'Upload failed');
                setIsUploading(false);
                return false;
              }
            } catch (parseError) {
              console.warn('Failed to parse SSE data:', parseError);
            }
          }
        }
      }

      setIsUploading(false);
      return true;

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      
      if (error instanceof Error && error.name === 'AbortError') {
        setProgress({
          step: 'idle',
          progress: 0,
          detail: 'Upload cancelled',
        });
        setIsUploading(false);
        return false;
      }

      setProgress({
        step: 'error',
        progress: 0,
        detail: errorMessage,
        filename: file.name,
        error: errorMessage,
      });
      
      options.onError?.(errorMessage);
      setIsUploading(false);
      return false;
    }
  }, [options]);

  const cancel = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsUploading(false);
    reset();
  }, [reset]);

  return {
    uploadWithStreaming,
    isUploading,
    progress,
    reset,
    cancel,
  };
}

export default useStreamingUpload;
