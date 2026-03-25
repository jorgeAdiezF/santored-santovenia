import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  searchMaterials,
  getMaterial,
  createMaterial,
  updateMaterial,
  getMaterialAliases,
  addAlias,
  getFamilies,
  getProviders,
  getProvider,
  createProvider,
  updateProvider,
} from '../api/materials';
import type { ListParams, CreateMaterialRequest, AddAliasRequest, CreateProviderRequest } from '../types';

export const useMaterials = (params?: ListParams) => {
  return useQuery({
    queryKey: ['materials', params],
    queryFn: () => searchMaterials(params),
  });
};

export const useMaterial = (id: number) => {
  return useQuery({
    queryKey: ['material', id],
    queryFn: () => getMaterial(id),
    enabled: !!id,
  });
};

export const useCreateMaterial = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateMaterialRequest) => createMaterial(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materials'] });
    },
  });
};

export const useUpdateMaterial = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<CreateMaterialRequest> }) =>
      updateMaterial(id, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['materials'] });
      queryClient.invalidateQueries({ queryKey: ['material', variables.id] });
    },
  });
};

export const useMaterialAliases = (materialId: number) => {
  return useQuery({
    queryKey: ['material-aliases', materialId],
    queryFn: () => getMaterialAliases(materialId),
    enabled: !!materialId,
  });
};

export const useAddAlias = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ materialId, data }: { materialId: number; data: AddAliasRequest }) =>
      addAlias(materialId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['material-aliases', variables.materialId] });
      queryClient.invalidateQueries({ queryKey: ['material', variables.materialId] });
    },
  });
};

export const useFamilies = () => {
  return useQuery({
    queryKey: ['families'],
    queryFn: getFamilies,
  });
};

export const useProviders = (params?: ListParams) => {
  return useQuery({
    queryKey: ['providers', params],
    queryFn: () => getProviders(params),
  });
};

export const useProvider = (id: number) => {
  return useQuery({
    queryKey: ['provider', id],
    queryFn: () => getProvider(id),
    enabled: !!id,
  });
};

export const useCreateProvider = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateProviderRequest) => createProvider(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['providers'] });
    },
  });
};

export const useUpdateProvider = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<CreateProviderRequest> }) =>
      updateProvider(id, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['providers'] });
      queryClient.invalidateQueries({ queryKey: ['provider', variables.id] });
    },
  });
};
