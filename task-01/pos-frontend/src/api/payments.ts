import { api } from './client';
import type { PaymentOutcome, PaymentResult } from '../types';

export const processPayment = async (
  orderId: number,
  idempotencyKey: string,
  outcome: PaymentOutcome
): Promise<PaymentResult> => {
  const { data } = await api.post(
    `/orders/${orderId}/pay`,
    { simulate_outcome: outcome },
    {
      headers: {
        'Idempotency-Key': idempotencyKey,
      },
    }
  );
  return data;
};