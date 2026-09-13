import { api } from './client';

export const login = async (username: string, password: string): Promise<string> => {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('password', password);
  const { data } = await api.post('/auth/login', formData);
  return data.access_token;
};

export const register = async (email: string, password: string): Promise<void> => {
  await api.post('/auth/register', { email, password });
};