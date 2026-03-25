import apiClient from './client';
import type {
  Invoice,
  InvoiceLine,
  UpdateInvoiceHeaderRequest,
  UpdateInvoiceLineRequest,
  HomologateLineRequest,
  PaginatedResponse,
  ListParams,
} from '../types';

export const getPendingInvoices = async (params?: ListParams): Promise<PaginatedResponse<Invoice>> => {
  const response = await apiClient.get<PaginatedResponse<Invoice>>('/api/invoices', {
    params: { ...params, status: params?.status || 'pending_review' },
  });
  return response.data;
};

export const getInvoice = async (id: number): Promise<Invoice> => {
  const response = await apiClient.get<Invoice>(`/api/invoices/${id}`);
  return response.data;
};

export const updateInvoiceHeader = async (
  id: number,
  data: UpdateInvoiceHeaderRequest
): Promise<Invoice> => {
  const response = await apiClient.put<Invoice>(`/api/invoices/${id}`, data);
  return response.data;
};

export const updateInvoiceLine = async (
  invoiceId: number,
  lineId: number,
  data: UpdateInvoiceLineRequest
): Promise<InvoiceLine> => {
  const response = await apiClient.put<InvoiceLine>(
    `/api/invoices/${invoiceId}/lines/${lineId}`,
    data
  );
  return response.data;
};

export const finalizeInvoice = async (id: number): Promise<Invoice> => {
  const response = await apiClient.post<Invoice>(`/api/invoices/${id}/approve`);
  return response.data;
};

export const rejectInvoice = async (id: number, reason: string): Promise<Invoice> => {
  const response = await apiClient.post<Invoice>(`/api/invoices/${id}/reject`, { reason });
  return response.data;
};

export const getPendingHomologation = async (
  params?: ListParams
): Promise<PaginatedResponse<InvoiceLine>> => {
  const response = await apiClient.get<PaginatedResponse<InvoiceLine>>(
    '/api/invoices/lines/pending-homologation',
    { params }
  );
  return response.data;
};

export const homologateLine = async (
  invoiceId: number,
  lineId: number,
  data: HomologateLineRequest
): Promise<InvoiceLine> => {
  const response = await apiClient.post<InvoiceLine>(
    `/api/invoices/${invoiceId}/lines/${lineId}/homologate`,
    data
  );
  return response.data;
};
