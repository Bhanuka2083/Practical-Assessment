// src/api/auth.ts
import { api } from './client';
import type { LoginResponse } from '../types';

export const login = async (username: string, password: string): Promise<LoginResponse> => {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('password', password);
  const { data } = await api.post<LoginResponse>('/auth/login', formData);
  return data;
};

export const register = async (email: string, password: string): Promise<void> => {
  await api.post('/auth/register', { email, password });
};