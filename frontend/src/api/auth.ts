import apiClient from './client';
import type { LoginRequest, LoginResponse, RefreshTokenResponse, User } from '../types';

export const login = async (credentials: LoginRequest): Promise<LoginResponse> => {
  const formData = new FormData();
  formData.append('username', credentials.username);
  formData.append('password', credentials.password);

  const response = await apiClient.post<LoginResponse>('/api/auth/login', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const getMe = async (): Promise<User> => {
  const response = await apiClient.get<User>('/api/auth/me');
  return response.data;
};

export const refreshToken = async (): Promise<RefreshTokenResponse> => {
  const response = await apiClient.post<RefreshTokenResponse>('/api/auth/refresh');
  return response.data;
};

export const createUser = async (data: {
  username: string;
  email: string;
  full_name: string;
  password: string;
  role: string;
}): Promise<User> => {
  const response = await apiClient.post<User>('/api/users', data);
  return response.data;
};

export const listUsers = async (): Promise<User[]> => {
  const response = await apiClient.get<User[]>('/api/users');
  return response.data;
};

export const updateUser = async (id: number, data: Partial<User>): Promise<User> => {
  const response = await apiClient.put<User>(`/api/users/${id}`, data);
  return response.data;
};

export const deleteUser = async (id: number): Promise<void> => {
  await apiClient.delete(`/api/users/${id}`);
};
