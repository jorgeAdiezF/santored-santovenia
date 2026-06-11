import apiClient from './client';
import type {
  Destination,
  CreateDestinationRequest,
  AssignDestinationRequest,
  InvoiceLineDestination,
  PaginatedResponse,
} from '../types';

export const listDestinations = async (params?: {
  page?: number;
  size?: number;
  search?: string;
}): Promise<PaginatedResponse<Destination>> => {
  const response = await apiClient.get<PaginatedResponse<Destination>>('/api/destinations', { params });
  return response.data;
};

export const createDestination = async (data: CreateDestinationRequest): Promise<Destination> => {
  const response = await apiClient.post<Destination>('/api/destinations', data);
  return response.data;
};

export const updateDestination = async (
  id: number,
  data: Partial<CreateDestinationRequest>
): Promise<Destination> => {
  const response = await apiClient.put<Destination>(`/api/destinations/${id}`, data);
  return response.data;
};

export const deleteDestination = async (id: number): Promise<void> => {
  await apiClient.delete(`/api/destinations/${id}`);
};

export const assignDestination = async (
  _invoiceId: number,
  data: AssignDestinationRequest
): Promise<InvoiceLineDestination> => {
  const response = await apiClient.post<InvoiceLineDestination>(
    `/api/invoice-lines/${data.line_id}/destinations`,
    { destination_id: data.destination_id, quantity: data.quantity }
  );
  return response.data;
};
