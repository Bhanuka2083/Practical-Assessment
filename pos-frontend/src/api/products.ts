import { api } from './client';
import type { Product } from '../types/index.ts';

export const getProducts = async (): Promise<Product[]> => {
  const { data } = await api.get('/products');
  return data;
};