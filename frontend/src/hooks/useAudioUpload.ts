import { useState, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { audioApi, handleApiError } from '../services/api';
import type { UploadProgress } from '../types/api';
import toast from 'react-hot-toast';

export const useAudioUpload = () => {
  const [uploadProgress, setUploadProgress] = useState<Map<string, UploadProgress>>(new Map());
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: audioApi.uploadAudio,
    onSuccess: (data, file) => {
      // Update progress to completed
      setUploadProgress(prev => {
        const newMap = new Map(prev);
        const fileKey = `${file.name}-${file.size}`;
        newMap.set(fileKey, {
          file,
          progress: 100,
          status: 'completed',
          result: data,
        });
        return newMap;
      });

      // Invalidate transcriptions query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['transcriptions'] });
      
      toast.success(`Audio "${file.name}" procesado exitosamente`);
    },
    onError: (error, file) => {
      const errorMessage = handleApiError(error);
      
      // Update progress to error
      setUploadProgress(prev => {
        const newMap = new Map(prev);
        const fileKey = `${file.name}-${file.size}`;
        newMap.set(fileKey, {
          file,
          progress: 0,
          status: 'error',
          error: errorMessage,
        });
        return newMap;
      });

      toast.error(`Error procesando "${file.name}": ${errorMessage}`);
    },
  });

  const uploadFiles = useCallback(async (files: File[]) => {
    const validFiles = files.filter(file => {
      const validTypes = ['audio/wav', 'audio/mpeg', 'audio/mp3'];
      const validExtensions = ['.wav', '.mp3'];
      const hasValidType = validTypes.includes(file.type);
      const hasValidExtension = validExtensions.some(ext => 
        file.name.toLowerCase().endsWith(ext)
      );
      
      if (!hasValidType && !hasValidExtension) {
        toast.error(`Formato no válido para "${file.name}". Solo se permiten archivos WAV y MP3.`);
        return false;
      }
      
      if (file.size > 25 * 1024 * 1024) { // 25MB limit
        toast.error(`Archivo "${file.name}" demasiado grande. Máximo 25MB.`);
        return false;
      }
      
      return true;
    });

    if (validFiles.length === 0) {
      return;
    }

    // Initialize progress for all files
    setUploadProgress(prev => {
      const newMap = new Map(prev);
      validFiles.forEach(file => {
        const fileKey = `${file.name}-${file.size}`;
        newMap.set(fileKey, {
          file,
          progress: 0,
          status: 'uploading',
        });
      });
      return newMap;
    });

    // Upload files sequentially to avoid overwhelming the server
    for (const file of validFiles) {
      const fileKey = `${file.name}-${file.size}`;
      
      try {
        // Update progress to processing
        setUploadProgress(prev => {
          const newMap = new Map(prev);
          newMap.set(fileKey, {
            file,
            progress: 50,
            status: 'processing',
          });
          return newMap;
        });

        await uploadMutation.mutateAsync(file);
      } catch (error) {
        // Error handling is done in the mutation's onError
        console.error(`Upload failed for ${file.name}:`, error);
      }
    }
  }, [uploadMutation]);

  const removeUpload = useCallback((fileKey: string) => {
    setUploadProgress(prev => {
      const newMap = new Map(prev);
      newMap.delete(fileKey);
      return newMap;
    });
  }, []);

  const clearCompleted = useCallback(() => {
    setUploadProgress(prev => {
      const newMap = new Map();
      prev.forEach((progress, key) => {
        if (progress.status !== 'completed') {
          newMap.set(key, progress);
        }
      });
      return newMap;
    });
  }, []);

  const clearAll = useCallback(() => {
    setUploadProgress(new Map());
  }, []);

  return {
    uploadFiles,
    uploadProgress: Array.from(uploadProgress.entries()).map(([key, progress]) => ({
      key,
      ...progress,
    })),
    isUploading: uploadMutation.isPending,
    removeUpload,
    clearCompleted,
    clearAll,
  };
};
