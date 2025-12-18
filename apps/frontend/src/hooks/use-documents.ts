'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { DocumentFile } from '@/components/documents/file-preview';
import type { UploadProgress } from '@/components/documents/upload-progress';

// Mock API functions (replace with actual API calls)
const documentsApi = {
  getAll: async (): Promise<DocumentFile[]> => {
    // TODO: Replace with actual API call
    return [];
  },
  
  upload: async (file: File, onProgress?: (progress: number) => void): Promise<DocumentFile> => {
    // TODO: Replace with actual API call with progress tracking
    return {
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      size: file.size,
      type: file.type,
      uploadedAt: new Date().toISOString(),
    };
  },
  
  download: async (id: string): Promise<Blob> => {
    // TODO: Replace with actual API call
    throw new Error('Not implemented');
  },
  
  delete: async (id: string): Promise<void> => {
    // TODO: Replace with actual API call
  },
};

export function useDocuments() {
  const queryClient = useQueryClient();
  const [uploadProgress, setUploadProgress] = useState<UploadProgress[]>([]);

  const query = useQuery({
    queryKey: ['documents'],
    queryFn: documentsApi.getAll,
  });

  const uploadMutation = useMutation({
    mutationFn: async (files: File[]) => {
      const uploads: UploadProgress[] = files.map((file) => ({
        fileName: file.name,
        progress: 0,
        status: 'uploading' as const,
      }));
      setUploadProgress(uploads);

      const results = await Promise.all(
        files.map(async (file, index) => {
          try {
            const result = await documentsApi.upload(file, (progress) => {
              setUploadProgress((prev) =>
                prev.map((item, i) =>
                  i === index ? { ...item, progress } : item
                )
              );
            });

            setUploadProgress((prev) =>
              prev.map((item, i) =>
                i === index
                  ? { ...item, progress: 100, status: 'success' as const }
                  : item
              )
            );

            return result;
          } catch (error) {
            setUploadProgress((prev) =>
              prev.map((item, i) =>
                i === index
                  ? {
                      ...item,
                      status: 'error' as const,
                      error: error instanceof Error ? error.message : 'Upload failed',
                    }
                  : item
              )
            );
            throw error;
          }
        })
      );

      // Clear progress after 3 seconds
      setTimeout(() => setUploadProgress([]), 3000);

      return results;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: documentsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  const downloadDocument = async (id: string) => {
    try {
      const blob = await documentsApi.download(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'document'; // You might want to get the actual filename
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  return {
    documents: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error,
    uploadDocuments: uploadMutation.mutate,
    deleteDocument: deleteMutation.mutate,
    downloadDocument,
    uploadProgress,
    isUploading: uploadMutation.isPending,
  };
}

