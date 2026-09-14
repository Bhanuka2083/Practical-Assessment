import React, { useState } from "react";
import { login, register } from "../api/auth";
import { Lock, Mail, X, LogIn, UserPlus } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onAuthSuccess: () => void;
}

export const AuthModal: React.FC<Props> = ({
  isOpen,
  onClose,
  onAuthSuccess,
}) => {
  const queryClient = useQueryClient();
  const [isLoginView, setIsLoginView] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isLoginView) {
        const data = await login(email, password);
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("role", data.role);
        localStorage.setItem("email", data.email);
        queryClient.invalidateQueries({ queryKey: ["cart"] });
        queryClient.invalidateQueries({ queryKey: ["products"] });
        onAuthSuccess();
        onClose();
      } else {
        // Registration Flow: Register then automatically login
        await register(email, password);
        const data = await login(email, password);
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("role", data.role);
        localStorage.setItem("email", data.email);
        queryClient.invalidateQueries({ queryKey: ["cart"] });
        queryClient.invalidateQueries({ queryKey: ["products"] });
        onAuthSuccess();
        onClose();
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : "Authentication failed. Please check credentials.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-slate-800 border border-slate-700 w-full max-w-md rounded-2xl p-6 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors"
        >
          <X size={20} />
        </button>

        <div className="text-center mb-6">
          <div className="w-12 h-12 bg-indigo-600/20 border border-indigo-500/30 rounded-xl mx-auto flex items-center justify-center text-indigo-400 mb-3">
            {isLoginView ? <LogIn size={24} /> : <UserPlus size={24} />}
          </div>
          <h2 className="text-xl font-bold text-white">
            {isLoginView ? "Sign in to Terminal" : "Create an Account"}
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            {isLoginView
              ? "Authenticate to manage cart and place orders"
              : "Register to start reserving inventory"}
          </p>
        </div>

        {error && (
          <div className="p-3 mb-4 bg-rose-950/40 border border-rose-800 text-rose-300 text-xs rounded-xl">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Email Address
            </label>
            <div className="relative">
              <Mail
                className="absolute left-3.5 top-3 text-slate-500"
                size={16}
              />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="user@example.com"
                className="w-full bg-slate-900 border border-slate-700 rounded-xl py-2.5 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-indigo-500 transition-colors"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Password
            </label>
            <div className="relative">
              <Lock
                className="absolute left-3.5 top-3 text-slate-500"
                size={16}
              />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-900 border border-slate-700 rounded-xl py-2.5 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-indigo-500 transition-colors"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 text-white rounded-xl font-semibold text-sm transition-all shadow-lg shadow-indigo-600/20 mt-2"
          >
            {loading
              ? "Processing..."
              : isLoginView
                ? "Sign In"
                : "Create Account"}
          </button>
        </form>

        <div className="mt-5 text-center text-xs text-slate-400">
          {isLoginView ? (
            <p>
              Don't have an account?{" "}
              <button
                type="button"
                onClick={() => {
                  setIsLoginView(false);
                  setError(null);
                }}
                className="text-indigo-400 hover:text-indigo-300 font-semibold ml-1"
              >
                Sign up
              </button>
            </p>
          ) : (
            <p>
              Already have an account?{" "}
              <button
                type="button"
                onClick={() => {
                  setIsLoginView(true);
                  setError(null);
                }}
                className="text-indigo-400 hover:text-indigo-300 font-semibold ml-1"
              >
                Log in
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
