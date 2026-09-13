export interface User {
  id: number;
  email: string;
  created_at: string;
}

export interface Product {
  id: number;
  name: string;
  price: string | number;
  total_stock: number;
  reserved_stock: number;
  available_stock: number;
}

export interface CartItem {
  id: number;
  product_id: number;
  quantity: number;
  product: Product;
}

export interface Cart {
  id: number;
  user_id: number;
  status: 'ACTIVE' | 'CONVERTED';
  items: CartItem[];
}

export type OrderStatus = 'PENDING' | 'RESERVED' | 'PAID' | 'CANCELLED' | 'EXPIRED' | 'FAILED';

export interface OrderItem {
  id: number;
  product_id: number;
  quantity: number;
  unit_price: string | number;
}

export interface Order {
  id: number;
  user_id: number;
  status: OrderStatus;
  total_amount: string | number;
  expires_at: string | null;
  items: OrderItem[];
  created_at: string;
  updated_at: string;
}

export type PaymentOutcome = 'SUCCESS' | 'FAILURE' | 'TIMEOUT';

export interface PaymentResult {
  payment: {
    id: number;
    order_id: number;
    idempotency_key: string;
    amount: string | number;
    status: 'INITIATED' | 'SUCCESS' | 'FAILED' | 'TIMEOUT';
    gateway_reference?: string;
    created_at: string;
  };
  order_status: OrderStatus;
  message: string;
}