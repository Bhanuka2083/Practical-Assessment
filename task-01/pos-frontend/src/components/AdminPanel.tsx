import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getProducts,
  createProduct,
  updateProduct,
  deleteProduct,
} from "../api/products";
import type { Product } from "../types";
import { PlusCircle, Trash2, Edit3, Check, X, Layers } from "lucide-react";

interface Props {
  onClose: () => void;
}

interface EditFormState {
  id: number;
  name: string;
  price: number;
  total_stock: number;
}

export const AdminPanel: React.FC<Props> = ({ onClose }) => {
  const queryClient = useQueryClient();

  // Create form state
  const [name, setName] = useState("");
  const [price, setPrice] = useState("");
  const [totalStock, setTotalStock] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Unified inline row editing state
  const [editingRow, setEditingRow] = useState<EditFormState | null>(null);

  const { data: products = [], isLoading } = useQuery({
    queryKey: ["products"],
    queryFn: getProducts,
    refetchInterval: 3000,
  });

  const createMutation = useMutation({
    mutationFn: createProduct,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      setName("");
      setPrice("");
      setTotalStock("");
      setErrorMsg(null);
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail;
      setErrorMsg(
        typeof detail === "string" ? detail : "Failed to create product",
      );
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: number;
      payload: { name?: string; price?: number; total_stock?: number };
    }) => updateProduct(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.invalidateQueries({ queryKey: ["cart"] });
      setEditingRow(null);
      setErrorMsg(null);
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail;
      setErrorMsg(
        typeof detail === "string" ? detail : "Failed to update product",
      );
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteProduct,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.invalidateQueries({ queryKey: ["cart"] });
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail;
      setErrorMsg(
        typeof detail === "string" ? detail : "Failed to delete product",
      );
    },
  });

  const handleStartEdit = (prod: Product) => {
    setEditingRow({
      id: prod.id,
      name: prod.name,
      price: Number(prod.price),
      total_stock: prod.total_stock,
    });
  };

  const handleSaveEdit = (id: number) => {
    if (!editingRow) return;
    if (
      !editingRow.name.trim() ||
      editingRow.price <= 0 ||
      editingRow.total_stock < 0
    ) {
      setErrorMsg("Invalid name, price, or total stock value.");
      return;
    }

    updateMutation.mutate({
      id,
      payload: {
        name: editingRow.name.trim(),
        price: editingRow.price,
        total_stock: editingRow.total_stock,
      },
    });
  };

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const p = parseFloat(price);
    const s = parseInt(totalStock, 10);
    if (!name.trim() || isNaN(p) || isNaN(s) || s < 0 || p <= 0) {
      setErrorMsg(
        "Please enter valid product name, positive price, and stock count.",
      );
      return;
    }
    createMutation.mutate({ name: name.trim(), price: p, total_stock: s });
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 z-50 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700 w-full max-w-5xl rounded-2xl p-6 shadow-2xl space-y-6 my-8 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2">
            <Layers className="text-indigo-400" size={24} />
            <div>
              <h2 className="text-xl font-bold text-white">
                Inventory & Product Management
              </h2>
              <p className="text-xs text-slate-400">
                Update item names, pricing, and live warehouse inventory
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {errorMsg && (
          <div className="p-3 bg-rose-950/40 border border-rose-800 text-rose-300 text-xs rounded-xl">
            {errorMsg}
          </div>
        )}

        {/* Create Product Form */}
        <form
          onSubmit={handleCreateSubmit}
          className="bg-slate-800/60 border border-slate-700 p-4 rounded-xl"
        >
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-1.5">
            <PlusCircle size={16} className="text-emerald-400" /> Create New
            Inventory Item
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <input
              type="text"
              placeholder="Product Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              required
            />
            <input
              type="number"
              step="0.01"
              placeholder="Price ($)"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              required
            />
            <input
              type="number"
              placeholder="Initial Total Stock"
              value={totalStock}
              onChange={(e) => setTotalStock(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              required
            />
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 text-white text-sm font-semibold rounded-lg px-4 py-2 transition-colors flex items-center justify-center gap-1.5 shadow-md shadow-emerald-600/20"
            >
              {createMutation.isPending ? "Saving..." : "Add Product"}
            </button>
          </div>
        </form>

        {/* Product Stock Table */}
        <div className="flex-1 overflow-y-auto border border-slate-800 rounded-xl">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-800/80 text-xs uppercase font-semibold text-slate-400 sticky top-0 border-b border-slate-700">
              <tr>
                <th className="py-3 px-4">ID</th>
                <th className="py-3 px-4">Name</th>
                <th className="py-3 px-4">Price ($)</th>
                <th className="py-3 px-4 text-center">Total Stock</th>
                <th className="py-3 px-4 text-center">Reserved</th>
                <th className="py-3 px-4 text-center">Available</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 bg-slate-900/40">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="text-center py-6 text-slate-500">
                    Loading catalog...
                  </td>
                </tr>
              ) : products.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-6 text-slate-500">
                    No inventory found.
                  </td>
                </tr>
              ) : (
                products.map((prod) => {
                  const isEditing = editingRow?.id === prod.id;

                  return (
                    <tr
                      key={prod.id}
                      className="hover:bg-slate-800/30 transition-colors"
                    >
                      <td className="py-3 px-4 font-mono text-xs text-slate-500">
                        #{prod.id}
                      </td>

                      {/* Name Column */}
                      <td className="py-3 px-4">
                        {isEditing ? (
                          <input
                            type="text"
                            value={editingRow.name}
                            onChange={(e) =>
                              setEditingRow({
                                ...editingRow,
                                name: e.target.value,
                              })
                            }
                            className="bg-slate-800 border border-indigo-500 rounded px-2 py-1 text-white text-sm w-full max-w-45"
                          />
                        ) : (
                          <span className="font-medium text-white">
                            {prod.name}
                          </span>
                        )}
                      </td>

                      {/* Price Column */}
                      <td className="py-3 px-4">
                        {isEditing ? (
                          <input
                            type="number"
                            step="0.01"
                            value={editingRow.price}
                            onChange={(e) =>
                              setEditingRow({
                                ...editingRow,
                                price: parseFloat(e.target.value) || 0,
                              })
                            }
                            className="w-24 bg-slate-800 border border-indigo-500 rounded px-2 py-1 text-white text-sm font-mono"
                          />
                        ) : (
                          <span className="font-mono text-emerald-400 font-semibold">
                            ${Number(prod.price).toFixed(2)}
                          </span>
                        )}
                      </td>

                      {/* Total Stock Column */}
                      <td className="py-3 px-4 text-center font-mono">
                        {isEditing ? (
                          <input
                            type="number"
                            value={editingRow.total_stock}
                            onChange={(e) =>
                              setEditingRow({
                                ...editingRow,
                                total_stock: parseInt(e.target.value, 10) || 0,
                              })
                            }
                            className="w-20 bg-slate-800 border border-indigo-500 rounded px-2 py-1 text-center text-white text-sm font-mono"
                          />
                        ) : (
                          <span className="text-white font-bold">
                            {prod.total_stock}
                          </span>
                        )}
                      </td>

                      {/* Reserved Stock */}
                      <td className="py-3 px-4 text-center font-mono">
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-bold ${
                            prod.reserved_stock > 0
                              ? "bg-amber-950/60 text-amber-300 border border-amber-800/60"
                              : "text-slate-500"
                          }`}
                        >
                          {prod.reserved_stock}
                        </span>
                      </td>

                      {/* Available Stock */}
                      <td className="py-3 px-4 text-center font-mono">
                        <span
                          className={`px-2.5 py-1 rounded text-xs font-bold ${
                            prod.available_stock <= 0
                              ? "bg-rose-950/60 text-rose-300 border border-rose-800/60"
                              : "bg-emerald-950/60 text-emerald-300 border border-emerald-800/60"
                          }`}
                        >
                          {prod.available_stock}
                        </span>
                      </td>

                      {/* Actions */}
                      <td className="py-3 px-4 text-right">
                        {isEditing ? (
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              onClick={() => handleSaveEdit(prod.id)}
                              disabled={updateMutation.isPending}
                              className="text-emerald-400 hover:text-emerald-300 p-1.5 hover:bg-emerald-950/40 rounded transition-colors"
                              title="Save changes"
                            >
                              <Check size={16} />
                            </button>
                            <button
                              onClick={() => setEditingRow(null)}
                              className="text-slate-400 hover:text-slate-300 p-1.5 hover:bg-slate-800 rounded transition-colors"
                              title="Cancel"
                            >
                              <X size={16} />
                            </button>
                          </div>
                        ) : (
                          <div className="flex items-center justify-end gap-1">
                            <button
                              onClick={() => handleStartEdit(prod)}
                              className="text-slate-400 hover:text-indigo-400 p-1.5 hover:bg-slate-800 rounded-lg transition-colors"
                              title="Edit product"
                            >
                              <Edit3 size={15} />
                            </button>
                            <button
                              onClick={() => {
                                if (
                                  confirm(
                                    `Are you sure you want to delete "${prod.name}"?`,
                                  )
                                ) {
                                  deleteMutation.mutate(prod.id);
                                }
                              }}
                              disabled={deleteMutation.isPending}
                              className="text-rose-400 hover:text-rose-300 p-1.5 hover:bg-rose-950/30 rounded-lg transition-colors"
                              title="Delete product"
                            >
                              <Trash2 size={15} />
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center text-xs text-slate-400 pt-2 border-t border-slate-800">
          <span>Live catalog sync active</span>
          <button
            onClick={onClose}
            className="bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold px-4 py-2 rounded-xl transition-colors"
          >
            Close Dashboard
          </button>
        </div>
      </div>
    </div>
  );
};
