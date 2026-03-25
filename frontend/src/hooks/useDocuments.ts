import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  listDocuments,
  getDocument,
  deleteDocument,
  getDocumentSegments,
  confirmSegment,
  triggerOcr,
  uploadDocuments,
} from '../api/documents';
import type { ListParams } from '../types';

export const useDocuments = (params?: ListParams) => {
  return useQuery({
    queryKey: ['documents', params],
    queryFn: () => listDocuments(params),
  });
};

export const useDocument = (id: number) => {
  return useQuery({
    queryKey: ['document', id],
    queryFn: () => getDocument(id),
    enabled: !!id,
  });
};

export const useDocumentSegments = (id: number) => {
  return useQuery({
    queryKey: ['document-segments', id],
    queryFn: () => getDocumentSegments(id),
    enabled: !!id,
  });
};

export const useDeleteDocument = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
};

export const useConfirmSegment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ documentId, segmentId }: { documentId: number; segmentId: number }) =>
      confirmSegment(documentId, segmentId),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['document', variables.documentId] });
      queryClient.invalidateQueries({ queryKey: ['document-segments', variables.documentId] });
    },
  });
};

export const useTriggerOcr = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: triggerOcr,
    onSuccess: (_data, documentId) => {
      queryClient.invalidateQueries({ queryKey: ['document', documentId] });
    },
  });
};

export const useUploadDocuments = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ files, onProgress }: { files: File[]; onProgress?: (progress: number) => void }) =>
      uploadDocuments(files, onProgress),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
};
