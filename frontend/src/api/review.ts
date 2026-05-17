import apiClient from './client';
import type {
  Invoice,
  InvoiceLine,
  PaginatedResponse,
  UpdateInvoiceHeaderRequest,
  UpdateInvoiceLineRequest,
  HomologateLineRequest,
  ListParams,
} from '../types';

export const getPendingInvoices = async (params?: ListParams): Promise<PaginatedResponse<Invoice>> => {
  const response = await apiClient.get<PaginatedResponse<Invoice>>('/api/reviews/invoices/pending', { params });
  return response.data;
};

export const getInvoice = async (id: number): Promise<Invoice> => {
  const response = await apiClient.get<Invoice>(`/api/reviews/invoices/${id}`);
  return response.data;
};

export const updateInvoiceHeader = async (
  id: number,
  data: UpdateInvoiceHeaderRequest
): Promise<Invoice> => {
  const response = await apiClient.put<Invoice>(`/api/reviews/invoices/${id}`, data);
  return response.data;
};

export const updateInvoiceLine = async (
  invoiceId: number,
  lineId: number,
  data: UpdateInvoiceLineRequest
): Promise<InvoiceLine> => {
  const response = await apiClient.put<InvoiceLine>(
    `/api/reviews/invoices/${invoiceId}/lines/${lineId}`,
    data
  );
  return response.data;
};

export const finalizeInvoice = async (id: number): Promise<Invoice> => {
  const response = await apiClient.post<Invoice>(`/api/reviews/invoices/${id}/finalize`);
  return response.data;
};

export const rejectInvoice = async (id: number, reason: string): Promise<Invoice> => {
  const response = await apiClient.post<Invoice>(`/api/reviews/invoices/${id}/reject`, { reason });
  return response.data;
};

export const getPendingHomologation = async (params?: ListParams): Promise<InvoiceLine[]> => {
  const response = await apiClient.get<InvoiceLine[]>('/api/reviews/homologation/pending', {
    params,
  });
  return response.data;
};

export const homologateLine = async (
  _invoiceId: number,
  lineId: number,
  data: HomologateLineRequest
): Promise<InvoiceLine> => {
  const response = await apiClient.put<InvoiceLine>(
    `/api/reviews/lines/${lineId}/homologate`,
    data
  );
  return response.data;
};
