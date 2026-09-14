import React, { useState, useEffect } from "react";
import type { Order, PaymentOutcome, PaymentResult } from "../types";
import { processPayment } from "../api/payments";
import { cancelOrder } from "../api/orders";
import { v4 as uuidv4 } from "uuid";
import {
  Timer,
  CheckCircle,
  XCircle,
  AlertTriangle,
  ShieldCheck,
} from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

interface Props {
  order: Order;
  onClose: () => void;
}

export const CheckoutModal: React.FC<Props> = ({ order, onClose }) => {
  const queryClient = useQueryClient();
  const [timeLeft, setTimeLeft] = useState<number>(0);
  const [idempotencyKey] = useState<string>(() => uuidv4());
  const [outcome, setOutcome] = useState<PaymentOutcome>("SUCCESS");
  const [paymentResult, setPaymentResult] = useState<PaymentResult | null>(
    null,
  );
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Synchronized Expiry Countdown
  useEffect(() => {
    if (!order.expires_at) return;

    const targetTime = new Date(order.expires_at).getTime();

    const interval = setInterval(() => {
      const now = new Date().getTime();
      const remaining = Math.max(0, Math.floor((targetTime - now) / 1000));
      setTimeLeft(remaining);

      if (remaining <= 0) {
        clearInterval(interval);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [order.expires_at]);

  const handlePay = async () => {
    setIsProcessing(true);
    setErrorMessage(null);
    try {
      const res = await processPayment(order.id, idempotencyKey, outcome);
      setPaymentResult(res);
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.invalidateQueries({ queryKey: ["cart"] });
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || "Payment request failed.");
      queryClient.invalidateQueries({ queryKey: ["products"] });
    } finally {
      setIsProcessing(false);
    }
  };

  const [isCancelling, setIsCancelling] = useState(false);

  const handleCancel = async () => {
    if (isCancelling) return;
    setIsCancelling(true);
    setErrorMessage(null);

    try {
      await cancelOrder(order.id);
    } catch (err: any) {
      // If the order was already expired or cancelled, we still want to dismiss the modal
      console.warn(
        "Cancellation error (likely already expired):",
        err.response?.data?.detail,
      );
    } finally {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.invalidateQueries({ queryKey: ["cart"] });
      setIsCancelling(false);
      onClose(); // Always dismiss modal so it cannot loop
    }
  };

  const minutes = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;
  const isExpired = timeLeft <= 0 && !paymentResult;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-slate-800 border border-slate-700 w-full max-w-lg rounded-2xl p-6 shadow-2xl">
        <div className="flex justify-between items-center border-b border-slate-700 pb-4">
          <h2 className="text-xl font-bold text-white">Complete Purchase</h2>
          <div
            className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-bold ${
              isExpired
                ? "bg-rose-900/50 text-rose-300"
                : "bg-amber-900/40 text-amber-300 border border-amber-700/50"
            }`}
          >
            <Timer size={14} />
            {isExpired
              ? "EXPIRED"
              : `${minutes}:${seconds < 10 ? `0${seconds}` : seconds}`}
          </div>
        </div>

        {/* Order Details */}
        <div className="py-4 space-y-3">
          <div className="flex justify-between text-sm text-slate-300">
            <span>Order Reference:</span>
            <span className="font-mono text-white">#{order.id}</span>
          </div>
          <div className="flex justify-between text-sm text-slate-300">
            <span>Total Payable:</span>
            <span className="font-bold text-emerald-400 font-mono text-lg">
              ${Number(order.total_amount).toFixed(2)}
            </span>
          </div>
          {/* <div className="text-xs text-slate-400 bg-slate-900 p-2.5 rounded-lg border border-slate-800 flex items-center gap-2">
            <ShieldCheck size={14} className="text-indigo-400 shrink-0" />
            <span className="truncate">
              Idempotency-Key:{" "}
              <span className="font-mono text-slate-200">{idempotencyKey}</span>
            </span>
          </div> */}
        </div>

        {/* Payment Outcome Simulator */}
        {/* {!paymentResult && !isExpired && (
          <div className="bg-slate-900/70 border border-slate-700/60 p-4 rounded-xl space-y-3 my-2">
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Simulate Gateway Response
            </label>
            <div className="grid grid-cols-3 gap-2">
              {(["SUCCESS", "FAILURE", "TIMEOUT"] as PaymentOutcome[]).map(
                (mode) => (
                  <button
                    key={mode}
                    type="button"
                    onClick={() => setOutcome(mode)}
                    className={`py-2 text-xs font-bold rounded-lg border transition-all ${
                      outcome === mode
                        ? mode === "SUCCESS"
                          ? "bg-emerald-600 border-emerald-400 text-white"
                          : mode === "FAILURE"
                            ? "bg-rose-600 border-rose-400 text-white"
                            : "bg-amber-600 border-amber-400 text-white"
                        : "bg-slate-800 border-slate-700 text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {mode}
                  </button>
                ),
              )}
            </div>
          </div>
        )} */}

        {/* Results Feedback */}
        {paymentResult && (
          <div
            className={`p-4 rounded-xl my-4 border flex items-start gap-3 ${
              paymentResult.order_status === "PAID"
                ? "bg-emerald-950/40 border-emerald-600/50 text-emerald-200"
                : paymentResult.payment.status === "TIMEOUT"
                  ? "bg-amber-950/40 border-amber-600/50 text-amber-200"
                  : "bg-rose-950/40 border-rose-600/50 text-rose-200"
            }`}
          >
            {paymentResult.order_status === "PAID" ? (
              <CheckCircle
                size={20}
                className="text-emerald-400 shrink-0 mt-0.5"
              />
            ) : paymentResult.payment.status === "TIMEOUT" ? (
              <AlertTriangle
                size={20}
                className="text-amber-400 shrink-0 mt-0.5"
              />
            ) : (
              <XCircle size={20} className="text-rose-400 shrink-0 mt-0.5" />
            )}
            <div>
              <p className="font-bold text-sm">{paymentResult.message}</p>
              <p className="text-xs opacity-80 mt-1">
                Final Status: {paymentResult.order_status}
              </p>
            </div>
          </div>
        )}

        {errorMessage && (
          <div className="p-3 bg-rose-950/40 border border-rose-700/50 rounded-xl text-rose-300 text-xs my-3">
            {errorMessage}
          </div>
        )}

        {/* Action Controls */}
        <div className="flex gap-3 mt-5">
          {!paymentResult ? (
            <>
              <button
                type="button"
                onClick={handleCancel}
                disabled={isProcessing || isCancelling}
                className="flex-1 py-2.5 px-4 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-slate-200 rounded-xl font-medium transition-colors text-sm"
              >
                {isCancelling ? "Releasing..." : "Release Hold & Cancel"}
              </button>
              <button
                onClick={handlePay}
                disabled={isProcessing || isExpired}
                className="flex-1 py-2.5 px-4 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-xl font-medium transition-colors text-sm shadow-lg shadow-emerald-600/20"
              >
                {isProcessing
                  ? "Authorizing..."
                  : `Submit Payment (${outcome})`}
              </button>
            </>
          ) : (
            <button
              onClick={onClose}
              className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-medium transition-colors text-sm"
            >
              Done
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
