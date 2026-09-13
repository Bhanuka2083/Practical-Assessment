import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getProducts } from "./api/products";
import { getCart, addToCart, removeFromCart } from "./api/cart";
import { checkoutCart } from "./api/orders";
import { ProductCard } from "./components/ProductCard";
import { CheckoutModal } from "./components/CheckoutModal";
import { AuthModal } from "./components/AuthModal";
import type { Order } from "./types";

import {
  ShoppingBag,
  ArrowRight,
  RefreshCw,
  LogIn,
  LogOut,
  User,
} from "lucide-react";

export default function App() {
  const queryClient = useQueryClient();
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem("token"),
  );
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [activeOrder, setActiveOrder] = useState<Order | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);

  // 1. Fetch Real-time Catalog
  const { data: products = [], isLoading: productsLoading } = useQuery({
    queryKey: ["products"],
    queryFn: getProducts,
    refetchInterval: 5000,
  });

  // 2. Fetch User Cart (Only runs when authenticated)
  const { data: cart } = useQuery({
    queryKey: ["cart"],
    queryFn: getCart,
    enabled: !!token,
    retry: false,
  });

  const handleLogout = () => {
    localStorage.removeItem("token");
    setToken(null);
    queryClient.removeQueries({ queryKey: ["cart"] });
  };

  // 3. Add to Cart Mutation
  // const addMutation = useMutation({
  //   mutationFn: (productId: number) => addToCart(productId, 1),
  //   onSuccess: () => {
  //     queryClient.invalidateQueries({ queryKey: ["cart"] });
  //     queryClient.invalidateQueries({ queryKey: ["products"] });
  //   },
  //   onError: (err: any) => {
  //     setAuthError(err.response?.data?.detail || "Failed to add item to cart");
  //   },
  // });

  // const handleAddToCart = (productId: number) => {
  //   if (!token) {
  //     setIsAuthOpen(true);
  //     return;
  //   }
  //   addMutation.mutate(productId);
  // };

  // Inside src/App.tsx

  // Update the mutation to accept arbitrary delta quantities
  const addMutation = useMutation({
    mutationFn: ({
      productId,
      quantity,
    }: {
      productId: number;
      quantity: number;
    }) => addToCart(productId, quantity),
    onSuccess: () => {
      setAuthError(null);
      queryClient.invalidateQueries({ queryKey: ["cart"] });
      queryClient.invalidateQueries({ queryKey: ["products"] });
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail;
      // Handle Pydantic 422 array of objects vs standard string errors
      if (Array.isArray(detail)) {
        setAuthError(detail.map((e: any) => e.msg).join(", "));
      } else if (typeof detail === "object" && detail !== null) {
        setAuthError(JSON.stringify(detail));
      } else {
        setAuthError(detail || "Failed to update item quantity");
      }
    },
  });

  // Inside src/App.tsx, add removeMutation:
  const removeMutation = useMutation({
    mutationFn: (productId: number) => removeFromCart(productId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cart"] });
      queryClient.invalidateQueries({ queryKey: ["products"] });
    },
  });

  const handleDecrementItem = (productId: number, currentQty: number) => {
    if (currentQty <= 1) {
      removeMutation.mutate(productId);
    } else {
      addMutation.mutate({ productId, quantity: -1 });
    }
  };

  const handleAddToCart = (productId: number, quantity: number) => {
    if (!token) {
      setIsAuthOpen(true);
      return;
    }
    addMutation.mutate({ productId, quantity });
  };

  // 4. Checkout Reservation Mutation
  const checkoutMutation = useMutation({
    mutationFn: checkoutCart,
    onSuccess: (order: Order) => {
      setActiveOrder(order);
      queryClient.invalidateQueries({ queryKey: ["cart"] });
      queryClient.invalidateQueries({ queryKey: ["products"] });
    },
    onError: (err: any) => {
      setAuthError(
        err.response?.data?.detail ||
          "Checkout failed due to a stock conflict.",
      );
      queryClient.invalidateQueries({ queryKey: ["products"] });
    },
  });

  const cartTotal =
    cart?.items?.reduce(
      (acc, item) => acc + Number(item.product.price) * item.quantity,
      0,
    ) || 0;

  return (
    <div className="min-h-screen pb-16">
      {/* Header / Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShoppingBag className="text-indigo-500" />
            <span className="font-bold text-lg text-white">POS Terminal</span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() =>
                queryClient.invalidateQueries({ queryKey: ["products"] })
              }
              className="text-xs bg-slate-800 hover:bg-slate-700 px-3 py-2 rounded-lg border border-slate-700 flex items-center gap-1.5 transition-colors text-slate-300"
            >
              <RefreshCw size={14} /> Refresh Catalog
            </button>

            {token ? (
              <div className="flex items-center gap-2">
                <span className="text-xs bg-slate-800 border border-slate-700 px-3 py-2 rounded-lg text-slate-300 flex items-center gap-1.5">
                  <User size={14} className="text-emerald-400" /> Authenticated
                </span>
                <button
                  onClick={handleLogout}
                  className="text-xs bg-rose-950/40 hover:bg-rose-900/50 border border-rose-800 text-rose-300 px-3 py-2 rounded-lg flex items-center gap-1.5 transition-colors"
                >
                  <LogOut size={14} /> Logout
                </button>
              </div>
            ) : (
              <button
                onClick={() => setIsAuthOpen(true)}
                className="text-xs bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-3.5 py-2 rounded-lg flex items-center gap-1.5 shadow-md shadow-indigo-600/20 transition-colors"
              >
                <LogIn size={14} /> Sign In
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 mt-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Products Catalog */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-xl font-bold text-white">Available Products</h2>

          {authError && (
            <div className="p-3 bg-rose-950/40 border border-rose-800 text-rose-300 text-sm rounded-xl">
              {authError}
            </div>
          )}

          {productsLoading ? (
            <div className="text-slate-400">Loading catalog...</div>
          ) : products.length === 0 ? (
            <div className="text-slate-400 p-8 text-center bg-slate-800/50 rounded-2xl border border-slate-700">
              Catalog is empty. Seed products in the backend database.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {products.map((product) => (
                <ProductCard
                  key={product.id}
                  product={product}
                  onAddToCart={(productId, quantity) =>
                    handleAddToCart(productId, quantity)
                  }
                  isLoading={addMutation.isPending}
                />
              ))}
            </div>
          )}
        </div>

        {/* Intent Cart Sidebar */}
        {/* Intent Cart Sidebar */}
        <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-6 h-fit sticky top-24">
          <h3 className="font-bold text-lg text-white mb-4">
            Current Cart (Intent)
          </h3>

          {!token ? (
            <div className="text-center py-8">
              <p className="text-slate-400 text-sm mb-4">
                Please sign in to view your cart and reserve items.
              </p>
              <button
                onClick={() => setIsAuthOpen(true)}
                className="w-full py-2.5 bg-slate-700 hover:bg-slate-600 text-white rounded-xl text-sm font-semibold transition-colors"
              >
                Sign In
              </button>
            </div>
          ) : !cart?.items?.length ? (
            <p className="text-slate-400 text-sm py-8 text-center">
              Cart is empty.
            </p>
          ) : (
            <div className="space-y-4">
              <div className="divide-y divide-slate-700 max-h-80 overflow-y-auto pr-1">
                {cart.items.map((item) => (
                  <div
                    key={item.id}
                    className="py-3 flex justify-between items-center text-sm"
                  >
                    <div className="space-y-1">
                      <p className="font-medium text-white">
                        {item.product.name}
                      </p>

                      {/* Stepper controls with safe decrement & delete */}
                      <div className="flex items-center space-x-2">
                        <button
                          type="button"
                          onClick={() =>
                            handleDecrementItem(item.product_id, item.quantity)
                          }
                          disabled={
                            addMutation.isPending || removeMutation.isPending
                          }
                          className="w-6 h-6 rounded bg-slate-700 hover:bg-slate-600 disabled:opacity-40 flex items-center justify-center text-xs text-slate-200 transition-colors"
                        >
                          -
                        </button>
                        <span className="font-mono text-slate-300 text-xs px-1 font-bold">
                          {item.quantity}
                        </span>
                        <button
                          type="button"
                          onClick={() =>
                            addMutation.mutate({
                              productId: item.product_id,
                              quantity: 1,
                            })
                          }
                          disabled={
                            addMutation.isPending ||
                            item.quantity >= item.product.available_stock
                          }
                          className="w-6 h-6 rounded bg-slate-700 hover:bg-slate-600 disabled:opacity-40 flex items-center justify-center text-xs text-slate-200 transition-colors"
                        >
                          +
                        </button>
                      </div>
                    </div>

                    <span className="font-mono text-slate-200 font-semibold">
                      ${(Number(item.product.price) * item.quantity).toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>

              <div className="pt-4 border-t border-slate-700 flex justify-between items-center">
                <span className="text-slate-300 font-medium">Subtotal</span>
                <span className="text-xl font-bold font-mono text-emerald-400">
                  ${cartTotal.toFixed(2)}
                </span>
              </div>

              <button
                onClick={() => checkoutMutation.mutate()}
                disabled={checkoutMutation.isPending}
                className="w-full mt-4 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 text-white rounded-xl font-semibold flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 transition-all"
              >
                {checkoutMutation.isPending ? "Reserving..." : "Proceed to Pay"}
                <ArrowRight size={16} />
              </button>
            </div>
          )}
        </div>
      </main>

      {/* Auth Modal */}
      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onAuthSuccess={() => setToken(localStorage.getItem("token"))}
      />

      {/* Checkout Modal */}
      {activeOrder && (
        <CheckoutModal
          order={activeOrder}
          onClose={() => setActiveOrder(null)}
        />
      )}
    </div>
  );
}
