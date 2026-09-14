import { api } from './client';
import type { Cart } from '../types';

export const getCart = async (): Promise<Cart> => {
  const { data } = await api.get('/cart');
  return data;
};

export const addToCart = async (productId: number, quantity: number = 1): Promise<Cart> => {
  const { data } = await api.post('/cart/items', { product_id: productId, quantity });
  return data;
};

export const removeFromCart = async (productId: number): Promise<void> => {
  await api.delete(`/cart/items/${productId}`);
};