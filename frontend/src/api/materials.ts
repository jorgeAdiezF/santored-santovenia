import apiClient from './client';
import type {
  MaterialMaster,
  MaterialAlias,
  MaterialFamily,
  Provider,
  CreateMaterialRequest,
  AddAliasRequest,
  CreateProviderRequest,
  PaginatedResponse,
  ListParams,
} from '../types';

export const searchMaterials = async (params?: ListParams): Promise<PaginatedResponse<MaterialMaster>> => {
  const response = await apiClient.get<PaginatedResponse<MaterialMaster>>('/api/materials', { params });
  return response.data;
};

export const getMaterial = async (id: number): Promise<MaterialMaster> => {
  const response = await apiClient.get<MaterialMaster>(`/api/materials/${id}`);
  return response.data;
};

export const createMaterial = async (data: CreateMaterialRequest): Promise<MaterialMaster> => {
  const response = await apiClient.post<MaterialMaster>('/api/materials', data);
  return response.data;
};

export const updateMaterial = async (
  id: number,
  data: Partial<CreateMaterialRequest>
): Promise<MaterialMaster> => {
  const response = await apiClient.put<MaterialMaster>(`/api/materials/${id}`, data);
  return response.data;
};

export const getMaterialAliases = async (materialId: number): Promise<MaterialAlias[]> => {
  const response = await apiClient.get<MaterialAlias[]>(`/api/materials/${materialId}/aliases`);
  return response.data;
};

export const addAlias = async (
  materialId: number,
  data: AddAliasRequest
): Promise<MaterialAlias> => {
  const response = await apiClient.post<MaterialAlias>(
    `/api/materials/${materialId}/aliases`,
    data
  );
  return response.data;
};

export const getFamilies = async (): Promise<MaterialFamily[]> => {
  const response = await apiClient.get<MaterialFamily[]>('/api/materials/families');
  return response.data;
};

export const getProviders = async (params?: ListParams): Promise<PaginatedResponse<Provider>> => {
  const response = await apiClient.get<PaginatedResponse<Provider>>('/api/providers', { params });
  return response.data;
};

export const getProvider = async (id: number): Promise<Provider> => {
  const response = await apiClient.get<Provider>(`/api/providers/${id}`);
  return response.data;
};

export const createProvider = async (data: CreateProviderRequest): Promise<Provider> => {
  const response = await apiClient.post<Provider>('/api/providers', data);
  return response.data;
};

export const updateProvider = async (
  id: number,
  data: Partial<CreateProviderRequest>
): Promise<Provider> => {
  const response = await apiClient.put<Provider>(`/api/providers/${id}`, data);
  return response.data;
};
