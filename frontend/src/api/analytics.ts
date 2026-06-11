import apiClient from './client';
import type {
  LastPriceResponse,
  PriceHistoryPoint,
  MaterialStats,
  ProviderComparison,
  DashboardStats,
  ProviderSpend,
  SpendingByFamily,
} from '../types';

export const getLastPrice = async (
  materialId: number,
  providerId?: number
): Promise<LastPriceResponse> => {
  const response = await apiClient.get<LastPriceResponse>(`/api/analytics/last-price/${materialId}`, {
    params: providerId ? { provider_id: providerId } : {},
  });
  return response.data;
};

export const getPriceHistory = async (
  materialId: number,
  params?: { provider_id?: number; date_from?: string; date_to?: string }
): Promise<PriceHistoryPoint[]> => {
  const response = await apiClient.get<PriceHistoryPoint[]>(
    `/api/analytics/price-history/${materialId}`,
    { params }
  );
  return response.data;
};

export const getMaterialsStats = async (params?: {
  date_from?: string;
  date_to?: string;
  family_id?: number;
  limit?: number;
}): Promise<MaterialStats[]> => {
  const response = await apiClient.get<MaterialStats[]>('/api/analytics/materials-stats', { params });
  return response.data;
};

export const getProviderComparison = async (
  materialId: number,
  params?: { date_from?: string; date_to?: string }
): Promise<ProviderComparison[]> => {
  const response = await apiClient.get<ProviderComparison[]>(
    `/api/analytics/provider-comparison/${materialId}`,
    { params }
  );
  return response.data;
};

export const getDashboard = async (): Promise<DashboardStats> => {
  const response = await apiClient.get<DashboardStats>('/api/analytics/dashboard');
  return response.data;
};

export const getSpendingByProvider = async (params?: {
  date_from?: string;
  date_to?: string;
}): Promise<ProviderSpend[]> => {
  const response = await apiClient.get<ProviderSpend[]>('/api/analytics/spending-by-provider', {
    params,
  });
  return response.data;
};

export const getSpendingByFamily = async (params?: {
  date_from?: string;
  date_to?: string;
}): Promise<SpendingByFamily[]> => {
  const response = await apiClient.get<SpendingByFamily[]>('/api/analytics/spending-by-family', {
    params,
  });
  return response.data;
};
