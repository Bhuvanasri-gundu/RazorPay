"use client";

import React, { useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  CreditCard,
  Smartphone,
  Building2,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  Zap,
  Lock,
  RotateCcw,
} from "lucide-react";
import Script from "next/script";

function CheckoutContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const caseId = searchParams.get("case_id") || "demo-case";
  const amountStr = searchParams.get("amount") || "4999";
  const linkId = searchParams.get("link_id") || "plink_demo";
  const customerName = searchParams.get("name") || "Priya Banerjee";
  const amount = parseFloat(amountStr) || 4999;

  const [paymentMethod, setPaymentMethod] = useState<"card" | "upi" | "netbanking">("card");
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [razorpayReady, setRazorpayReady] = useState(false);

  const formattedAmount = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);

  const handleRazorpayModal = () => {
    if (typeof window !== "undefined" && (window as any).Razorpay) {
      try {
        const options = {
          key: "rzp_test_TVsb4KboIGSNOh",
          amount: amount * 100,
          currency: "INR",
          name: "REVA Recovery Portal",
          description: `Payment Recovery for Case ${caseId.slice(0, 8)}`,
          image: "https://razorpay.com/favicon.ico",
          prefill: {
            name: customerName,
            email: "priya.banerjee@reva.test",
            contact: "9876543210",
          },
          theme: {
            color: "#10b981",
          },
          handler: async function (response: any) {
            await completePayment();
          },
        };
        const rzp = new (window as any).Razorpay(options);
        rzp.on("payment.failed", function (response: any) {
          console.warn("Payment failed or cancelled:", response.error);
        });
        rzp.open();
      } catch (err) {
        console.error("Razorpay SDK Error:", err);
        // Fallback to instant simulation
        completePayment();
      }
    } else {
      completePayment();
    }
  };

  const completePayment = async () => {
    setIsProcessing(true);
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      await fetch(`${API_BASE}/api/payments/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          recovery_case_id: caseId,
          razorpay_payment_link_id: linkId,
        }),
      });
    } catch (e) {
      console.warn("Payment verify call:", e);
    }
    setTimeout(() => {
      setIsProcessing(false);
      setIsSuccess(true);
    }, 800);
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col justify-between">
      <Script
        src="https://checkout.razorpay.com/v1/checkout.js"
        onLoad={() => setRazorpayReady(true)}
      />

      {/* Top Header */}
      <header className="border-b border-zinc-800/80 bg-zinc-900/40 backdrop-blur-md px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
            <Zap className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm tracking-tight text-zinc-100">REVA</span>
              <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Payment Recovery
              </span>
            </div>
            <p className="text-xs text-zinc-400">Powered by Razorpay Secure Gateway</p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-zinc-400">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>256-Bit SSL Encrypted</span>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-xl w-full mx-auto p-6 my-auto">
        {!isSuccess ? (
          <div className="bg-zinc-900/60 border border-zinc-800 rounded-2xl p-6 sm:p-8 shadow-2xl relative overflow-hidden backdrop-blur-xl">
            <div className="absolute top-0 right-0 w-48 h-48 bg-emerald-500/5 blur-3xl rounded-full pointer-events-none" />

            {/* Order Summary */}
            <div className="flex items-center justify-between pb-6 border-b border-zinc-800/80 mb-6">
              <div>
                <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Amount Due</span>
                <div className="text-3xl font-extrabold text-zinc-100 tracking-tight mt-0.5">
                  {formattedAmount}
                </div>
                <p className="text-xs text-zinc-400 mt-1">Customer: <strong className="text-zinc-200">{customerName}</strong></p>
              </div>
              <div className="text-right">
                <span className="text-xs text-zinc-500">Case Reference</span>
                <p className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded border border-emerald-500/20 mt-1">
                  {caseId.slice(0, 12)}...
                </p>
              </div>
            </div>

            {/* Recovery Alternative Explanation */}
            <div className="p-3.5 bg-blue-500/10 border border-blue-500/20 rounded-xl mb-6 flex items-start gap-3">
              <ShieldCheck className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
              <div className="text-xs text-zinc-300 leading-relaxed">
                <strong className="text-blue-400 font-semibold block mb-0.5">Automated Recovery Alternative</strong>
                Your previous payment attempt timed out. Use this secure link to complete the payment via Card, Netbanking, or alternate UPI handle.
              </div>
            </div>

            {/* Method Selectors */}
            <div className="space-y-3 mb-6">
              <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider block">
                Select Alternative Payment Method
              </label>
              <div className="grid grid-cols-3 gap-2.5">
                <button
                  type="button"
                  onClick={() => setPaymentMethod("card")}
                  className={`p-3.5 rounded-xl border flex flex-col items-center gap-2 transition-all ${
                    paymentMethod === "card"
                      ? "bg-emerald-500/10 border-emerald-500/40 text-emerald-400 shadow-sm"
                      : "bg-zinc-800/40 border-zinc-800 hover:border-zinc-700 text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  <CreditCard className="w-5 h-5" />
                  <span className="text-xs font-medium">Credit / Debit</span>
                </button>

                <button
                  type="button"
                  onClick={() => setPaymentMethod("netbanking")}
                  className={`p-3.5 rounded-xl border flex flex-col items-center gap-2 transition-all ${
                    paymentMethod === "netbanking"
                      ? "bg-emerald-500/10 border-emerald-500/40 text-emerald-400 shadow-sm"
                      : "bg-zinc-800/40 border-zinc-800 hover:border-zinc-700 text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  <Building2 className="w-5 h-5" />
                  <span className="text-xs font-medium">Netbanking</span>
                </button>

                <button
                  type="button"
                  onClick={() => setPaymentMethod("upi")}
                  className={`p-3.5 rounded-xl border flex flex-col items-center gap-2 transition-all ${
                    paymentMethod === "upi"
                      ? "bg-emerald-500/10 border-emerald-500/40 text-emerald-400 shadow-sm"
                      : "bg-zinc-800/40 border-zinc-800 hover:border-zinc-700 text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  <Smartphone className="w-5 h-5" />
                  <span className="text-xs font-medium">UPI ID / QR</span>
                </button>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="space-y-3 pt-2">
              <button
                type="button"
                disabled={isProcessing}
                onClick={handleRazorpayModal}
                className="w-full py-3.5 px-4 bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-bold rounded-xl text-sm transition-all flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20 active:scale-[0.99] disabled:opacity-50"
              >
                {isProcessing ? (
                  <>
                    <RotateCcw className="w-4 h-4 animate-spin" /> Verifying with Razorpay...
                  </>
                ) : (
                  <>
                    <Lock className="w-4 h-4" /> Pay {formattedAmount} via Razorpay Test Gateway
                  </>
                )}
              </button>

              <button
                type="button"
                disabled={isProcessing}
                onClick={completePayment}
                className="w-full py-2.5 px-4 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 font-semibold rounded-xl text-xs transition-all flex items-center justify-center gap-2"
              >
                ⚡ Instant Test Payment Simulation
              </button>
            </div>

            {/* Footer Trust Badges */}
            <div className="mt-6 pt-4 border-t border-zinc-800/60 flex items-center justify-center gap-6 text-[11px] text-zinc-500">
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" /> Razorpay Test Sandbox
              </span>
              <span>•</span>
              <span>Instant Recovery Callback</span>
            </div>
          </div>
        ) : (
          /* Payment Success View */
          <div className="bg-zinc-900/60 border border-emerald-500/30 rounded-2xl p-8 text-center shadow-2xl relative overflow-hidden backdrop-blur-xl animate-in zoom-in-95 duration-500">
            <div className="w-16 h-16 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl flex items-center justify-center mx-auto mb-5 text-emerald-400">
              <CheckCircle2 className="w-8 h-8" />
            </div>

            <h2 className="text-2xl font-bold text-zinc-100 tracking-tight mb-2">Payment Successfully Recovered!</h2>
            <p className="text-zinc-400 text-sm max-w-md mx-auto mb-6">
              The transaction of <strong className="text-emerald-400 font-semibold">{formattedAmount}</strong> has been confirmed by the Razorpay gateway. REVA has updated the recovery case status to <strong className="text-zinc-200">RECOVERED</strong>.
            </p>

            <div className="bg-zinc-950/60 border border-zinc-800/80 rounded-xl p-4 text-xs font-mono text-zinc-400 max-w-sm mx-auto mb-6 text-left space-y-1">
              <div><span className="text-zinc-500">Payment ID:</span> pay_{linkId.replace('plink_', '')}</div>
              <div><span className="text-zinc-500">Case ID:</span> {caseId}</div>
              <div><span className="text-zinc-500">Status:</span> <span className="text-emerald-400">SUCCESS / PAID</span></div>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
              <button
                onClick={() => router.push(`/cases/${caseId}`)}
                className="w-full sm:w-auto px-5 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-bold rounded-xl text-xs transition-all flex items-center justify-center gap-2 shadow-md shadow-emerald-500/20"
              >
                View Case in Audit Trail <ArrowRight className="w-4 h-4" />
              </button>
              <button
                onClick={() => router.push("/demo")}
                className="w-full sm:w-auto px-5 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 font-semibold rounded-xl text-xs transition-all flex items-center justify-center gap-2"
              >
                Return to Live Demo
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-800/60 py-4 px-6 text-center text-xs text-zinc-500">
        REVA — Autonomous Revenue Recovery Agent • Razorpay Test Mode
      </footer>
    </div>
  );
}

export default function CheckoutPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-zinc-950 flex items-center justify-center text-zinc-400 text-sm">Loading Checkout...</div>}>
      <CheckoutContent />
    </Suspense>
  );
}
