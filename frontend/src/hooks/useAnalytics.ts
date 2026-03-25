import { useQuery } from '@tanstack/react-query';
import {
  getLastPrice,
  getPriceHistory,
  getMaterialsStats,
  getProviderComparison,
  getDashboard,
  getSpendingByProvider,
  getSpendingByFamily,
} from '../api/analytics';

export const useDashboard = () => {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: getDashboard,
    staleTime: 2 * 60 * 1000,
  });
};

export const useLastPrice = (materialId: number, providerId?: number) => {
  return useQuery({
    queryKey: ['last-price', materialId, providerId],
    queryFn: () => getLastPrice(materialId, providerId),
    enabled: !!materialId,
  });
};

export const usePriceHistory = (
  materialId: number,
  params?: { provider_id?: number; date_from?: string; date_to?: string }
) => {
  return useQuery({
    queryKey: ['price-history', materialId, params],
    queryFn: () => getPriceHistory(materialId, params),
    enabled: !!materialId,
  });
};

export const useMaterialsStats = (params?: {
  date_from?: string;
  date_to?: string;
  family_id?: number;
  limit?: number;
}) => {
  return useQuery({
    queryKey: ['materials-stats', params],
    queryFn: () => getMaterialsStats(params),
  });
};

export const useProviderComparison = (
  materialId: number,
  params?: { date_from?: string; date_to?: string }
) => {
  return useQuery({
    queryKey: ['provider-comparison', materialId, params],
    queryFn: () => getProviderComparison(materialId, params),
    enabled: !!materialId,
  });
};

export const useSpendingByProvider = (params?: { date_from?: string; date_to?: string }) => {
  return useQuery({
    queryKey: ['spending-by-provider', params],
    queryFn: () => getSpendingByProvider(params),
  });
};

export const useSpendingByFamily = (params?: { date_from?: string; date_to?: string }) => {
  return useQuery({
    queryKey: ['spending-by-family', params],
    queryFn: () => getSpendingByFamily(params),
  });
};
