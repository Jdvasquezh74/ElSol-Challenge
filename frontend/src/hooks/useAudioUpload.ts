import { useState, useCallback, useEffect } from 'react';
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
      // Update progress to processing (not completed yet)
      setUploadProgress(prev => {
        const newMap = new Map(prev);
        const fileKey = `${file.name}-${file.size}`;
        newMap.set(fileKey, {
          file,
          progress: 80,
          status: 'processing',
          result: data,
        });
        return newMap;
      });

      // Start polling for transcription status
      startPollingForResult(data.id, file);
      
      toast.success(`Audio "${file.name}" subido exitosamente. Procesando transcripción...`);
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

      toast.error(`Error subiendo "${file.name}": ${errorMessage}`);
    },
  });

  // Function to poll for transcription results
  const startPollingForResult = useCallback(async (transcriptionId: string, file: File) => {
    const fileKey = `${file.name}-${file.size}`;
    let attempts = 0;
    const maxAttempts = 60; // Poll for up to 5 minutes (60 * 5 seconds)

    const pollInterval = setInterval(async () => {
      attempts++;
      
      try {
        const result = await audioApi.getTranscription(transcriptionId);
        
        if (result.status === 'completed') {
          // Processing completed successfully
          setUploadProgress(prev => {
            const newMap = new Map(prev);
            newMap.set(fileKey, {
              file,
              progress: 100,
              status: 'completed',
              result: result,
            });
            return newMap;
          });

          // Invalidate transcriptions query to refetch the list
          queryClient.invalidateQueries({ queryKey: ['transcriptions'] });
          
          toast.success(`Transcripción de "${file.name}" completada exitosamente`);
          clearInterval(pollInterval);
          
        } else if (result.status === 'failed') {
          // Processing failed
          setUploadProgress(prev => {
            const newMap = new Map(prev);
            newMap.set(fileKey, {
              file,
              progress: 0,
              status: 'error',
              error: result.error_message || 'Error en el procesamiento',
            });
            return newMap;
          });

          toast.error(`Error procesando "${file.name}": ${result.error_message || 'Error desconocido'}`);
          clearInterval(pollInterval);
          
        } else if (attempts >= maxAttempts) {
          // Timeout
          setUploadProgress(prev => {
            const newMap = new Map(prev);
            newMap.set(fileKey, {
              file,
              progress: 80,
              status: 'error',
              error: 'Tiempo de espera agotado. El procesamiento puede continuar en segundo plano.',
            });
            return newMap;
          });

          toast.error(`Tiempo de espera agotado para "${file.name}"`);
          clearInterval(pollInterval);
        }
        // If status is still 'processing' or 'pending', continue polling
        
      } catch (error) {
        console.error('Error polling transcription status:', error);
        
        if (attempts >= maxAttempts) {
          setUploadProgress(prev => {
            const newMap = new Map(prev);
            newMap.set(fileKey, {
              file,
              progress: 80,
              status: 'error',
              error: 'Error verificando el estado del procesamiento',
            });
            return newMap;
          });

          clearInterval(pollInterval);
        }
      }
    }, 5000); // Poll every 5 seconds
  }, [queryClient]);

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
