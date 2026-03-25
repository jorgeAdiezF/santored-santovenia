import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getPendingInvoices,
  getInvoice,
  updateInvoiceHeader,
  updateInvoiceLine,
  finalizeInvoice,
  rejectInvoice,
  getPendingHomologation,
  homologateLine,
} from '../api/review';
import type { ListParams, UpdateInvoiceHeaderRequest, UpdateInvoiceLineRequest, HomologateLineRequest } from '../types';

export const usePendingInvoices = (params?: ListParams) => {
  return useQuery({
    queryKey: ['pending-invoices', params],
    queryFn: () => getPendingInvoices(params),
  });
};

export const useInvoice = (id: number) => {
  return useQuery({
    queryKey: ['invoice', id],
    queryFn: () => getInvoice(id),
    enabled: !!id,
  });
};

export const useUpdateInvoiceHeader = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateInvoiceHeaderRequest }) =>
      updateInvoiceHeader(id, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['invoice', variables.id] });
    },
  });
};

export const useUpdateInvoiceLine = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      invoiceId,
      lineId,
      data,
    }: {
      invoiceId: number;
      lineId: number;
      data: UpdateInvoiceLineRequest;
    }) => updateInvoiceLine(invoiceId, lineId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['invoice', variables.invoiceId] });
    },
  });
};

export const useFinalizeInvoice = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: finalizeInvoice,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['invoice', data.id] });
      queryClient.invalidateQueries({ queryKey: ['pending-invoices'] });
    },
  });
};

export const useRejectInvoice = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) => rejectInvoice(id, reason),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['invoice', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['pending-invoices'] });
    },
  });
};

export const usePendingHomologation = (params?: ListParams) => {
  return useQuery({
    queryKey: ['pending-homologation', params],
    queryFn: () => getPendingHomologation(params),
  });
};

export const useHomologateLine = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      invoiceId,
      lineId,
      data,
    }: {
      invoiceId: number;
      lineId: number;
      data: HomologateLineRequest;
    }) => homologateLine(invoiceId, lineId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['invoice', variables.invoiceId] });
      queryClient.invalidateQueries({ queryKey: ['pending-homologation'] });
    },
  });
};
