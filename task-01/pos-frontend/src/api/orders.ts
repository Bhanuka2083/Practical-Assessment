import { api } from './client';
import type { Order } from '../types';

export const checkoutCart = async (): Promise<Order> => {
  const { data } = await api.post('/orders/checkout');
  return data;
};

export const cancelOrder = async (orderId: number): Promise<void> => {
  await api.post(`/orders/${orderId}/cancel`);
};

export const getOrder = async (orderId: number): Promise<Order> => {
  const { data } = await api.get(`/orders/${orderId}`);
  return data;
};