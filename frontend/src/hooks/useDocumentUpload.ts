import { useState, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { documentApi, handleApiError } from '../services/api';
import type { UploadProgress } from '../types/api';
import toast from 'react-hot-toast';

export const useDocumentUpload = () => {
  const [uploadProgress, setUploadProgress] = useState<Map<string, UploadProgress>>(new Map());
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: ({ file, metadata }: { 
      file: File; 
      metadata?: { patient_name?: string; document_type?: string; description?: string } 
    }) => {
      return documentApi.uploadDocument(file, metadata);
    },
    onSuccess: (data, { file }) => {
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

      // Start polling for document processing status
      startPollingForResult(data.document_id, file);
      
      toast.success(`Documento "${file.name}" subido exitosamente. Procesando OCR...`);
    },
    onError: (error, { file }) => {
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

  // Function to poll for document processing results
  const startPollingForResult = useCallback(async (documentId: string, file: File) => {
    const fileKey = `${file.name}-${file.size}`;
    let attempts = 0;
    const maxAttempts = 60; // Poll for up to 5 minutes (60 * 5 seconds)

    const pollInterval = setInterval(async () => {
      attempts++;
      
      try {
        const result = await documentApi.getDocument(documentId);
        
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

          // Invalidate documents query to refetch the list
          queryClient.invalidateQueries({ queryKey: ['documents'] });
          
          toast.success(`Procesamiento OCR de "${file.name}" completado exitosamente`);
          clearInterval(pollInterval);
          
        } else if (result.status === 'failed') {
          // Processing failed
          setUploadProgress(prev => {
            const newMap = new Map(prev);
            newMap.set(fileKey, {
              file,
              progress: 0,
              status: 'error',
              error: result.error_message || 'Error en el procesamiento OCR',
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
        console.error('Error polling document status:', error);
        
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

  const uploadFiles = useCallback(async (
    files: File[], 
    metadata?: { patient_name?: string; document_type?: string; description?: string }
  ) => {
    const validFiles = files.filter(file => {
      const validTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff'];
      const validExtensions = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif'];
      const hasValidType = validTypes.includes(file.type);
      const hasValidExtension = validExtensions.some(ext => 
        file.name.toLowerCase().endsWith(ext)
      );
      
      if (!hasValidType && !hasValidExtension) {
        toast.error(`Formato no válido para "${file.name}". Solo se permiten PDFs e imágenes (JPG, PNG, TIFF).`);
        return false;
      }
      
      if (file.size > 10 * 1024 * 1024) { // 10MB limit
        toast.error(`Archivo "${file.name}" demasiado grande. Máximo 10MB.`);
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

    // Upload files sequentially
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

        await uploadMutation.mutateAsync({ file, metadata });
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
