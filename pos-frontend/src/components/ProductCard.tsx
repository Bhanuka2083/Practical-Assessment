// src/components/ProductCard.tsx
import React, { useState } from "react";
import type { Product } from "../types";
import { ShoppingCart, AlertCircle, Plus, Minus } from "lucide-react";

interface Props {
  product: Product;
  onAddToCart: (id: number, quantity: number) => void;
  isLoading: boolean;
}

export const ProductCard: React.FC<Props> = ({
  product,
  onAddToCart,
  isLoading,
}) => {
  const [qty, setQty] = useState<number>(1);
  const isOutOfStock = product.available_stock <= 0;

  const handleIncrement = () => {
    if (qty < product.available_stock) {
      setQty((prev) => prev + 1);
    }
  };

  const handleDecrement = () => {
    if (qty > 1) {
      setQty((prev) => prev - 1);
    }
  };

  const handleAdd = () => {
    if (qty <= 0) return;
    onAddToCart(product.id, qty);
    setQty(1);
  };

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 flex flex-col justify-between hover:border-slate-600 transition-all shadow-md">
      <div>
        <div className="flex justify-between items-start mb-2">
          <h3 className="font-semibold text-lg text-white">{product.name}</h3>
          <span className="text-emerald-400 font-mono font-bold text-lg">
            ${Number(product.price).toFixed(2)}
          </span>
        </div>

        <div className="mt-3 flex items-center space-x-2 text-sm">
          <div
            className={`px-2.5 py-1 rounded-md text-xs font-semibold ${
              isOutOfStock
                ? "bg-rose-900/50 text-rose-300 border border-rose-700"
                : "bg-slate-700 text-slate-300"
            }`}
          >
            {isOutOfStock
              ? "Out of Stock"
              : `${product.available_stock} Available`}
          </div>
          {product.reserved_stock > 0 && (
            <span className="text-amber-400 text-xs flex items-center gap-1">
              <AlertCircle size={12} /> {product.reserved_stock} on hold
            </span>
          )}
        </div>
      </div>

      <div className="mt-6 space-y-3">
        {!isOutOfStock && (
          <div className="flex items-center justify-between bg-slate-900 border border-slate-700 rounded-lg p-1.5">
            <span className="text-xs text-slate-400 ml-2 font-medium">
              Quantity:
            </span>
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={handleDecrement}
                disabled={qty <= 1 || isLoading}
                className="w-7 h-7 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 flex items-center justify-center text-slate-300 transition-colors"
              >
                <Minus size={12} />
              </button>
              <span className="font-mono text-sm text-white w-6 text-center font-bold">
                {qty}
              </span>
              <button
                type="button"
                onClick={handleIncrement}
                disabled={qty >= product.available_stock || isLoading}
                className="w-7 h-7 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 flex items-center justify-center text-slate-300 transition-colors"
              >
                <Plus size={12} />
              </button>
            </div>
          </div>
        )}

        <button
          type="button"
          onClick={handleAdd}
          disabled={isOutOfStock || isLoading}
          className={`w-full py-2.5 px-4 rounded-lg flex items-center justify-center gap-2 font-medium transition-colors ${
            isOutOfStock
              ? "bg-slate-700 text-slate-500 cursor-not-allowed"
              : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/20"
          }`}
        >
          <ShoppingCart size={16} />
          {isOutOfStock
            ? "Unavailable"
            : `Add ${qty > 1 ? `${qty} items` : "to Cart"}`}
        </button>
      </div>
    </div>
  );
};
