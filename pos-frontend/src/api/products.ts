import { api } from './client';
import type { Product } from '../types/index.ts';

export const getProducts = async (): Promise<Product[]> => {
  const { data } = await api.get('/products');
  return data;
};

export const createProduct = async (payload: {
  name: string;
  price: number;
  total_stock: number;
}): Promise<Product> => {
  const { data } = await api.post('/products', payload);
  return data;
};

export const updateProduct = async (
  id: number,
  payload: { name?: string; price?: number; total_stock?: number }
): Promise<Product> => {
  const { data } = await api.patch(`/products/${id}`, payload);
  return data;
};

export const deleteProduct = async (id: number): Promise<void> => {
  await api.delete(`/products/${id}`);
};