import apiClient from './client';
import type { Document, DocumentListItem, DetectedDoc, PaginatedResponse, ListParams } from '../types';

export const uploadDocuments = async (
  files: File[],
  onProgress?: (progress: number) => void
): Promise<Document[]> => {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });

  const response = await apiClient.post<Document[]>('/api/documents/upload', formData, {
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(progress);
      }
    },
  });
  return response.data;
};

export const listDocuments = async (params?: ListParams): Promise<PaginatedResponse<DocumentListItem>> => {
  const response = await apiClient.get<PaginatedResponse<DocumentListItem>>('/api/documents', { params });
  return response.data;
};

export const getDocument = async (id: number): Promise<Document> => {
  const response = await apiClient.get<Document>(`/api/documents/${id}`);
  return response.data;
};

export const deleteDocument = async (id: number): Promise<void> => {
  await apiClient.delete(`/api/documents/${id}`);
};

export const getDocumentSegments = async (id: number): Promise<DetectedDoc[]> => {
  const response = await apiClient.get<DetectedDoc[]>(`/api/documents/${id}/segments`);
  return response.data;
};

export const confirmSegment = async (documentId: number, segmentId: number): Promise<DetectedDoc> => {
  const response = await apiClient.post<DetectedDoc>(
    `/api/documents/${documentId}/segments/${segmentId}/confirm`
  );
  return response.data;
};

export const triggerOcr = async (documentId: number): Promise<{ message: string }> => {
  const response = await apiClient.post<{ message: string }>(`/api/documents/${documentId}/ocr`);
  return response.data;
};
